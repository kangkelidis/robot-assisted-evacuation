"""
This module serves as the entry point for running experiments in a simulation environment.
"""

from typing import Any

from core.simulations.load_config import load_config, load_scenarios
from core.simulations.results_analysis import perform_analysis
from core.simulations.simulation import Scenario
from core.simulations.simulation_manager import start_experiments
from core.utils.cleanup import cleanup_workspace
from core.utils.helper import setup_folders, setup_logger
from core.utils.paths import CONFIG_FILE, WORKSPACE_FOLDER
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

        config: dict[str, Any] = load_config(CONFIG_FILE)
        scenarios: list[Scenario] = load_scenarios(config)
        experiments_results = start_experiments(config, scenarios)

        perform_analysis(experiments_results)
        logger.info("******* ==Experiment Finished== *******\n")
    except Exception as e:
        logger.critical(f"Error in main: {e}")
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt: Cleaning up workspace.")
    finally:
        cleanup_workspace(WORKSPACE_FOLDER)


if __name__ == "__main__":
    # test_batch_run()
    main()
