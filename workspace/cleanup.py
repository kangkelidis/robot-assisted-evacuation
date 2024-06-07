import os

from utils import cleanup_workspace

"""
Deletes all the excess folders created by Netlogo in the directory the script is located.
"""
if __name__ == '__main__':
    current_location = os.path.dirname(os.path.abspath(__file__))
    cleanup_workspace(current_location)
