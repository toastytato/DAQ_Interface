import nidaqmx
import matplotlib.pyplot as plt


# TODO: get values function
#       connect to NI instruments

MAX_VALUES = 30


def out_voltage():
    with nidaqmx.Task() as task:
        task.ao_channels.add_ao_voltage_chan('cDAQ1Mod2/ao0')   # voltage channel 1
        print('1 Channel 1 Sample Write: ')
        print(task.write(1.0))


class ChannelData:
    def __init__(self, period):
        self.t_interval = period/1000
        self.voltage_set = 0
        self.times = [0]   # time counter
        self.setpoints = [self.voltage_set]   # setpoint values
        self.inputs = [0]   # values from input

    def update_values(self, input=0):
        self.inputs.append(input)
        self.setpoints.append(self.voltage_set)
        self.times.append(self.times[-1] + self.t_interval)

        if len(self.times) > MAX_VALUES:
            self.times.pop(0)
            self.inputs.pop(0)
            self.setpoints.pop(0)
