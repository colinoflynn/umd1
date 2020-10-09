from serial import *
from threading import Thread
from collections import deque

displacementx = 0
displacementy = 0
displacementz = 0

"""
 Standard (Single Axis) Data (8 values):

   0: REF Frequency Count = REF frequency/Sample Frequency
   1: MEAS Frequency Count 1 = MEAS 1 frequency/Sample Frequency
   2: Displacement 1 ( in 1/2, 1/4, or 1/8 wavelength)
   3: Velocity Count 1 = (Displacement 1 - Previous Displacement 1)/Sample Frequency
   4: Phase 1 = Signed fractional offset between Displacement increments * 256

      If Phase is not valid, then an error code is sent instead:

        0x200 = no counter 1st REF
        0x400 = no counter 2nd REF
        0x800 = no counter MEAS 1
        0x1000 = no PORTB 1st REF
        0x2000 = no PORTB 2nd REF
        0x4000 = no PORTB MEAS 1

   5: Sequence Number (Unique serial number for each sample)
   6: LowSpeedCode (See below)
   7: LowSpeedData (see below)
 
   The following 8 values will also be sent when Multiple Axis Mode is active:

   8: MEAS Frequency Count 2
   9: Displacement 2
  10: Velocity Count 2
  11: Phase 2
  12: MEAS Frequency Count 3
  13: Displacement 3
  14: Velocity Count 3
  15: Phase 3

  LowSpeedCode (specifies contents of LowSpeedData):

     0-99: GUI Data/Control:

      0: No Data
      1: Laser Power
      2: Signal Strength
      3: Temperature 1 (XXX.YY, °C, 0 to 70.00)
      4: Temperature 2 (XXX.YY, °C, 0 to 70.00)
      5: Pressure (XXX.YY mBar, 500.00 to 2000.00)
      6: Humidity (XXX.Y percent, 0 to 100.0)

      8: Sample Frequency (XXX.YY Hz)

     10: Firmware Version (XXX.YY)

     20: Homodyne Interferometer (if non-zero)
          Low byte: # homodyne axes
          Next byte: counts/cycle (4 for quadpulse)

     (Not all of these are currently implemented.)

   100-199: Diagnostics

   200-255: Reserved
"""

def phase_error(phase):
    """ Convert a phase measurement into error string if relevant"""
    if phase < 256:
        return None
    
    phase_errors = "#1 ERRORS: "
    
    if phase & 0x200:
        phase_errors += "no counter 1st REF, "
    
    if phase & 0x400:
        phase_errors += "no counter 2nd REF, "
    
    if phase & 0x800:
        phase_errors += "no counter MEAS 1, "
    
    if phase & 0x1000:
        phase_errors += "no PORTB 1st REF, "
    
    if phase & 0x2000:
        phase_errors += "no PORTB 2nd REF, "
    
    if phase & 0x4000:
        phase_errors += "no PORTB MEAS 1, "
        
    return phase_errors


def decode_line(line, allow2=False, allow3=False):
    """Decode a line into a displacement measurement"""

    displacement1 = None
    displacement2 = None
    displacement3 = None

    if len(line) < 10:
        raise ValueError("Invalid input length: " + str(line) + " is too small.")
        
    values = line.split(b" ")
    
    if len(values) != 8 and len(values) != 16:
        raise IOError("Invalid line " + str(line) + ": Only " + str(len(values)) + "items  detected.")
    
    ref_freq_count = int(values[0])
    meas_freq_count = int(values[1])
    displacement1 = int(values[2])
    phase1 = int(values[4])
    if phase1 & 0x100:
        phase1 = -(phase1 & 0xFF)
    
    seq_no = int(values[5])
    lowspeedcode = int(values[6])
    lowspeeddata = str(values[7])
    
    if (len(values) == 16) and ((allow2 == True) or (allow3 == True)):
    
        if allow2:
            meas2_freq_count = int(values[8])
            displacement2 = int(values[9])
            phase2 = int(values[11])
            
            if phase2 & 0x100:
                phase2 = -(phase2 & 0xFF)
                
            if phase_error(phase2):
                print(phase_error(phase2))
                displacement2 = None
        
        if allow3:
            meas3_freq_count = int(values[12])
            displacement3 = int(values[13])
            phase3 = int(values[15])
            
            if phase3 & 0x100:
                phase3 = -(phase3 & 0xFF)
            
            if phase_error(phase3):
                print(phase_error(phase3))
                displacement3 = None
    
    if phase_error(phase1):
        print(phase_error(phase1))
        phase1 = None
        displacement1 = None
    
    #Interpolate with phase if possible
    if displacement1 and phase1:
        displacement1 += (phase1 / 256.0)

    if displacement2 and phase2:
        displacement2 += (phase2 / 256.0)
        
    if displacement3 and phase3:
        displacement3 += (phase3 / 256.0)

    #Uncomment for debug
    #if lowspeedcode == 10:
    #    print("FW Version: " + lowspeeddata)
    
    return displacement1, displacement2, displacement3


class UMD1(object):

    def __init__(self, comport, enable1=True, enable2=False, enable3=False):
        self.ser = Serial(
            port="COM62",
            baudrate=115200,
            timeout=0.1)

        ser.write(b"\r\n")
        
        
    def start_thread(self):
        self.thread = Thread(target=ReceivingThread, args=(self.ser,))
        self.thread.daemon = True
        self.thread.start()

class MovingAverage(deque):
    """ Standard `deque` class with addition of an `avg()` function"""

    def avg(self):
        """Return average of all elements in the deque"""
        return sum(self) / float(len(self))

def ReceivingThread(ser):
    """Thread for talking to the serial port"""

    global displacement1
    global displacement2
    global displacement3
    
    running = True
    
    displacementbase = 158.25E-9
    
    displacement1q = MovingAverage(maxlen=10)
    displacement2q = MovingAverage(maxlen=10)
    displacement3q = MovingAverage(maxlen=10)

    buffer = b''

    while running:

        buffer += ser.read(ser.inWaiting())
        if b'\r\n' in buffer:
            last_received, buffer = buffer.split(b'\r\n')[-2:]
            
            displacement1, displacement2, displacement3 = decode_line(last_received)
            
            if displacement1:
                displacement1 *= displacementbase
                displacement1q.append(displacement1)
                displacement1 = displacement1q.avg()
            
            if displacement2:
                displacement2 *= displacementbase
                displacement2q.append(displacement2)
                displacement2 = displacement2q.avg()
            
            if displacement3:
                displacement3 *= displacementbase
                displacement3q.append(displacement3)
                displacement3 = displacement3q.avg()

if __name__ == '__main__':

    um1 = UMD1()
    
    um1.start_thread()

    while True:
        time.sleep(1)
        print(displacement1 * 1000.0)
        if displacement2:
            print(displacement2 * 1000.0)
        #if displacement3:
        #    print(displacement3 * 1000.0)
   

if __name__ ==  '_2_main_2_':

    print("Rocking...")

    ser = Serial(

        port="COM62",

        baudrate=115200,

        bytesize=EIGHTBITS,

        parity=PARITY_NONE,

        stopbits=STOPBITS_ONE,

        timeout=0.1,

        xonxoff=0,

        rtscts=0,

        interCharTimeout=None

    )
    
    ser.write(b"\r\n")

    Thread(target=ReceivingThread, args=(ser,)).start()
    
    while True:
        time.sleep(1)
        print(displacement1 * 1000.0)
        if displacement2:
            print(displacement2 * 1000.0)
        #if displacement3:
        #    print(displacement3 * 1000.0)
   