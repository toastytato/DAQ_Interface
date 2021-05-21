from PyQt5 import QtGui
from config import CHANNEL_NAMES
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import pyqtgraph as pg
import numpy as np

# Graph Widget
class SignalPlot(pg.PlotWidget):
    def __init__(self, legend=None):
        super().__init__()
        # PlotWidget super functions
        self.line_width = 1

        if legend is None:  # default colors if no legend has been created
            self.curve_colors = ["b", "g", "r", "c", "y", "m"]
        else:
            self.curve_colors = legend.curve_colors

        self.pens = [pg.mkPen(i, width=self.line_width) for i in self.curve_colors]
        self.showGrid(y=True)
        # self.disableAutoRange('y')

    def update_plot(self, incoming_data):
        self.clear()
        for i, data in enumerate(incoming_data):
            self.plot(data, clear=False, pen=self.pens[i])


class LegendItem(QWidget):
    def __init__(self, color, name, channel):
        super().__init__()
        self.curve_label = QLabel()
        self.curve_label.setAlignment(Qt.AlignCenter)

        self.color = color
        self.name = name
        self.channel = channel

        layout = QHBoxLayout()
        layout.addWidget(self.curve_label)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)
        self.update()  # calls paintEvent

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, ch):
        self._channel = ch
        self.text = self.name + " Input (Ch." + str(self._channel) + ")"
        self.curve_label.setText(self.text)

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(pg.mkColor(self.color), 3, Qt.SolidLine))

        width, height = painter.device().width(), painter.device().height()
        line_length = 25
        line_start = width / 2 - 70
        painter.drawLine(line_start, height / 2, line_start + line_length, height / 2)


class Legend(QWidget):
    def __init__(self, channels):
        super().__init__()

        layout = QHBoxLayout()
        self.curve_colors = ["b", "g", "r", "c", "y", "m"]

        self.legend_items = [
            LegendItem(color=self.curve_colors[i], name=name, channel=channels[i])
            for i, name in enumerate(CHANNEL_NAMES)
        ]

        for item in self.legend_items:
            layout.addWidget(item)

        self.setLayout(layout)

    def update_channels(self, channels):
        for i, item in enumerate(self.legend_items):
            item.channel = channels[i]
