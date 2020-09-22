import view
import model
import tkinter as tk

REFRESH_RATE = 2    # number of refreshes per second
REFRESH_PERIOD = (1000/REFRESH_RATE)


root = tk.Tk()
root.title("DAQ Control Interface")

channel_views = list()
num_channels = 3

# create the 3 output channels
for i in range(0, num_channels):
    channel_views.append(view.ChannelView(root, channel=i))
    channel_views[i].pack()

root.mainloop()


def refresh():
    pass
