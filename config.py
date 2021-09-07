# Global contants

# True if no NI-DAQ Hardware is attached. Data will be simulated
DEBUG_MODE = True

# Sets the number of concurrent output/input channels as well as their names
# Make sure CHANNEL_NAMES_OUT has at least 3 names assigned
# also keep the same order to have the correct real life axis representation
CHANNEL_NAMES_OUT = ["X", "Y", "Z"]
CHANNEL_NAMES_IN = ["X1", "X2", "Y1"]

# Voltage Limits on output DAQ
MAX_VOLTAGE = 10
MIN_VOLTAGE = -10

# Reset to default param values (used when changes are made to param_tree code)
RESET_DEFAULT_PARAMS = True
