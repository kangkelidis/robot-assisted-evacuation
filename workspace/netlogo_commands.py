from config import WORKSPACE_FOLDER

NETLOGO_PROJECT_DIRECTORY = "/home/src/"  # type:str
NETLOGO_MODEL_FILE = WORKSPACE_FOLDER + "netlogo/v2.11.1.nlogo"  # type:str
NETLOGO_HOME = "/home/netlogo"  # type:str
RESULTS_CSV_FILE = WORKSPACE_FOLDER + "data/{}_fall_{}_samples_experiment_results.csv"  # type:str

NETLOGO_VERSION = "5"  # type:str

TURTLE_PRESENT_REPORTER = "count turtles"  # type:str
EVACUATED_REPORTER = "number_passengers - count agents + 1"  # type:str
DEAD_REPORTER = "count agents with [ st_dead = 1 ]"  # type:str
SEED_SIMULATION_REPORTER = "seed-simulation"

SET_SIMULATION_ID_COMMAND = 'set SIMULATION_ID "{}"'  # type:str
SET_STAFF_SUPPORT_COMMAND = "set REQUEST_STAFF_SUPPORT {}"  # type: str
SET_PASSENGER_SUPPORT_COMMAND = "set REQUEST_BYSTANDER_SUPPORT {}"  # type: str
SET_FALL_LENGTH_COMMAND = "set DEFAULT_FALL_LENGTH {}"  # type:str
SET_FRAME_GENERATION_COMMAND = "set ENABLE_FRAME_GENERATION {}"  # type: str
SET_FALL_LENGTH_COMMAND = "set DEFAULT_FALL_LENGTH {}"  # type: str
SET_FALL_CHANCE_COMMAND = "set FALL_CHANCE {}"  # type: str

SET_NUM_OF_ROBOTS_COMMAND = "set NUM_OF_ROBOTS {}"  # type: str
SET_NUM_OF_PASSENGERS_COMMAND = "set NUM_OF_PASSENGERS {}"  # type: str
SET_NUM_OF_STAFF_COMMAND = "set NUM_OF_STAFF {}"  # type: str

ENABLE_STAFF_COMMAND = SET_STAFF_SUPPORT_COMMAND.format("TRUE")  # type:str
ENABLE_PASSENGER_COMMAND = SET_PASSENGER_SUPPORT_COMMAND.format("TRUE")  # type:str
ENABLE_FRAME_GENERATION_COMMAND = SET_FRAME_GENERATION_COMMAND.format("TRUE")  # type:str

