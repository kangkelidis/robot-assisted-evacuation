import os
import re
import random
import logging

from typing import List
from multiprocessing import cpu_count

from config import WORKSPACE_FOLDER, ADAPTATION_STRATEGY, GROUP_IDENTIFYING_PERCENTAGE, BOOST_HELPING_CHANCE, REDUCE_HELPING_CHANCE

logger_imported = False
try:
    from concurrent_log_handler import ConcurrentRotatingFileHandler # sometimes causes an error
    logger_imported = True
except ImportError:
    print("Import error")


def setup_logger():
    # logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger()
    # Check if the logger has handlers
    if not logger.handlers and logger_imported:
        # Create a handler that writes log messages to a file
        log_file = 'simulation.log'
        handler = ConcurrentRotatingFileHandler(log_file, "a", 512*1024, 5)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        # Set up the logger to use the handler
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logger()


def is_netlogo_folder(path, file_name):
    return  os.path.isdir(path) and re.match(r'\w{6}', file_name) and not file_name == 'frames' \
            and (  os.path.isfile(os.path.join(path, "count turtles.txt"))\
                or os.path.isfile(os.path.join(path, "number_passengers - count agents + 1.txt"))\
                or os.path.isfile(os.path.join(path, "count agents with [ st_dead = 1 ].txt"))\
                or not os.listdir(path) )


def cleanup_workspace(directory=WORKSPACE_FOLDER):
    """ Deletes all the excess folders created by Netlogo."""

    for file_name in os.listdir(directory):
        path = os.path.join(directory, file_name)
        if is_netlogo_folder(path, file_name):
            print("Deleting folder: ", file_name)
            os.system("rm -r " + path)


def load_adaptation_strategy():
    """ Loads the adaptation strategy from the config file."""
    
    return ADAPTATION_STRATEGY


def adjust_helping_chance(helping_chance):
    # type: (float) -> float

    logger('helping_chance: ', helping_chance)
    """ Adjusts the helping chance based on the group identifying percentage. """

    # TODO: this is called twice, one here and once in the strategy. Should be the same for a single agent
    # increase the helping chance if the potential helper has a group identity by a 50%, decrease otherwise
    if random.random() < GROUP_IDENTIFYING_PERCENTAGE:
        return min(helping_chance + BOOST_HELPING_CHANCE, 1)
    else:
        return max(helping_chance - REDUCE_HELPING_CHANCE, 0)
    

def timeout_exception_handler(signum, frame):
    raise Exception("The function took too long to execute.")


def get_available_cpus():
    # type: () -> int
    """ Returns the number of CPUs available in the system. If the number of CPUs cannot be determined, returns 4."""

    try:
        num_cpus = cpu_count() # type: int
    except:
        num_cpus = 4
    logger.debug("Number of CPUs available: %s", num_cpus)
    return num_cpus