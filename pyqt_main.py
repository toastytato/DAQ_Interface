import sys

import pyqtgraph as pg
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize, pyqtSlot
from PyQt5.QtWidgets import (QMainWindow, QLabel, QGridLayout, QWidget,
                             QPushButton, QLineEdit)

# --- From DAQ Control --- #
from reader import *
from writer import *
from parameters import *


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_daq_io()

    def init_ui(self):
        self.resize(700, 700) # non maximized size
        self.setWindowState(QtCore.Qt.WindowMaximized)
        # self.setMinimumSize(QSize(500, 400))
        self.setWindowTitle("DAQ Interface")

        self.mainbox = QWidget(self)
        self.setCentralWidget(self.mainbox)
        layout = QGridLayout()
        self.mainbox.setLayout(layout)

        title = QLabel("DAQ Controller", self)
        title.setAlignment(QtCore.Qt.AlignHCenter)
        self.plotter = SignalPlot()
        # self.plotter.setMaximumSize(800, 600)

        self.b1 = QPushButton('Press to start signal out')
        self.b1.clicked.connect(self.button_on_click)

        self.channel_param_tree = ChannelParamTree()  # From ParameterTree.py
        # Connect the output signal from changes in the param tree to change
        self.channel_param_tree.paramChange.connect(self.change)
        self.channel_param_tree.setMinimumSize(100, 200)

        self.setting_param_tree = ConfigParamTree()
        self.setting_param_tree.paramChange.connect(self.change)

        # place widgets in their respective locations
        layout.addWidget(title)  # row, col, rowspan, colspan
        layout.addWidget(self.plotter)
        layout.addWidget(self.b1)
        # layout.addWidget(self.setting_param_tree, 3, 1, 1, 1)
        layout.addWidget(self.channel_param_tree)

    def init_daq_io(self):

        voltages = []
        frequencies = []
        for i in range(NUM_CHANNELS):
            branch = 'Channel ' + str(i)
            voltages.append(self.channel_param_tree.get_param_value(branch, 'Voltage RMS'))
            frequencies.append(self.channel_param_tree.get_param_value(branch, 'Frequency'))

        # When NI instrument is attached
        if not DEBUG_MODE:
            # initiate read threads for analog input
            self.read_thread = SignalReader(
                sample_rate=self.setting_param_tree.get_param_value('Reader Config', 'Sample Rate'),
                sample_size=self.setting_param_tree.get_param_value('Reader Config', 'Sample Size'))
            self.read_thread.incoming_data.connect(self.plotter.update_plot)
            self.read_thread.start()

            # initiate writer for analog output
            # not handled on separate thread b/c not blocking
            self.writer = SignalWriter(
                voltages=voltages,
                frequencies=frequencies,
                sample_rate=self.setting_param_tree.get_param_value('Writer Config', 'Sample Rate'),
                sample_size=self.setting_param_tree.get_param_value('Writer Config', 'Sample Size'), )
            self.writer.create_task()

        # Debugging without NI instrument
        else:
            # Use software signal generator and read from that
            self.writer = DebugSignalGenerator(
                voltages=voltages,
                frequencies=frequencies,
                sample_rate=self.setting_param_tree.get_param_value('Writer Config', 'Sample Rate'),
                sample_size=self.setting_param_tree.get_param_value('Writer Config', 'Sample Size'))
            self.writer.newData.connect(self.plotter.update_plot)

    @pyqtSlot()
    def button_on_click(self):
        if self.writer.is_running:
            print("Stopped DAQ signal")
            self.writer.pause()
            self.b1.setText("Press to resume signal")
        else:
            print("Started DAQ signal")
            self.writer.resume()
            self.b1.setText("Press to pause signal")

    def change(self, parameter, changes):
        # parameter: the GroupParameter object that holds the Channel Params
        # changes: list that contains [ParameterObject, 'value', data]

        for param, change, data in changes:

            if parameter.name() == 'channel_params':
                path = self.channel_param_tree.param.childPath(param)
                ch = int(path[0].split()[1])  # splits 'Channel 0' into 0

                if path[1] == 'Toggle Output':
                    self.writer.output_state[ch] = data
                if path[1] == 'Voltage RMS':
                    self.writer.voltages[ch] = data
                if path[1] == 'Frequency':
                    self.writer.frequencies[ch] = data

            elif parameter.name() == 'setting_params':
                path = self.setting_param_tree.param.childPath(param)

                if path[1] == 'Sample Rate':
                    print('hi')

    def closeEvent(self, event):
        print("Closing...")
        if not DEBUG_MODE:
            self.read_thread.is_running = False
            self.read_thread.wait()

            self.writer.is_running = False
            self.writer.end()
        else:
            self.writer.end()


class SignalPlot(pg.PlotWidget):
    def __init__(self):
        super().__init__()
        # PlotWidget super functions
        self.line_width = 1
        self.curve_colors = ['b', 'g', 'r', 'c', 'y', 'm']
        self.pens = [pg.mkPen(i, width=self.line_width) for i in self.curve_colors]
        self.showGrid(y=True)
        # self.disableAutoRange('y')

    def update_plot(self, incoming_data):
        self.clear()
        for i in range(np.shape(incoming_data)[0]):
            self.plot(incoming_data[i], clear=False, pen=self.pens[i])


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
