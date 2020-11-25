import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QWidget
from PyQt5.QtCore import QSize
import pyqtgraph as pg
import numpy as np

# --- From DAQ Control --- #
from reader import *
from writer import *

# --- System states --- #
debug_mode = True


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_threads()

    def init_ui(self):
        self.setMinimumSize(QSize(640, 480))
        self.setWindowTitle("Hello world")

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        grid_layout = QGridLayout(self)
        central_widget.setLayout(grid_layout)

        title = QLabel("Signal Debugger", self)
        title.setAlignment(QtCore.Qt.AlignHCenter)
        self.plotter = SignalPlot()

        grid_layout.addWidget(title)
        grid_layout.addWidget(self.plotter)

    def init_threads(self):
        if not debug_mode:
            # initiate read threads for analog input
            self.read_thread = SignalReader(sample_rate=1000,
                                            sample_size=500)
            self.read_thread.newData.connect(self.plotter.update_plot)
            self.read_thread.start()

            # initiate write threads for analog output
            self.write_thread = SignalWriter(voltage=5,
                                             frequency=4,
                                             sample_rate=4000,
                                             chunks_per_sec=2)

        else:
            # read from a waveform generator
            self.read_thread = DebugSignalGenerator(voltage=1,
                                                    frequency=1.23,
                                                    sample_rate=1000,
                                                    sample_size=1000)
            self.read_thread.newData.connect(self.plotter.update_plot)
            self.read_thread.start()

    def closeEvent(self, event):
        print("Closing...")
        self.read_thread.is_running = False
        self.read_thread.exit()


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
