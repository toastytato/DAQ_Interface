import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QWidget, QPushButton
from PyQt5.QtCore import QSize, pyqtSlot
import pyqtgraph as pg
import numpy as np

# --- From DAQ Control --- #
from reader import *
from writer import *


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_threads()

    def init_ui(self):
        self.setMinimumSize(QSize(720, 360))
        self.setWindowTitle("DAQ Interface")

        self.mainbox = QWidget(self)
        self.setCentralWidget(self.mainbox)
        layout = QGridLayout()
        self.mainbox.setLayout(layout)

        title = QLabel("Signal Debugger", self)
        title.setAlignment(QtCore.Qt.AlignHCenter)
        self.plotter = SignalPlot()

        self.button = QPushButton('Start Signal Out')
        self.button.clicked.connect(self.button_on_click)

        layout.addWidget(title)
        layout.addWidget(self.plotter)
        layout.addWidget(self.button)

    def init_threads(self):
        # When NI instrument is attached
        if not DEBUG_MODE:
            # initiate read threads for analog input
            self.write_thread = SignalReader(sample_rate=1000,
                                             sample_size=500)
            self.write_thread.newData.connect(self.plotter.update_plot)
            self.write_thread.start()

            # initiate write threads for analog output
            self.write_thread = SignalWriter(voltage=5,
                                             frequency=4,
                                             sample_rate=4000,
                                             chunks_per_sec=2)
            self.write_thread.create_task()
        # Debugging without NI instrument
        else:
            # read from a waveform generator
            self.write_thread = DebugSignalGenerator(voltage=1,
                                                     frequency=5,
                                                     sample_rate=500,
                                                     sample_size=500)
            self.write_thread.newData.connect(self.plotter.update_plot)

    @pyqtSlot()
    def button_on_click(self):
        if not DEBUG_MODE:
            if self.write_thread.is_running:
                self.write_thread.stop_signal()
                self.button.setText("Press to start signal")
                print("Started signal")
            else:
                self.write_thread.start_signal()
                self.button.setText("Press to stop signal")
                print("Stopped signal")
        else:
            if not self.write_thread.is_running:
                self.write_thread.start()
                self.button.setText("Signal outputting")
                print("Started Debug signal")

    def closeEvent(self, event):
        print("Closing...")
        self.write_thread.is_running = False
        self.write_thread.exit()


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
        for i in range(0, np.shape(incoming_data)[0]):
            self.plot(incoming_data[i], clear=False, pen=self.pens[i])


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
