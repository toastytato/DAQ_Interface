import tkinter as tk
from tkinter import ttk
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
        # self.graph_view = GraphView(self)
        self.controls_view = ControlsView(self)

        # self.data_view.grid(column=0, row=0)
        # self.graph_view.grid(column=1, row=0)
        self.controls_view.grid(column=0, row=0, sticky=tk.NSEW)
        self.grid_columnconfigure(0, weight=1)



class AllGraphNotebook(tk.Frame):
    def __init__(self, parent, num_channels):
        tk.Frame.__init__(self, parent)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack()
        self.big_graph = BigGraphView(self.notebook, num_channels)
        self.channel_graphs = []

        self.notebook.add(self.big_graph, text="All Graphs")
        for i in range(num_channels):
            self.channel_graphs.append(GraphView(self.notebook))
            self.notebook.add(self.channel_graphs[i], text=("Channel: " + str(i+1)))
        self.notebook.pack()


class DataView(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.text = tk.Label(self, text="Data")
        self.text.pack()


class BigGraphView(tk.Frame):
    def __init__(self, parent, num_channels):
        tk.Frame.__init__(self, parent)
        self.text = tk.Label(self, text="Big Graph")
        self.text.grid(row=0, columnspan=num_channels*2)

        self.fig = plt.Figure(figsize=(10, 3))
        self.title = "Voltage"
        self.needs_animate = True

        self.axes = self.fig.add_subplot(111)

        # self.axes.set_title("hi")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=1, columnspan=num_channels*2)

        input_toggle = []
        input_checkbutton = []
        for i in range(num_channels):
            input_toggle.append(tk.IntVar())
            input_checkbutton.append(tk.Checkbutton(self, text=("Input: " + str(i+1)),
                                                    variable=input_toggle[i]))
            input_checkbutton[i].grid(row=2, column=i)
        setpoint_toggle = []
        setpoint_checkbutton = []
        for i in range(num_channels):
            setpoint_toggle.append(tk.IntVar())
            setpoint_checkbutton.append(tk.Checkbutton(self, text=("Setpoint: " + str(i+1)),
                                                       variable=setpoint_toggle[i]))
            setpoint_checkbutton[i].grid(row=2, column=num_channels+i)


    def animate(self, t_setpoint, vars_setpoint, t_sensors, vars_sensor):
        self.axes.clear()
        self.axes.set_ylabel(self.title)
        self.axes.set_xlabel('Time')
        self.axes.set_ylim([0, 6])
        self.axes.spines['right'].set_visible(False)
        self.axes.spines['top'].set_visible(False)
        for var in vars_setpoint:
            self.axes.plot(t_setpoint, var)
        for var in vars_sensor:
            self.axes.plot(t_sensors, var)
        # self.axes.xaxis.set_major_formatter(plt.NullFormatter())
        self.fig.tight_layout()
        self.canvas.draw()


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
        self.text = tk.Label(self, text="Voltage Out:")
        self.text.grid(row=0, column=0, sticky=tk.E, pady=(15, 0))
        self.voltage_slider = tk.Scale(self,
                                       from_=0, to=5.0, resolution=0.01,
                                       orient='horizontal')
        self.voltage_slider.grid(row=0, column=1, sticky=tk.EW, padx=(0, 15))
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

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

