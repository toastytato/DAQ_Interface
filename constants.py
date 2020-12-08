
# CONSTANTS used

# Constants for main
DEBUG_MODE = True

# Number of channels to sample/display
NUM_CHANNELS = 1
# Refresh rate for GUI display and slider sampling
REFRESH_RATE = 24
REFRESH_PERIOD = int(1000/REFRESH_RATE)     # in ms
# Refresh rate for sensor sampling
POLLING_RATE = 10
POLLING_PERIOD = int(1000 / POLLING_RATE)  # in ms

# Constants for model
MAX_VOLTAGE = 5
MAX_FREQUENCY = 200
CURRENT_SHUNT_RESISTANCE = 1

# viewing frame time of big graph in seconds
TIME_WINDOW = 2

# parameters for IO and debugger
PARAMS = {
    "writer": {
        "voltage": [2, 1],
        "frequency": [10, 5],
        "sample_rate": 4000,
        "chunks_per_sec": 2
    },
    "reader": {
        "sample_rate": 500,
        "sample_size": 500
    },
    "debugger": {
        "voltage": [1, 2],
        "frequency": [.5645, 2.5],
        "sample_rate": 500,
        "sample_size": 250
    }
}
