"""
This module provides functionality for cleaning up the workspace
from folders created by the NetLogo simulations.
"""
import os
import shutil
import sys

from utils.paths import FRAMES_FOLDER, RESULTS_FOLDER, WORKSPACE_FOLDER


def signal_handler(sig, frame):
    print("Server stopped")
    cleanup_workspace()
    sys.exit(0)


def clear_empty_results_folders():
    """
    Deletes all the empty results folders.
    """
    for folder in os.listdir(RESULTS_FOLDER):
        if not os.path.isdir(os.path.join(RESULTS_FOLDER, folder)):
            continue

        experiment_folder_path = os.path.join(RESULTS_FOLDER, folder)
        if experiment_folder_path == FRAMES_FOLDER[:-1]:
            continue

        # if all the sub-folders are empty, delete the experiment folder
        all_empty = True
        for subfolder in os.listdir(experiment_folder_path):
            subfolder_path = os.path.join(experiment_folder_path, subfolder)
            if os.path.isdir(subfolder_path) and os.listdir(subfolder_path):
                all_empty = False  # Found a non-empty subfolder
                break
        if all_empty:
            print("Deleting empty experiment folder: ", experiment_folder_path)
            shutil.rmtree(experiment_folder_path)


def cleanup_workspace(directory: str = WORKSPACE_FOLDER) -> None:
    """
    Deletes all the excess folders created by Netlogo and by the program.

    Args:
        directory: The path to the directory to clean up.
    """
    clear_empty_results_folders()

    # Delete error log files from java
    for file_name in os.listdir(directory):
        if file_name.startswith("hs_err_pid"):
            print("Deleting error log: ", file_name)
            os.system("rm -r " + os.path.join(directory, file_name))


if __name__ == '__main__':
    # When called directly, from parent directory
    cleanup_workspace('workspace/')
