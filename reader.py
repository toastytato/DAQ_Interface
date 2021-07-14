import time
import nidaqmx
import numpy as np
from nidaqmx.constants import AcquisitionType
from nidaqmx.stream_readers import AnalogMultiChannelReader
from pyqtgraph.Qt import QtCore

from config import *

# Thread for capturing input signal through DAQ
class SignalReader(QtCore.QThread):
    incoming_data = QtCore.pyqtSignal(object)

    def __init__(self, sample_rate, sample_size, channels, dev_name="Dev2"):
        super().__init__()

        self.reader = None
        self.is_running = False
        self.input_channels = channels
        self.daq_in_name = dev_name

        self.sample_rate = sample_rate
        self.sample_size = sample_size
        self.input = np.empty(shape=(len(CHANNEL_NAMES_IN), self.sample_size))

    # called on start()
    def run(self):
        self.is_running = True
        print("reader input channels:", self.input_channels)
        try:
            task = nidaqmx.Task("Reader Task")
        except OSError:
            print("DAQ is not connected, task could not be created")
            return

        try:
            for ch in self.input_channels:
                channel_name = self.daq_in_name + "/ai" + str(ch)
                task.ai_channels.add_ai_voltage_chan(channel_name)
                print(channel_name)
        except Exception as e:
            print("DAQ is not connected, channel could not be added")
            return

        task.timing.cfg_samp_clk_timing(
            rate=self.sample_rate, sample_mode=AcquisitionType.CONTINUOUS
        )

        reader = AnalogMultiChannelReader(task.in_stream)
        task.start()
        
        while self.is_running:
            try:
                reader.read_many_sample(
                    data=self.input, number_of_samples_per_channel=self.sample_size
                )
                self.incoming_data.emit(self.input)
                print("read_many_samples success")

            except Exception as e:
                print("Error with read_many_sample")
                print(e)
                break

        task.close()


if __name__ == "__main__":
    print("\nRunning demo for SignalReader\n")

    # reader_thread = SignalReader(sample_rate=1000, sample_size=1000, channels=[])
    # reader_thread.start()
    # input("Press return to stop")
    # reader_thread.is_running = False
    # reader_thread.wait()
    # print("\nTask done")
