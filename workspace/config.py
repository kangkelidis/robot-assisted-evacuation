# -----data path-----
WORKSPACE_FOLDER = "/home/workspace/"   # type:str
RESULTS_FOLDER = WORKSPACE_FOLDER + "results/"  # type:str
DATA_FOLDER = RESULTS_FOLDER + "data/"  # type:str
FRAMES_FOLDER = RESULTS_FOLDER + "frames/"  # type:str
IMAGE_FOLDER = RESULTS_FOLDER + "img/"  # type:str
VIDEO_FOLDER = RESULTS_FOLDER + "video/"  # type:str

# -----simulation parameters-----
NUM_SAMPLES = 2

MAX_NETLOGO_TICKS = 2000  # type: int

# -----adaptation strategy-----
# Set to None to run a simulation of all strategies
ADAPTATION_STRATEGY = "C"

SIMULATION_SCENARIOS = [
    {
        'name': 'no-support',
        'description': 'No support',

    }
]


# -----Options-----
GENERATE_VIDEO = True