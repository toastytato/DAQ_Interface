# https://pythonprogramminglanguage.com/pyqt5-hello-world/
import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QWidget
from PyQt5.QtCore import QSize
import pyqtgraph as pg
import numpy as np

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.setMinimumSize(QSize(640, 480))
        self.setWindowTitle("Hello world")

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        grid_layout = QGridLayout(self)
        central_widget.setLayout(grid_layout)

        title = QLabel("Hello World from PyQt", self)
        title.setAlignment(QtCore.Qt.AlignHCenter)
        grid_layout.addWidget(title, 0, 0)

class SignalPlot(pg.PlotWidget):
    def __init__(self):
        super().__init__()
        # PlotWidget super functions
        self.line_width = 1
        self.curve_colors = ['b', 'g', 'r', 'c', 'y', 'm']
        self.pens = [pg.mkPen(i, width=self.line_width) for i in self.curve_colors]
        self.showGrid(y=True)
        self.disableAutoRange('y')

    def update_plot(self, incoming_data):
        self.clear()
        for i in range(0, np.shape(incoming_data)[0]):
            self.plot(incoming_data[i], clear=False, pen=self.pens[i])


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
