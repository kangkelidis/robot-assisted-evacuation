import time
import traceback
from multiprocessing import Process
from typing import List

from core.simulations.simulation import Scenario, Simulation
from core.utils.helper import get_available_cpus, setup_logger
from core.utils.paths import *

logger = setup_logger()


def simulation_processor(simulation):
    # type: (Simulation) -> None
    """ Executes the simulation."""
    try:
        simulation.run()
    except Exception as e:
        logger.error("Exception in simulation: %s", e)
        traceback.print_exc()


def execute_parallel_simulations(simulations):
    # type: (List[Simulation]) -> None
    """ Executes the simulations in parallel using the available CPUs."""
    num_cpus = get_available_cpus()
    logger.info("Total number of simulations to run: %i.", len(simulations))
    try:
        while simulations:
            processes = []
            for _ in range(num_cpus):
                if simulations:
                    simulation = simulations.pop()
                    process = Process(target=simulation_processor,
                                      args=(simulation,))
                    processes.append(process)
                    process.start()
                    logger.debug(
                        "Started process %i. Simulations left: %i", process.pid, len(simulations))

            for process in processes:
                try:
                    process.join()
                except Exception as e:
                    logger.error("Exception in joining process: %s", e)
                    traceback.print_exc()
                    process.terminate()

                logger.debug("Process %s terminated.", process.pid)
            logger.info(
                "All processes in current batch finished. Simulations left: %i ", len(simulations))
        logger.info("Finished all simulations.")

    except Exception as e:
        logger.error("Exception in parallel simulation")
        print(e)
        traceback.print_exc()


def build_simulation_pool(scenarios):
    # type: (List[Scenario]) -> List[Simulation]
    """ Builds a list of simulations from the provided scenarios."""
    simulatios_pool = []
    for scenario in scenarios:
        simulatios_pool.extend(scenario.simulations)
    return simulatios_pool


def start_experiments(scenarios):
    # type: (List[Scenario]) -> None
    """ Starts the simulations for the provided scenarios and saves the results to a CSV file. """
    start_time = time.time()  # type: float
    simulations_pool = build_simulation_pool(scenarios)  # type: List[Simulation]
    execute_parallel_simulations(simulations_pool)  # type: List[SimulationResult]
    end_time = time.time()  # type: float
    logger.info("Simulation finished after {} seconds".format(end_time - start_time))
    logger.info("--------------------------------------------\n")
