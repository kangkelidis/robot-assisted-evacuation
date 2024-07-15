"""
This module provides functionality for cleaning up the workspace
from folders created by the NetLogo simulations.
"""
# TODO: delete results dated folder if empty
import os
from pathlib import Path

from utils.paths import DATA_FOLDER, IMAGE_FOLDER, VIDEO_FOLDER


def is_netlogo_folder(path: str) -> bool:
    """
    Checks if the folder is created by NetLogo.

    A NetLogo folder is a folder that contains the reporter commands for the simulation.

    Args:
        path: The path to check.

    Returns:
        True if the folder is created by NetLogo, False otherwise.
    """
    return os.path.isdir(path) and \
        (os.path.isfile(os.path.join(path, "count turtles.txt")) or
         os.path.isfile(os.path.join(path, "number_passengers - count agents + 1.txt")) or
         os.path.isfile(os.path.join(path, "count agents with [ st_dead = 1 ].txt")) or
         not os.listdir(path))


def cleanup_workspace(directory: str) -> None:
    """
    Deletes all the excess folders created by Netlogo and the tempfiles by the program.

    Args:
        directory: The path to the directory to clean up.
    """
    for file_name in os.listdir(directory):
        path = os.path.join(directory, file_name)
        if is_netlogo_folder(path):
            print("Deleting folder: ", file_name)
            os.system("rm -r " + path)

    # Delete empty folders in the results folder
    for folder in [DATA_FOLDER, IMAGE_FOLDER, VIDEO_FOLDER]:
        for folder in Path(folder).iterdir():
            if folder.is_dir():
                items = list(folder.iterdir())
                if not items or len(items) == 1 and items[0].name.endswith('.json'):
                    print("Deleting empty folder: ", folder)
                    os.system(f"rm -r {folder}")

    # Delete error log files from java
    for file_name in os.listdir(directory):
        if file_name.startswith("hs_err_pid"):
            print("Deleting error log: ", file_name)
            os.system("rm -r " + os.path.join(directory, file_name))


if __name__ == '__main__':
    # When called directly, from parent directory
    cleanup_workspace('workspace/')
