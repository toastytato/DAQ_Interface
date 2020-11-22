import nidaqmx
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from nidaqmx.constants import AcquisitionType, RegenerationMode
from constants import *
import numpy as np
from threading import Thread, Event


class SignalWriter(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.writer = None
        self.task_counter = 0

        self.is_running = False
        self.exit = False
        self.start_thread_flag = Event()
        self.daq_out_name = 'Dev1'
        self.signal_rate = 8000  # signals per second
        self.chunks_per_second = 10
        self.write_chunk_size = self.signal_rate // self.chunks_per_second
        # size of chunk to write (nearest floor integer)
        self.WaveGen = [WaveGenerator()] * NUM_CHANNELS
        self.output = np.empty(NUM_CHANNELS)

        self.voltage = 0
        self.freq = 0
        self.mode = 'AC'
        self.task = []

    # ---- DAQ Control method 2 based on tenss_Python_DAQ_examples

    def create_task(self):
        try:
            self.task = nidaqmx.Task()
        except OSError:
            print("DAQ is not connected, task could not be created")
            return

        channel_name = self.daq_out_name + "/ao0"
        self.task.ao_channels.add_ao_voltage_chan(channel_name)

        buffer_length = self.write_chunk_size * 4
        self.task.timing.cfg_samp_clk_timing(rate=self.signal_rate,
                                             samps_per_chan=buffer_length,
                                             sample_mode=AcquisitionType.CONTINUOUS)

        self.task.out_stream.regen_mode = RegenerationMode.ALLOW_REGENERATION
        print("Regeneration mode is set to: " + str(self.task.out_stream.regen_mode))

        print("Voltage is: %d, Frequency is: %d" % (self.voltage, self.freq))
        output = self.WaveGen[0].generate_wave(self.voltage,
                                               self.freq,
                                               self.signal_rate,
                                               self.write_chunk_size)
        self.task.write(data=output, timeout=2)

    def start_signal(self):
        if not self.task_created():
            return

        self.is_running = True
        self.task.start()

    def stop_signal(self):
        if not self.task_created():
            return

        self.is_running = False
        self.task.stop()

        # House-keeping methods follow

    def task_created(self):
        """
        Return True if a task has been created
        """

        if isinstance(self.task, nidaqmx.task.Task):
            return True
        else:
            print('No task created: run the create_task method')
            return False

    # ---- DAQ Control method 1 based on MuControl ----

    # tells thread to stop blocking and restart
    def restart(self):
        self.start_thread_flag.set()

    # basically a one time call to start the write task
    def run(self):
        # first run, set start signal
        self.restart()
        # keep thread running
        while True:
            self.start_thread_flag.wait()
            self.start_thread_flag.clear()
            # checks flag for exiting thread
            if self.exit is True:
                return

            # flag for starting or ending nidaqmx.Task() object
            self.is_running = True

            print("Signal Writer Run")

            try:
                self.task = nidaqmx.Task()  # Start the task
                self.task_counter += 1
            except OSError:
                print("DAQ is not connected, task could not be created")
                continue

            # Add input channels
            for i in range(NUM_CHANNELS):
                channel_string = self.daq_out_name + '/' + f'ao{i}'
                try:
                    print("Channel ", channel_string, " added to task ", self.task.name)
                    self.task.ao_channels.add_ao_voltage_chan(channel_string)
                except Exception as e:
                    if i == 0:
                        print('Could not open write channels:')
                        print(e)
                        continue

            if self.mode == 'DC':
                print("output DC")
                self.task.write(self.voltage)
                print("DC write finished")
                continue

            print("Channel names: ", self.task.channel_names)

            # Set the generation rate, and buffer size.
            self.task.timing.cfg_samp_clk_timing(
                rate=self.signal_rate,
                sample_mode=AcquisitionType.CONTINUOUS)

            # Set more properties for continuous signal modulation
            self.task.out_stream.regen_mode = RegenerationMode.DONT_ALLOW_REGENERATION
            self.task.out_stream.output_buf_size = 2 * self.write_chunk_size

            # Register the listening method to add more data
            try:
                self.task.register_every_n_samples_transferred_from_buffer_event(
                    sample_interval=self.write_chunk_size,
                    callback_method=self.callback)
            except Exception as e:
                print("Problem with callback method:")
                print(e)
                continue

            # Initialize the writer
            self.writer = AnalogMultiChannelWriter(self.task.out_stream)

            self.output = self.package_waves(self.voltage, self.freq, self.signal_rate, self.write_chunk_size)

            # Write the first set of data into the output buffer
            try:
                # Write two chunks of beginning data to avoid interruption
                self.writer.write_many_sample(data=self.output)
            except Exception as e:
                print("Could not write to channel:")
                print(e)
                continue

            self.writer.write_many_sample(data=self.output)
            # start task, which will hold thread at this location continuously calling add_more_data
            self.task.start()

    # called by the task listener method
    # won't get called when DAQ is not attached
    def callback(self, task_handle, every_n_samples_event_type, number_of_samples, callback_data):
        if self.is_running:
            self.output = self.package_waves(self.voltage, self.freq, self.write_chunk_size)
            self.writer.write_many_sample(self.output)
        else:
            print("closed write task")
            self.task.close()

        return 0

    # puts all waves into a single array for AnalogMultiChannelWriter
    def package_waves(self, volt, freq, signal_rate, chunk_size):
        output = np.empty(shape=(NUM_CHANNELS, chunk_size))
        for ch in range(NUM_CHANNELS):
            output[ch] = self.WaveGen[ch].generate_wave(volt, freq, signal_rate, chunk_size)
        return output


# creates the sine wave to output
class WaveGenerator:
    def __init__(self):
        self.counter = 0
        self.last_freq = 0

    def generate_wave(self, voltage, frequency, sample_rate, samples_per_chunk):
        """

        :param voltage: RMS voltage, which will be converted to amplitude in signal
        :param frequency: frequency of signal in Hz
        :param sample_rate: # of signals per second
        :param samples_per_chunk: # of samples that will be written in this output buffer
        :return: np.array with signals that correspond to sine wave

        """
        if self.last_freq != frequency:
            self.counter = 0
            self.last_freq = frequency
        else:
            self.counter += 1

        amplitude = np.sqrt(2) * voltage  # get peak voltage from RMS voltage
        # frequency = waves_per_second
        rad_per_second = 2 * np.pi * frequency   # rad_per_second is the frequency in (radians / second)
        chunks_per_sec = sample_rate / samples_per_chunk   #
        rad_per_chunk = rad_per_second / chunks_per_sec
        waves_per_chunk = frequency / chunks_per_sec
        start_fraction = waves_per_chunk % 1    # shift the frequency if starting in the middle of a wave

        freq_shifter = self.counter * (2 * np.pi + start_fraction)

        # create an array with samples_per_signal
        # min is 0, max is rad_per_chunk
        # the task will write at signal_rate
        #
        output_samples = np.linspace(start=0, stop=rad_per_chunk, num=samples_per_chunk)
        output_buffer = amplitude * np.sin(output_samples * rad_per_second + freq_shifter)
        return output_buffer


if __name__ == '__main__':
    print('\nRunning demo for SignalWriter\n')
    writer = SignalWriter()

    writer.voltage = 5
    writer.freq = 10
    writer.mode = 'AC'

    writer.create_task()
    writer.start_signal()
    input("Press return to stop")
    writer.stop_signal()
