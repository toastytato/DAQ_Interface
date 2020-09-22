import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# GUI elements

# TODO: output current
#       output voltage
#       output frequency
#       three channels


class ChannelView(tk.LabelFrame):
    def __init__(self, parent, channel):
        tk.LabelFrame.__init__(self, parent, text=("Channel: " + str(channel+1)))
        self.graph = GraphsView(self)
        self.controls = ControlsView(self)

        self.graph.grid(column=0, row=0)
        self.controls.grid(column=1, row=0)


class GraphsView(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.text = tk.Label(self, text="Graph")
        self.text.pack()

        fig = plt.Figure(figsize=(10, 2))

        self.axes = fig.add_subplot(111)
        self.axes.set_title("hi")
        self.graph = FigureCanvasTkAgg(fig, master=self)

        fig.tight_layout()
        self.graph.get_tk_widget().pack()

    def update(self):
        pass


class ControlsView(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.text = tk.Label(self, text="Controls")
        self.text.pack()

    def update(self):
        pass
