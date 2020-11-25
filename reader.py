import nidaqmx
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx.constants import AcquisitionType
from nidaqmx.system import System
from pyqtgraph.Qt import QtCore
import numpy as np
from threading import Thread, Event
import matplotlib.pyplot as plt
import time

from constants import *
from writer import WaveGenerator


class SignalReader(QtCore.QThread):
    newData = QtCore.pyqtSignal(object)

    def __init__(self, sample_rate, sample_size, dev_name='Dev2'):
        super().__init__()

        self.reader = None
        self.is_running = False
        self.daq_in_name = dev_name

        self.sample_rate = sample_rate
        self.read_chunk_size = sample_size
        self.input = np.empty(shape=(1, self.read_chunk_size))

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
                self.newData.emit(self.input)

            except Exception as e:
                print("Error with read_many_sample")
                print(e)
                break

        task.close()


class DebugSignalGenerator(QtCore.QThread):
    """
    Used as debug signal generator to create a waveform while debugging to create waveforms
    without initializing NI method that can raise errors
    """

    newData = QtCore.pyqtSignal(object)

    def __init__(self, voltage, frequency, sample_rate, sample_size):
        super().__init__()

        self.is_running = False

        self.voltage = voltage
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.chunk_size = sample_size
        self.output = np.empty(shape=(1, self.chunk_size))

    def run(self):
        self.is_running = True

        wave_gen = WaveGenerator()

        while self.is_running:
            self.output = wave_gen.generate_wave(self.voltage,
                                                 self.frequency,
                                                 self.sample_rate,
                                                 self.chunk_size)
            self.output = np.around(self.output, 4)
            self.output = self.output.reshape((1, self.chunk_size))
            # print(self.output)
            self.newData.emit(self.output)
            time.sleep(self.chunk_size / self.sample_rate)


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
