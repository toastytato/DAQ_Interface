import pprint

from pyqtgraph.Qt import QtCore
from pyqtgraph.parametertree import *
from PyQt5.QtCore import QSettings

from config import *

class ParamTreeBase(ParameterTree):
    # ParamTree will output a signal that has the param and the output
    paramChange = QtCore.pyqtSignal(object, object)

    def __init__(self, name, params):
        super().__init__()

        self.name = name
        self.settings = QSettings("DAQ_Control", self.name)

        self.param = Parameter.create(
            name=self.name, type="group", children=params
        )

        if self.settings.value("State") != None and not RESET_DEFAULT_PARAMS:
            self.state = self.settings.value("State")
            self.param.restoreState(self.state)
        else:
            print("Loading default params for", self.name)

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
        self.state = self.param.saveState()
        self.settings.setValue("State", self.state)

    def print(self):
        print(self.name)
        print(self.param)

# data container for parameters controlling output and input on each channel
class ChannelParameters(ParamTreeBase):
    def __init__(self):
        self.channel_params = []
        for ch in CHANNEL_NAMES_OUT:
            param = {
                "name": "Output " + ch,
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
                        "value": 0,
                        "step": 0.1,
                        "limits": (MIN_VOLTAGE, MAX_VOLTAGE),
                        "suffix": "V",
                    },
                    {
                        "name": "Frequency",
                        "type": "float",
                        "value": 0,
                        "step": 1,
                        "suffix": "Hz",
                    },
                    {
                        "name": "Phase Shift",
                        "type": "float",
                        "value": 0,
                        "step": 10,
                        "suffix": u"\N{DEGREE SIGN}",
                    },
                ],
            }
            self.channel_params.append(param)

        super().__init__(name="Channel Params", params=self.channel_params)        

# data container for parameters controlling settings saved in configurations tab
class ConfigParamTree(ParamTreeBase):
    def __init__(self):
        self.setting_params = [
            {
                "name": "Writer Config",
                "type": "group",
                "children": [
                    {
                        "name": "Device Name",
                        "type": "str",
                        "value": "Dev1",
                    },
                    {
                        "name": "Sample Rate",
                        "type": "int",
                        "value": 1000,
                    },
                    {
                        "name": "Sample Size",
                        "type": "int",
                        "value": 1000,
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
                        "value": "Dev2",
                    },
                    {
                        "name": "Sample Rate",
                        "type": "int",
                        "value": 500,
                        "limits": (1, 10000),
                    },
                    {
                        "name": "Sample Size",
                        "type": "int",
                        "value": 1000,
                        "limits": (1, 10000),
                    },
                ],
            },
        ]
        # add in the different channels dynamically
        for i, ch in enumerate(CHANNEL_NAMES_OUT):
            self.setting_params[0]["children"].append(
                {
                    "name": ch + " Output Channel",
                    "type": "int",
                    "value": i,
                }
            )
        for i, ch in enumerate(CHANNEL_NAMES_IN):
            self.setting_params[1]["children"].append(
                {
                    "name": ch + " Input Channel",
                    "type": "int",
                    "value": i,
                }
            )

        super().__init__(name="Config Param", params=self.setting_params)

    def get_read_channels(self):
        channels = [
            self.get_param_value("Reader Config", ch + " Input Channel")
            for ch in CHANNEL_NAMES_IN
        ]
        return channels

    def get_write_channels(self):
        channels = [
            self.get_param_value("Writer Config", ch + " Output Channel")
            for ch in CHANNEL_NAMES_OUT
        ]
        return channels


class ControlsParamTree(ParamTreeBase):

    def __init__(self):
        self.control_params = [
            {
                "name": "3D Alignment",
                "type": "group",
                "children": [
                    {
                        "name": "Toggle Output",
                        "type": "bool",
                        "value": False,
                        "tip": "Toggle the output",
                    },
                    {
                        "name": "Amplitude",
                        "type": "float",
                        "value": 0,
                        "step": 0.1,
                    },
                    {
                        "name": "Frequency",
                        "type": "float",
                        "value": 0,
                        "step": 1,
                        "suffix": "Hz",
                    },
                    {
                        "name": "Elevation",
                        "type": "float",
                        "value": 0,
                        "step": 0.1,
                        "suffix": "\N{DEGREE SIGN}",
                    },
                    {
                        "name": "Z-phase",
                        "type": "float",
                        "value": 0,
                        "step": 0.1,
                        "suffix": "\N{DEGREE SIGN}",
                    },
                    {
                        "name": "Coefficients",
                        "type": "group",
                        "expanded": False,
                        "children": [
                            {
                                "name": "kx",
                                "type": "float",
                                "value": 1,
                                "step": 0.1,
                            },
                            {
                                "name": "ky",
                                "type": "float",
                                "value": 1,
                                "step": 0.1,
                            },
                            {
                                "name": "kz",
                                "type": "float",
                                "value": 2,
                                "step": 0.1,
                            },
                        ],
                    },
                ],
            },
            {
                "name": "3D Rotation",
                "type": "group",
                "children": [
                    {
                        "name": "Toggle Output",
                        "type": "bool",
                        "value": False,
                        "tip": "Toggle the output",
                    },
                    {
                        "name": "Amplitude",
                        "type": "float",
                        "value": 0,
                        "step": 0.1,
                    },
                    {
                        "name": "Frequency",
                        "type": "float",
                        "value": 0,
                        "step": 1,
                        "suffix": "Hz",
                    },
                    {
                        "name": "Elevation",
                        "type": "float",
                        "value": 0,
                        "step": 0.1,
                        "suffix": "\N{DEGREE SIGN}",
                    },
                    {
                        "name": "Azimuth ",
                        "type": "float",
                        "value": 0,
                        "step": 0.1,
                        "suffix": "\N{DEGREE SIGN}",
                    },
                    {
                        "name": "Coefficients",
                        "type": "group",
                        "expanded": False,
                        "children": [
                            {
                                "name": "kx",
                                "type": "float",
                                "value": 1,
                                "step": 0.1,
                            },
                            {
                                "name": "ky",
                                "type": "float",
                                "value": 1,
                                "step": 0.1,
                            },
                            {
                                "name": "kz",
                                "type": "float",
                                "value": 2,
                                "step": 0.1,
                            },
                        ],
                    },
                ],
            },
        ]

        super().__init__(name="Controls Param", params=self.control_params)

if __name__ == "__main__":
    print("\nRunning demo for ParameterTree\n")
    param_tree = ChannelParameters()
    param_tree.print()
