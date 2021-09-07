
from old.model import ChannelInterfaceData
from re import S
import numpy as np
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from config import CHANNEL_NAMES_IN, CHANNEL_NAMES_OUT, DEBUG_MODE

'''
Make new window
(assumes DAQ output is correct)
Step 1:
Hook up DAQ output into DAQ input directly
Step 2:
Run calibration
- go through each channel, see what it reads when output is known (0V, 1V, 3V)
- reset voltages on writer to saved params
- save the offsets
Step 3:
Hook up back onto coils
-Save and finish
'''

class CalibrationWindow(QtGui.QMainWindow):
    """
    Calibrates the DAQ reader to ensure the correct offset for all channels
    """

    # data with offsets applied
    corrected_data = QtCore.pyqtSignal(object)
    
    def __init__(self, parent, writer, reader):
        super().__init__(parent)
        self.writer = writer
        self.reader = reader

        self.calibration_state = True
        self.calibration_voltage = 0
        self.offsets = [0 for x in CHANNEL_NAMES_OUT]

        # testing calibration 
        self.reader.incoming_data.connect(self.on_data_collected)

        self.init_ui()
        self.calibration_btn.clicked.connect(self.on_calibration_btn_clicked)

    def init_ui(self):
        self.setWindowTitle("Calibration")

        self.mainbox = QWidget(self)
        self.setCentralWidget(self.mainbox)
        layout = QVBoxLayout(self)
        self.mainbox.setLayout(layout)

        for i, ch in enumerate(CHANNEL_NAMES_IN):
            pass
            # make associations between daq input channel and the daq out channel it is receiving voltage from

        self.calibration_voltage_label = QLabel("Calibration Voltage: {}V".format(self.calibration_voltage))
        self.calibration_btn = QPushButton("Start Calibration")

        layout.addWidget(self.calibration_voltage_label)
        layout.addWidget(self.calibration_btn)

    def on_calibration_btn_clicked(self):
        if self.calibration_state:
            self.run_calibration()
        else:
            self.close()

    def on_data_collected(self, data):
        print("Calibration data received")
        # collect mean of data in buffer, and apply offset to plotter
        for i, ch in enumerate(CHANNEL_NAMES_OUT):
            self.offsets[i] = self.calibration_voltage - np.mean(data[i])
        
        print("Offset:", self.offsets)

        self.halt_flag = False
        self.calibration_btn.setText("Finish Calibration")
        self.calibration_state = False

    def run_calibration(self):
        # set params
        saved_writer_states = self.writer.output_states
        saved_writer_frequencies = self.writer.frequencies
        saved_writer_voltages = self.writer.voltages

        self.halt_flag = True
        # set calibration voltages
        for i, ch in enumerate(CHANNEL_NAMES_OUT):
            print("Calibrating channel", ch)
            self.writer.output_states[i] = True
            self.writer.voltages[i] = self.calibration_voltage
            self.writer.frequencies[i] = 0
        
        self.writer.resume()
        # wait until calibration receives data on input
        while(self.halt_flag):
            print("waiting")

        self.writer.pause()
        
        self.writer.output_states = saved_writer_states
        self.writer.voltages = saved_writer_voltages
        self.writer.frequencies = saved_writer_frequencies

    # handler takes input from reader and then emits the correct data
    def apply_calibration(self, data):
        corrected = [chan_data + self.offsets[i] for i, chan_data in enumerate(data)]
        self.corrected_data.emit(corrected)

    def closeEvent(self, event):
        # prevent on_data_collected from being called once calibration is done
        self.writer.incoming_data.disconnect(self.on_data_collected)
        print("Exited Calibration")