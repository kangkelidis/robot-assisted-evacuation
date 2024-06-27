import logging
import os
from multiprocessing import cpu_count

from paths import *

logger_imported = False
try:
    from concurrent_log_handler import ConcurrentRotatingFileHandler
    logger_imported = True
except ImportError:
    print("Import error. concurrent_log_handler in logging.py")


def setup_logger():
    # type: () -> logging.Logger
    """
    Creates a logger object and sets up the logging configuration.
    Saves the log file in the current working directory.
    """
    logger = logging.getLogger()
    if not logger.handlers and logger_imported:
        log_file = LOGS_FOLDER + 'simulation.log'
        handler = ConcurrentRotatingFileHandler(log_file, "a", 512 * 1024, 5)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = setup_logger()


def convert_camelCase_to_snake_case(camelCase_str):
    # type: (str) -> str
    return ''.join(['_' + i.lower() if i.isupper() else i for i in camelCase_str]).lstrip('_')


def generate_simulation_id(scenario, index):
    # type: (str, int) -> str
    return scenario + "_" + str(index)


def get_scenario_name(simulation_id):
    # type: (str) -> str
    return simulation_id.split("_")[0]


def get_scenario_index(simulation_id):
    # type: (str) -> str
    return simulation_id.split("_")[1]


def setup_folders():
    # type: () -> None
    """ Creates the necessary folders for the workspace."""
    if not os.path.exists(RESULTS_FOLDER):
        os.makedirs(RESULTS_FOLDER)

    if not os.path.exists(LOGS_FOLDER):
        os.makedirs(LOGS_FOLDER)

    experiment_folder_name = get_experiment_folder()
    for folder in [DATA_FOLDER, FRAMES_FOLDER, IMAGE_FOLDER, VIDEO_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    for folder in [DATA_FOLDER, IMAGE_FOLDER]:
        experiment_folder_path = os.path.join(folder, experiment_folder_name)
        if not os.path.exists(experiment_folder_path):
            os.makedirs(experiment_folder_path)


def timeout_exception_handler(signum, frame):
    raise Exception("The function took too long to execute.")


def get_available_cpus():
    # type: () -> int
    """
    Returns the number of CPUs available in the system.
    If the number of CPUs cannot be determined, returns 4.
    """
    try:
        num_cpus = cpu_count()  # type: int
    except Exception as e:
        num_cpus = 4
        logger.error("Exception in getting number of CPUs. 4 used. : %s", e)
    return num_cpus
