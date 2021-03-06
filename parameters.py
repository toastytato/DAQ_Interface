import pprint

from pyqtgraph.Qt import QtCore
from pyqtgraph.parametertree import *
from PyQt5.QtCore import QSettings

from config import *


class ChannelParamTree(ParameterTree):
    # ParamTree will output a signal that has the param and the output
    paramChange = QtCore.pyqtSignal(object, object)

    def __init__(self):
        super().__init__()

        self.settings = QSettings("DAQ_Control", "Channels Param")

        self.channel_params = []
        for i in range(NUM_CHANNELS):
            param = {
                "name": "Channel " + str(i),
                "type": "group",
                "children": [
                    {
                        "name": "Toggle Output",
                        "type": "bool",
                        "value": False,
                        "tip": "Toggle the output",
                    },
                    {
                        "name": "Voltage RMS",
                        "type": "float",
                        "value": self.settings.value("Ch" + str(i) + "Voltage"),
                        "step": 0.1,
                        "suffix": "V",
                    },
                    {
                        "name": "Frequency",
                        "type": "float",
                        "value": self.settings.value("Ch" + str(i) + "Frequency"),
                        "step": 1,
                        "suffix": "Hz",
                    },
                    {
                        "name": "Phase Shift",
                        "type": "float",
                        "value": self.settings.value("Ch" + str(i) + "Phase"),
                        "step": 10,
                        "suffix": u"\N{DEGREE SIGN}",
                    },
                ],
            }
            self.channel_params.append(param)

        self.param = Parameter.create(
            name="channel params", type="group", children=self.channel_params
        )
        self.setParameters(self.param, showTop=False)
        # When the params change, send to method to emit.
        self.param.sigTreeStateChanged.connect(self.send_change)

    def send_change(self, param, changes):
        self.paramChange.emit(param, changes)

    # Convienience methods for modifying parameter values.
    def get_param_value(self, branch, child):
        """Get the current value of a parameter."""
        return self.param.param(branch, child).value()

    def set_param_value(self, branch, child, value):
        """Set the current value of a parameter."""
        return self.param.param(branch, child).setValue(value)

    def step_param_value(self, child, delta, branch):
        """Change a parameter by a delta. Can be negative or positive."""
        param = self.param.param(branch, child)
        curVal = param.value()
        newVal = curVal + delta
        return param.setValue(newVal)

    def save_settings(self):
        for i in range(NUM_CHANNELS):
            print(self.get_param_value("Channel " + str(i), "Voltage RMS"))
            self.settings.setValue(
                "Ch" + str(i) + "Voltage",
                self.get_param_value("Channel " + str(i), "Voltage RMS"),
            )

            self.settings.setValue(
                "Ch" + str(i) + "Frequency",
                self.get_param_value("Channel " + str(i), "Frequency"),
            )
            self.settings.setValue(
                "Ch" + str(i) + "Phase",
                self.get_param_value("Channel " + str(i), "Phase Shift"),
            )

    def print(self):
        print("Settings")
        pprint.pprint(self.channel_params)


