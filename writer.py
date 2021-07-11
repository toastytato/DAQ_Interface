import nidaqmx
import numpy as np
from nidaqmx.constants import AcquisitionType, RegenerationMode
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from pyqtgraph.Qt import QtCore

# --- From DAQ Control --- #
from config import *


class RotationalFieldGenerator(QtCore.QObject):
    def __init__(self, writer):
        super().__init__()
        self.writer = writer
        self._frequency = 0
        self._voltage = 0
        self.num_channels = len(CHANNEL_NAMES)

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, value):
        self._frequency = value
        for ch in range(self.num_channels):
            self.writer.frequencies[ch] = self._frequency

    @property
    def voltage(self):
        return self.voltage

    @voltage.setter
    def voltage(self, value):
        self._voltage = value
        for ch in range(self.num_channels):
            self.writer.voltages[ch] = self._voltage

    def resume_signal(self):
        for ch in range(self.num_channels):
            self.writer.output_state[ch] = True
            self.writer.voltages[ch] = self._voltage
            self.writer.frequencies[ch] = self._frequency
            self.writer.shifts[ch] = (360 / self.num_channels) * ch

    def pause_signal(self):
        for ch in range(self.num_channels):
            self.writer.output_state[ch] = False


class SignalGeneratorBase(QtCore.QObject):
    """
    Used as debug signal generator to create a waveform while debugging to create waveforms
    without initializing NI method that can raise errors
    """

    new_data = QtCore.pyqtSignal(object)

    def __init__(
        self, voltages, frequencies, shifts, output_states, sample_rate, sample_size
    ):
        super().__init__()

        self.is_running = False

        self.num_channels = len(CHANNEL_NAMES)
        self.wave_gen = [WaveGenerator() for i in range(self.num_channels)]

        self.voltages = voltages
        self.frequencies = frequencies
        self.shifts = shifts
        self.output_state = output_states
        
        self.sample_rate = sample_rate  # resolution (signals/second)
        self.sample_size = sample_size  # buffer size sent on each callback

        self.timer = QtCore.QTimer()
        self.timer.setTimerType(QtCore.Qt.PreciseTimer)

        self.timer.timeout.connect(self.callback)

    @property
    def sample_size(self):
        return self._sample_size

    @sample_size.setter
    def sample_size(self, value):
        self._sample_size = value
        self.output_waveform = np.empty(shape=(self.num_channels, self.sample_size))

    # makes sure all waveforms start at the same place so phase shifts work as intended for multi-channel processes
    def realign_channel_phases(self):
        for i in range(self.num_channels):
            self.wave_gen[i].reset_counter()

    # callback for the Debug sig_gen to create signal and send to data reader
    def callback(self):
        for i in range(self.num_channels):
            if self.output_state[i]:
                self.output_waveform[i] = self.wave_gen[i].generate_wave(
                    self.voltages[i],
                    self.frequencies[i],
                    self.shifts[i],
                    self.sample_rate,
                    self.sample_size,
                )
            else:
                self.output_waveform[i] = np.zeros(self.sample_size)

        self.new_data.emit(self.output_waveform)

    def resume(self):
        print("Signal resumed")
        self.is_running = True
        self.output_state = [True for x in range(self.num_channels)]
        self.signal_time = 1000 * (self.sample_size / self.sample_rate)
        self.callback()
        self.timer.start(self.signal_time)

    def pause(self):
        print("Signal paused")
        self.is_running = False
        self.output_state = [False for x in range(self.num_channels)]
        self.callback()
        self.timer.stop()

    def end(self):
        self.is_running = False
        self.timer.stop()


