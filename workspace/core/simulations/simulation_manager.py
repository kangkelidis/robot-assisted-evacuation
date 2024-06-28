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
from typing import List, Optional

import pandas as pd  # type: ignore
import pyNetLogo
from core.simulations.load_config import (load_netlogo_model_path,
                                          load_scenarios)
from core.simulations.simulation import (NetLogoParams, Result, Scenario,
                                         Simulation)
from core.utils.helper import (get_available_cpus, setup_logger,
                               timeout_exception_handler)
from core.utils.paths import *
from core.utils.video_generation import generate_video
from netlogo_commands import *
from pyNetLogo import NetLogoException

logger = setup_logger()


def update_simulations_with(results_queue, simulations):
    simulations_dict = {simulation.id: simulation for simulation in simulations}
    while not results_queue.empty():
        simulation_result = results_queue.get()
        if simulation_result.simulation_id in simulations_dict:
            simulations_dict[simulation_result.simulation_id].result = simulation_result


def execute_comands(simulation_id, netlogo_params, netlogo_link):
    # type: (str, NetLogoParams, pyNetLogo) -> None
    """
    Executes Netlogo commands to setup global model parameters in NetLogo.

    Each parameter is mapped to a Netlogo command and executed.
    The process is performed before the initail simulation setup.

    Args:
        simulation_id (str): The simulation id in the form of <scenario_indx>.
        netlogo_params (NetLogoParams): The parameters to be set in NetLogo.
        netlogo_link (pyNetLogo): The NetLogo link object.
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
            logger.debug("Executed %s", command.format(value))

    except Exception as e:
        logger.error("Commands failed for id: {}. Exception: {}".format(id, e))
        traceback.print_exc()
    logger.debug("Commands executed for id: {}".format(id))


def setup_simulation(simulation_id, netlogo_link, netlogo_params):
    # type: (str, pyNetLogo, NetLogoParams) -> None
    """
    Prepares the simulation.

    Clears the environment in Netlogo, executes the commands using the parameters provided
    and calls the set-up function of the Netlogo model.

    Args:
        simulation_id (str): The simulation id in the form of <scenario_indx>.
        netlogo_link (pyNetLogo): The NetLogo link object.
        netlogo_params (NetLogoParams): The parameters to be set in NetLogo.
    """
    logger.debug('Setting up simulation for id: {}.'.format(simulation_id))
    netlogo_link.command('clear')

    logger.debug('Cleared environment for id: {}'.format(simulation_id))
    execute_comands(simulation_id, netlogo_params, netlogo_link)

    netlogo_link.command('setup')
    logger.info("Setup completed for id: {}".format(simulation_id))


def get_netlogo_report(simulation_id, netlogo_link, netlogo_params):
    # type: (str, pyNetLogo, NetLogoParams) -> Optional[int]
    """
    Runs the simulation and returns the results.

    If the simulation is unsucessful, it tries again. If it still fails, it returns None.

    Args:
        simulation_id (str): The simulation id in the form of <scenario_indx>.
        netlogo_link (pyNetLogo): The NetLogo link object.
        netlogo_params (NetLogoParams): The parameters to be set in NetLogo.

    Returns:
        evacuation_ticks (int): The number of ticks it took for the evacuation to finish.
    """
    # ! Only woeks the first time, alarm does not reset.
    signal.signal(signal.SIGALRM, timeout_exception_handler)
    TIME_LIMIT_SECONDS = 120
    MAX_RETRIES = 2

    for i in range(MAX_RETRIES):
        try:
            signal.alarm(TIME_LIMIT_SECONDS)

            logger.info("Starting reporter for %s, attempt no. %i", simulation_id, i + 1)
            metrics_dataframe = netlogo_link.repeat_report(
                netlogo_reporter=[TURTLE_PRESENT_REPORTER, EVACUATED_REPORTER, DEAD_REPORTER],
                reps=netlogo_params.max_netlogo_ticks)  # type: pd.DataFrame
            signal.alarm(0)

            if metrics_dataframe is not None:
                evacuation_ticks = get_evacuation_ticks(metrics_dataframe, simulation_id)
                # Reapeat the simulation if it did not finish under max ticks.
                if evacuation_ticks is not None:
                    return evacuation_ticks

        except Exception as e:
            logger.error("Exception in %s attempt no.%i: %s", simulation_id, i + 1, e)
            signal.alarm(0)

    logger.error("Simulation %s failed. Did not return any results", simulation_id)
    return None


def initialise_netlogo_link(netlogo_model_path):
    # type: (str) -> pyNetLogo.NetLogoLink
    """
    Initialises the NetLogo link and loads the model.

    Args:
        netlogo_model_path (str): The path to the NetLogo model.

    Returns:
        netlogo_link (pyNetLogo.NetLogoLink): The NetLogo link object.
    """
    logger.debug("Initialising NetLogo link from model path: %s", netlogo_model_path)
    netlogo_link = pyNetLogo.NetLogoLink(netlogo_home=NETLOGO_HOME,
                                         netlogo_version=NETLOGO_VERSION, gui=False)
    netlogo_link.load_model(netlogo_model_path)
    return netlogo_link


def get_evacuation_ticks(metrics_dataframe, simulation_id):
    # type: (pd.DataFrame, str) -> Optional[int]
    """
    Calculates and returns the number of ticks it took for the evacuation to finish.

    It uses the results from NetLogo to find the first tick where only dead turtles remain.
    If the evacuation did not finish within the tick limit, it returns None.

    Args:
        metrics_dataframe (pd.DataFrame): The metrics dataframe from NetLogo.
        simulation_id (str): The simulation id in the form of <scenario_indx>.

    Returns:
        evacuation_ticks (int): The number of ticks it took for the evacuation to finish.
    """
    evacuation_finished = metrics_dataframe[
        metrics_dataframe[TURTLE_PRESENT_REPORTER] == metrics_dataframe[DEAD_REPORTER]]

    evacuation_ticks = evacuation_finished.index.min()  # type: float
    # Evacuation did not finish on time.
    if math.isnan(evacuation_ticks):
        logger.warning("Id: {} - Evacuation did not finish on time.".format(simulation_id))
        return None

    return int(evacuation_ticks)


def run_simulation(simulation_id, netlogo_model_path, netlogo_params):
    # type: (str, str, NetLogoParams) -> Result
    """
    Runs a single simulation with the provided parameters and returns the results.

    Initialises a new Netlogo link, sets up the simulation using Neltlogo commands,
    calculates the execution time, generates a video if applicable and
    creates and returns a Result object.

    Args:
        simulation_id (str): The simulation id in the form of <scenario_indx>.
        netlogo_model_path (str): The path to the NetLogo model.
        netlogo_params (NetLogoParams): The parameters to be set in NetLogo.

    Returns:
        result (Result): The result object containing the simulation results.
    """
    try:
        start_time = time.time()

        netlogo_link = initialise_netlogo_link(netlogo_model_path)
        setup_simulation(simulation_id, netlogo_link, netlogo_params)
        evacuation_ticks = get_netlogo_report(simulation_id, netlogo_link, netlogo_params)
        netlogo_link.kill_workspace()

        endtime = time.time()
        evacuation_time = round(endtime - start_time, 2)

        if netlogo_params.enable_video:
            generate_video(simulation_id)

        return Result(simulation_id, evacuation_ticks, evacuation_time,
                      evacuation_ticks is not None)

    except NetLogoException as e:
        logger.error("id:{} NetLogo exception: {}".format(id, e))
        traceback.print_exc()
    except Exception as e:
        logger.error("id:{} Exception: {}".format(id, e))
        traceback.print_exc()
    return Result(simulation_id, None, None, False)


def simulation_processor(results_queue, simulation_id, netlogo_params, netlogo_model_path):
    # type: (Queue, str, NetLogoParams, str) -> None
    """
    Used to run a simulation in a dedicated Process.

    It runs the simulation and puts the results in the thread safe results_queue.

    Args:
        results_queue (Queue): The queue to store the results.
        simulation_id (str): The simulation id in the form of <scenario_indx>.
        netlogo_params (NetLogoParams): The parameters to be set in NetLogo.
        netlogo_model_path (str): The path to the NetLogo model.
    """
    try:
        result = run_simulation(simulation_id, netlogo_model_path, netlogo_params)  # type: Result
    except Exception as e:
        logger.error("Exception in simulation: %s", e)
        traceback.print_exc()

    results_queue.put(result)
    logger.info("Simulation id: %s finished. - Result: %s. ", simulation_id, result)


def execute_parallel_simulations(simulations, netlogo_model_path):
    # type: (List[Simulation], str) -> None
    """
    Executes the simulations in parallel using the available CPUs.

    It creates a pool of processes to run a single simulation in each,
    using the paramaters from each Simulation object.
    It uses the number of CPUs available to run simulations in paraller.
    It waits for all processes to finish and updates the Simulation objects with the results.

    Args:
        simulations (List[Simulation]): The simulations to be executed.
        netlogo_model_path (str): The path to the NetLogo model.
    """
    # Using multiprocessing.Queue to allow for inter-process communication and store the results
    results_queue = Queue()  # type: Queue[Result]
    # Makes a shallow copy of the list of Simulation to update them with the results
    simulations_copy = simulations[:]
    num_cpus = get_available_cpus()
    logger.info("Total number of simulations to run: %i.", len(simulations))

    try:
        while simulations:
            processes = []
            for _ in range(num_cpus):
                if simulations:
                    simulation = simulations.pop()
                    # Simulation objects are not passed to the Process, becouse they will be copied
                    process = Process(target=simulation_processor,
                                      args=(results_queue,
                                            simulation.id,
                                            simulation.netlogo_params,
                                            netlogo_model_path))
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

        update_simulations_with(results_queue, simulations_copy)

    except Exception as e:
        logger.error("Exception in parallel simulation")
        print(e)
        traceback.print_exc()


def build_simulation_pool(scenarios):
    # type: (List[Scenario]) -> List[Simulation]
    """
    Combines all simulations from the provided scenarios into a list.

    Args:
        scenarios (List[Scenario]): The scenarios to be combined.

    Returns:
        simulations_pool (List[Simulation]): The list of all simulations.
    """
    simulatios_pool = []
    for scenario in scenarios:
        simulatios_pool.extend(scenario.simulations)
    return simulatios_pool


def save_and_return_simulation_results(scenarios):
    # type: (List[Scenario]) -> pd.DataFrame
    """
    Gets the robot actions for each simulation and saves the results for each scenario.
    Then it combines all the results in a dataframe, saves it as a csv and returns it.

    Args:
        scenarios (List[Scenario]): The scenarios to get the results from.

    Returns:
        experiments_results (pd.DataFrame): The combined results of all simulations.
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
        logger.error("Error creating folder: {}".format(e))

    try:
        results_file_name = "experiment_results.csv"
        results_file_path = os.path.join(experiment_folder_path, results_file_name)
        experiments_results.to_csv(results_file_path)
    except Exception as e:
        logger.error("Error saving results file: {}".format(e))

    return experiments_results


