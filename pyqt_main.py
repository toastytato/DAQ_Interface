import sys

import pyqtgraph as pg
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize, pyqtSlot
from PyQt5.QtWidgets import (QMainWindow, QLabel, QGridLayout, QWidget,
                             QPushButton, QLineEdit)

# --- From DAQ Control --- #
from reader import *
from writer import *


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_threads()

    def init_ui(self):
        self.setMinimumSize(QSize(720, 480))
        self.setWindowTitle("DAQ Interface")

        self.mainbox = QWidget(self)
        self.setCentralWidget(self.mainbox)
        layout = QGridLayout()
        self.mainbox.setLayout(layout)

        title = QLabel("Signal Debugger", self)
        title.setAlignment(QtCore.Qt.AlignHCenter)
        self.plotter = SignalPlot()

        self.b1 = QPushButton('Start Signal Out')
        self.b1.clicked.connect(self.button_on_click)

        self.t1 = QLineEdit()

        layout.addWidget(title)
        layout.addWidget(self.plotter)
        layout.addWidget(self.t1)
        layout.addWidget(self.b1)

    def init_threads(self):
        # When NI instrument is attached
        if not DEBUG_MODE:
            # initiate read threads for analog input
            self.read_thread = SignalReader(sample_rate=500,
                                            sample_size=500)
            self.read_thread.incoming_data.connect(self.plotter.update_plot)
            self.read_thread.start()

            # initiate writer for analog output
            # not handled on separate thread b/c not blocking
            self.writer = SignalWriter(voltage=2,
                                       frequency=5.5,
                                       sample_rate=2000,
                                       chunks_per_sec=2)
            self.writer.create_task()

        # Debugging without NI instrument
        else:
            # Use software signal generator and read from that
            self.debug_writer = DebugSignalGenerator(voltage=1,
                                                     frequency=5.23,
                                                     sample_rate=500,
                                                     sample_size=100)
            self.debug_writer.newData.connect(self.plotter.update_plot)

    @pyqtSlot()
    def button_on_click(self):
        if not DEBUG_MODE:
            if self.writer.is_running:
                print("Stopped DAQ signal")
                self.writer.pause()
                self.b1.setText("Press to start signal")
            else:
                print("Started DAQ signal")
                self.writer.resume()
                self.b1.setText("Press to stop signal")
        else:   # if debugging
            if self.debug_writer.is_running:
                self.debug_writer.pause()
            else:
                self.debug_writer.resume()


    def closeEvent(self, event):
        print("Closing...")
        if not DEBUG_MODE:
            self.read_thread.is_running = False
            self.read_thread.wait()

            self.writer.is_running = False
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
        for i in range(0, np.shape(incoming_data)[0]):
            self.plot(incoming_data[i], clear=False, pen=self.pens[i])


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
