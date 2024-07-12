"""
This module, manages the parallel execution of simulations in NetLogo.

It provides functionality to run simulations and save the results.
It uses the pyNetLogo library, to configure simulation parameters and retrieve simulation results.

Key functionalities include:
- Initialization of the NetLogo link and model loading.
- Configuration of simulation parameters and execution of setup commands in NetLogo.
- Running simulations in parallel, utilizing available CPU resources.
- Collecting and processing simulation results from a multiprocessing queue.
- Saving simulation results into a CSV file for further analysis.
"""

import math
import os
import signal
import time
import traceback
from multiprocessing import Process, Queue
from typing import Any, Optional

import pandas as pd  # type: ignore
import pyNetLogo
from core.simulations.load_config import get_netlogo_model_path, load_scenarios
from core.simulations.netlogo_commands import *
from core.simulations.simulation import (NetLogoParams, Result, Scenario,
                                         Simulation)
from core.utils.helper import (get_available_cpus, get_custom_bar_format,
                               setup_logger, timeout_exception_handler)
from core.utils.paths import *
from core.utils.video_generation import generate_video
from pyNetLogo import NetLogoException
from tqdm import tqdm  # type: ignore

logger = setup_logger()


def update_simulations_with(results_queue: Queue, simulations: list[Simulation]) -> None:
    """
    Updates the Simulation objects with the results from the results_queue.

    Args:
        results_queue: The queue containing the results.
        simulations: The Simulation objects to be updated.
    """
    simulations_dict = {simulation.id: simulation for simulation in simulations}
    while not results_queue.empty():
        simulation_result = results_queue.get()
        if simulation_result.simulation_id in simulations_dict:
            simulations_dict[simulation_result.simulation_id].result = simulation_result


def execute_comands(simulation_id: str,
                    netlogo_params: NetLogoParams,
                    netlogo_link: pyNetLogo.NetLogoLink) -> None:
    """
    Executes Netlogo commands to setup global model parameters in NetLogo.

    Each parameter is mapped to a Netlogo command and executed.
    The process is performed before the initail simulation setup.

    Args:
        simulation_id: The simulation id in the form of <scenario_indx>.
        netlogo_params: The parameters to be set in NetLogo.
        netlogo_link: The NetLogo link object.
    """
    commands = {
        SET_SIMULATION_ID_COMMAND: simulation_id,
        SET_NUM_OF_ROBOTS_COMMAND: netlogo_params.num_of_robots,
        SET_NUM_OF_PASSENGERS_COMMAND: netlogo_params.num_of_passengers,
        SET_NUM_OF_STAFF_COMMAND: netlogo_params.num_of_staff,
        SET_FALL_LENGTH_COMMAND: netlogo_params.fall_length,
        SET_FALL_CHANCE_COMMAND: netlogo_params.fall_chance,
        SET_STAFF_SUPPORT_COMMAND: "TRUE" if netlogo_params.allow_staff_support
        else "FALSE",
        SET_PASSENGER_SUPPORT_COMMAND: "TRUE" if netlogo_params.allow_passenger_support
        else "FALSE",
        SET_FRAME_GENERATION_COMMAND: "TRUE" if netlogo_params.enable_video else "FALSE",
        SET_ROOM_ENVIRONMENT_TYPE: netlogo_params.room_type
    }

    try:
        for command, value in commands.items():
            netlogo_link.command(command.format(value))
            logger.debug(f"Executed {command.format(value)}")

    except Exception as e:
        logger.error(f"Commands failed for id: {id}. Exception: {e}")
    logger.debug(f"Commands executed for id: {id}")


