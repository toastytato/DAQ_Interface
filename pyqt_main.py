import sys

import pyqtgraph as pg
from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# --- From DAQ Control --- #
from reader import *
from writer import *
from parameters import *


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_daq_io()

        # Connect the output signal from changes in the param tree to change
        self.b1.clicked.connect(self.button_on_click)
        self.tabs.currentChanged.connect(self.on_tab_change)
        self.controls_param_tree.paramChange.connect(self.controls_param_change)
        self.channel_param_tree.paramChange.connect(self.channels_param_change)
        self.setting_param_tree.paramChange.connect(self.settings_param_change)

    def init_ui(self):
        self.resize(700, 700)  # non maximized size
        # self.setWindowState(QtCore.Qt.WindowMinimized)
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

        self.controls_param_tree = ControlsParamTree()

        self.channel_param_tree = ChannelParamTree()  # From ParameterTree.py
        # self.channel_param_tree.setMinimumSize(100, 200)

        self.setting_param_tree = ConfigParamTree()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.controls_param_tree, "Main Controls")
        self.tabs.addTab(self.channel_param_tree, "Channels Controls")
        self.tabs.addTab(self.setting_param_tree, "DAQ Settings")
        self.tabs.setCurrentIndex(1)

        # place widgets in their respective locations
        layout.addWidget(title)  # row, col, rowspan, colspan
        layout.addWidget(self.plotter)
        layout.addWidget(self.b1)
        # layout.addWidget(self.setting_param_tree, 3, 1, 1, 1)
        layout.addWidget(self.tabs)

    def init_daq_io(self):

        voltages = []
        frequencies = []
        shifts = []
        for i in range(NUM_CHANNELS):
            branch = 'Channel ' + str(i)
            voltages.append(self.channel_param_tree.get_param_value(branch, 'Voltage RMS'))
            frequencies.append(self.channel_param_tree.get_param_value(branch, 'Frequency'))
            shifts.append(self.channel_param_tree.get_param_value(branch, 'Phase Shift'))

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
                shifts=shifts,
                sample_rate=self.setting_param_tree.get_param_value('Writer Config', 'Sample Rate'),
                sample_size=self.setting_param_tree.get_param_value('Writer Config', 'Sample Size'), )
            self.writer.create_task()

        # Debugging without NI instrument
        else:
            # Use software signal generator and read from that
            self.writer = DebugSignalGenerator(
                voltages=voltages,
                frequencies=frequencies,
                shifts=shifts,
                sample_rate=self.setting_param_tree.get_param_value('Writer Config', 'Sample Rate'),
                sample_size=self.setting_param_tree.get_param_value('Writer Config', 'Sample Size'))
            self.writer.newData.connect(self.plotter.update_plot)

        # pass by reference writer so field generator can manipulate it when it needs to
        self.field_generator = RotationalFieldGenerator(self.writer)

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

    @pyqtSlot(int)
    def on_tab_change(self, i):
        print("changed to tab: ", i)

        if i == 0:
            self.writer.realign_channels()
            self.field_generator.resume_signal()
        elif i == 1:
            self.writer.realign_channels()
            for i in range(NUM_CHANNELS):
                channel = "Channel " + str(i)
                parent = self.channel_param_tree.param.child(channel)
                self.writer.output_state[i] = parent.child("Toggle Output").value()
                self.writer.voltages[i] = parent.child("Voltage RMS").value()
                self.writer.frequencies[i] = parent.child("Frequency").value()
                self.writer.shifts[i] = parent.child("Phase Shift").value()
        elif i == 2:
            pass

        print(self.channel_param_tree.param.child("Channel 0").child("Toggle Output").value())

    def channels_param_change(self, parameter, changes):
        # parameter: the GroupParameter object that holds the Channel Params
        # changes: list that contains [ParameterObject, 'value', data]
        for param, change, data in changes:

            path = self.channel_param_tree.param.childPath(param)
            ch = int(path[0].split()[1])  # eg. splits 'Channel 0' into integer 0

            if path[1] == 'Toggle Output':
                self.writer.output_state[ch] = data
            if path[1] == 'Voltage RMS':
                self.writer.voltages[ch] = data
            if path[1] == 'Frequency':
                self.writer.frequencies[ch] = data
            if path[1] == 'Phase Shift':
                self.writer.shifts[ch] = data

    def controls_param_change(self, parameter, changes):
        for param, change, data in changes:

            path = self.controls_param_tree.param.childPath(param)

            if path[1] == 'Toggle Output':
                if data:
                    self.field_generator.resume_signal()
                else:
                    self.field_generator.pause_signal()
            if path[1] == 'Voltage RMS':
                self.field_generator.voltage = data
                print(self.writer.voltages)
            if path[1] == 'Frequency':
                self.field_generator.frequency = data
                print(self.writer.frequencies)
            if path[1] == 'Arrangement':
                print(data)

    def settings_param_change(self, parameter, changes):
        pass

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
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
