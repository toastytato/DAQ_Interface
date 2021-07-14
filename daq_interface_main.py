import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# --- From DAQ Control --- #
from reader import *
from writer import *
from parameters import *
from plotter import *


# TODO:


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_daq_io()

        # Connect the output signal from changes in the param tree to change
        self.start_signal_btn.clicked.connect(self.start_signal_btn_click)
        self.save_settings_btn.clicked.connect(self.commit_settings_btn_click)
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
        layout = QVBoxLayout()
        self.mainbox.setLayout(layout)

        # initialize parameters database
        self.controls_param_tree = ControlsParamTree()
        self.channel_param_tree = ChannelParameters()
        self.setting_param_tree = ConfigParamTree()

        title = QLabel("DAQ Controller")
        title.setAlignment(Qt.AlignHCenter)
        self.legend = Legend(self.setting_param_tree.get_read_channels())

        # TODO: update legend frequency on startup with param tree values
        self.plotter = SignalPlot(self.legend)
        # self.plotter.setMaximumSize(800, 360)

        self.start_signal_btn = QPushButton("Press to start signal out")

        # self.channel_param_tree.setMinimumSize(100, 200)

        self.settings_tab = QWidget()
        self.settings_tab.layout = QVBoxLayout(self)
        self.save_settings_btn = QPushButton("Commit Settings")
        self.settings_tab.layout.addWidget(self.setting_param_tree)
        self.settings_tab.layout.addWidget(self.save_settings_btn)
        self.settings_tab.setLayout(self.settings_tab.layout)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.controls_param_tree, "Main Controls")
        self.tabs.addTab(self.channel_param_tree, "Channels Controls")
        self.tabs.addTab(self.settings_tab, "DAQ Settings")
        self.tabs.setCurrentIndex(1)

        # place widgets in their respective locations
        layout.addWidget(title)  # row, col, rowspan, colspan
        layout.addWidget(self.plotter)
        layout.addWidget(self.legend)
        layout.addWidget(self.start_signal_btn)
        # layout.addWidget(self.setting_param_tree, 3, 1, 1, 1)
        layout.addWidget(self.tabs)

    def init_daq_io(self):
        voltages = []
        frequencies = []
        shifts = []
        output_states = []

        for ch in CHANNEL_NAMES_OUT:
            branch = "Output " + ch
            voltages.append(
                self.channel_param_tree.get_param_value(branch, "Voltage RMS")
            )
            frequencies.append(
                self.channel_param_tree.get_param_value(branch, "Frequency")
            )
            shifts.append(
                self.channel_param_tree.get_param_value(branch, "Phase Shift")
            )
            output_states.append(
                self.channel_param_tree.get_param_value(branch, "Toggle Output")
            )

        self.legend.update_rms_params(
            sample_rate=self.setting_param_tree.get_param_value(
                "Reader Config", "Sample Rate"
            )
        )

        # When NI instrument is attached
        if not DEBUG_MODE:
            # initiate read threads for analog input
            self.read_thread = SignalReader(
                sample_rate=self.setting_param_tree.get_param_value(
                    "Reader Config", "Sample Rate"
                ),
                sample_size=self.setting_param_tree.get_param_value(
                    "Reader Config", "Sample Size"
                ),
                channels=self.setting_param_tree.get_read_channels(),
                dev_name=self.setting_param_tree.get_param_value(
                    "Reader Config", "Device Name"
                ),
            )
            self.read_thread.incoming_data.connect(self.plotter.update_plot)
            self.read_thread.incoming_data.connect(self.legend.on_new_data)
            self.read_thread.start()

            # initiate writer for analog output
            # not handled on separate thread b/c not blocking

            self.writer = SignalWriterDAQ(
                voltages=voltages,
                frequencies=frequencies,
                shifts=shifts,
                output_states=output_states,
                sample_rate=self.setting_param_tree.get_param_value(
                    "Writer Config", "Sample Rate"
                ),
                sample_size=self.setting_param_tree.get_param_value(
                    "Writer Config", "Sample Size"
                ),
                channels=self.setting_param_tree.get_write_channels(),
                dev_name=self.setting_param_tree.get_param_value(
                    "Writer Config", "Device Name"
                ),
            )
            self.writer.create_task()

        # Debugging on computer without NI instrument
        else:
            # Use software signal generator and read from that
            # Plot is displaying the samples and rate at which the real
            # signal generator would write to the output DAQ
            self.writer = SignalGeneratorBase(
                voltages=voltages,
                frequencies=frequencies,
                shifts=shifts,
                output_states=output_states,
                sample_rate=self.setting_param_tree.get_param_value(
                    "Writer Config", "Sample Rate"
                ),
                sample_size=self.setting_param_tree.get_param_value(
                    "Writer Config", "Sample Size"
                ),
            )
            self.writer.new_data.connect(self.plotter.update_plot)
            self.writer.new_data.connect(self.legend.on_new_data)

        # pass writer so field generator can manipulate it when it needs to
        self.field_generator = RotationalFieldGenerator(self.writer)

    @pyqtSlot()
    def start_signal_btn_click(self):
        if self.writer.is_running:
            print("Stopped DAQ signal")
            self.writer.pause()
            self.start_signal_btn.setText("Press to resume signal")
        else:
            print("Started DAQ signal")
            self.writer.resume()
            self.start_signal_btn.setText("Press to pause signal")

    @pyqtSlot()
    def commit_settings_btn_click(self):
        print("Commit settings btn pressed")

        writer_sample_rate = self.setting_param_tree.get_param_value(
            "Writer Config", "Sample Rate"
        )
        writer_sample_size = self.setting_param_tree.get_param_value(
            "Writer Config", "Sample Size"
        )
        reader_sample_rate = self.setting_param_tree.get_param_value(
            "Reader Config", "Sample Rate"
        )
        reader_sample_size = self.setting_param_tree.get_param_value(
            "Reader Config", "Sample Size"
        )
        # update read channel names
        self.legend.update_channels(self.setting_param_tree.get_read_channels())
        self.legend.update_rms_params(sample_rate=writer_sample_rate)

        if not DEBUG_MODE:
            # TODO:
            #   Reader will probably not be able to update new sample settings
            #   - need to not start and stop thread but restart task

            # close the current task and wait until it has fully ended
            self.read_thread.is_running = False
            self.read_thread.wait()

            # change the task parameters
            self.read_thread.input_channels = (
                self.setting_param_tree.get_read_channels()
            )
            self.read_thread.sample_rate = reader_sample_rate
            self.read_thread.sample_size = reader_sample_size

            self.writer.sample_rate = writer_sample_rate
            self.writer.sample_size = writer_sample_size

            # start the task again
            self.read_thread.start()
            # restart writer to update refresh times
            self.writer.pause()
            self.writer.resume()

        else:
            self.writer.sample_rate = writer_sample_rate
            self.writer.sample_size = writer_sample_size
            # update refresh times in debug writer
            self.writer.pause()
            self.writer.resume()
            print("Restarted signal reader")

    @pyqtSlot(int)
    def on_tab_change(self, t):
        print("changed to tab: ", t)

        if t == 0:
            self.writer.realign_channel_phases()
            self.field_generator.resume_signal()
        elif t == 1:
            self.writer.realign_channel_phases()
            for i, ch in enumerate(CHANNEL_NAMES_OUT):
                parent = self.channel_param_tree.param.child("Output " + ch)
                self.writer.output_state[i] = parent.child("Toggle Output").value()
                self.writer.voltages[i] = parent.child("Voltage RMS").value()
                self.writer.frequencies[i] = parent.child("Frequency").value()
                self.writer.shifts[i] = parent.child("Phase Shift").value()
        elif t == 2:
            pass

    def controls_param_change(self, parameter, changes):
        for param, change, data in changes:

            path = self.controls_param_tree.param.childPath(param)

            if path[1] == "Toggle Output":
                if data:
                    self.field_generator.resume_signal()
                else:
                    self.field_generator.pause_signal()
            if path[1] == "Amplitude":
                self.field_generator.voltage = data
                print(self.writer.voltages)
            if path[1] == "Frequency":
                self.field_generator.frequency = data
                print(self.writer.frequencies)
            if path[1] == "Arrangement":
                print(data)

    def channels_param_change(self, parameter, changes):
        # parameter: the GroupParameter object that holds the Channel Params
        # changes: list that contains [ParameterObject, 'value', data]
        for param, change, data in changes:

            path = self.channel_param_tree.param.childPath(param)
            ch = CHANNEL_NAMES_OUT.index(path[0].split()[1])
            print(ch)
            if path[1] == "Toggle Output":
                self.writer.output_state[ch] = data
            if path[1] == "Voltage RMS":
                self.writer.voltages[ch] = data
            if path[1] == "Frequency":
                self.writer.frequencies[ch] = data
                self.legend.legend_items[ch].frequency = data
            if path[1] == "Phase Shift":
                self.writer.shifts[ch] = data

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

        self.channel_param_tree.save_settings()
        self.setting_param_tree.save_settings()
        self.controls_param_tree.save_settings()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())