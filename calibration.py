from numpy.core.arrayprint import format_float_positional
from old.model import ChannelInterfaceData
from re import S
import numpy as np
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMainWindow
)

from config import CALIBRATION_VOLTAGE, CHANNEL_NAMES_IN, CHANNEL_NAMES_OUT, DEBUG_MODE

"""
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
"""

# TODO: if previous session has a sin wave, calibration will end up using that sin wave instead of
#       the calibration voltage


class CalibrationWindow(QMainWindow):
    """
    Calibrates the DAQ reader to ensure the correct offset for all channels
    """

    # data with offsets applied
    corrected_data = QtCore.pyqtSignal(object)
    offsets_received = QtCore.pyqtSignal(object)

    def __init__(
        self, parent, writer, reader, write_channels, read_channels, saved_offsets
    ):
        super().__init__(parent)
        self.writer = writer
        self.reader = reader
        self.write_channels = write_channels
        self.read_channels = read_channels

        self.calibration_state = True
        self.calibration_voltage = CALIBRATION_VOLTAGE

        self.handler_counter = 0
        self.offsets = saved_offsets
        # value represents the index of the output channel to take voltage readings from
        self.assigned_output = [int for x in CHANNEL_NAMES_IN]

        self.init_ui()
        self.calibration_btn.clicked.connect(self.on_calibration_btn_clicked)

    def init_ui(self):
        """
        Initialize the calibration UI with the widgets and their values
        """
        self.setWindowTitle("Calibration")

        self.mainbox = QWidget(self)
        self.setCentralWidget(self.mainbox)
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        self.mainbox.setLayout(layout)

        grid_layout = QGridLayout(self)
        self.sel_output_ch_combo = [QComboBox(self) for i in CHANNEL_NAMES_IN]

        grid_layout.addWidget(QLabel("Input Ch."), 0, 0)
        grid_layout.addWidget(QLabel("Output Ch."), 0, 1)
        grid_layout.addWidget(QLabel("Offsets"), 0, 2)

        for i, ch_in in enumerate(CHANNEL_NAMES_IN):
            for j, ch_out in enumerate(CHANNEL_NAMES_OUT):
                item = ch_out + " (ao" + str(self.write_channels[j]) + ")"
                self.sel_output_ch_combo[i].addItem(item, userData=i)
            # set -1 to trigger event handler for all combo boxes on creation
            self.sel_output_ch_combo[i].setCurrentIndex(-1)
            # first argument of handler when connected is index of selection (indicated by _).
            # ignore so the selected combobox qt object can be passed instead
            handler = lambda _, combo=self.sel_output_ch_combo[i]: self.on_output_channel_selected(
                combo)
            self.sel_output_ch_combo[i].currentIndexChanged.connect(handler)
            self.sel_output_ch_combo[i].setCurrentIndex(0)

            self.offsets_label = [
                QLabel(str(self.offsets[i]) + "V")
                for i, ch in enumerate(CHANNEL_NAMES_IN)
            ]
            grid_layout.addWidget(
                QLabel(
                    ch_in + " (ai" + str(self.read_channels[i]) + ")"), i + 1, 0
            )
            grid_layout.addWidget(self.sel_output_ch_combo[i], i + 1, 1)
            grid_layout.addWidget(self.offsets_label[i], i + 1, 2)
            # make associations between daq input channel and the daq out channel it is receiving voltage from

        self.calibration_voltage_label = QLabel(
            "Calibration Voltage: {}V\n".format(self.calibration_voltage)
        )
        self.calibration_btn = QPushButton("Start Calibration")

        instructions = "\nEnsure the input DAQ channels are connected to the corresponding"
        instructions += "\noutput DAQ channels before starting calibration\n"
        instructions += "\n(Exit to skip calibration)\n"

        layout.addWidget(self.calibration_voltage_label)
        layout.addLayout(grid_layout)
        layout.addWidget(QLabel(instructions))
        layout.addWidget(self.calibration_btn)

    # combo = contains the info for the selected output DAQ we are reading from
    # combo.currentData() = input channel that we are assigning to
    def on_output_channel_selected(self, combo):
        self.assigned_output[combo.currentData()] = combo.currentIndex()
        print(self.assigned_output)

    def on_calibration_btn_clicked(self):
        """
        If calibration has not started, start calibration
        Else calibration has finished and close this window
        """
        if self.calibration_state:
            self.run_calibration()
        else:
            print("Exited Calibration")
            self.close()

    def on_data_collected(self, data):
        """
        handler that is called when reader takes in a buffer
        When the DAQ reader is on, it will repeated call this function
        We will read the second/third buffer to ensure that any previous values are flushed
        This new value should be whatever is connected to the DAQ Input
        The calibration offset = True voltage (self.calibration_voltage) - Measured voltage (current reading)
        """
        self.handler_counter += 1
        # allow the DAQ to clear its buffer before taking in voltage
        if self.handler_counter < 2:
            return

        self.handler_counter = 0
        print("Calibration data received")
        # collect mean of data in buffer, and apply offset to plotter
        for i, ch in enumerate(CHANNEL_NAMES_IN):
            index = self.assigned_output[i]
            self.offsets[i] = self.calibration_voltage - np.mean(data[index])
            self.offsets_label[i].setText(str(self.offsets[i]) + "V")

        print("Offset:", self.offsets)
        self.offsets_received.emit(self.offsets)

        self.calibration_btn.setText("Finish Calibration")
        self.calibration_state = False

        # writer.pause will make one more call to this handler once paused
        # disconnect before writer can make another call to this handler
        self.reader.incoming_data.disconnect(self.on_data_collected)

        self.writer.pause()  # will end up emitting on_data_collected again
        self.writer.output_states = self.saved_writer_states
        self.writer.voltages = self.saved_writer_voltages
        self.writer.frequencies = self.saved_writer_frequencies

    def run_calibration(self):
        """
        When calibration is running, all new data will also pass through the on_data_collected function
        This will allow the program to process the true and measured voltage and calibrate accordingly
        """
        print("Calibration Started")
        # connect to reader to get input
        self.reader.incoming_data.connect(self.on_data_collected)

        # save previous output states
        self.saved_writer_states = self.writer.output_states
        self.saved_writer_frequencies = self.writer.frequencies
        self.saved_writer_voltages = self.writer.voltages

        # set calibration voltages
        for i, ch in enumerate(CHANNEL_NAMES_OUT):
            self.writer.output_states[i] = True
            self.writer.voltages[i] = self.calibration_voltage
            self.writer.frequencies[i] = 0

        self.writer.resume()

    # handler takes input from reader and then emits the calibrated data
    # maybe put in another object
    def apply_calibration(self, data):
        """
        This function is called as a bridge between the received signal and the used signal
        Applies calibration offset all incoming data
        """
        corrected = [chan_data + self.offsets[i]
                     for i, chan_data in enumerate(data)]
        self.corrected_data.emit(corrected)
