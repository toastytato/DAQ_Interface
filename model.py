import nidaqmx
import time
import math
import matplotlib.pyplot as plt


# TODO: get values function
#       connect to NI instruments

MAX_VALUES = 30     # num of datapoints in view
TIME_WINDOW = 3     # viewing frame time in seconds

def out_voltage():
    with nidaqmx.Task() as task:
        task.ao_channels.add_ao_voltage_chan('cDAQ1Mod2/ao0')   # voltage channel 1
        print('1 Channel 1 Sample Write: ')
        print(task.write(1.0))


class ChannelData:
    def __init__(self, period):
        self.t_interval = period/1000
        self.voltage_set = 0

        self.time_init = time.time()
        self.times = [time.time() - self.time_init]  # time counter
        self.setpoints = [self.voltage_set]   # setpoint values
        self.inputs = [float()]   # values from input

    def update_values(self, data_in=0):
        self.times.append(time.time() - self.time_init)
        self.inputs.append(2*math.sin(3*data_in*self.times[-1])+3)
        self.setpoints.append(self.voltage_set)

        if (self.times[-1] - self.times[0]) >= TIME_WINDOW:
            self.times.pop(0)
            self.inputs.pop(0)
            self.setpoints.pop(0)
