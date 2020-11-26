from pyqtgraph.Qt import QtCore
from pyqtgraph.parametertree import Parameter, ParameterTree
from PyQt5.QtCore import Qt
import pprint

from constants import *


class MyParamTree(ParameterTree):
    # ParamTree will output a signal that has the param and the output
    param_change = QtCore.pyqtSignal(object, object)

    def __init__(self):
        super().__init__()
        default_voltage = 0
        default_frequency = 0

        self.params = []

        for i in range(NUM_CHANNELS):
            channel_params = {
                'name': 'Channel Params',
                'channel': i,
                'children': [
                    {'name': 'Toggle Output',
                     'type': 'bool',
                     'value': False,
                     'tip': "Toggle the output"},
                    {'name': 'Voltage RMS',
                     'type': 'float',
                     'value': default_voltage,
                     'step': 0.25},
                    {'name': 'Frequency',
                     'type': 'float',
                     'value': default_frequency,
                     'step': 10,
                     'siPrefix': True,
                     'suffix': 'Hz'},
                ]
            }
            self.params.append(channel_params)

        self.p = Parameter.create(name='self.params', type='group', children=self.params)
        self.setParameters(self.p, showTop=False)

    def print(self):
        print("Settings")
        pprint.pprint(self.params)


if __name__ == '__main__':
    print('\nRunning demo for ParameterTree\n')
    param_tree = MyParamTree()
    param_tree.print()
