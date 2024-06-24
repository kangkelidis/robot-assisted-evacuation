import pandas as pd
import traceback

from typing import Dict, List

from core.abm_manager import start_experiments
from core.abm_results_analysis import perform_analysis
from core.adaptation_strategies import adaptation_strategies
from utils.utils import setup_logger, setup_folders
from config import DATA_FOLDER, TARGET_SCENARIO
from utils.netlogo_commands import *
from core.Scenario import Scenario, get_simulation_scenarios

logger = setup_logger()

# TODO: should run a set of scenarios. A scenarion should be an object with all the configs and the strategy. 
# The resulrs should be stored in a folder with the date of execution and includes the scenario names for the results.



def main():
    simulation_scenarios=get_simulation_scenarios()

    results_file_name = DATA_FOLDER + "experiments.csv"  # type:str

    start_experiments(simulation_scenarios, results_file_name)
    # metrics = pd.DataFrame(
    #     [perform_analysis(TARGET_SCENARIO, simulation_scenarios, results_file_name)])  # type: pd.DataFrame
    # metrics.to_csv(DATA_FOLDER + "metrics.csv")


if __name__ == "__main__":
    try:
        # setup_folders()
        main()
    except Exception as e:
        logger.critical("Error in main: %s", e)
        traceback.print_exc()

