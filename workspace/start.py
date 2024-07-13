"""
This module serves as the entry point for running experiments in a simulation environment.
"""

import traceback
from typing import Any

import requests
from utils.cleanup import cleanup_workspace
from utils.helper import setup_folders, setup_logger
from utils.paths import WORKSPACE_FOLDER

logger = setup_logger()


def main() -> None:
    """
    Main function .
    """
    try:
        setup_folders()

        url = "http://localhost:5000/run"
        response = requests.get(url)
        print(response.text)

    except Exception as e:
        logger.error(f"Error in main: {e}")
        traceback.print_exc()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt: Cleaning up workspace.")
    finally:
        cleanup_workspace(WORKSPACE_FOLDER)


if __name__ == "__main__":
    main()
