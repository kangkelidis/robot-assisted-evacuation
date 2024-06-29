"""
This module serves as the entry point for running experiments in a simulation environment.
"""

import traceback

from core.simulations.results_analysis import perform_analysis
from core.simulations.simulation_manager import start_experiments
from core.utils.helper import setup_folders, setup_logger
from examples.default_scenarios import get_default_experiment_scenarios

logger = setup_logger()


def main():
    """
    Main function to initiate and analyse the simulations.
    """
    try:
        logger.info("******* ==Starting Experiment== *******")
        setup_folders()

        # It is possible to use the default scenarios, or create new ones.
        # default_scenarios ./= get_default_experiment_scenarios()
        # Any list of Scenario objects can be passed to start_experiments.
        # Alternatively, if no parameters are passed,
        # the scenarios from congig.json will be used.
        experiments_results = start_experiments()

        perform_analysis(experiments_results)
        logger.info("******* ==Experiment Finished== *******\n")
    except Exception as e:
        logger.critical("Error in main: %s", e)
        traceback.print_exc()


if __name__ == "__main__":
    main()
