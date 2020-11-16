import nidaqmx
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from nidaqmx.constants import AcquisitionType
from constants import *
import numpy as np
from model import WaveGenerator
from threading import Thread, Event

class SignalWriter(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.writer = None
        self.task = None

        self.running = False
        self.exit = False
        self.start_signal = Event()
        self.funcg_name = 'Dev1'
        self.signals_per_sec = 8000  # signals per second
        self.write_chunk_size = self.signals_per_sec // 10    # size of chunk to write (nearest floor integer)
        self.WaveGen = [WaveGenerator()] * NUM_CHANNELS
        self.output = np.empty(NUM_CHANNELS)

        self.voltage = 0
        self.freq = 0
        self.mode = 'AC'

    # tells thread to stop blocking and restart
    def restart(self):
        self.start_signal.set()

    # basically a one time call to start the write task
    def run(self):
        # first run, set start signal
        self.restart()
        # keep thread running
        while True:
            self.start_signal.wait()
            self.start_signal.clear()
            # checks flag for exiting thread
            if self.exit is True:
                return

            # flag for starting or ending nidaqmx.Task() object
            self.running = True

            print("Signal Writer Run")

            try:
                self.task = nidaqmx.Task()  # Start the task
            except OSError:
                print("DAQ is not connected")
                continue

            # Add input channels
            for i in range(NUM_CHANNELS):
                channel_string = self.funcg_name + '/' + f'ao{i}'
                try:
                    self.task.ao_channels.add_ao_voltage_chan(channel_string)
                except Exception as e:
                    if i == 0:
                        print('Could not open write channels')
                        continue

            if self.mode == 'DC':
                print("output DC")
                self.task.write(self.voltage)
                print("DC write finished")
                continue

            # Set the generation rate, and buffer size.
            self.task.timing.cfg_samp_clk_timing(
                rate=self.signals_per_sec,
                sample_mode=AcquisitionType.CONTINUOUS)

            # Set more properties for continuous signal modulation
            self.task.out_stream.regen_mode = nidaqmx.constants.RegenerationMode.DONT_ALLOW_REGENERATION
            self.task.out_stream.output_buf_size = 2 * self.write_chunk_size

            # Register the listening method to add more data
            self.task.register_every_n_samples_transferred_from_buffer_event(
                sample_interval=self.write_chunk_size,
                callback_method=self.add_more_data)

            # Initialize the writer
            self.writer = AnalogMultiChannelWriter(self.task.out_stream)

            self.output = self.package_waves(self.voltage, self.freq, self.write_chunk_size)

            # Write the first set of data into the output buffer
            try:
                self.writer.write_many_sample(data=self.output)  # Write two chunks of beginning data to avoid interruption
            except:
                print("Could not write to channel")
                continue

            self.writer.write_many_sample(data=self.output)
            # start task, which will hold thread at this location continuously calling add_more_data
            self.task.start()

    # called by the task listener method
    # won't get called when DAQ is not attached
    def add_more_data(self, task_handle, every_n_samples_event_type, number_of_samples, callback_data):
        if self.running:
            self.output = self.package_waves(self.voltage, self.freq, self.write_chunk_size)
            self.writer.write_many_sample(self.output)
        else:
            print("closed write task")
            self.task.close()

        return 0

    # puts all waves into a single array for AnalogMultiChannelWriter
    def package_waves(self, volt, freq, chunk_size):
        output = np.empty(NUM_CHANNELS)
        for ch in range(NUM_CHANNELS):
            output[ch] = self.WaveGen[ch].generate_wave(volt, freq, chunk_size)
        return output


        