def setup_simulation(simulation_id: str,
                     simulation_seed: int,
                     netlogo_link: pyNetLogo.NetLogoLink,
                     netlogo_params: NetLogoParams) -> int:
    """
    Prepares the simulation.

    Clears the environment in Netlogo, executes the commands using the parameters provided
    and calls the set-up function of the Netlogo model.

    Args:
        simulation_id: The simulation id in the form of <scenario_indx>.
        simulation_seed: The seed for the simulation.
        netlogo_link: The NetLogo link object.
        netlogo_params: The parameters to be set in NetLogo.

    Returns:
        current_seed: The seed used by netlogo for the simulation.
    """
    logger.debug(f'Setting up simulation for id: {simulation_id}.')
    netlogo_link.command('clear')

    logger.debug(f'Cleared environment for id: {simulation_id}')
    execute_comands(simulation_id, netlogo_params, netlogo_link)

    current_seed: int = int(netlogo_link.report(SEED_SIMULATION_REPORTER.format(simulation_seed)))
    logger.debug(f"Simulation {simulation_id},  Current seed: {current_seed}")

    netlogo_link.command('setup')
    logger.debug(f"Setup completed for id: {simulation_id}")

    return current_seed


def get_netlogo_report(simulation_id: str,
                       netlogo_link: pyNetLogo.NetLogoLink,
                       netlogo_params: NetLogoParams) -> Optional[int]:
    """
    Runs the simulation and returns the results.

    If the simulation is unsucessful, it tries again. If it still fails, it returns None.

    Args:
        simulation_id: The simulation id in the form of <scenario_indx>.
        netlogo_link: The NetLogo link object.
        netlogo_params: The parameters to be set in NetLogo.

    Returns:
        evacuation_ticks: The number of ticks it took for the evacuation to finish.
    """
    # ! Only works the first time, alarm does not reset.
    signal.signal(signal.SIGALRM, timeout_exception_handler)
    TIME_LIMIT_SECONDS = 120
    MAX_RETRIES = 2

    for i in range(MAX_RETRIES):
        try:
            signal.alarm(TIME_LIMIT_SECONDS)
            logger.debug(f"Starting reporter for {simulation_id}, attempt no. {i + 1}")
            metrics_dataframe: pd.DataFrame = netlogo_link.repeat_report(
                netlogo_reporter=[TURTLE_PRESENT_REPORTER, EVACUATED_REPORTER, DEAD_REPORTER],
                reps=netlogo_params.max_netlogo_ticks)
            signal.alarm(0)

            if metrics_dataframe is not None:
                evacuation_ticks = get_evacuation_ticks(metrics_dataframe, simulation_id)
                # Repeat the simulation if it did not finish under max ticks.
                if evacuation_ticks is not None:
                    return evacuation_ticks

        except Exception as e:
            logger.error(f"Exception in {simulation_id} attempt no.{i + 1}: {e}")
            signal.alarm(0)

    logger.error(f"Simulation {simulation_id} failed. Did not return any results")
    return None


def initialise_netlogo_link(netlogo_model_path: str) -> pyNetLogo.NetLogoLink:
    """
    Initialises the NetLogo link and loads the model.

    Args:
        netlogo_model_path: The path to the NetLogo model.

    Returns:
        netlogo_link: The NetLogo link object.
    """
    logger.debug("Initialising NetLogo link from model path: %s", netlogo_model_path)
    netlogo_link: pyNetLogo.NetLogoLink = pyNetLogo.NetLogoLink(netlogo_home=NETLOGO_HOME,
                                                                netlogo_version=NETLOGO_VERSION,
                                                                gui=False)
    netlogo_link.load_model(netlogo_model_path)
    return netlogo_link


def get_evacuation_ticks(metrics_dataframe: pd.DataFrame, simulation_id: str) -> Optional[int]:
    """
    Calculates and returns the number of ticks it took for the evacuation to finish.

    It uses the results from NetLogo to find the first tick where only dead turtles remain.
    If the evacuation did not finish within the tick limit, it returns None.

    Args:
        metrics_dataframe: The metrics dataframe from NetLogo.
        simulation_id: The simulation id in the form of <scenario_indx>.

    Returns:
        evacuation_ticks: The number of ticks it took for the evacuation to finish.
    """
    evacuation_finished = metrics_dataframe[
        metrics_dataframe[TURTLE_PRESENT_REPORTER] == metrics_dataframe[DEAD_REPORTER]]

    evacuation_ticks = evacuation_finished.index.min()  # type: float
    # Evacuation did not finish on time.
    if math.isnan(evacuation_ticks):
        logger.warning(f"Id: {simulation_id} - Evacuation did not finish on time.")
        return None

    return int(evacuation_ticks)


