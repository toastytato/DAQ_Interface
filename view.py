import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# GUI elements

# TODO: output current
#       output voltage
#       output frequency
#       three channels
#       calibrate voltage to input


class ChannelView(tk.LabelFrame):
    def __init__(self, parent, channel):
        tk.LabelFrame.__init__(self, parent, text=("Channel: " + str(channel+1)))
        self.data_view = DataView(self)
        self.graph_view = GraphView(self)
        self.controls_view = ControlsView(self)

        self.data_view.grid(column=0, row=0)
        self.graph_view.grid(column=1, row=0)
        self.controls_view.grid(column=2, row=0)


class DataView(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.text = tk.Label(self, text="Data")
        self.text.pack()


class GraphView(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.text = tk.Label(self, text="Graph")
        self.text.pack()

        self.fig = plt.Figure(figsize=(9, 2))
        self.title = "Voltage"
        self.needs_animate = True

        self.axes = self.fig.add_subplot(111)

        # self.axes.set_title("hi")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH)

    def animate(self, t, y, z):
        # if self.needs_animate:

        self.axes.clear()
        self.axes.set_ylabel(self.title)
        self.axes.set_xlabel('Time')
        self.axes.set_ylim([0, 6])
        self.axes.plot(t, y,
                       t, z)
        self.axes.xaxis.set_major_formatter(plt.NullFormatter())
        self.fig.tight_layout()
        self.canvas.draw()

        # if all(val == y[-1] for val in y) and all(val == z[-1] for val in z) and (t[-1] - t[0]) >= 2:
        #     self.needs_animate = False
        # else:
        #     self.needs_animate = True


class ControlsView(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.text = tk.Label(self, text="Controls")
        self.text.grid(row=0, column=0)
        self.voltage_slider = tk.Scale(self,
                                       from_=0, to=5.0, resolution=0.01,
                                       orient='horizontal')
        self.voltage_slider.grid(row=0, column=1)

    def update(self):
        pass


class DebugMenuView(tk.LabelFrame):
    def __init__(self, parent, num):
        tk.LabelFrame.__init__(self, parent, text="Debug Menu")
        self.input_sliders = [tk.Scale(self,
                                       from_=0, to=5, resolution=0.01,
                                       orient='horizontal') for i in range(num)]
        [slider.pack() for slider in self.input_sliders]


class CalibrationWindow(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

