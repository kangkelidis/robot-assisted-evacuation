"""
This module serves as the entry point for running experiments in a simulation environment.
"""

import shutil
import traceback

import requests
from src.results_analysis import perform_analysis
from src.server import BASE_URL
from utils.cleanup import cleanup_workspace
from utils.helper import setup_folders, setup_logger
from utils.paths import EXPERIMENT_FOLDER_STRUCT, WORKSPACE_FOLDER

logger = setup_logger()


def main() -> None:
    """
    Main function .
    """
    try:
        terminal_size = shutil.get_terminal_size(fallback=(80, 20))

        setup_folders()
        logger.info("-" * terminal_size.columns)
        logger.info("******* Starting Experiment *******")

        url = BASE_URL + "/start"
        response = requests.post(url, json={"experiment_folder": EXPERIMENT_FOLDER_STRUCT})

        if response.status_code != 200:
            logger.critical(response.text)
        else:
            logger.info("-" * terminal_size.columns)
            logger.info("Starting Results Analysis...")
            perform_analysis(EXPERIMENT_FOLDER_STRUCT)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        traceback.print_exc()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt: Cleaning up workspace.")
    finally:
        cleanup_workspace(WORKSPACE_FOLDER)
        logger.info("Done!")


if __name__ == "__main__":
    main()
    # TODO add arguments to either run or analyse a given folder
    # perform_analysis('240714_222344')
