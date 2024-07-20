"""
This module serves as the entry point for running experiments.
"""

import argparse
import shutil
import traceback

import requests
from src.results_analysis import perform_analysis
from src.server import BASE_URL
from utils.cleanup import cleanup_workspace
from utils.helper import setup_folders, setup_logger
from utils.paths import EXPERIMENT_FOLDER_STRUCT, WORKSPACE_FOLDER

logger = setup_logger()


def analyse_folder(folder_name: str) -> None:
    """
    Analyse the results of a given folder, in the results folder.

    Args:
        folder_name: The folder name to analyse.
    """
    logger.info(f"Analysing folder: {folder_name}")
    perform_analysis(None, folder_name)


def run_experiment() -> None:
    """ Calls the server to start the experiment and analyses the results. """
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


def main() -> None:
    """
    Main function. Parses the arguments and runs the experiment or analyses a given folder.
    """
    usage_text = "Usage: %(prog)s [--analyse FOLDER]"
    parser = argparse.ArgumentParser(description='Run an experiment or analyse a given folder.',
                                     usage=usage_text)
    parser.add_argument('--analyse', nargs=1, type=str,
                        help='Analyse the results in a given folder.')
    args = parser.parse_args()

    if args.analyse:
        folder_name = args.analyse[0]
        analyse_folder(folder_name)
    else:
        run_experiment()


if __name__ == "__main__":
    main()
