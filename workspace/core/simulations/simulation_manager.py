import math
import os
import signal
import time
import traceback
from multiprocessing import Process, Queue
from typing import Dict, List

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
    """ Executes commands to setup the parameters in NetLogo."""
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
    Sets up the simulation in NetLogo.
    Clears the environment, executes the commands and sets up the simulation.
    """
    logger.debug('Setting up simulation for id: {}.'.format(simulation_id))
    netlogo_link.command('clear')
    logger.debug('Cleared environment for id: {}'.format(simulation_id))
    execute_comands(simulation_id, netlogo_params, netlogo_link)
    netlogo_link.command('setup')
    logger.info("Setup completed for id: {}".format(simulation_id))


# TODO: retry if max_netlogo_ticks is reached?
def get_netlogo_report(simulation_id, netlogo_link, netlogo_params):
    # type: (str, pyNetLogo, NetLogoParams) -> pd.DataFrame
    """
    Runs the simulation and returns the results.
    If the simulation is unsucessful, it tries again.
    """
    signal.signal(signal.SIGALRM, timeout_exception_handler)
    TIME_LIMIT_SECONDS = 120
    MAX_RETRIES = 2

    metrics_dataframe = None
    for i in range(MAX_RETRIES):
        try:
            signal.alarm(TIME_LIMIT_SECONDS)
            logger.info("Starting reporter for %s, attempt no. %i", simulation_id, i + 1)
            metrics_dataframe = netlogo_link.repeat_report(
                netlogo_reporter=[TURTLE_PRESENT_REPORTER, EVACUATED_REPORTER, DEAD_REPORTER],
                reps=netlogo_params.max_netlogo_ticks)  # type: pd.DataFrame
            netlogo_link.kill_workspace()
            signal.alarm(0)

            if metrics_dataframe is not None:
                break
        except Exception as e:
            logger.error("Exception in %s attempt no.%i: %s", simulation_id, i + 1, e)
            signal.alarm(0)
    return metrics_dataframe


# ? Can't it be initialised only once? Use a global variable?
def initialise_netlogo_link(netlogo_model_path):
    # type: (str) -> pyNetLogo.NetLogoLink
    """ Initialises the NetLogo link and loads the model."""
    logger.debug("Initialising NetLogo link from model path: %s", netlogo_model_path)
    netlogo_link = pyNetLogo.NetLogoLink(netlogo_home=NETLOGO_HOME,
                                         netlogo_version=NETLOGO_VERSION, gui=False)
    netlogo_link.load_model(netlogo_model_path)
    return netlogo_link


def run_simulation(simulation_id, netlogo_model_path, netlogo_params):
    # type: (str, str, NetLogoParams) -> None
    """ Runs the simulation."""
    try:
        start_time = time.time()
        netlogo_link = initialise_netlogo_link(netlogo_model_path)
        setup_simulation(simulation_id, netlogo_link, netlogo_params)
        metrics_dataframe = get_netlogo_report(simulation_id, netlogo_link, netlogo_params)

        if metrics_dataframe is None:
            logger.error("Simulation %s failed. Did not return any results", simulation_id)

        evacuation_finished = metrics_dataframe[
            metrics_dataframe[TURTLE_PRESENT_REPORTER] == metrics_dataframe[DEAD_REPORTER]]
        evacuation_ticks = int(evacuation_finished.index.min())  # type: int
        # TODO: think how to handle this case?
        if math.isnan(evacuation_ticks):
            metrics_dataframe.to_csv(DATA_FOLDER + "nan_df.csv")
            logger.warning("DEBUG!!! info to {}nan_df.csv".format(DATA_FOLDER))
            # simulation did not finish on time, use max time/ticks)
            evacuation_ticks = netlogo_params.max_netlogo_ticks
        endtime = time.time()
        evacuation_time = round(endtime - start_time, 2)
        result = Result(simulation_id, evacuation_ticks, evacuation_time, True)
        if netlogo_params.enable_video:
            generate_video(simulation_id)
        return result
    except NetLogoException as e:
        logger.error("id:{} NetLogo exception: {}".format(id, e))
        traceback.print_exc()
    except Exception as e:
        logger.error("id:{} Exception: {}".format(id, e))
        traceback.print_exc()
    return Result(simulation_id, None, None, False)


def simulation_processor(results_queue, simulation_id, netlogo_params, netlogo_model_path):
    # type: (Queue, str, NetLogoParams, str) -> None
    """ Executes the simulation."""
    try:
        result = run_simulation(simulation_id, netlogo_model_path, netlogo_params)  # type: Result
    except Exception as e:
        logger.error("Exception in simulation: %s", e)
        traceback.print_exc()

    results_queue.put(result)
    logger.info("Simulation id: %s finished. - Result: %s. ", simulation_id, result)


def execute_parallel_simulations(simulations, netlogo_model_path):
    # type: (List[Simulation], str) -> None
    """ Executes the simulations in parallel using the available CPUs."""
    # Using multiprocessing.Queue to allow for inter-process communication and store the results
    results_queue = Queue()  # type: Queue[Result]
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
    """ Combines all simulations from the provided scenarios."""
    simulatios_pool = []
    for scenario in scenarios:
        simulatios_pool.extend(scenario.simulations)
    return simulatios_pool


def save_and_return_simulation_results(scenarios):
    # type: (List[Scenario]) -> pd.DataFrame
    """
    Gets the robot actions for each simulation and saves the results for each scenario.
    Then it combines all the results in a dataframe saves it as a csv and returns it.
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


def start_experiments():
    # type: () -> pd.DataFrame
    """ Starts the simulations for the provided scenarios and saves and returns the results. """
    start_time = time.time()  # type: float
    scenarios = load_scenarios()  # type: List[Scenario]
    netlogo_model_path = load_netlogo_model_path()
    simulations_pool = build_simulation_pool(scenarios)  # type: List[Simulation]
    execute_parallel_simulations(simulations_pool, netlogo_model_path)
    experiments_results = save_and_return_simulation_results(scenarios)
    end_time = time.time()  # type: float
    log_execution_time(start_time, end_time)
    return experiments_results
