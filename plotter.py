from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import pyqtgraph as pg

# --- From DAQ Control --- #
from config import CHANNEL_NAMES_IN, CHANNEL_NAMES_OUT
from misc_functions import calculate_rms_value


# Graph Widget
class SignalPlot(pg.PlotWidget):
    """
    Inherits plot widget in order to plot voltage values
    """

    def __init__(self, legend=None):
        super().__init__()
        # PlotWidget super functions
        self.line_width = 1
        self.legend = legend

        if self.legend is None:  # default colors if no legend has been created
            self.curve_colors = ["b", "g", "r", "c", "y", "m"]
        else:
            self.curve_colors = self.legend.curve_colors

        self.pens = [pg.mkPen(i, width=self.line_width) for i in self.curve_colors]
        self.showGrid(y=True)
        # self.disableAutoRange('y')

        self.setLabel("left", "Voltage", units="V")
        self.setLabel("bottom", "Samples")
    
    def on_offsets_received(self, data):
        """
        Holds calibration offset state values here
        """
        self.offsets = data

    def update_plot(self, incoming_data):
        """
        Refresh plot widget to display incoming_data array values
        """
        self.clear()

        # adds each channel's offset to incoming channel
        for i, data in enumerate(incoming_data):
            # this is kinda ugly but it works so let's roll with it
            if self.legend.legend_items[i].toggle_box.isChecked():
                self.plot(data, clear=False, pen=self.pens[i])

#***

class LegendItem(QWidget):
    """"
    Individual widget item for a single plot
    - Allows for toggling visualization on and off
    - Displays current values for said channel
    """
    def __init__(self, color, name, channel):
        super().__init__()
        self.curve_label = QLabel()
        self.curve_label.setAlignment(Qt.AlignCenter)

        self.current_rms_label = QLabel()
        self.current_rms_label.setAlignment(Qt.AlignCenter)

        self.toggle_box = QCheckBox("Test")
        self.toggle_box.setChecked(True)

        self.sample_rate = int()
        self.frequency = float()
        self.current = float()

        self.color = color
        self.name = name
        self.channel = channel

        layout = QVBoxLayout()
        # layout.addWidget(self.curve_label)
        layout.addWidget(self.toggle_box)
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
        self.toggle_box.setText(self.text)

    def set_current_rms(self, data):
        rms = str(calculate_rms_value(data, self.sample_rate, self.frequency))
        self.current_rms_label.setText(rms)

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(pg.mkColor(self.color), 3, Qt.SolidLine))

        width, height = painter.device().width(), painter.device().height()
        line_length = 25
        line_start = 98
        line_height_start = 7
        painter.drawLine(
            line_start, line_height_start, line_start + line_length, line_height_start
        )


class Legend(QWidget):
    """
    Holds multiple legend items and combines them into a single widget
    """
    def __init__(self, channels):
        super().__init__()

        layout = QHBoxLayout()
        self.curve_colors = ["b", "g", "r", "c", "y", "m"]

        self.legend_items = [
            LegendItem(color=self.curve_colors[i], name=name, channel=channels[i])
            for i, name in enumerate(CHANNEL_NAMES_IN)
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
            # prevent index error when more input channels than output channels in DEBUG_MODE
            if i >= len(CHANNEL_NAMES_OUT):
                return
            item.set_current_rms(data[i])
