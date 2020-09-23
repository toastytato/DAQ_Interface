import view
import model
import tkinter as tk

NUM_CHANNELS = 4
REFRESH_RATE = 24    # number of refreshes per second
REFRESH_PERIOD = int(1000/REFRESH_RATE)     # refresh period in ms
POLLING_RATE = 25
POLLING_PERIOD = int(1000/POLLING_RATE)

channel_views = list()
channel_data = list()

active_channel = -1
active_widget = -1
active_tab = -1

# periodic function for animations/live feedback

def refresh_graph_output():
    vars_setpoint = []
    vars_sensor = []
    for ch in range(NUM_CHANNELS):
        setpoint = channel_views[ch].controls_view.voltage_slider.get()
        channel_data[ch].update_setpoints(setpoint)
        vars_setpoint.append(channel_data[ch].setpoints)
        vars_sensor.append(channel_data[ch].inputs)

    t_setpoint = channel_data[0].setpoint_times
    t_sensor = channel_data[0].input_times
    graph_notebook.big_graph.animate(t_setpoint, vars_setpoint, t_sensor, vars_sensor)

    root.after(REFRESH_PERIOD, refresh_graph_output)

def refresh_sensor_input():
    for ch in range(NUM_CHANNELS):
        sensor_val = debug_view.input_sliders[ch].get()
        channel_data[ch].update_inputs(sensor_val)
    root.after(POLLING_PERIOD, refresh_sensor_input)


# on event functions

def on_slider_press(event, channel, id):
    global active_channel
    global active_widget
    active_channel = channel
    active_widget = id
    print(active_channel)
    print("pressed")


def on_slider_release(event):
    global active_channel
    global active_widget
    active_channel = -1
    active_widget = -1
    print("released")


def on_notebook_select(event):
    nb = graph_notebook.notebook
    tab_idx = nb.tk.call(nb._w, "identify", "tab", event.x, event.y)
    try:
        active_tab = nb.tab(tab_idx, 'text')
    except:
        print("Nothing selectedD")
        return
    print(active_tab)


# initializations

if __name__ == '__main__':
    root = tk.Tk()
    root.title("DAQ Control Interface")

    debug_view = view.DebugMenuView(root, NUM_CHANNELS)
    graph_notebook = view.AllGraphNotebook(root, NUM_CHANNELS)
    graph_notebook.notebook.bind('<Button-1>', on_notebook_select)
    graph_notebook.grid(row=0, columnspan=NUM_CHANNELS+1)

    # create the 3 output channels
    for i in range(NUM_CHANNELS):
        channel_views.append(view.ChannelView(root, channel=i))
        channel_data.append(model.ChannelData(REFRESH_PERIOD))
        channel_views[i].controls_view.voltage_slider.bind('<Button-1>',
                                                           lambda event, channel=i, id='v':
                                                           on_slider_press(event, channel, id))
        debug_view.input_sliders[i].bind('<Button-1>',
                                         lambda event, channel=4, id=i:
                                         on_slider_press(event, channel, id))

        channel_views[i].controls_view.voltage_slider.bind('<ButtonRelease-1>', on_slider_release)
        debug_view.input_sliders[i].bind('<ButtonRelease-1>', on_slider_release)
        channel_views[i].grid(row=1, column=i, sticky=tk.NSEW)

    debug_view.grid(row=1, column=NUM_CHANNELS, sticky=tk.NSEW)

    refresh_sensor_input()
    refresh_graph_output()
    root.mainloop()
