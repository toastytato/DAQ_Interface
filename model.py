import time

import nidaqmx
import numpy as np
from nidaqmx.constants import AcquisitionType
from nidaqmx.system import System

from constants import *


# MODEL: handles backend of the program
# contains data containers as well as helper functions for output to DAQ


def find_ni_devices():
    system = System.local()
    dev_name_list = []
    for device in system.devices:
        assert device is not None
        # device looks like "Device(name=cDAQ1Mod1)"
        dev_name = str(device).replace(')', '').split('=')[1]
        dev_name_list.append(dev_name)
    return str(dev_name_list)


# helper functions
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
    return volt / CURRENT_SHUNT_RESISTANCE


# Holds the data for plotting to the graph
class ChannelInterfaceData:
    def __init__(self):
        self.time_init = time.time()
        self.inputs = []  # values from input
        self.input_times = []  # time counter
        self.outputs = []  # setpoint values
        self.output_times = []

    def append_graph_inputs(self, sensor_val):
        curr_time = time.time() - self.time_init
        self.input_times.append(curr_time)
        self.inputs.append(sensor_val)
        while self.input_times[-1] - self.input_times[0] >= TIME_WINDOW:
            self.input_times.pop(0)
            self.inputs.pop(0)

    def append_graph_outputs(self, output_val):
        curr_time = time.time() - self.time_init
        self.output_times.append(curr_time)
        self.outputs.append(output_val)
        while self.output_times[-1] - self.output_times[0] >= TIME_WINDOW:
            self.output_times.pop(0)
            self.outputs.pop(0)


# Handles the input and output to the DAQ for each channel
class ChannelIO:
    def __init__(self, channel):
        self.channel = channel
        self.output_buffer = []
        self.output_samples = []

        self.sampling_rate = int(44100)
        # samples_in_window = 1 * 44100
        self.graph_times = [0]
        self.graph_outputs = [0]

        self.time = time.time()
        self.time_prev = time.time()

    def dc_out(self, voltage):
        path = "Dev1/ao" + str(self.channel)
        print(path)
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(path)
            print(task.write(voltage))

    # generates a sin wave to output to the DAQ
    # continues the frequency with signals up till the polling period
    # at the end of polling period ac_out should be called again
    # this should create a continuous variable frequency signal
    def ac_out(self, voltage, frequency, debug):
        try:
            signal_time = (1 / POLLING_RATE) * 1.5  # 1/frequency  # period of the sin wave
        except ZeroDivisionError:
            signal_time = 0

        if signal_time < 1:
            samples_per_signal = int(signal_time * self.sampling_rate)  # number of signals in buffer
        else:
            samples_per_signal = self.sampling_rate  # preventing excess samples in buffer when frequency is low
        # try:
        #     phase = self.output_samples[-1] % (2 * np.pi)
        # except IndexError:
        #     phase = 0

        amplitude = np.sqrt(2) * voltage  # get peak voltage from RMS voltage
        w = 2 * np.pi * frequency

        self.time = time.time() - self.time_prev
        # print(self.time)
        self.output_samples = np.linspace(self.time, self.time + signal_time, num=samples_per_signal)
        self.output_buffer = amplitude * np.sin(self.output_samples * w)

        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan('Dev1/ao' + str(self.channel))
            task.timing.cfg_samp_clk_timing(rate=self.sampling_rate,
                                            sample_mode=AcquisitionType.CONTINUOUS,
                                            samps_per_chan=samples_per_signal)
            analog_writer = nidaqmx.stream_writers.AnalogSingleChannelWriter(task.out_stream, auto_start=True)
            analog_writer.write_many_sample(self.output_buffer)
            # task.wait_until_done()
        # self.extend_graph_outputs()

    def extend_graph_outputs(self):
        last_end = len(self.graph_times) - 1
        for i, t in enumerate(self.output_samples):
            if t > self.graph_times[last_end]:
                self.graph_times.append(t)
                self.graph_outputs.append(self.output_buffer[i])
                if self.graph_times[-1] - self.graph_times[0] > TIME_WINDOW:
                    self.graph_times.pop(0)
                    self.graph_outputs.pop(0)

        print(self.output_buffer)

    def analog_in(self):
        # Same as above, change as needed
        # path = "Dev2/ai" + str(self.channel)
        # with nidaqmx.Task() as task:
        #     task.ai_channels.add_ai_voltage_chan(path)
        #     input = task.read()
        #     print(input[0])
        #     return input
        return 0
