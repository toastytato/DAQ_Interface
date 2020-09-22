import nidaqmx
import matplotlib.pyplot as plt


# TODO: get values function
#       connect to NI instruments

def out_voltage():
    with nidaqmx.Task() as task:
        task.ao_channels.add_ao_voltage_chan('cDAQ1Mod2/ao0')   # voltage channel 1
        print('1 Channel 1 Sample Write: ')
        print(task.write(1.0))