class ConfigParamTree(ParameterTree):
    paramChange = QtCore.pyqtSignal(object, object)

    def __init__(self):
        super().__init__()

        self.settings = QSettings("DAQ_Control", "Config Param")

        self.setting_params = [
            {
                "name": "Writer Config",
                "type": "group",
                "children": [
                    {
                        "name": "Device Name",
                        "type": "str",
                        "value": self.settings.value("Writer Device Name"),
                    },
                    {
                        "name": "X Output",
                        "type": "int",
                        "value": self.settings.value("X Output Channel"),
                    },
                    {
                        "name": "Y Output",
                        "type": "int",
                        "value": self.settings.value("Y Output Channel"),
                    },
                    {
                        "name": "Z Output",
                        "type": "int",
                        "value": self.settings.value("Z Output Channel"),
                    },
                    {
                        "name": "Sample Rate",
                        "type": "int",
                        "value": self.settings.value("Writer Sample Rate"),
                    },
                    {
                        "name": "Sample Size",
                        "type": "int",
                        "value": self.settings.value("Writer Sample Size"),
                    },
                ],
            },
            {
                "name": "Reader Config",
                "type": "group",
                "children": [
                    {
                        "name": "Device Name",
                        "type": "str",
                        "value": self.settings.value("Reader Device Name"),
                    },
                    {
                        "name": "X Input",
                        "type": "int",
                        "value": self.settings.value("X Input Channel"),
                    },
                    {
                        "name": "Y Input",
                        "type": "int",
                        "value": self.settings.value("Y Input Channel"),
                    },
                    {
                        "name": "Z Input",
                        "type": "int",
                        "value": self.settings.value("Z Input Channel"),
                    },
                    {
                        "name": "Sample Rate",
                        "type": "int",
                        "value": self.settings.value("Reader Sample Rate"),
                    },
                    {
                        "name": "Sample Size",
                        "type": "int",
                        "value": self.settings.value("Reader Sample Size"),
                    },
                ],
            },
        ]

        self.param = Parameter.create(
            name="setting params", type="group", children=self.setting_params
        )
        self.setParameters(self.param, showTop=False)
        # When the params change, send to method to emit.
        self.param.sigTreeStateChanged.connect(self.send_change)

    def send_change(self, param, changes):
        self.paramChange.emit(param, changes)

    # Convienience methods for modifying parameter values.
    def get_param_value(self, branch, child):
        """Get the current value of a parameter."""
        return self.param.param(branch, child).value()

    def set_param_value(self, branch, child, value):
        """Set the current value of a parameter."""
        return self.param.param(branch, child).setValue(value)

    def get_read_channels(self):
        channels = [
            self.get_param_value("Reader Config", "X Input"),
            self.get_param_value("Reader Config", "Y Input"),
            self.get_param_value("Reader Config", "Z Input"),
        ]
        return channels

    def get_write_channels(self):
        channels = [
            self.get_param_value("Writer Config", "X Output"),
            self.get_param_value("Writer Config", "Y Output"),
            self.get_param_value("Writer Config", "Z Output"),
        ]
        return channels

    def save_settings(self):
        for i in range(NUM_CHANNELS):
            self.settings.setValue(
                "Writer Device Name",
                self.get_param_value("Writer Config", "Device Name"),
            )
            self.settings.setValue(
                "X Output Channel", self.get_param_value("Writer Config", "X Output")
            )
            self.settings.setValue(
                "Y Output Channel", self.get_param_value("Writer Config", "Y Output")
            )
            self.settings.setValue(
                "Z Output Channel", self.get_param_value("Writer Config", "Z Output")
            )
            self.settings.setValue(
                "Writer Sample Rate",
                self.get_param_value("Writer Config", "Sample Rate"),
            )
            self.settings.setValue(
                "Writer Sample Size",
                self.get_param_value("Writer Config", "Sample Size"),
            )

            self.settings.setValue(
                "Reader Device Name",
                self.get_param_value("Reader Config", "Device Name"),
            )
            self.settings.setValue(
                "X Input Channel", self.get_param_value("Reader Config", "X Input")
            )
            self.settings.setValue(
                "Y Input Channel", self.get_param_value("Reader Config", "Y Input")
            )
            self.settings.setValue(
                "Z Input Channel", self.get_param_value("Reader Config", "Z Input")
            )
            self.settings.setValue(
                "Reader Sample Rate",
                self.get_param_value("Reader Config", "Sample Rate"),
            )
            self.settings.setValue(
                "Reader Sample Size",
                self.get_param_value("Reader Config", "Sample Size"),
            )

    def print(self):
        print("Settings")
        pprint.pprint(self.setting_params)


class ControlsParamTree(ParameterTree):
    paramChange = QtCore.pyqtSignal(object, object)

    def __init__(self):
        super().__init__()

        default_frequency = 0
        default_voltage = 0

        self.control_params = [
            {
                "name": "Rotating Field",
                "type": "group",
                "children": [
                    {
                        "name": "Toggle Output",
                        "type": "bool",
                        "value": False,
                        "tip": "Toggle the output",
                    },
                    {
                        "name": "Voltage RMS",
                        "type": "float",
                        "value": default_voltage,
                        "step": 0.1,
                        "suffix": "V",
                    },
                    {
                        "name": "Frequency",
                        "type": "float",
                        "value": default_frequency,
                        "step": 1,
                        "suffix": "Hz",
                    },
                    {
                        "name": "Arrangement",
                        "type": "list",
                        "values": ["0 - 1 - 2", "0 - 2 - 1"],
                    },
                ],
            }
        ]

        self.param = Parameter.create(
            name="control params", type="group", children=self.control_params
        )
        # self.param.addChild(parameterTypes.ListParameter())
        self.setParameters(self.param, showTop=False)
        # When the params change, send to method to emit.
        self.param.sigTreeStateChanged.connect(self.send_change)

    def send_change(self, param, changes):
        self.paramChange.emit(param, changes)

    # Convienience methods for modifying parameter values.
    def get_param_value(self, branch, child):
        """Get the current value of a parameter."""
        return self.param.param(branch, child).value()

    def set_param_value(self, branch, child, value):
        """Set the current value of a parameter."""
        return self.param.param(branch, child).setValue(value)

    def print(self):
        print("Controls")
        pprint.pprint(self.control_params)


if __name__ == "__main__":
    print("\nRunning demo for ParameterTree\n")
    param_tree = ChannelParamTree()
    param_tree.print()
