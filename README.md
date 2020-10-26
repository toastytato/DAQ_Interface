# DAQ_Interface
GUI for controlling NI DAQ devices and monitoring output/input voltages, current, and other variables

## Installation
For standalone application, just download main.exe in the 'dist'.
Run the main.exe file in 'dist' to launch the program.

## Usage
For purposes of debugging, the interface will not output to the DAQ during debugging mode or else the program will crash.
To test output values, switch to normal mode in the 'Debug Menu' section and if doesn't crash, it should have detected
the NIDAQ devices. 

DEBUGGING:
The sliders change the input values, and output values doesn't affect external devices

NORMAL:
The debug sliders are deactivated, and the output sliders now affect the external devices
Inputs should be reading from external devices as well. 