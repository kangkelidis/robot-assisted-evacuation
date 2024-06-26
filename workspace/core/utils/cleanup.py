import os

from paths import SCENARIOS_TEMP_FILE_RELATIVE_PATH


def is_netlogo_folder(path):
    # type: (str) -> bool
    return os.path.isdir(path) and \
        (os.path.isfile(os.path.join(path, "count turtles.txt")) or
         os.path.isfile(os.path.join(path, "number_passengers - count agents + 1.txt")) or
         os.path.isfile(os.path.join(path, "count agents with [ st_dead = 1 ].txt")) or
         not os.listdir(path))


def cleanup_workspace(directory):
    # type: (str) -> None
    """ Deletes all the excess folders created by Netlogo."""
    for file_name in os.listdir(directory):
        path = os.path.join(directory, file_name)
        if is_netlogo_folder(path):
            print("Deleting folder: ", file_name)
            os.system("rm -r " + path)

    temp_file_path = 'workspace/' + SCENARIOS_TEMP_FILE_RELATIVE_PATH
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)


if __name__ == '__main__':
    cleanup_workspace('workspace/')
