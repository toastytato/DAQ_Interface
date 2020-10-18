import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as tick

# GUI elements

class JoystickView(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        w = 200
        h = 200
        self.canvas = tk.Canvas(self, width=w, height=h)
        self.canvas.pack(side="top")

        self.canvas.create_rectangle(0,0, w, h, fill="gray")


class ChannelView(tk.LabelFrame):
    def __init__(self, parent, channel):
        tk.LabelFrame.__init__(self, parent, text=("Channel: " + str(channel)))
        self.data_view = DataView(self)
        # self.graph_view = GraphView(self)
        self.controls_view = ControlsView(self)

        # self.graph_view.grid(column=1, row=0)
        self.controls_view.grid(column=0, row=0, sticky=tk.NSEW, padx=(0,5), pady=(5,10))
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
            self.notebook.add(self.channel_graphs[i], text=("Channel: " + str(i)))
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

        self.fig = plt.Figure(figsize=(11, 4))
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
            self.input_checkbutton.append(ttk.Checkbutton(self, text=("Input: " + str(i)),
                                                          takefocus=0,
                                                          variable=self.sensors_draw[i]))
            self.input_checkbutton[i].invoke()
            self.input_checkbutton[i].grid(row=2, column=i)
        self.setpoints_draw = []
        self.setpoint_checkbutton = []
        for i in range(num_channels):
            self.setpoints_draw.append(tk.IntVar())
            self.setpoint_checkbutton.append(ttk.Checkbutton(self, text=("Setpoint: " + str(i)),
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
                self.axes.plot(time, var, label="Chan: " + str(i), linewidth=1)
        for i, (time, var) in enumerate(zip(t_sensors, vars_sensor)):
            if self.sensors_draw[i].get() == 1:
                self.axes.plot(time, var, label="Input: " + str(i), linewidth=1)
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

        modes = ["DC", "AC"]
        self.mode_state = tk.StringVar(self)
        self.mode_state.set(modes[0])

        self.volt_frame = tk.Frame(self)
        self.freq_frame = tk.Frame(self)

        self.mode_options = ttk.OptionMenu(self.volt_frame, self.mode_state, modes[0], *modes)

        self.ac_volt_label = tk.Label(self.volt_frame, text='(V)')
        self.ac_freq_label = tk.Label(self.freq_frame, text="Frequency (Hz): ")

        self.voltage_slider = ttk.Scale(self.volt_frame,
                                        from_=0, to=5.0, # resolution=0.01,
                                        orient='horizontal') #, showvalue=0)
        self.frequency_slider = ttk.Scale(self.freq_frame,
                                        from_=0, to=200,  # resolution=0.01,
                                        orient='horizontal')  # , showvalue=0)

        self.voltage_entry = tk.Entry(self.volt_frame, width=6)
        self.voltage_entry.insert(0, self.voltage_slider.get())

        self.frequency_entry = tk.Entry(self.freq_frame, width=6)
        self.frequency_entry.insert(0, self.frequency_slider.get())

        self.mode_options.pack(side='left')
        self.ac_volt_label.pack(side='left')
        self.voltage_slider.pack(side='right', anchor='e')
        self.voltage_entry.pack(side='right')

        self.ac_freq_label.pack(side='left')
        self.frequency_slider.pack(side='right')
        self.frequency_entry.pack(side='right')

        self.volt_frame.pack(fill='x')
        self.freq_frame.pack()

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

    def refresh_entry(self):
        self.voltage_entry.delete(0, tk.END)
        self.voltage_entry.insert(0, "{:.2f}".format(self.voltage_slider.get()))

        self.frequency_entry.delete(0, tk.END)
        self.frequency_entry.insert(0, "{:.2f}".format(self.frequency_slider.get()))

    def enable_frequency(self):
        print("enable")
        self.ac_freq_label.configure(foreground='black')
        self.frequency_entry.configure(state='normal')
        self.frequency_slider.configure(state='normal')

    def disable_frequency(self):
        print("disable")
        self.ac_freq_label.configure(foreground='gray')
        self.frequency_entry.configure(state='disabled')
        self.frequency_slider.configure(state='disabled')


class DebugMenuView(tk.LabelFrame):
    def __init__(self, parent, num):
        tk.LabelFrame.__init__(self, parent, text="Debug Menu")
        self.input_sliders = [tk.Scale(self,
                                       from_=0, to=5, resolution=0.01,
                                       orient='horizontal', showvalue=0) for i in range(num)]
        self.status_text = tk.StringVar()
        self.status_text.set("Debugging")
        self.status_label = tk.Label(self, textvariable=self.status_text, foreground="red")
        self.toggle_text = tk.StringVar()
        self.toggle_text.set("Switch: Normal")
        self.toggle_btn = tk.Button(self, textvariable=self.toggle_text)

        self.status_label.pack()
        [slider.pack() for slider in self.input_sliders]
        self.toggle_btn.pack()


class CalibrationWindow(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

