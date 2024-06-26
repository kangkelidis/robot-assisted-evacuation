# Base workspace folder, copy of this workspace in the container
WORKSPACE_FOLDER = "/home/workspace/"
# Contains Netlogo installation files
NETLOGO_HOME = "/home/netlogo_installation/"

# Contains the core logic of the project
CORE_FOLDER = WORKSPACE_FOLDER + "core/"
# Core subdirectories
# Coontains the model and config files
NETLOGO_FOLDER = CORE_FOLDER + "netlogo/"
# Contains the logic for running the simulations
SIMULATIONS_FOLDER = CORE_FOLDER + "simulations/"
# Contains the utility functions
UTILS_FOLDER = CORE_FOLDER + "utils/"

# Contains the logs
LOGS_FOLDER = WORKSPACE_FOLDER + "logs/"

# Contains the output of the simulations
RESULTS_FOLDER = WORKSPACE_FOLDER + "results/"
# Results subdirectories
DATA_FOLDER = RESULTS_FOLDER + "data/"
FRAMES_FOLDER = RESULTS_FOLDER + "frames/"
IMAGE_FOLDER = RESULTS_FOLDER + "img/"
VIDEO_FOLDER = RESULTS_FOLDER + "video/"
RESULTS_CSV_FILE = DATA_FOLDER + "experiments.csv"

# Contains the adaptation strategies
STRATEGIES_FOLDER = WORKSPACE_FOLDER + "strategies/"

CONFIG_FILE = WORKSPACE_FOLDER + 'config.json'
SCENARIOS_TEMP_FILE_RELATIVE_PATH = 'core/netlogo/' + 'scenarios_temp.json'
