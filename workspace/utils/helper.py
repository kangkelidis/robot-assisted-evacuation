"""
This module provides a set of utility functions for setting up and managing the workspace
for NetLogo simulations.
"""
from __future__ import annotations

import logging
import os
from multiprocessing import cpu_count
from typing import Any, Optional, Union

from utils.paths import *

logger_imported = False
try:
    from concurrent_log_handler import ConcurrentRotatingFileHandler
    logger_imported = True
except ImportError:
    print("Import error. concurrent_log_handler not installed.")


def setup_logger() -> logging.Logger:
    """
    Creates a logger object and sets up the logging configuration.

    This function sets up a logger object and configures it to log messages to a rotating
    log file in the LOGS_FOLDER directory.

    Returns:
        The configured logger object.
    """
    logger = logging.getLogger()
    if not logger.handlers and logger_imported:
        # File handler for debug and above
        log_file = LOGS_FOLDER + 'simulation.log'
        file_handler = ConcurrentRotatingFileHandler(log_file, "a", 512 * 1024, 5)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

        # Console handler for info and above
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

        # Set the logger's level to DEBUG to capture everything
        logger.setLevel(logging.DEBUG)

    return logger


logger = setup_logger()


def convert_dict_to_snake_case(dictionary: dict[str, Any]) -> dict[str, Any]:
    """
    Converts the keys of a dictionary from camelCase to snake_case.

    Args:
        dictionary: The dictionary to be converted.

    Returns:
        The converted dictionary.
    """
    return {convert_camelCase_to_snake_case(key): value for key, value in dictionary.items()}


def convert_camelCase_to_snake_case(camelCase_str: str) -> str:
    """
    Converts a camelCase string to a snake_case string.

    This function takes a camelCase string as input and converts it to a snake_case
    string by inserting underscores before uppercase letters and converting all
    letters to lowercase.

    Args:
        camelCase_str: The camelCase string to be converted.

    Returns:
        The converted snake_case string.
    """
    return ''.join(['_' + i.lower() if i.isupper() else i for i in camelCase_str]).lstrip('_')


def setup_folders() -> None:
    """
    Creates the necessary folders for the workspace.

    This function sets up the folder structure for the NetLogo simulation workspace.
    It creates the RESULTS_FOLDER, LOGS_FOLDER, the experiments folder and sub-folders for data,
    frames, images, and videos. And creates a folder for the current experiment.
    """
    for folder in [RESULTS_FOLDER, LOGS_FOLDER, FRAMES_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # make the experiment folder and its sub-folders
    for path in EXPERIMENT_FOLDER_STRUCT.values():
        if not os.path.exists(path):
            os.makedirs(path)


def get_available_cpus() -> int:
    """
    Returns the number of CPUs available in the system.

    This function attempts to determine the number of CPUs available on the system
    using the `cpu_count()` function from the `multiprocessing` module. If the
    number of CPUs cannot be determined, it returns 1 as a fallback and will run
    simulations sequentially.

    Note:
        Docker will need to use some of the cores available on the system. This may
        lead in a situation where a process running in one of the cores will be terminated.

    Returns:
        The number of available CPUs.
    """
    try:
        num_cpus = cpu_count()  # type: int
    except Exception as e:
        num_cpus = 1
        logger.error(f"Exception in getting number of CPUs. 1 used. : {e}")
    return num_cpus


def get_custom_bar_format() -> str:
    """
    Creates a custom progress bar.

    Returns:
        The custom progress bar format.
    """
    green_color = '\033[92m'

    # Reset color to default
    reset_color = '\033[0m'

    # Custom bar_format with green color
    custom_bar_format = (
        "{}{{l_bar}}{{bar}}{}| {{n_fmt}}/{{total_fmt}} [Elapsed: {{elapsed}}, "
        "Remaining: {{remaining}}, {{rate_fmt}}{{postfix}}]"
    ).format(green_color, reset_color)
    return custom_bar_format
