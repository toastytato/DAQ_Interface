import nidaqmx
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx.constants import AcquisitionType, RegenerationMode
from constants import *
import numpy as np
from threading import Thread, Event
import matplotlib.pyplot as plt


class SignalReader(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.reader = None
        self.is_running = False
        self.daq_in_name = 'Dev0'

        self.sample_rate = 1000
        self.read_chunk_size = 500
        self.input = np.empty(self.read_chunk_size)

    def run(self):
        self.is_running = True
        try:
            with nidaqmx.Task() as task:
                channel_name = self.daq_in_name + "/ai0"

                try:
                    task.ai_channels.add_ai_voltage_chan(channel_name)
                except Exception as e:
                    print("DAQ is not connected, task could not be created")
                    print(e)
                    return

                task.timing.cfg_samp_clk_timing(rate=self.sample_rate,
                                                sample_mode=AcquisitionType.CONTINUOUS)

                reader = AnalogMultiChannelReader(task.in_stream)
                task.start()

                while self.is_running:
                    try:
                        reader.read_many_sample(data=self.input,
                                                number_of_samples_per_channel=self.read_chunk_size)
                        plt.plot(self.input)
                        plt.show()
                    except Exception as e:
                        print(e)
                        continue

        except OSError:
            print("DAQ not connected, could not create task")
            return


if __name__ == '__main__':
    print('\nRunning demo for SignalReader\n')
    reader = SignalReader()
    reader.run()
