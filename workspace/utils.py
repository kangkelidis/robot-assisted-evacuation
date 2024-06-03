from config import WORKSPACE_FOLDER, ADAPTATION_STRATEGY
import os
import re

def cleanup_workspace():
    """ Deletes all the excess folders created by Netlogo."""

    for folder in os.listdir(WORKSPACE_FOLDER):
        if re.match(r'\w{6}', folder):
            if os.path.isfile(WORKSPACE_FOLDER + folder + "/count turtles.txt"):
                print("Deleting folder: ", folder)
                os.system("rm -r " + WORKSPACE_FOLDER + folder)

def load_adaptation_strategy():
    """ Loads the adaptation strategy from the config file."""
    
    return ADAPTATION_STRATEGY
