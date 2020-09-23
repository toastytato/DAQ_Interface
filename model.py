import nidaqmx
import time
import math
import matplotlib.pyplot as plt


# TODO: get values function
#       connect to NI instruments

MAX_VALUES = 30     # num of datapoints in view
TIME_WINDOW = 2     # viewing frame time in seconds

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
        self.inputs = [float()]   # values from input
        self.input_times = [time.time() - self.time_init]  # time counter
        self.setpoints = [float()]   # setpoint values
        self.setpoint_times = [time.time() - self.time_init]

    def update_inputs(self, sensor_val):
        self.input_times.append(time.time() - self.time_init)
        self.inputs.append(math.sin(self.input_times[-1]-sensor_val) + 3)
        # print(self.inputs)
        if (self.input_times[-1] - self.input_times[0]) >= TIME_WINDOW:
            self.input_times.pop(0)
            self.inputs.pop(0)

    def update_setpoints(self, setpoint):
        self.setpoint_times.append(time.time() - self.time_init)
        self.setpoints.append(setpoint)

        if (self.setpoint_times[-1] - self.setpoint_times[0]) >= TIME_WINDOW:
            self.setpoint_times.pop(0)
            self.setpoints.pop(0)
