from pyqtgraph.Qt import QtCore
from pyqtgraph.parametertree import Parameter, ParameterTree
from PyQt5.QtCore import Qt
import pprint

from constants import *


class MyParamTree(ParameterTree):
    # ParamTree will output a signal that has the param and the output
    paramChange = QtCore.pyqtSignal(object, object)

    def __init__(self):
        super().__init__()
        default_voltage = 0
        default_frequency = 0
        default_sample_rate = 2000
        default_sample_size = 1000

        # self.setting_params = [{
        #     {'name': 'Config',
        #      'type': 'group',
        #      'children': [
        #          {'name': 'Sample Rate',
        #           'type': 'int',
        #           'value': default_sample_rate},
        #          {'name': 'Sample Size',
        #           'type': 'int',
        #           'value': default_sample_size},
        #      ]}
        # }]

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
                     'step': 0.25,
                     'suffix': 'V'},
                    {'name': 'Frequency',
                     'type': 'float',
                     'value': default_frequency,
                     'step': 1,
                     'suffix': 'Hz'},
                ]
            }
            self.channel_params.append(param)

        self.p = Parameter.create(name='self.params', type='group', children=self.channel_params)
        self.setParameters(self.p, showTop=False)
        self.p.sigTreeStateChanged.connect(self.send_change)  # When the params change, send to method to emit.

    def send_change(self, param, changes):
        self.paramChange.emit(param, changes)

    # Convienience methods for modifying parameter values.
    def get_param_value(self, branch, child):
        """Get the current value of a parameter."""
        return self.p.param(branch, child).value()

    def set_param_value(self, branch, child, value):
        """Set the current value of a parameter."""
        return self.p.param(branch, child).setValue(value)

    def step_param_value(self, child, delta, branch):
        """Change a parameter by a delta. Can be negative or positive."""
        param = self.p.param(branch, child)
        curVal = param.value()
        newVal = curVal + delta
        return param.setValue(newVal)

    def print(self):
        print("Settings")
        pprint.pprint(self.channel_params)


if __name__ == '__main__':
    print('\nRunning demo for ParameterTree\n')
    param_tree = MyParamTree()
    param_tree.print()
