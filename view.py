import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as tick

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

        # self.graph_view.grid(column=1, row=0)
        self.controls_view.grid(column=0, row=0, sticky=tk.NSEW, padx=(0,5), pady=(10,10))
        self.data_view.grid(column=0, row=1, pady=(0, 10))

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
        self.vout_text = tk.StringVar()
        self.vout_text.set("V_out: 0")
        self.vout_label = tk.Label(self, textvariable=self.vout_text)

        self.vin_text = tk.StringVar()
        self.vin_text.set("V_in: 0")
        self.vin_label = tk.Label(self, textvariable=self.vin_text)

        self.iin_text = tk.StringVar()
        self.iin_text.set("I_in: 0")
        self.iin_label = tk.Label(self, textvariable=self.iin_text)

        self.vout_label.grid()
        self.vin_label.grid()
        self.iin_label.grid()

    def update_val(self, v_out, v_in, current):
        self.vout_text.set("V_out: " + "{:.2f}".format(v_out) + " V")
        self.vin_text.set("V_in: " + "{:.2f}".format(v_in) + " V")
        self.iin_text.set("I_in: " + "{:.2f}".format(current) + " mA")


class BigGraphView(tk.Frame):
    def __init__(self, parent, num_channels):
        tk.Frame.__init__(self, parent)
        self.text = tk.Label(self, text="Big Graph")
        self.text.grid(row=0, columnspan=num_channels*2)

        self.fig = plt.Figure(figsize=(10, 4))
        self.fig.patch.set_facecolor('#E0E0E0')

        self.title = "Voltage"
        self.axes = self.fig.add_subplot(111)

        # self.axes.set_title("hi")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=1, columnspan=num_channels*2)

        self.sensors_draw = []
        self.input_checkbutton = []
        for i in range(num_channels):
            self.sensors_draw.append(tk.IntVar())
            self.input_checkbutton.append(ttk.Checkbutton(self, text=("Input: " + str(i+1)),
                                                          takefocus=0,
                                                          variable=self.sensors_draw[i]))
            self.input_checkbutton[i].invoke()
            self.input_checkbutton[i].grid(row=2, column=i)
        self.setpoints_draw = []
        self.setpoint_checkbutton = []
        for i in range(num_channels):
            self.setpoints_draw.append(tk.IntVar())
            self.setpoint_checkbutton.append(ttk.Checkbutton(self, text=("Setpoint: " + str(i+1)),
                                                             takefocus=0,
                                                             variable=self.setpoints_draw[i]))
            self.setpoint_checkbutton[i].invoke()
            self.setpoint_checkbutton[i].grid(row=2, column=num_channels+i)

    def animate(self, t_setpoint, vars_setpoint, t_sensors, vars_sensor):
        self.axes.clear()
        # self.axes.set_facecolor('#40E0D0')
        self.axes.set_ylabel(self.title)
        self.axes.set_xlabel('Time')
        self.axes.set_ylim([0, 6])
        self.axes.spines['right'].set_visible(False)
        self.axes.spines['top'].set_visible(False)
        for i, (time, var) in enumerate(zip(t_setpoint, vars_setpoint)):
            if self.setpoints_draw[i].get() == 1:
                self.axes.plot(time, var, label="Chan: " + str(i+1))
        for i, (time, var) in enumerate(zip(t_sensors, vars_sensor)):
            if self.sensors_draw[i].get() == 1:
                self.axes.plot(time, var, label="Input: " + str(i+1))
        self.axes.legend(loc='upper right', frameon=False, ncol=len(vars_setpoint)*2)
        self.axes.xaxis.set_major_locator(tick.MaxNLocator(integer=True))
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
        self.voltage_slider = ttk.Scale(self,
                                        from_=0, to=5.0, # resolution=0.01,
                                        orient='horizontal') #, showvalue=0)
        self.voltage_entry = tk.Entry(self, width=5)
        self.voltage_entry.insert(0, self.voltage_slider.get())

        self.text.grid(row=0, column=0) # , sticky=tk.E) # , pady=(15, 0))
        self.voltage_entry.grid(row=0, column=1, sticky=tk.W)
        self.voltage_slider.grid(row=0, column=2, sticky=tk.EW)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

    def refresh_entry(self):
        self.voltage_entry.delete(0, tk.END)
        self.voltage_entry.insert(0, "{:.2f}".format(self.voltage_slider.get()))


class DebugMenuView(tk.LabelFrame):
    def __init__(self, parent, num):
        tk.LabelFrame.__init__(self, parent, text="Debug Menu")
        self.input_sliders = [tk.Scale(self,
                                       from_=0, to=5, resolution=0.01,
                                       orient='horizontal', showvalue=0) for i in range(num)]
        self.toggle_text = tk.StringVar()
        self.toggle_text.set("Debug")
        self.toggle_btn = tk.Button(self, textvariable=self.toggle_text)

        [slider.pack() for slider in self.input_sliders]
        self.toggle_btn.pack()


class CalibrationWindow(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

