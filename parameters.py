import pprint

from pyqtgraph.Qt import QtCore
from pyqtgraph.parametertree import *

from config import *


class ChannelParamTree(ParameterTree):
    # ParamTree will output a signal that has the param and the output
    paramChange = QtCore.pyqtSignal(object, object)

    def __init__(self):
        super().__init__()
        default_voltage = 1
        default_frequency = 5

        self.channel_params = []
        for i in range(NUM_CHANNELS):
            param = {
                'name': 'Channel ' + str(i),
                'type': 'group',
                'children': [
                    {'name': 'Toggle Output',
                     'type': 'bool',
                     'value': False,
                     'tip': "Toggle the output"},
                    {'name': 'Voltage RMS',
                     'type': 'float',
                     'value': default_voltage,
                     'step': 0.1,
                     'suffix': 'V'},
                    {'name': 'Frequency',
                     'type': 'float',
                     'value': default_frequency,
                     'step': 1,
                     'suffix': 'Hz'},
                    {'name': 'Phase Shift',
                     'type': 'float',
                     'value': 0,
                     'step': 10,
                     'suffix': u'\N{DEGREE SIGN}'}
                ]
            }
            self.channel_params.append(param)

        self.param = Parameter.create(name='channel params', type='group', children=self.channel_params)
        self.setParameters(self.param, showTop=False)
        self.param.sigTreeStateChanged.connect(self.send_change)  # When the params change, send to method to emit.

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

    def print(self):
        print("Settings")
        pprint.pprint(self.channel_params)


class ConfigParamTree(ParameterTree):
    paramChange = QtCore.pyqtSignal(object, object)

    def __init__(self):
        super().__init__()
        default_sample_rate = 1000
        default_sample_size = 1000

        self.setting_params = [{
            'name': 'Writer Config',
            'type': 'group',
            'children': [
                {'name': 'Device Name',
                 'type': 'str',
                 'value': 'Dev1'},
                {'name': 'X Output',
                 'type': 'int',
                 'value': 0},
                {'name': 'Y Output',
                 'type': 'int',
                 'value': 1},
                {'name': 'Z Output',
                 'type': 'int',
                 'value': 2},
                {'name': 'Sample Rate',
                 'type': 'int',
                 'value': default_sample_rate},
                {'name': 'Sample Size',
                 'type': 'int',
                 'value': default_sample_size},
            ]},
            {
                'name': 'Reader Config',
                'type': 'group',
                'children': [
                    {'name': 'Device Name',
                     'type': 'str',
                     'value': 'Dev2'},
                    {'name': 'X Input',
                     'type': 'int',
                     'value': 0},
                    {'name': 'Y Input',
                     'type': 'int',
                     'value': 1},
                    {'name': 'Z Input',
                     'type': 'int',
                     'value': 2},
                    {'name': 'Sample Rate',
                     'type': 'int',
                     'value': 1000},
                    {'name': 'Sample Size',
                     'type': 'int',
                     'value': 1000},
                ]
            }]

        self.param = Parameter.create(name='setting params', type='group', children=self.setting_params)
        self.setParameters(self.param, showTop=False)
        self.param.sigTreeStateChanged.connect(self.send_change)  # When the params change, send to method to emit.

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
        channels = [self.get_param_value('Reader Config', 'X Input'),
                    self.get_param_value('Reader Config', 'Y Input'),
                    self.get_param_value('Reader Config', 'Z Input')]
        return channels

    def get_write_channels(self):
        channels = [self.get_param_value('Writer Config', 'X Output'),
                    self.get_param_value('Writer Config', 'Y Output'),
                    self.get_param_value('Writer Config', 'Z Output')]
        return channels

    def print(self):
        print("Settings")
        pprint.pprint(self.setting_params)


class ControlsParamTree(ParameterTree):
    paramChange = QtCore.pyqtSignal(object, object)

    def __init__(self):
        super().__init__()

        default_frequency = 0
        default_voltage = 0

        self.control_params = [{
            'name': 'Rotating Field',
            'type': 'group',
            'children': [
                {'name': 'Toggle Output',
                 'type': 'bool',
                 'value': False,
                 'tip': "Toggle the output"},
                {'name': 'Voltage RMS',
                 'type': 'float',
                 'value': default_voltage,
                 'step': 0.1,
                 'suffix': 'V'},
                {'name': 'Frequency',
                 'type': 'float',
                 'value': default_frequency,
                 'step': 1,
                 'suffix': 'Hz'},
                {'name': 'Arrangement',
                 'type': 'list',
                 'values': ["0 - 1 - 2",
                            "0 - 2 - 1"], }
            ]}]

        self.param = Parameter.create(name='control params', type='group', children=self.control_params)
        # self.param.addChild(parameterTypes.ListParameter())
        self.setParameters(self.param, showTop=False)
        self.param.sigTreeStateChanged.connect(self.send_change)  # When the params change, send to method to emit.

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


if __name__ == '__main__':
    print('\nRunning demo for ParameterTree\n')
    param_tree = ChannelParamTree()
    param_tree.print()
