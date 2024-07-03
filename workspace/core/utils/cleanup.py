"""
This module provides functionality for cleaning up the workspace
from folders created by the NetLogo simulations.
"""
# TODO: delete results dated folder if empty
import os
from pathlib import Path

from paths import ROBOTS_ACTIONS_FILE_NAME, SCENARIOS_TEMP_FILE_NAME


def is_netlogo_folder(path):
    # type: (str) -> bool
    """
    Checks if the folder is created by NetLogo.

    A NetLogo folder is a folder that contains the reporter commands for the simulation.

    Args:
        path (str): The path to check.

    Returns:
        bool: True if the folder is created by NetLogo, False otherwise.
    """
    return os.path.isdir(path) and \
        (os.path.isfile(os.path.join(path, "count turtles.txt")) or
         os.path.isfile(os.path.join(path, "number_passengers - count agents + 1.txt")) or
         os.path.isfile(os.path.join(path, "count agents with [ st_dead = 1 ].txt")) or
         not os.listdir(path))


def cleanup_workspace(directory):
    # type: (str) -> None
    """
    Deletes all the excess folders created by Netlogo and the tempfiles by the program.

    Args:
        directory (str): The path to the directory to clean up.
    """
    for file_name in os.listdir(directory):
        path = os.path.join(directory, file_name)
        if is_netlogo_folder(path):
            print("Deleting folder: ", file_name)
            os.system("rm -r " + path)

    directory_path = Path(directory)
    temp_file_path = directory_path / 'core/netlogo/' / SCENARIOS_TEMP_FILE_NAME
    if os.path.exists(str(temp_file_path)):
        os.remove(str(temp_file_path))

    temp_file_path = directory_path / 'core/netlogo/' / ROBOTS_ACTIONS_FILE_NAME
    if os.path.exists(str(temp_file_path)):
        os.remove(str(temp_file_path))


if __name__ == '__main__':
    # When called directly, from parent directory
    cleanup_workspace('workspace/')
