import sys
import view
import model
from old.constants import *
import tkinter as tk
from functools import partial
from writer import SignalWriter

# MAIN: the controller passing data from the view (UI) and model (Data)
# Consists of:
# - Initializing the view elements
# - Callback functions for event triggers on view elements
# - Passing data to model
# - Refreshing the interface
# - Calling the output/input functions to the DAQ

channel_views = []
channel_data = []
channel_io = []

# these flags keep track of which widget or tab is active/activated
active_channel = -1
active_widget = -1
active_tab = 0

# default debug state is true because running the NI DAQ functions without
# the devices connected crashes the program
debug_mode = True


# periodic callback function to refresh the graph animations
def refresh_interface():
    # list for holding the points to plot for all channels
    vars_output = []
    time_output = []
    vars_input = []
    time_input = []

    for ch in range(NUM_CHANNELS):

        # grab inputs from debug menu if debugging
        if debug_mode:
            sensor_val = debug_view.input_sliders[ch].get()
            channel_data[ch].append_graph_inputs(sensor_val)

        # get outputs and store in channel data
        voltage = channel_views[ch].controls_view.voltage_slider.get()
        channel_data[ch].append_graph_outputs(voltage)

        # get last value recorded for inputs to display as text
        v_out = voltage
        v_in = channel_data[ch].inputs[-1]
        i_in = model.voltage_to_current(v_in)
        channel_views[ch].data_view.update_val(v_out, v_in, i_in)

        # add the output and input graph values for all channels to the empty list for plotting
        vars_output.append(channel_data[ch].outputs)
        time_output.append(channel_data[ch].output_times)

        vars_input.append(channel_data[ch].inputs)
        time_input.append(channel_data[ch].input_times)

        # for displaying the frequency graph
        if active_tab - 1 == ch:
            times = channel_io[ch].output_samples
            outputs = channel_io[ch].output_buffer
            graph_notebook.channel_graphs[ch].animate(times, outputs)

    if 0 <= active_channel < NUM_CHANNELS:
        channel_views[active_channel].controls_view.refresh_entry()

    if active_tab == 0:
        graph_notebook.big_graph.animate(time_output, vars_output,
                                         time_input, vars_input)

    root.after(REFRESH_PERIOD, refresh_interface)


# periodic callback function to read and output to the DAQ I/O
def refresh_io():
    for ch in range(NUM_CHANNELS):

        # INPUTS

        # get inputs from DAQ and store in channel data if not debugging
        if not debug_mode:
            sensor_val = channel_io[ch].analog_in()
            channel_data[ch].append_graph_inputs(sensor_val)

        # OUTPUTS

        output_mode = channel_views[ch].controls_view.output_mode_state.get()  # get the selected output mode
        voltage = channel_data[ch].outputs[-1]  # grab latest voltage from the graph outputs

        if voltage == 0:
            writer_thread.running = False
        else:
            if writer_thread.running is False:
                try:
                    writer_thread.start()
                except RuntimeError:  # thread is already started
                    writer_thread.restart()

        # if voltage == 0:
        #     if writer_thread.is_running is True:
        #         writer_thread.stop_signal()
        # else:
        #     if writer_thread.task_created() is False:
        #         writer_thread.create_task()
        #     if writer_thread.is_running is False:
        #         writer_thread.start_signal()

        # update the variables in writer with output parameters
        if output_mode == 'AC' and active_channel:
            frequency = channel_views[ch].controls_view.frequency_slider.get()
            writer_thread.mode = 'AC'
            writer_thread.frequencies = frequency
            writer_thread.voltages = voltage
        elif output_mode == 'DC' and active_channel:
            writer_thread.mode = 'DC'
            writer_thread.voltages = voltage

    root.after(POLLING_PERIOD, refresh_io)


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
    if widget == 'vt':
        value = model.verify_input(event.widget.get(), 0, MAX_VOLTAGE)
        channel_views[channel].controls_view.voltage_slider.set(value)
    elif widget == 'ft':
        value = model.verify_input(event.widget.get(), 0, MAX_FREQUENCY)
        channel_views[channel].controls_view.frequency_slider.set(value)

    print('entered')


