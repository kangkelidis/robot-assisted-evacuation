import traceback
from typing import Dict, List

import pandas as pd  # type: ignore
from core.simulations.load_config import load_scenarios
from core.simulations.simulation import Scenario
from core.simulations.simulation_manager import start_experiments
from core.utils.helper import setup_folders, setup_logger

logger = setup_logger()


def main():
    simulation_scenarios = load_scenarios()  # type: List[Scenario]
    start_experiments(simulation_scenarios)
    # metrics = pd.DataFrame(
    #     [perform_analysis
    # "adaptive-support", simulation_scenarios, results_file_name)])  # type: pd.DataFrame
    # metrics.to_csv(DATA_FOLDER + "metrics.csv")


if __name__ == "__main__":
    try:
        setup_folders()
        main()
    except Exception as e:
        logger.critical("Error in main: %s", e)
        traceback.print_exc()
