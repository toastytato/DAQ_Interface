import nidaqmx
import numpy as np
from nidaqmx.constants import AcquisitionType, RegenerationMode
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from pyqtgraph.Qt import QtCore

# --- From DAQ Control --- #
from constants import *


class SignalWriter(QtCore.QObject):

    def __init__(self, voltage, frequency, sample_rate, chunks_per_sec, dev_name='Dev1'):
        super().__init__()
        self.writer = None
        self.task_counter = 0

        self.is_running = False
        self.exit = False

        self.daq_out_name = dev_name
        self.signal_rate = sample_rate  # signals per second
        self.chunks_per_second = chunks_per_sec
        self.write_chunk_size = self.signal_rate // self.chunks_per_second
        # size of chunk to write (nearest floor integer)
        if len(voltage) != len(frequency):
            print("Error: voltage list size not the same as frequency list size")

        num_channels = len(voltage)
        self.wave_gen = [WaveGenerator() for i in range(num_channels)]
        self.output_waveform = np.empty(shape=(num_channels, self.write_chunk_size))

        self.voltage = voltage
        self.frequency = frequency

    # ---- DAQ Control method 3 based on meEEE ----

    def create_task(self):
        try:
            self.task = nidaqmx.Task()
        except OSError:
            print("DAQ is not connected, task could not be created")
            return

        channel_name = self.daq_out_name + "/ao0"
        self.task.ao_channels.add_ao_voltage_chan(channel_name)

        signals_in_buffer = 4
        buffer_length = self.write_chunk_size * signals_in_buffer
        self.task.timing.cfg_samp_clk_timing(rate=self.signal_rate,
                                             samps_per_chan=buffer_length,
                                             sample_mode=AcquisitionType.CONTINUOUS)

        self.task.out_stream.regen_mode = RegenerationMode.DONT_ALLOW_REGENERATION
        # self.task.out_stream.output_buf_size = buffer_length

        print("Regeneration mode is set to: " + str(self.task.out_stream.regen_mode))

        print("Voltage is: %.2f, Frequency is: %.2f Hz" % (self.voltage, self.frequency))

        self.writer = AnalogMultiChannelWriter(self.task.out_stream)

        # fill the buffer
        self.write_signal_to_buffer()

        self.timer = QtCore.QTimer()
        self.timer.setTimerType(QtCore.Qt.PreciseTimer)
        self.signal_time = 1000 / self.chunks_per_second
        self.timer.timeout.connect(self.write_signal_to_buffer)

        # start thread (calls self.run)
        self.start()

    def run(self):
        self.exec_()

    def write_signal_to_buffer(self):
        print("Writing wave to task")
        for i in range(NUM_CHANNELS):
            self.output_waveform[i] = self.wave_gen[i].generate_wave(self.voltage[i],
                                                                     self.frequency[i],
                                                                     self.signal_rate,
                                                                     self.write_chunk_size)
        try:
            self.writer.write_many_sample(self.output_waveform)
        except Exception as e:
            print("Error writing:")
            print(e)
            return

    def resume(self):
        print("Signal writer resumed")
        self.is_running = True
        # self.write_signal_to_buffer()
        self.timer.start(self.signal_time)
        self.task.start()

    def pause(self):
        print("Signal writer paused")
        self.is_running = False
        self.timer.stop()
        self.task.stop()

    def end(self):
        print("Signal writer stopped")
        self.is_running = False
        self.exit = True
        self.timer.stop()
        self.task.close()


class DebugSignalGenerator(QtCore.QObject):
    """
    Used as debug signal generator to create a waveform while debugging to create waveforms
    without initializing NI method that can raise errors
    """

    newData = QtCore.pyqtSignal(object)

    def __init__(self, voltage, frequency, sample_rate, sample_size):
        super().__init__()

        self.is_running = False
        self.event_trigger = False
        self.exit = False

        if len(voltage) != len(frequency):
            print("Error: voltage list size not the same as frequency list size")

        num_channels = len(voltage)
        self.voltage = voltage
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.sample_size = sample_size
        self.output = np.empty(shape=(num_channels, self.sample_size))

        self.wave_gen = [WaveGenerator() for i in range(num_channels)]

        self.timer = QtCore.QTimer()
        self.timer.setTimerType(QtCore.Qt.PreciseTimer)

        self.signal_time = 1000 * (self.sample_size / self.sample_rate)
        self.timer.timeout.connect(self.callback)

        print('Init doing stuff in:', QtCore.QThread.currentThread())

    def resume(self):
        print("Signal resumed")
        self.is_running = True
        self.callback()
        self.timer.start(self.signal_time)

    def pause(self):
        print("Signal paused")
        print('Slot doing stuff in:', QtCore.QThread.currentThread())

        self.is_running = False
        self.timer.stop()

    def callback(self):
        print("Callback called")
        for i in range(len(self.output)):
            self.output[i] = self.wave_gen[i].generate_wave(self.voltage[i],
                                                            self.frequency[i],
                                                            self.sample_rate,
                                                            self.sample_size)

        # print(self.output)
        print(self.output)
        self.newData.emit(self.output)

    def end(self):
        self.exit = True


