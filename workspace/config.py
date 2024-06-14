# -----data path-----
WORKSPACE_FOLDER = "/home/workspace/"   # type:str
DATA_FOLDER = WORKSPACE_FOLDER + "data/"  # type:str
FRAMES_FOLDER = WORKSPACE_FOLDER + "frames/"  # type:str
IMAGE_FOLDER = WORKSPACE_FOLDER + "img/"  # type:str
VIDEO_FOLDER = WORKSPACE_FOLDER + "video/"  # type:str

# -----simulation parameters-----
NUM_SAMPLES = 1

MAX_NETLOGO_TICKS = 2000  # type: int

# -----identity prediction-----
GROUP_IDENTIFYING_PERCENTAGE = 0.8
IDENTITY_PREDICTION_ACCURANCY = 0.9

BOOST_HELPING_CHANCE = 0 # [0, 1]
REDUCE_HELPING_CHANCE = 0

# -----adaptation strategy-----
# Set to None to run a simulation of all strategies
ADAPTATION_STRATEGY = "C"

# -----Options-----
GENERATE_VIDEO = True