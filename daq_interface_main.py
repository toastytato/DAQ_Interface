import sys

from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
# --- From DAQ Control --- #
from reader import *
from writer import *
from parameters import *
from plotter import *
from calibration import *


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super().__init__()

        # initialize parameters database
        self.magnetic_param_tree = MagneticControlsParamTree()
        self.channel_param_tree = ChannelParameters()
        self.setting_param_tree = ConfigParamTree()

        self.init_ui()
        self.init_daq_io()

        saved_offsets = [
            self.setting_param_tree.get_param_value(
                "Reader Config", "Calibration Offsets", ch
            )
            for ch in CHANNEL_NAMES_IN
        ]
        if DEBUG_MODE:
            self.calibration_dialog = CalibrationWindow(
                parent=self,
                writer=self.writer,
                reader=self.writer,
                write_channels=self.setting_param_tree.get_write_channels(),
                read_channels=self.setting_param_tree.get_read_channels(),
                saved_offsets=saved_offsets,
            )
            self.writer.incoming_data.connect(self.calibration_dialog.apply_calibration)
        # DAQ connected mode
        else:
            self.calibration_dialog = CalibrationWindow(
                parent=self,
                writer=self.writer,
                reader=self.read_thread,
                write_channels=self.setting_param_tree.get_write_channels(),
                read_channels=self.setting_param_tree.get_read_channels(),
                saved_offsets=saved_offsets,
            )
            self.read_thread.incoming_data.connect(
                self.calibration_dialog.apply_calibration
            )

        self.calibration_dialog.corrected_data.connect(self.plotter.update_plot)
        self.calibration_dialog.corrected_data.connect(self.legend.on_new_data)
        self.calibration_dialog.offsets_received.connect(
            self.setting_param_tree.save_offsets
        )
        self.calibration_dialog.show()

        # Connect the output signal from changes in the param tree to change
        self.start_signal_btn.clicked.connect(self.start_signal_btn_click)
        self.save_settings_btn.clicked.connect(self.commit_settings_btn_click)
        self.tabs.currentChanged.connect(self.on_tab_change)

        self.magnetic_param_tree.paramChange.connect(self.magnetic_param_change)
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

        title = QLabel("DAQ Controller")
        title.setAlignment(Qt.AlignHCenter)
        self.legend = Legend(self.setting_param_tree.get_read_channels())

        # TODO: update legend frequency on startup with param tree values
        #   use signals instead of passing in legend might be better
        self.plotter = SignalPlot(self.legend)
        # self.plotter.setMaximumSize(800, 360)

        self.start_signal_btn = QPushButton("Press to start signal out")

        # self.channel_param_tree.setMinimumSize(100, 200)

        self.settings_tab = QWidget(self)
        self.settings_tab.layout = QVBoxLayout(self)
        self.save_settings_btn = QPushButton("Commit Settings")
        self.settings_tab.layout.addWidget(self.setting_param_tree)
        self.settings_tab.layout.addWidget(self.save_settings_btn)
        self.settings_tab.setLayout(self.settings_tab.layout)

        self.tabs = QTabWidget(self)
        self.tabs.addTab(self.magnetic_param_tree, "Magnetic Controls")
        self.tabs.addTab(self.channel_param_tree, "Channels Controls")
        self.tabs.addTab(self.settings_tab, "DAQ Settings")
        self.current_tab = 0
        self.tabs.setCurrentIndex(self.current_tab)

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

        # pass initialized writer so the magnetic manipulators can use it when it needs to
        self.mag_alignment = MagneticAlignment(
            writer=self.writer,
            state=self.magnetic_param_tree.get_param_value(
                "3D Alignment", "Toggle Output"
            ),
            phi=self.magnetic_param_tree.get_param_value("3D Alignment", "Elevation"),
            theta=self.magnetic_param_tree.get_param_value("3D Alignment", "Azimuth"),
            amplitude=self.magnetic_param_tree.get_param_value(
                "3D Alignment", "Amplitude"
            ),
            frequency=self.magnetic_param_tree.get_param_value(
                "3D Alignment", "Frequency"
            ),
            kx=self.magnetic_param_tree.get_param_value(
                "3D Alignment", "Coefficients", "kx"
            ),
            ky=self.magnetic_param_tree.get_param_value(
                "3D Alignment", "Coefficients", "ky"
            ),
            kz=self.magnetic_param_tree.get_param_value(
                "3D Alignment", "Coefficients", "kz"
            ),
        )
        self.mag_rotation = MagneticRotation(
            writer=self.writer,
            state=self.magnetic_param_tree.get_param_value(
                "3D Rotation", "Toggle Output"
            ),
            phi=self.magnetic_param_tree.get_param_value("3D Rotation", "Elevation"),
            theta=self.magnetic_param_tree.get_param_value("3D Rotation", "Azimuth"),
            amplitude=self.magnetic_param_tree.get_param_value(
                "3D Rotation", "Amplitude"
            ),
            frequency=self.magnetic_param_tree.get_param_value(
                "3D Rotation", "Frequency"
            ),
            kx=self.magnetic_param_tree.get_param_value(
                "3D Rotation", "Coefficients", "kx"
            ),
            ky=self.magnetic_param_tree.get_param_value(
                "3D Rotation", "Coefficients", "ky"
            ),
            kz=self.magnetic_param_tree.get_param_value(
                "3D Rotation", "Coefficients", "kz"
            ),
        )

    @pyqtSlot()
    def start_signal_btn_click(self):
        if self.writer.is_running:
            print("Stopped DAQ signal")
            self.writer.pause()
            self.start_signal_btn.setText("Press to resume signal")
        else:
            print("Started DAQ signal")
            if self.current_tab == 0:
                self.writer.realign_channel_phases()
                if self.mag_alignment.output_state:
                    self.mag_alignment.update_params()
                elif self.mag_rotation.output_state:
                    self.mag_rotation.update_params()
                self.writer.resume()
            if self.current_tab == 1:
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
            # change the task parameters
            self.read_thread.input_channels = (
                self.setting_param_tree.get_read_channels()
            )
            self.read_thread.sample_rate = reader_sample_rate
            self.read_thread.sample_size = reader_sample_size

            self.writer.sample_rate = writer_sample_rate
            self.writer.sample_size = writer_sample_size

            # restart writer to update refresh times
            self.read_thread.restart()
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
        self.current_tab = t
        if t == 0:
            self.writer.realign_channel_phases()
            if self.mag_alignment.output_state:
                self.mag_alignment.update_params()
            if self.mag_rotation.output_state:
                self.mag_rotation.update_params()
        elif t == 1:
            self.writer.realign_channel_phases()
            for i, ch in enumerate(CHANNEL_NAMES_OUT):
                parent = self.channel_param_tree.params.child("Output " + ch)
                self.writer.output_states[i] = parent.child("Toggle Output").value()
                self.writer.voltages[i] = parent.child("Voltage RMS").value()
                self.writer.frequencies[i] = parent.child("Frequency").value()
                self.writer.shifts[i] = parent.child("Phase Shift").value()
        elif t == 2:
            pass

    # TODO: 3D alignment will be changed to 3D Rotation when 
    #       3D rotation param is changed, and vice versa
    def magnetic_param_change(self, parameter, changes):
        for param, change, data in changes:

            path = self.magnetic_param_tree.params.childPath(param)
            print(path)
            if path[0] == "3D Alignment":
                if path[1] == "Toggle Output":
                    if data:
                        self.mag_alignment.update_params()
                        self.magnetic_param_tree.set_param_value(
                            False, "3D Rotation", "Toggle Output"
                        )
                    self.mag_alignment.output_state = data
                elif path[1] == "Amplitude":
                    self.mag_alignment.amplitude = data
                    self.mag_alignment.update_params()
                elif path[1] == "Frequency":
                    self.mag_alignment.frequency = data
                elif path[1] == "Elevation":
                    self.mag_alignment.phi = data
                    self.mag_alignment.update_params()
                elif path[1] == "Azimuth":
                    self.mag_alignment.theta = data
                    self.mag_alignment.update_params()
                elif path[1] == "Coefficients":
                    print(path[2])
                    if path[2] == "k" + CHANNEL_NAMES_OUT[0].lower():
                        self.mag_alignment.kx = data
                    if path[2] == "k" + CHANNEL_NAMES_OUT[1].lower():
                        self.mag_alignment.ky = data
                    if path[2] == "k" + CHANNEL_NAMES_OUT[2].lower():
                        self.mag_alignment.kz = data
                    self.mag_alignment.update_params()

            elif path[0] == "3D Rotation":
                if path[1] == "Toggle Output":
                    if data:
                        self.mag_rotation.update_params()
                        self.magnetic_param_tree.set_param_value(
                            False, "3D Alignment", "Toggle Output"
                        )
                    self.mag_rotation.output_state = data
                elif path[1] == "Amplitude":
                    self.mag_rotation.amplitude = data
                    self.mag_rotation.update_params()
                elif path[1] == "Frequency":
                    self.mag_rotation.frequency = data
                elif path[1] == "Elevation":
                    self.mag_rotation.phi = data
                    self.mag_rotation.update_params()
                elif path[1] == "Azimuth":
                    self.mag_rotation.theta = data
                    self.mag_rotation.update_params()
                elif path[1] == "Coefficients":
                    print(path[2])
                    if path[2] == "k" + CHANNEL_NAMES_OUT[0].lower():
                        self.mag_rotation.kx = data
                    if path[2] == "k" + CHANNEL_NAMES_OUT[1].lower():
                        self.mag_rotation.ky = data
                    if path[2] == "k" + CHANNEL_NAMES_OUT[2].lower():
                        self.mag_rotation.kz = data
                    self.mag_rotation.update_params()

    def channels_param_change(self, parameter, changes):
        # parameter: the GroupParameter object that holds the Channel Params
        # changes: list that contains [ParameterObject, 'value', data]
        for param, change, data in changes:

            path = self.channel_param_tree.params.childPath(param)
            ch = CHANNEL_NAMES_OUT.index(path[0].split()[1])
            print(ch)
            if path[1] == "Toggle Output":
                self.writer.output_states[ch] = data
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
        self.magnetic_param_tree.save_settings()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
