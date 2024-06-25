import re
import time
import traceback
from multiprocessing import Process
from typing import Dict, List

import pandas as pd
from config import (FALL_CHANCE, FALL_LENGTH, NETLOGO_CONFIG,
                    NUM_OF_PASSENGERS, NUM_OF_ROBOTS)
from core.Scenario import Scenario
from utils.utils import get_available_cpus, setup_logger

logger = setup_logger()


def simulation_processor(scenario: Scenario) -> None:
    try:
        scenario.run()
    except Exception as e:
        logger.error("Exception in simulation_processor: %s", e)
        traceback.print_exc()


def execute_parallel_simulations(scenarios: List[Scenario]) -> None:
    """ Runs each simulations in the simulation_pool in parallel using multiprocessing. """
    num_cpus = get_available_cpus()

    logger.info("Total number of simulations to run: %i.", len(scenarios))
    try:
        while scenarios:
            processes = []
            for _ in range(num_cpus):
                if scenarios:
                    scenario = scenarios.pop()
                    process = Process(target=simulation_processor,
                                      args=(scenario,))
                    processes.append(process)
                    process.start()
                    logger.debug(
                        f"Started process {process.pid}. Remaining simulations: {len(scenarios)}")

            for process in processes:
                try:
                    process.join()
                except Exception as e:
                    logger.error("Exception in joining process: %s", e)
                    traceback.print_exc()
                    process.terminate()

                logger.debug("Process %s terminated.", process.pid)
            logger.info(
                f"All processes in current batch finished. Remaining simulations: {len(scenarios)}")
        logger.info("Finished all simulations.")

    except Exception as e:
        logger.error("Exception in parallel simulation")
        print(e)
        traceback.print_exc()


def extract_evacuation_times(scenarios: List[Scenario]) -> Dict[str, List[int]]:
    """ Extracts the evacuation times from the results and groups them by scenario name. """

    simulation_times = {}  # type: Dict[str, List[int]]
    for scenario in scenarios:
        if scenario.name in simulation_times:
            simulation_times[scenario.name].append(scenario.results)
        else:
            simulation_times[scenario.name] = [scenario.results]
    return simulation_times


def modify_config_nls() -> None:
    """ Modifies config file, before initialitising model"""
    # TODO use object
    with open(NETLOGO_CONFIG, 'r') as file:
        original_config = file.read()

    modified_config = re.sub(r'set NUM_OF_ROBOTS \d+', 'set NUM_OF_ROBOTS {}'
                             .format(NUM_OF_ROBOTS), original_config, 1)
    modified_config = re.sub(r'set NUM_OF_PASSENGERS \d+', 'set NUM_OF_PASSENGERS {}'
                             .format(NUM_OF_PASSENGERS), modified_config, 1)
    modified_config = re.sub(r'set FALL_CHANCE \d+(\.\d+)?', 'set FALL_CHANCE {}'
                             .format(FALL_CHANCE), modified_config, 1)
    modified_config = re.sub(r'set DEFAULT_FALL_LENGTH \d+', 'set DEFAULT_FALL_LENGTH {}'
                             .format(FALL_LENGTH), modified_config, 1)

    with open(NETLOGO_CONFIG, 'w') as file:
        file.write(modified_config)
    logger.info("Modified config file")


def start_experiments(scenarios: List[Scenario], results_file: str) -> None:
    start_time = time.time()

    modify_config_nls()
    execute_parallel_simulations(scenarios)
    experiment_data = extract_evacuation_times(scenarios)

    end_time = time.time()  # type: float
    logger.info("Simulation finished after {} seconds"
                .format(end_time - start_time))

    # TODO: make sure the experiment_data has the same length for all scenarios
    try:
        experiment_results = pd.DataFrame(experiment_data)  # type:pd.DataFrame
        experiment_results.to_csv(results_file)
        logger.debug("Data written to {}".format(results_file))
    except Exception as e:
        logger.warning("Error writing data to file. Experiment data: {}. \n{}"
                       .format(experiment_data, e))