def log_execution_time(start_time, end_time):
    # type: (float, float) -> None
    minutes, seconds = divmod(end_time - start_time, 60)
    logger.info(
        "Experiment finished after {:d} minutes and {:.2f} seconds".format(int(minutes), seconds))
    logger.info("--------------------------------------------")


def start_experiments(scenarios=None):
    # type: (List[Scenario]) -> pd.DataFrame
    """
    Starts the simulations for the provided scenarios.

    If no scenarios are provided, it loads them from the config file.
    It runs the simulations in parallel and saves the result in their respective Scenario objects.
    Then it combines all the results and saves them in a csv file.
    Finally, it returns the results for further analysis.

    Args:
        scenarios (List[Scenario]): The scenarios to be executed.

    Returns:
        experiments_results (pd.DataFrame): The combined results of all simulations.
    """
    start_time = time.time()  # type: float

    # Load scenarios from the config file if not provided and create simulations
    if scenarios is None:
        scenarios = load_scenarios()  # type: List[Scenario]

    netlogo_model_path = load_netlogo_model_path()
    simulations_pool = build_simulation_pool(scenarios)  # type: List[Simulation]

    execute_parallel_simulations(simulations_pool, netlogo_model_path)

    experiments_results = save_and_return_simulation_results(scenarios)

    end_time = time.time()  # type: float
    log_execution_time(start_time, end_time)
    return experiments_results
