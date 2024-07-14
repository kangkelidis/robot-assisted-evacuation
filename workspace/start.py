"""
This module serves as the entry point for running experiments in a simulation environment.
"""

import traceback

import requests
from src.results_analysis import perform_analysis
from src.server import BASE_URL
from utils.cleanup import cleanup_workspace
from utils.helper import setup_folders, setup_logger
from utils.paths import (DATA_FOLDER, EXPERIMENT_FOLDER_NAME, RESULTS_CSV_FILE,
                         WORKSPACE_FOLDER)

logger = setup_logger()


def main() -> None:
    """
    Main function .
    """
    try:
        setup_folders()
        logger.info("-" * 100)
        logger.info("******* Starting Experiment *******")
        data_path = DATA_FOLDER + EXPERIMENT_FOLDER_NAME + "/" + RESULTS_CSV_FILE

        url = BASE_URL + "/start"
        response = requests.post(url, json={"data_path": data_path})

        if response.status_code != 200:
            logger.critical(response.text)
        else:
            logger.info("-" * 100)
            logger.info("Starting Results Analysis...")
            # perform_analysis(data_path)
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
