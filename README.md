# DAQ_Interface
GUI for controlling NI DAQ devices and monitoring output/input voltages, current, and other variables

## Installation
For standalone application, just download main.exe in the 'dist' and run the file.

Recommended to use Python 3.7.8 (able to run on Windows Vista) <br/>
Install NI DAQ API and Matplotlib version 3.2.2 (stability issues with newer version)
```
pip install nidaqmx
pip install matplotlib==3.2.2
```

## Usage
Change the slider values to change output to DAQ hardware. Currently still debugging so some of the features are not present yet

## Credits
This application uses Open Source components. You can find their source code below:

Project: MuControl <br/>
Link: https://github.com/czimm79/MuControl-release/blob/master/LICENSE.txt

Project: Python DAQmx examples <br/>
Link: https://github.com/tenss/Python_DAQmx_examples/blob/master/LICENSE

## License
[GNU Public License v3](https://www.gnu.org/licenses/gpl-3.0.html)