import view
import model
import tkinter as tk
import threading

REFRESH_RATE = 10    # number of refreshes per second
REFRESH_PERIOD = int(1000/REFRESH_RATE)     # refresh period in ms
NUM_CHANNELS = 3    # number of output channels

channel_views = list()
channel_data = list()


active_channel = -1
active_widget = -1

# independent thread event to speed up runtime

def thread_function(t, y, z):
    pass

# periodic function for animations/live feedback

def refresh():
    threads = []
    for i in range(NUM_CHANNELS):
        if active_channel != -1 and active_channel < NUM_CHANNELS:  # active_channel is not the debug
            voltage = channel_views[active_channel].controls_view.voltage_slider.get()
            channel_data[active_channel].voltage_set = voltage
        # get input from debug menu
        # TODO: get it from NI device later
        in_data = debug_view.input_sliders[i].get()
        channel_data[i].update_values(in_data)
        # t, y, z are lists of values to plot
        t = channel_data[i].times
        y = channel_data[i].setpoints
        z = channel_data[i].inputs
        channel_views[i].graph_view.animate(t, y, z)

    root.after(REFRESH_PERIOD, refresh)

# on event functions

def slider_press(event, channel, id):
    global active_channel
    global active_widget
    active_channel = channel
    active_widget = id
    print(active_channel)
    print("pressed")


def slider_release(event):
    global active_channel
    global active_widget
    active_channel = -1
    active_widget = -1
    print("released")


# initializations

if __name__ == '__main__':
    root = tk.Tk()
    root.title("DAQ Control Interface")

    debug_view = view.DebugMenuView(root, NUM_CHANNELS)

    # create the 3 output channels
    for i in range(NUM_CHANNELS):
        channel_views.append(view.ChannelView(root, channel=i))
        channel_data.append(model.ChannelData(REFRESH_PERIOD))
        channel_views[i].controls_view.voltage_slider.bind('<Button-1>',
                                                           lambda event, channel=i, id='v':
                                                           slider_press(event, channel, id))
        debug_view.input_sliders[i].bind('<Button-1>',
                                         lambda event, channel=4, id=i:
                                         slider_press(event, channel, id))

        channel_views[i].controls_view.voltage_slider.bind('<ButtonRelease-1>', slider_release)
        debug_view.input_sliders[i].bind('<ButtonRelease-1>', slider_release)
        channel_views[i].pack()

    debug_view.pack(side=tk.BOTTOM)

    refresh()
    root.mainloop()
