import nidaqmx
import numpy as np
from nidaqmx.constants import AcquisitionType, RegenerationMode
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from pyqtgraph.Qt import QtCore

# --- From DAQ Control --- #
from config import CHANNEL_NAMES_OUT
from misc_functions import *


class MagneticControlBase(QtCore.QObject):
    def __init__(
        self, writer, state, phi, theta, amplitude, frequency, kx=1, ky=1, kz=2
    ):
        super().__init__()
        self.writer = writer
        self.num_channels = len(CHANNEL_NAMES_OUT)

        self.output_state = state
        print(state)
        self.phi = phi
        self.theta = theta
        self.amplitude = amplitude
        self.frequency = frequency
        self.kx = kx
        self.ky = ky
        self.kz = kz

        self.voltages = [0, 0, 0]

        if self.num_channels != 3:
            print("Not enough write channels for 3D Magnetic Field Control!")

    def update_params(self):
        self.writer.voltages = self.voltages
        self.frequency = self._frequency

    @property
    def output_state(self):
        return self._output_state

    @output_state.setter
    def output_state(self, value):
        self._output_state = value
        self.writer.output_states[0] = self.output_state
        self.writer.output_states[1] = self.output_state
        self.writer.output_states[2] = self.output_state

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, value):
        self._frequency = value
        for ch in range(self.num_channels):
            self.writer.frequencies[ch] = self.frequency

    def resume_signal(self):
        for ch in range(self.num_channels):
            self.writer.output_state[ch] = self.output_state

    def pause_signal(self):
        for ch in range(self.num_channels):
            self.writer.output_state[ch] = False


class MagneticAlignment(MagneticControlBase):
    def __init__(self, writer, state, phi, theta, amplitude, frequency, kx, ky, kz):
        super().__init__(
            writer, state, phi, theta, amplitude, frequency, kx=kx, ky=ky, kz=kz
        )

    def update_params(self):
        # get voltages ( / sqrt(2) to convert to RMS)
        self.voltages[0] = (
            self.kx * self.amplitude * cos(self.phi) * cos(self.theta) / np.sqrt(2)
        )
        self.voltages[1] = (
            self.ky * self.amplitude * cos(self.phi) * sin(self.theta) / np.sqrt(2)
        )
        self.voltages[2] = self.kz * self.amplitude * sin(self.phi) / np.sqrt(2)

        self.writer.shifts[0] = 0
        self.writer.shifts[1] = 0
        self.writer.shifts[2] = 0

        super().update_params()


class MagneticRotation(MagneticControlBase):
    def __init__(self, writer, state, phi, theta, amplitude, frequency, kx, ky, kz):
        super().__init__(
            writer, state, phi, theta, amplitude, frequency, kx=kx, ky=ky, kz=kz
        )

    def update_params(self):
        # get voltages ( / sqrt(2) to convert to RMS)
        self.voltages[0] = self.kx * self.amplitude * cos(self.phi) / np.sqrt(2)
        self.voltages[1] = self.ky * self.amplitude * cos(self.phi) / np.sqrt(2)
        self.voltages[2] = self.kz * self.amplitude * sin(self.phi) / np.sqrt(2)

        self.writer.shifts[0] = 0
        self.writer.shifts[1] = self.writer.shifts[0] - 90
        self.writer.shifts[2] = self.theta

        super().update_params()


class SignalGeneratorBase(QtCore.QObject):
    """
    Used as debug signal generator to create a waveform while debugging to create waveforms
    without initializing NI method that can raise errors
    """

    # uses generated waveform as simulated input data
    incoming_data = QtCore.pyqtSignal(object)

    def __init__(
        self, voltages, frequencies, shifts, output_states, sample_rate, sample_size
    ):
        super().__init__()

        self.is_running = False

        self.num_channels = len(CHANNEL_NAMES_OUT)
        self.wave_gen = [WaveGenerator() for i in range(self.num_channels)]

        self.voltages = voltages
        self.frequencies = frequencies
        self.shifts = shifts
        self.output_states = output_states

        # TODO: change ability to dynamically change sample rate/size in UI settings
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

    def on_offsets_received(self, data):
        self.offsets = data

    # callback for the Debug sig_gen to create signal and send to data reader
    def callback(self):
        for i in range(self.num_channels):
            if self.output_states[i]:
                self.output_waveform[i] = self.wave_gen[i].generate_wave(
                    self.voltages[i],
                    self.frequencies[i],
                    self.shifts[i],
                    self.sample_rate,
                    self.sample_size,
                )
            else:
                self.output_waveform[i] = np.zeros(self.sample_size)

        # use as debug simulated input signal
        self.incoming_data.emit(self.output_waveform)

    def resume(self):
        print("Signal resumed")
        self.is_running = True
        self.output_states = [True for x in range(self.num_channels)]
        self.signal_time = 1000 * (self.sample_size / self.sample_rate)
        self.callback()
        self.timer.start(self.signal_time)

    def pause(self):
        print("Signal paused")
        self.is_running = False
        self.output_states = [False for x in range(self.num_channels)]
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
        super().callback()
        self.writer.write_many_sample(self.output_waveform)

    def resume(self):
        self.callback()  # extra callback to fill DAQ buffer
        super().resume()  # start timer
        self.task.start()  # start task

    # TODO: bug with this not setting output to 0 when DAQ is hooked up
    def pause(self):
        super().pause()
        self.task.stop()

    def end(self):
        super().end()
        self.task.close()


if __name__ == "__main__":
    print("\nRunning demo for SignalWriter\n")

    voltage = input("Input Voltage: ")
    frequency = input("Input Frequency: ")