class SignalWriterDAQ(SignalGeneratorBase):
    def __init__(
        self,
        voltages,
        frequencies,
        shifts,
        output_states,
        sample_rate,
        sample_size,
        channels,
        dev_name="Dev1",
    ):
        super().__init__(
            voltages,
            frequencies,
            shifts,
            output_states,
            sample_rate,
            sample_size,
        )
        
        self.output_channels = channels
        self.daq_out_name = dev_name

    # create the NI task for writing to DAQ
    def create_task(self):
        try:
            self.task = nidaqmx.Task()
        except OSError:
            print("DAQ is not connected, task could not be created")
            return

        for ch in self.output_channels:
            channel_name = self.daq_out_name + "/ao" + str(ch)
            self.task.ao_channels.add_ao_voltage_chan(channel_name)

        signals_in_buffer = 4
        buffer_length = self.sample_size * signals_in_buffer
        self.task.timing.cfg_samp_clk_timing(
            rate=self.sample_rate,
            samps_per_chan=buffer_length,
            sample_mode=AcquisitionType.CONTINUOUS,
        )

        self.task.out_stream.regen_mode = RegenerationMode.DONT_ALLOW_REGENERATION
        # apparently the samps_per_chan doesn't do much for buffer size
        self.task.out_stream.output_buf_size = buffer_length

        print("Regeneration mode is set to: " + str(self.task.out_stream.regen_mode))

        print("Voltage is: ", self.voltages, " -- Frequency is: ", self.frequencies)

        self.writer = AnalogMultiChannelWriter(self.task.out_stream)

        # fill the buffer
        self.callback()
        self.callback()

    def callback(self):
        # print("Writing wave to task {} at {} V, {} Hz".format(self.output_state, self.voltages, self.frequencies))
        super().callback()
        self.writer.write_many_sample(self.output_waveform)

    def resume(self):
        self.callback() # extra callback to fill DAQ buffer
        super().resume()

    def pause(self):
        super().pause()
        self.task.stop()

    def end(self):
        super().end()
        self.task.close()


# creates the sine wave to output
class WaveGenerator:
    def __init__(self):
        self.reset = False
        self.counter = 0
        self.last_freq = 0
        self.output_times = []

    def reset_counter(self):
        self.reset = True

    def generate_wave(self, voltage, frequency, shift, sample_rate, samples_per_chunk):
        """

        :param voltage: RMS voltage, which will be converted to amplitude in signal
        :param frequency: Determines if AC or DC. Frequency of signal in Hz if not 0, creates DC signal if frequency is 0
        :param shift: The phase shift in degrees
        :param sample_rate: # of data points per second
        :param samples_per_chunk: # of data points that will be written in this output buffer
        :return: np.array with waveform of input params

        """

        # return DC voltage if frequency is 0
        if frequency == 0:
            return np.full(shape=samples_per_chunk, fill_value=voltage)

        # determine if it needs to shift frequency based on which part of the waveform it's on
        if self.last_freq != frequency or self.reset:
            self.reset = False
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

        # phase shift based on parameter
        phase_shift = 2 * np.pi * shift / 360

        # shift the frequency if starting in the middle of a wave
        start_fraction = waves_per_chunk % 1
        freq_shifter = self.counter * 2 * np.pi * start_fraction

        self.output_times = np.linspace(
            start=0, stop=sec_per_chunk, num=samples_per_chunk
        )
        output_waveform = amplitude * np.sin(
            self.output_times * rad_per_sec + freq_shifter - phase_shift
        )

        return output_waveform

    # less used
    def generate_n_periods(self, voltage, frequency, shift, sample_rate, num=1):
        amplitude = np.sqrt(2) * voltage  # get peak voltage from RMS voltage

        rad_per_sec = 2 * np.pi * frequency
        samples_per_period = int(sample_rate / rad_per_sec)

        phase_shift = 2 * np.pi * shift / 360

        self.output_times = np.linspace(
            start=0, stop=num / frequency, num=samples_per_period * num
        )
        output_waveform = amplitude * np.sin(
            self.output_times * rad_per_sec - phase_shift
        )
        return output_waveform


if __name__ == "__main__":
    print("\nRunning demo for SignalWriter\n")

    voltage = input("Input Voltage: ")
    frequency = input("Input Frequency: ")