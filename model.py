from nidaqmx.constants import AcquisitionType

from constants import *
import nidaqmx
import numpy as np
import time
import math

# contains data containers as well as helper functions for output to DAQ

out_prefix = "Dev1"
in_prefix = "Dev2"

def analog_out(channel, voltage):
    # CHANGE PATH: adjust the path name as needed
    # 'Dev1' is the name of the device connected to the computer
    # You can find this name in NI-MAX
    path = out_prefix + "/ao" + str(channel)
    print(path)
    with nidaqmx.Task() as task:
        task.ao_channels.add_ao_voltage_chan(path)
        print(task.write(voltage))

def ac_out(channel, voltage):
    with nidaqmx.Task() as task:
        task.ao_channels.add_ao_voltage_chan('Dev1/ao' + str(channel))
        # rate is samples/second
        # samps_per_chan is number of samples in the buffer
        task.timing.cfg_samp_clk_timing(rate=80, sample_mode=AcquisitionType.CONTINUOUS, samps_per_chan=40)

        analog_writer = nidaqmx.stream_writers.AnalogSingleChannelWriter(task.out_stream, auto_start=True)

        buffer = np.append(5 * np.ones(30), np.zeros(10))

        analog_writer.write_many_sample(buffer)
        task.wait_until_done()


def analog_in(channel):
    # Same as above, change as needed
    path = in_prefix + "/ai" + str(channel)
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(path)
        input = task.read()
        print(input[0])
        return input

def verify_input(input, min, max):
    input = float(input)
    if input > max:
        print("Entered value exceeded max value, set to max")
        return max
    elif input < min:
        print("Entered value below min value, set to min")
        return min
    else:
        return input

def voltage_to_current(volt):
    return volt/CURRENT_SHUNT_RESISTANCE


class ChannelData:
    def __init__(self):
        self.voltage_in = 0
        self.current_in = 0

        self.time_init = time.time()
        self.inputs = []   # values from input
        self.input_times = []  # time counter
        self.setpoints = []   # setpoint values
        self.setpoint_times = []

    def update_inputs(self, sensor_val):
        self.voltage_in = sensor_val
        self.current_in = self.voltage_in/CURRENT_SHUNT_RESISTANCE

        self.input_times.append(time.time() - self.time_init)
        self.current_in = sensor_val
        self.inputs.append(self.current_in)
        while self.input_times[-1] - self.input_times[0] >= TIME_WINDOW:
            self.input_times.pop(0)
            self.inputs.pop(0)

    def update_setpoints(self, setpoint):
        self.setpoint_times.append(time.time() - self.time_init)
        self.setpoints.append(setpoint)
        while self.setpoint_times[-1] - self.setpoint_times[0] >= TIME_WINDOW:
            self.setpoint_times.pop(0)
            self.setpoints.pop(0)

# //inputs
# //sinusoidal output
# #