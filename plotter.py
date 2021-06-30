from PyQt5 import QtGui
from config import CHANNEL_NAMES
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import pyqtgraph as pg
import numpy as np
import math

# TODO:
#   account for 0 freq (DC)
#   if period > sample size --> rms of sample size
def calculate_rms_value(data, sample_rate, frequency):
    # freq = cycles / sec
    # period = 1 / freq
    # rate = samples / sec
    # data = samples
    # samples / cycle = rate * period

    if frequency != 0:
        num_samples_in_period = int(sample_rate * (1 / frequency))

        if num_samples_in_period < 500:
            num_samples_in_period = 500
    else:
        return data[0]  # only need 1st data point since DC

    # period_data = data[:num_samples_in_period]
    period_data = data
    print(len(period_data))
    rms = round(np.sqrt(np.mean(period_data ** 2)), 3)

    return rms


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

        self.current_rms_label = QLabel()
        self.current_rms_label.setAlignment(Qt.AlignCenter)

        self.sample_rate = int()
        self.frequency = float()
        self.current = float()

        self.color = color
        self.name = name
        self.channel = channel

        layout = QVBoxLayout()
        layout.addWidget(self.curve_label)
        layout.addWidget(self.current_rms_label)
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

    def set_current_rms(self, data):
        rms = str(calculate_rms_value(data, self.sample_rate, self.frequency))
        self.current_rms_label.setText(rms)

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(pg.mkColor(self.color), 3, Qt.SolidLine))

        width, height = painter.device().width(), painter.device().height()
        line_length = 25
        line_start = width / 2 - 70
        line_height_start = 7
        painter.drawLine(
            line_start, line_height_start, line_start + line_length, line_height_start
        )


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

    def update_rms_params(self, sample_rate, frequencies=None):
        for i, item in enumerate(self.legend_items):
            item.sample_rate = sample_rate
            if frequencies is not None:
                item.frequency = frequencies[i]

    def on_new_data(self, data):
        for i, item in enumerate(self.legend_items):
            item.set_current_rms(data[i])
