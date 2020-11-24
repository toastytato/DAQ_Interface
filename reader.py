import nidaqmx
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx.constants import AcquisitionType
from nidaqmx.system import System
from constants import *
import numpy as np
from threading import Thread, Event
import matplotlib.pyplot as plt
import pyqt_test as myplot


class SignalReader(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.reader = None
        self.is_running = False
        self.daq_in_name = 'Dev2'

        self.sample_rate = 1000
        self.read_chunk_size = 500
        self.input = np.empty(shape=(1, self.read_chunk_size))

        # self.plotter = myplot.SignalPlot()

    def run(self):
        self.is_running = True

        try:
            task = nidaqmx.Task()
        except OSError:
            print("DAQ is not connected, task could not be created")
            return

        channel_name = self.daq_in_name + "/ai0"

        try:
            task.ai_channels.add_ai_voltage_chan(channel_name)
        except Exception as e:
            print("DAQ is not connected, task could not be created")
            return

        task.timing.cfg_samp_clk_timing(rate=self.sample_rate,
                                        sample_mode=AcquisitionType.CONTINUOUS)

        reader = AnalogMultiChannelReader(task.in_stream)
        task.start()

        while self.is_running:
            try:
                reader.read_many_sample(data=self.input,
                                        number_of_samples_per_channel=self.read_chunk_size)
                # self.plotter.update_plot(self.input)
                print(self.input)
            except Exception as e:
                print(e)
                break

        task.close()

def find_ni_devices():
    system = System.local()
    dev_name_list = []
    for device in system.devices:
        assert device is not None
        # device looks like "Device(name=cDAQ1Mod1)"
        dev_name = str(device).replace(')', '').split('=')[1]
        dev_name_list.append(dev_name)
    return str(dev_name_list)


if __name__ == '__main__':
    print('\nRunning demo for SignalReader\n')
    print(find_ni_devices())
    reader_thread = SignalReader()
    reader_thread.start()
    input("Press return to stop")
    reader_thread.is_running = False
    reader_thread.join()
    print("\nTask done")