def on_output_mode_change(channel, *args):
    print('changed')
    print(channel_views[channel].controls_view.output_mode_state.get())
    if channel_views[channel].controls_view.output_mode_state.get() == 'DC':
        channel_views[channel].controls_view.disable_frequency()
    else:
        channel_views[channel].controls_view.enable_frequency()


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


def on_debug_mode_toggle(event):
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


def on_exit():
    if writer_thread.isRunning():
        writer_thread.exit = True
        writer_thread.restart()
        writer_thread.wait()
    # if writer_thread.is_alive():
    #     writer_thread.exit = True
    #     writer_thread.restart()
    #     writer_thread.join()
    sys.exit()


# initializations
# create the UI elements
# bind key/mouse presses to its assigned function

if __name__ == '__main__':
    root = tk.Tk()
    root.title("DAQ Control Interface")

    # to format the layout better
    SidePanel = tk.Frame(root)  # on the left side
    GraphPanel = tk.Frame(root)  # on the top right side
    ControlsPanel = tk.Frame(root)  # on the bottom right side

    joystick_view = view.JoystickView(SidePanel)
    debug_view = view.DebugMenuView(ControlsPanel, NUM_CHANNELS)
    debug_view.toggle_btn.bind('<Button-1>', on_debug_mode_toggle)
    graph_notebook = view.AllGraphNotebook(GraphPanel, NUM_CHANNELS)
    graph_notebook.notebook.bind('<Button-1>', on_notebook_select)

    # create the 3 output channels
    for i in range(NUM_CHANNELS):
        channel_views.append(view.ChannelView(ControlsPanel, channel=i))
        channel_data.append(model.ChannelInterfaceData())
        channel_io.append(model.ChannelIO(i))

        channel_views[i].controls_view.output_mode_state.trace('w', partial(on_output_mode_change, i))
        on_output_mode_change(i)  # make sure that the first initial state is configured

        channel_views[i].controls_view.voltage_slider.bind('<Button-1>',
                                                           lambda event, channel=i, widget='vs':
                                                           on_slider_press(event, channel, widget))
        channel_views[i].controls_view.frequency_slider.bind('<Button-1>',
                                                             lambda event, channel=i, widget='fs':
                                                             on_slider_press(event, channel, widget))

        channel_views[i].controls_view.voltage_slider.bind('<ButtonRelease-1>', on_slider_release)
        channel_views[i].controls_view.frequency_slider.bind('<ButtonRelease-1>', on_slider_release)

        channel_views[i].controls_view.voltage_entry.bind('<Return>',
                                                          lambda event, channel=i, widget='vt':
                                                          value_enter(event, channel, widget))
        channel_views[i].controls_view.frequency_entry.bind('<Return>',
                                                            lambda event, channel=i, widget='ft':
                                                            value_enter(event, channel, widget))

        debug_view.input_sliders[i].bind('<Button-1>',
                                         lambda event, channel=4, widget=i:
                                         on_slider_press(event, channel, widget))

        debug_view.input_sliders[i].bind('<ButtonRelease-1>', on_slider_release)

        channel_views[i].pack(side='left')

    debug_view.pack(side='left')
    joystick_view.pack()
    # SidePanel.grid(row=0, column=1, rowspan=2)
    graph_notebook.pack()
    GraphPanel.grid(row=0, column=0)
    ControlsPanel.grid(row=1, column=0)

    writer_thread = SignalWriter(voltages=2,
                                 frequencies=4,
                                 sample_rate=2000,
                                 chunks_per_sec=2)

    refresh_interface()
    refresh_io()

    root.protocol("WM_DELETE_WINDOW", on_exit)
    root.mainloop()
