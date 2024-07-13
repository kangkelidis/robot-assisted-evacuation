"""
This module serves as the entry point for running experiments in a simulation environment.
"""

import traceback
from typing import Any

from utils.helper import setup_logger

logger = setup_logger()


def main() -> None:
    """
    Main function .
    """
    pass


if __name__ == "__main__":
    # main()
    import requests
    url = "http://localhost:5000/run"
    response = requests.get(url)
    print(response.text)
