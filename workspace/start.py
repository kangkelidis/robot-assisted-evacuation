"""
This module serves as the entry point for running experiments in a simulation environment.
"""

import traceback

from core.simulations.results_analysis import perform_analysis
from core.simulations.simulation import Scenario
from core.simulations.simulation_manager import start_experiments
from core.utils.cleanup import cleanup_workspace
from core.utils.helper import setup_folders, setup_logger
from core.utils.paths import WORKSPACE_FOLDER
from examples.default_scenarios import get_default_experiment_scenarios
from experimental.batchrun import batch_run

logger = setup_logger()


def test_batch_run() -> None:
    scenario = Scenario()
    scenario.name = "test"
    scenario.adaptation_strategy = "RandomStrategy"
    scenario.netlogo_params.enable_video = True

    parameters = {
        'num_of_robots': range(1, 5),
        'num_of_staff': [2, 10]
    }

    scenarios = batch_run(scenario, parameters, 5)
    setup_folders()
    experiments_results = start_experiments(scenarios)
    perform_analysis(experiments_results)


def main() -> None:
    """
    Main function to initiate and analyse the simulations.
    """
    try:
        logger.info("******* ==Starting Experiment== *******")
        setup_folders()

        # It is possible to use the default scenarios, or create new ones.
        # default_scenarios = get_default_experiment_scenarios()
        # Any list of Scenario objects can be passed to start_experiments.
        # Alternatively, if no parameters are passed,
        # the scenarios from congig.json will be used.
        experiments_results = start_experiments()
        perform_analysis(experiments_results)
        logger.info("******* ==Experiment Finished== *******\n")
    except Exception as e:
        logger.critical(f"Error in main: {e}")
        traceback.print_exc()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt: Cleaning up workspace.")
    finally:
        cleanup_workspace(WORKSPACE_FOLDER)


if __name__ == "__main__":
    # test_batch_run()
    main()
