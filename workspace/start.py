import traceback
from typing import Dict, List

import pandas as pd
from abm_analysis import start_experiments
from abm_results_analysis import perform_analysis
from adptation_strategies import adaptation_strategies
from config import DATA_FOLDER, NUM_SAMPLES, WORKSPACE_FOLDER
from load_config import SimulationParameters, load_scenarios
from netlogo_commands import *
from utils import load_adaptation_strategy, setup_folders, setup_logger

logger = setup_logger()


def main():

    simulation_scenarios = load_scenarios()  # type: List[SimulationParameters]

    results_file_name = DATA_FOLDER + "experiments.csv"  # type:str

    start_experiments(simulation_scenarios, results_file_name)
    # metrics = pd.DataFrame(
    #     [perform_analysis("adaptive-support", simulation_scenarios, results_file_name)])  # type: pd.DataFrame
    # metrics.to_csv(DATA_FOLDER + "metrics.csv")


if __name__ == "__main__":
    try:
        setup_folders()
        main()
    except Exception as e:
        logger.critical("Error in main: %s", e)
        traceback.print_exc()