def run_simulation(simulation_id: str,
                   simulation_seed: int,
                   netlogo_model_path: str,
                   netlogo_params: NetLogoParams) -> Result:
    """
    Runs a single simulation with the provided parameters and returns the results.

    Initialises a new Netlogo link, sets up the simulation using Neltlogo commands,
    calculates the execution time, generates a video if applicable and
    creates and returns a Result object.

    Args:
        simulation_id: The simulation id in the form of <scenario_indx>.
        simulation_seed: The seed for the simulation.
        netlogo_model_path: The path to the NetLogo model.
        netlogo_params: The parameters to be set in NetLogo.

    Returns:
        result: The result object containing the simulation results.
    """
    try:
        start_time = time.time()

        netlogo_link = initialise_netlogo_link(netlogo_model_path)
        current_seed: int = setup_simulation(simulation_id,
                                             simulation_seed,
                                             netlogo_link,
                                             netlogo_params)
        evacuation_ticks = get_netlogo_report(simulation_id, netlogo_link, netlogo_params)
        netlogo_link.kill_workspace()

        endtime = time.time()
        evacuation_time = round(endtime - start_time, 2)

        if netlogo_params.enable_video:
            generate_video(simulation_id)

        return Result(current_seed, simulation_id, evacuation_ticks, evacuation_time,
                      evacuation_ticks is not None)

    except NetLogoException as e:
        logger.error(f"id:{id} NetLogo exception: {e}")
    except Exception as e:
        logger.error(f"id:{id} Exception: {e}")
    return Result(current_seed, simulation_id, None, None, False)


def simulation_processor(results_queue: Queue,
                         simulation_id: str,
                         simulation_seed: int,
                         netlogo_params: NetLogoParams,
                         netlogo_model_path: str) -> None:
    """
    Used to run a simulation in a dedicated Process.

    It runs the simulation and puts the results in the thread safe results_queue.

    Args:
        results_queue: The queue to store the results.
        simulation_id: The simulation id in the form of <scenario_indx>.
        simulation_seed: The seed for the simulation.
        netlogo_params: The parameters to be set in NetLogo.
        netlogo_model_path: The path to the NetLogo model.
    """
    result: Result = run_simulation(simulation_id,
                                    simulation_seed,
                                    netlogo_model_path,
                                    netlogo_params)
    results_queue.put(result)
    logger.debug(f"Simulation id: {simulation_id} finished. - Result: {result}.")


