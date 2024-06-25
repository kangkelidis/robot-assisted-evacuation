import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.paths import ROOT


def is_netlogo_folder(path, file_name):
    return  os.path.isdir(path) and re.match(r'\w{6}', file_name) and not file_name == 'frames' \
            and (  os.path.isfile(os.path.join(path, "count turtles.txt"))\
                or os.path.isfile(os.path.join(path, "number_passengers - count agents + 1.txt"))\
                or os.path.isfile(os.path.join(path, "count agents with [ st_dead = 1 ].txt"))\
                or not os.listdir(path) )


def cleanup_workspace(directory):
    """ Deletes all the excess folders created by Netlogo."""

    for file_name in os.listdir(directory):
        path = os.path.join(directory, file_name)
        if is_netlogo_folder(path, file_name):
            print("Deleting folder: ", file_name)
            os.system("rm -r " + path)


"""
Deletes all the excess folders created by Netlogo in the directory the script is located.
"""
if __name__ == '__main__':
    cleanup_workspace(ROOT)