# creates the sine wave to output
class WaveGenerator:
    def __init__(self):
        self.counter = 0
        self.last_freq = 0
        self.output_times = []

    def generate_n_periods(self, voltage, frequency, sample_rate, num=1):
        amplitude = np.sqrt(2) * voltage  # get peak voltage from RMS voltage

        rad_per_sec = 2 * np.pi * frequency
        samples_per_period = int(sample_rate / rad_per_sec)

        self.output_times = np.linspace(start=0,
                                        stop=num / frequency,
                                        num=samples_per_period * num)
        output_waveform = amplitude * np.sin(self.output_times * rad_per_sec)
        return output_waveform

    def generate_wave(self, voltage, frequency, sample_rate, samples_per_chunk):
        """

        :param voltage: RMS voltage, which will be converted to amplitude in signal
        :param frequency: Determines if AC or DC. Frequency of signal in Hz if not 0, creates DC signal if frequency is 0
        :param sample_rate: # of data points per second
        :param samples_per_chunk: # of data points that will be written in this output buffer
        :return: np.array with waveform of input params

        """
        if self.last_freq != frequency:
            self.counter = 0
            self.last_freq = frequency
        else:
            self.counter += 1

        amplitude = np.sqrt(2) * voltage  # get peak voltage from RMS voltage
        # waves_per_sec = frequency
        rad_per_sec = 2 * np.pi * frequency
        chunks_per_sec = sample_rate / samples_per_chunk
        sec_per_chunk = 1 / chunks_per_sec
        waves_per_chunk = frequency / chunks_per_sec

        # shift the frequency if starting in the middle of a wave
        start_fraction = waves_per_chunk % 1
        freq_shifter = self.counter * 2 * np.pi * start_fraction

        self.output_times = np.linspace(start=0, stop=sec_per_chunk, num=samples_per_chunk)
        output_waveform = amplitude * np.sin(self.output_times * rad_per_sec + freq_shifter)

        return output_waveform


if __name__ == '__main__':
    print('\nRunning demo for SignalWriter\n')

    voltage = input("Input Voltage: ")
    frequency = input("Input Frequency: ")

    writer = SignalWriter(voltage=voltage,
                          frequency=frequency,
                          sample_rate=1000,
                          chunks_per_sec=2)

    writer.start()

    input("Press return to stop")
    writer.end()

    # writer.stop_signal()

# # ---- DAQ Control method 1 based on MuControl ----
#
#     # tells thread to stop blocking and restart
#     def restart(self):
#         self.start_thread_flag.set()
#
#     # basically a one time call to start the write task
#     def run(self):
#         # first run, set start signal
#         self.restart()
#         # keep thread running
#         while True:
#             self.start_thread_flag.wait()
#             self.start_thread_flag.clear()
#             # checks flag for exiting thread
#             if self.exit is True:
#                 return
#
#             # flag for starting or ending nidaqmx.Task() object
#             self.is_running = True
#
#             print("Signal Writer Run")
#
#             try:
#                 self.task = nidaqmx.Task()  # Start the task
#                 self.task_counter += 1
#             except OSError:
#                 print("DAQ is not connected, task could not be created")
#                 continue
#
#             # Add input channels
#             for i in range(NUM_CHANNELS):
#                 channel_string = self.daq_out_name + '/' + f'ao{i}'
#                 try:
#                     print("Channel ", channel_string, " added to task ", self.task.name)
#                     self.task.ao_channels.add_ao_voltage_chan(channel_string)
#                 except Exception as e:
#                     if i == 0:
#                         print('Could not open write channels:')
#                         print(e)
#                         continue
#
#             print("Channel names: ", self.task.channel_names)
#
#             # Set the generation rate, and buffer size.
#             self.task.timing.cfg_samp_clk_timing(
#                 rate=self.signal_rate,
#                 sample_mode=AcquisitionType.CONTINUOUS)
#
#             # Set more properties for continuous signal modulation
#             self.task.out_stream.regen_mode = RegenerationMode.DONT_ALLOW_REGENERATION
#             self.task.out_stream.output_buf_size = 4 * self.write_chunk_size
#
#             # Register the listening method to add more data
#             try:
#                 self.task.register_every_n_samples_transferred_from_buffer_event(
#                     sample_interval=self.write_chunk_size,
#                     callback_method=self.callback)
#             except Exception as e:
#                 print("Problem with callback method:")
#                 print(e)
#                 continue
#
#             # Initialize the writer
#             self.writer = AnalogMultiChannelWriter(self.task.out_stream)
#
#             self.waveforms = self.package_waves(self.voltage, self.frequency, self.signal_rate, self.write_chunk_size)
#
#             # Write the first set of data into the output buffer
#             try:
#                 # Write two chunks of beginning data to avoid interruption
#                 self.writer.write_many_sample(data=self.waveforms)
#             except Exception as e:
#                 print("Could not write to channel:")
#                 print(e)
#                 continue
#
#             self.writer.write_many_sample(data=self.waveforms)
#             # start task, which will hold thread at this location continuously calling add_more_data
#             self.task.start()
#
#     # called by the task listener method
#     # won't get called when DAQ is not attached
#     def callback(self, task_handle, every_n_samples_event_type, number_of_samples, callback_data):
#         if self.is_running:
#             self.waveforms = self.package_waves(self.voltage, self.freq, self.write_chunk_size)
#             self.writer.write_many_sample(self.waveforms)
#         else:
#             print("closed write task")
#             self.task.close()
#
#         return 0
