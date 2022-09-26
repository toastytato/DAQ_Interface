# Global contants

# True if no NI-DAQ Hardware is attached. Data will be simulated
DEBUG_MODE = True

# Sets the number of concurrent output/input channels as well as their names
# Make sure CHANNEL_NAMES_OUT has at least 3 names assigned
# also keep the same order to have the correct real life axis representation
# Eg. ["X", "Y", "Z"] means Output X is on ao0, Y is on ao1, Z is on ao2
CHANNEL_NAMES_OUT = ["X", "Y", "Z"]
# Eg. ["X1", "X2", "Y1", "Y2", "Z"] means Input X1 is on ai0, X2 is on ai1, and so on
# the channel # is based on its index
CHANNEL_NAMES_IN = ["X1", "X2", "Y1", "Y2", "Z"]

# Voltage set in DAQ output to compare against when calibrating
CALIBRATION_VOLTAGE = 0

# Voltage Limits on output DAQ
MAX_VOLTAGE = 10
MIN_VOLTAGE = -10

# Reset to default param values (used when changes are made to param_tree code)
# True: Params will always be set to defaults in code
# False: Params will be what it was last set
# Suggested to set True when modifying parameter.py
RESET_DEFAULT_PARAMS = True
