import pandas as pd
import traceback

from typing import Dict, List

from abm_analysis import simulate_and_store
from abm_results_analysis import perform_analysis
from adptation_strategies import adaptation_strategies
from utils import load_adaptation_strategy, setup_logger, setup_folders
from config import WORKSPACE_FOLDER, NUM_SAMPLES, DATA_FOLDER
from netlogo_commands import *

logger = setup_logger()


def main():
    adaptation_strategy=load_adaptation_strategy()

    if adaptation_strategy:
        simulation_scenarios = {
            "no-support": [SET_FRAME_GENERATION_COMMAND.format("TRUE"),
                        SET_FALL_LENGTH_COMMAND.format(500)],
            "staff-support": [SET_FRAME_GENERATION_COMMAND.format("TRUE"),
                            SET_FALL_LENGTH_COMMAND.format(500),
                            SET_STAFF_SUPPORT_COMMAND.format("TRUE")],
            "passenger-support": [SET_FRAME_GENERATION_COMMAND.format("TRUE"),
                                SET_FALL_LENGTH_COMMAND.format(500),
                                SET_PASSENGER_SUPPORT_COMMAND.format("TRUE")],
            "adaptive-support": [SET_FRAME_GENERATION_COMMAND.format("TRUE"),
                                SET_FALL_LENGTH_COMMAND.format(500),
                                SET_PASSENGER_SUPPORT_COMMAND.format("TRUE"),
                                SET_STAFF_SUPPORT_COMMAND.format("TRUE")]
        }  # type: Dict[str, List[str]]
    else:  
        # Run multiple adaptation strategies, to find the best one 
        simulation_scenarios = {
            strategy_name: [SET_FRAME_GENERATION_COMMAND.format("FALSE"),
                            SET_FALL_LENGTH_COMMAND.format(500),
                            SET_PASSENGER_SUPPORT_COMMAND.format("TRUE"),
                            SET_STAFF_SUPPORT_COMMAND.format("TRUE")]
            for strategy_name in adaptation_strategies.keys()
        }


    results_file_name = DATA_FOLDER + "experiments.csv"  # type:str
    samples = NUM_SAMPLES # type: int

    simulate_and_store(simulation_scenarios, results_file_name, samples)
    metrics = pd.DataFrame(
        [perform_analysis("adaptive-support", simulation_scenarios, results_file_name)])  # type: pd.DataFrame
    metrics.to_csv(DATA_FOLDER + "metrics.csv")


if __name__ == "__main__":
    try:
        setup_folders()
        main()
    except Exception as e:
        logger.critical("Error in main: %s", e)
        traceback.print_exc()

