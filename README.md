# µMD1 Python Interface

This code is host Python code for the [Micro Measurement Display 1, or µMD1](http://www.repairfaq.org/sam/uMD1/).


## Hardware Setup

Hardware setup is out of scope for this project and document. See:

* [µMD1 page](http://www.repairfaq.org/sam/uMD1/)
* [Other Links on Manuals Page](https://www.repairfaq.org/sam/manuals/)

Note that the hardware automatically detects if you are in single-axis mode or multi-axis mode.

## Usage

todo

## Tech Notes


### Data Format

The data returns as a ASCII that continuously spits out the serial port. The format is described as this (from [µMD1 page](http://www.repairfaq.org/sam/uMD1/)).


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

Note that the data will rapidly overload a serial port buffer, so a receiving thread is needed to keep up.