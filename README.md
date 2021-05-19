# DAQ_Interface

GUI for controlling NI DAQ devices and monitoring output/input voltages in multiple channels

(![Screenshot of software as of 5/17/2021](https://github.com/toastytato/DAQ_Interface/blob/master/examples/daq_channels.png?raw=true)
)

## Installation

~~For standalone application, just download main.exe in the 'dist' and run the file.~~ <br/>

~~Recommended to use Python 3.7.8 (able to run on Windows Vista)~~ <br/>
~~Install NI DAQ API and Matplotlib version 3.2.2 (stability issues with newer version)~~ <br/>

~~Use PyQt5 version 5.9.2 to work on Windows Vista~~ <br/>

For newer machines, install Python 3.8.9 and the following modules:

```
pip install nidaqmx
pip install pyqt5
pip install pyqtgraph
```

Run pyqt_main.py and the interface should show up.

### Debug

There are two states for the interface, debug or not. Use debug when the National Instruments DAQ device is not connected to the PC, and all signal generated will be simulated. This is to prevent the nidaqmx library from
throwing errors. To change this, go into the config.py file and change the variable DEBUG_MODE to **True**. If DAQ is connected, set as **False**

## Usage

There is a graph/legend, master start/stop button, and a tab layout within the interface. Press the master start/stop button to start and stop all signals. The explanation of the tabs are as follows:

### **DAQ Settings**

This is where the device name, channel configurations, and sample rate/size is set for both input and output DAQs.

- Device Name: Name assigned to the DAQ. By default the output DAQ is Dev1 and input DAQ is Dev2.
- Sample Rate: The number of samples per second both the writer and reader will write/read per second.
- Sample Size: The number of samples the DAQ will write/read in each pass
- X/Y/Z Output Channel: The channel with which the DAQs will read/write from for the corresponding name.
  - The name assigned to each channel can be changed by going into config.py and changing strings inside the CONFIG_NAMES variable.
- Commit Settings: This button saves and updates the current configuration to the applied settings. Will restart the DAQ write and read process.

### **Channel Controls**

This is where each channel can be independently controlled.

- Toggle Output: Turns the channel on/off
- Voltage RMS: Sets the RMS voltage of the channel (Not amplitude)
- Frequency/Phase: <-- it does that

### **Main Controls**

This is where synchronous channel manipulations are controlled.

- **Rotating Field**: Generates a polyphase wave where each wave is equally phase shifted from each other.

## To-Do

- Update channels in legend when settings are committed
- ???

## Credits

This application uses Open Source components. You can find their source code below:

Project: MuControl <br/>
Link: https://github.com/czimm79/MuControl-release/blob/master/LICENSE.txt

Project: Python DAQmx examples <br/>
Link: https://github.com/tenss/Python_DAQmx_examples/blob/master/LICENSE

## License

[GNU Public License v3](https://www.gnu.org/licenses/gpl-3.0.html)
