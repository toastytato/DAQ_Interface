import sys
import view
import model
from constants import *
import tkinter as tk

channel_views = []
channel_data = []

active_channel = -1
active_widget = -1
active_tab = 0

debug_mode = True


# periodic function for animations/live feedback

def refresh_interface():
    vars_setpoint = []
    time_setpoint = []
    vars_sensor = []
    time_sensor = []

    for ch in range(NUM_CHANNELS):
        setpoint = channel_views[ch].controls_view.voltage_slider.get()
        channel_data[ch].update_setpoints(setpoint)
        if not debug_mode:
            model.analog_out(ch, setpoint)

        v_in = channel_data[ch].voltage_in
        i_in = channel_data[ch].current_in
        channel_views[ch].data_view.update_val(setpoint, v_in, i_in)

        vars_setpoint.append(channel_data[ch].setpoints)
        time_setpoint.append(channel_data[ch].setpoint_times)

        vars_sensor.append(channel_data[ch].inputs)
        time_sensor.append(channel_data[ch].input_times)

        if -1 < active_channel < NUM_CHANNELS:
            channel_views[active_channel].controls_view.refresh_entry()

    if active_tab == 0:
        graph_notebook.big_graph.animate(time_setpoint, vars_setpoint,
                                         time_sensor, vars_sensor)

    root.after(REFRESH_PERIOD, refresh_interface)


def refresh_sensor_input():
    for ch in range(NUM_CHANNELS):
        if debug_mode:
            sensor_val = debug_view.input_sliders[ch].get()
        else:
            sensor_val = model.analog_in(ch)
        channel_data[ch].update_inputs(sensor_val)
    root.after(POLLING_PERIOD, refresh_sensor_input)


# on event functions
# when a widget is interacted with it will call one of these functions

def on_slider_press(event, channel, widget):
    global active_channel
    global active_widget
    active_channel = channel
    active_widget = widget
    print(active_channel)
    print("pressed")


def on_slider_release(event):
    global active_channel
    global active_widget
    active_channel = -1
    active_widget = -1
    print("released")


def value_enter(event, channel, widget):
    value = model.verify_input(event.widget.get())
    channel_views[channel].controls_view.voltage_slider.set(value)
    print('entered')

#
# def usb_enter(event):
#     name = debug_view.usb_entry1.get()


def on_notebook_select(event):
    nb = graph_notebook.notebook
    global active_tab
    tab_idx = nb.tk.call(nb._w, "identify", "tab", event.x, event.y)
    try:
        name = nb.tab(tab_idx, 'text')
        active_tab = tab_idx
    except:
        print("Nothing selectedD")
        return
    print(active_tab)


def debug_mode_toggle(event):
    global debug_mode
    debug_mode = not debug_mode
    if debug_mode:
        debug_view.toggle_text.set("Switch: Normal")
        debug_view.status_text.set("Debugging")
        debug_view.status_label.configure(foreground="red")
    else:
        debug_view.toggle_text.set("Switch: Debug")
        debug_view.status_text.set("Normal")
        debug_view.status_label.configure(foreground="green")


# initializations

if __name__ == '__main__':
    root = tk.Tk()
    root.title("DAQ Control Interface")

    debug_view = view.DebugMenuView(root, NUM_CHANNELS)
    debug_view.toggle_btn.bind('<Button-1>', debug_mode_toggle)
    graph_notebook = view.AllGraphNotebook(root, NUM_CHANNELS)
    graph_notebook.notebook.bind('<Button-1>', on_notebook_select)

    # create the 3 output channels
    for i in range(NUM_CHANNELS):
        channel_views.append(view.ChannelView(root, channel=i))
        channel_data.append(model.ChannelData())
        channel_views[i].controls_view.voltage_slider.bind('<Button-1>',
                                                           lambda event, channel=i, widget='vs':
                                                           on_slider_press(event, channel, widget))
        debug_view.input_sliders[i].bind('<Button-1>',
                                         lambda event, channel=4, widget=i:
                                         on_slider_press(event, channel, widget))
        channel_views[i].controls_view.voltage_entry.bind('<Return>',
                                                          lambda event, channel=i, widget='vt':
                                                          value_enter(event, channel, widget))

        channel_views[i].controls_view.voltage_slider.bind('<ButtonRelease-1>', on_slider_release)
        debug_view.input_sliders[i].bind('<ButtonRelease-1>', on_slider_release)

        channel_views[i].grid(row=1, column=i, sticky=tk.NSEW)

    graph_notebook.grid(row=0, columnspan=NUM_CHANNELS + 1)
    debug_view.grid(row=1, column=NUM_CHANNELS, sticky=tk.NSEW)

    refresh_sensor_input()
    refresh_interface()
    root.protocol("WM_DELETE_WINDOW", sys.exit)
    root.mainloop()
