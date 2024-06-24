from core.paths import *

# -----simulation parameters-----
# Number of times to run the simulation for each scenario
NUM_SAMPLES = 1
NUM_OF_ROBOTS = 1
NUM_OF_PASSENGERS = 100
FALL_LENGTH = 500
FALL_CHANCE = 0.1
# The maximum number of ticks to run the simulation for, it will terminate if it reaches this number
MAX_NETLOGO_TICKS = 2000  # type: int

# -----adaptation strategy-----
# Set to None to run a simulation of all strategies
# set the strategy name to run a simulation of a single strategy
SIMULATION_SCENARIOS = [
    {
        'strategy_name': 'NoRobot',
        'options': {'video': True}
    },
    {
        'strategy_name': 'ProSelf',
        'options': {'video': False}
    },
    {
        'strategy_name': 'ProGroup',
        'options': {'video': False}
    },
    {
        'strategy_name': 'Random',
        'options': {'video': True}
    }
]

TARGET_SCENARIO = 'Random'
# -----Netlogo-----
NETLOGO_MODEL = NETLOGO_FOLDER + "v2.11.1.nlogo"
NETLOGO_CONFIG = NETLOGO_FOLDER + "config_v2.11.1.nls"

# -----Options-----