def execute_parallel_simulations(simulations: list[Simulation], netlogo_model_path: str) -> None:
    """
    Executes the simulations in parallel using the available CPUs.

    It creates a pool of processes to run a single simulation in each,
    using the paramaters from each Simulation object.
    It uses the number of CPUs available to run simulations in paraller.
    It waits for all processes to finish and updates the Simulation objects with the results.

    Args:
        simulations: The simulations to be executed.
        netlogo_model_path: The path to the NetLogo model.
    """
    # Using multiprocessing.Queue to allow for inter-process communication and store the results
    results_queue: Queue[Result] = Queue()
    # Makes a shallow copy of the list of Simulation to update them with the results
    simulations_copy = simulations[:]
    num_cpus = get_available_cpus()
    logger.info(f"Total number of simulations to run: {len(simulations)}.")

    try:
        with tqdm(total=len(simulations), desc="Running Simulations",
                  bar_format=get_custom_bar_format()) as pbar:
            while simulations:
                processes = []
                for _ in range(num_cpus):
                    if simulations:
                        simulation = simulations.pop()
                        # Simulation objects are not passed to the Process,
                        # because they will be coppied
                        process = Process(target=simulation_processor,
                                          args=(results_queue,
                                                simulation.id,
                                                simulation.seed,
                                                simulation.netlogo_params,
                                                netlogo_model_path))
                        processes.append(process)
                        process.start()
                        logger.debug(
                            f"Started process {process.pid}. Simulations left: {len(simulations)}")

                for process in processes:
                    try:
                        process.join()
                        pbar.update(1)
                    except Exception as e:
                        logger.error(f"Exception in joining process: {e}")
                        process.terminate()
                    finally:
                        logger.debug(f"Process {process.pid} terminated.")
                logger.debug(
                    f"All processes in current batch ended. Simulations left: {len(simulations)}")
            logger.info("Finished all simulations.")

        update_simulations_with(results_queue, simulations_copy)

    except Exception as e:
        logger.error(f"Exception in parallel simulation: {e}")
        traceback.print_exc()


def build_simulation_pool(scenarios: list[Scenario]) -> list[Simulation]:
    """
    Combines all simulations from the provided scenarios into a list.

    Args:
        scenarios: The scenarios to be combined.

    Returns:
        simulations_pool: The list of all simulations.
    """
    simulatios_pool = []
    for scenario in scenarios:
        logger.debug(
            f"Adding simulations for: {scenario.name}. List size {len(scenario.simulations)}")
        simulatios_pool.extend(scenario.simulations)
    return simulatios_pool


def save_and_return_simulation_results(scenarios: list[Scenario]) -> pd.DataFrame:
    """
    Gets the robot actions for each simulation and saves the results for each scenario.
    Then it combines all the results in a dataframe, saves it as a csv and returns it.

    Args:
        scenarios: The scenarios to get the results from.

    Returns:
        experiments_results: The combined results of all simulations.
    """
    experiments_results = pd.DataFrame()
    for scenario in scenarios:
        scenario.gather_results()
        scenario.save_results()
        experiments_results = pd.concat(
            [experiments_results, scenario.results_df], ignore_index=True)

    try:
        experiment_folder_name = get_experiment_folder()
        experiment_folder_path = os.path.join(DATA_FOLDER, experiment_folder_name)
        if not os.path.exists(experiment_folder_path):
            os.makedirs(experiment_folder_path)
    except Exception as e:
        logger.error(f"Error creating folder: {e}")

    try:
        results_file_name = "experiment_results.csv"
        results_file_path = os.path.join(experiment_folder_path, results_file_name)
        experiments_results.to_csv(results_file_path)
    except Exception as e:
        logger.error(f"Error saving results file: {e}")

    return experiments_results


def log_execution_time(start_time: float, end_time: float) -> None:
    minutes, seconds = divmod(end_time - start_time, 60)
    logger.info(f"Experiment finished after {int(minutes)} minutes and {seconds:.2f} seconds")
    logger.info("--------------------------------------------")


def start_experiments(config: dict[str, Any], scenarios: list[Scenario]) -> pd.DataFrame:
    """
    Starts the simulations for the provided scenarios.

    It runs the simulations in parallel and saves the result in their respective Scenario objects.
    Then it combines all the results and saves them in a csv file.
    Finally, it returns the results for further analysis.

    Args:
        config: The configuration parameters for the simulations.
        scenarios: The scenarios to be executed.

    Returns:
        experiments_results: The combined results of all simulations.
    """
    start_time = time.time()

    netlogo_model_path = config.get('netlogoModelPath')
    simulations_pool = build_simulation_pool(scenarios)
    execute_parallel_simulations(simulations_pool, netlogo_model_path)

    experiments_results = save_and_return_simulation_results(scenarios)
    end_time = time.time()
    log_execution_time(start_time, end_time)
    return experiments_results
