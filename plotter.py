import pyqtgraph as pg
import numpy as np

# Graph Widget
class SignalPlot(pg.PlotWidget):
    def __init__(self):
        super().__init__()
        # PlotWidget super functions
        self.line_width = 1
        self.curve_colors = ["b", "g", "r", "c", "y", "m"]
        self.pens = [pg.mkPen(i, width=self.line_width) for i in self.curve_colors]
        self.showGrid(y=True)
        self.addLegend()
        # self.disableAutoRange('y')

    def update_plot(self, incoming_data):
        self.clear()
        for i in range(np.shape(incoming_data)[0]):
            self.plot(incoming_data[i], clear=False, pen=self.pens[i])


class Legend:
    def __init__(self):
        super().__init__()
        pass