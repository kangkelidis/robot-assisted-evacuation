import traceback

from core.simulations.results_analysis import perform_analysis
from core.simulations.simulation_manager import start_experiments
from core.utils.helper import setup_folders, setup_logger

logger = setup_logger()


def main():
    try:
        logger.info("******* ==Starting Experiment== *******")
        setup_folders()
        experiments_results = start_experiments()
        perform_analysis(experiments_results)
        logger.info("******* ==Experiment Finished== *******\n")
    except Exception as e:
        logger.critical("Error in main: %s", e)
        traceback.print_exc()


if __name__ == "__main__":
    main()
