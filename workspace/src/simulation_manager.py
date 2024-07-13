"""
This module, manages the parallel execution of simulations in NetLogo.

It provides functionality to run simulations and save the results.
It uses the pyNetLogo library, to configure simulation parameters and retrieve simulation results.
"""

import os
import time
import traceback
from multiprocessing import Process, Queue
from typing import Any

import pandas as pd  # type: ignore
import pyNetLogo
import requests
from pyNetLogo import NetLogoException
from src.simulation import NetLogoParams, Result, Scenario, Simulation
from tqdm import tqdm  # type: ignore
from utils.helper import (get_available_cpus, get_custom_bar_format,
                          setup_logger)
from utils.netlogo_commands import *
from utils.paths import *
from utils.video_generation import generate_video

logger = setup_logger()


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
                     simulation_params: NetLogoParams,
                     netlogo_link: pyNetLogo.NetLogoLink) -> int:
    """
    Prepares the simulation.

    Clears the environment in Netlogo, executes the commands using the parameters provided
    and calls the set-up function of the Netlogo model.

    Args:
        simulation_id: The simulation id in the form of <scenario_indx>.
        simulation_seed: The seed for the simulation.
        simulation_params: The parameters to be set in NetLogo.
        netlogo_link: The NetLogo link object.

    Returns:
        current_seed: The seed used by netlogo for the simulation.
    """
    logger.debug(f'Setting up simulation for id: {simulation_id}.')
    netlogo_link.command('clear')

    logger.debug(f'Cleared environment for id: {simulation_id}')
    execute_comands(simulation_id, simulation_params, netlogo_link)

    current_seed: int = int(netlogo_link.report(SEED_SIMULATION_REPORTER.format(simulation_seed)))
    logger.debug(f"Simulation {simulation_id},  Current seed: {current_seed}")

    netlogo_link.command('setup')
    logger.debug(f"Setup completed for id: {simulation_id}")

    return current_seed


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


def _run_netlogo_model(netlogo_link: pyNetLogo.NetLogoLink) -> int | None:
    """
    Runs the NetLogo model and returns the number of ticks it took for the evacuation to finish.
    If the evacuation does not finish, it returns None.

    Args:
        netlogo_link: The NetLogo link object.

    Returns:
        evacuation_ticks: The number of ticks it took for the evacuation to finish.
                          None if it did not finish.
    """
    evacuation_ticks = None
    try:
        while not netlogo_link.report(EVACUATION_FINISHED_REPORTER):
            netlogo_link.command('go')
        evacuation_ticks = netlogo_link.report('ticks')
    except NetLogoException as e:
        logger.error(f"NetLogo exception: {e}")
    except Exception as e:
        logger.error(f"Exception: {e}")
    return evacuation_ticks


def run_simulation(simulation_id: str,
                   simulation_seed: int,
                   simulation_params: NetLogoParams,
                   netlogo_link: pyNetLogo.NetLogoLink) -> Result:
    """
    Runs a single simulation with the provided parameters and returns the results.

    Sets up the simulation using Neltlogo commands,
    calculates the execution time, generates a video if applicable and
    creates and returns a Result object.

    Args:
        simulation_id: The simulation id in the form of <scenario_indx>.
        simulation_seed: The seed for the simulation. To be used in Netlogo to create a random seed.
        simulation_params: The parameters to be set in NetLogo.
        neltogo_link: The link to the NetLogo model.

    Returns:
        result: The result object containing the simulation results.
    """
    start_time = time.time()
    current_seed: int = setup_simulation(simulation_id, simulation_seed, simulation_params,
                                         netlogo_link)
    evacuation_ticks: int = _run_netlogo_model(netlogo_link)
    endtime = time.time()
    evacuation_time = round(endtime - start_time, 2)

    if simulation_params.enable_video:
        generate_video(simulation_id)

    return Result(current_seed, simulation_id, evacuation_ticks, evacuation_time,
                  evacuation_ticks is not None)


def batch_processor(simulation_batch: list[dict[str, Any]], netlogo_model_path: str,
                    index: int, q: Queue) -> None:
    """
    Used to run a batch of simulations in a dedicated Process.

    It runs the simulations in the batch sequentially. It loads the netlogo model and
    runs each simulation before killing the link.

    Args:
        simulation_batch: A list of dictionaries containing the simulation id, seed and parameters.
        netlogo_model_path: The path to the NetLogo model.
        index: The index of the current batch.
    """
    netlogo_link = initialise_netlogo_link(netlogo_model_path)

    for simulation in simulation_batch:
        result = run_simulation(
            simulation['id'], simulation['seed'], simulation['params'], netlogo_link)
        q.get()
        url = "http://localhost:5000/put_results"
        requests.post(url, json=result.__dict__)
        logger.debug(f"Simulation id: {simulation['id']} finished. - Result: {result}.")

    logger.debug(f"Finished batch {index + 1}")
    netlogo_link.kill_workspace()


def build_batches(simulations: list[Simulation], num_cpus: int) -> list[list[dict[str, Any]]]:
    """
    Builds batches of simulations to be executed in parallel.

    It splits the list of simulations into batches and creates a list of dictionaries
    containing the simulation id, seed and parameters for each simualtion in each batch.
    Objects are not passed by refernce to the Process, but by value. This is why the
    simulations are converted to dictionaries.

    [[ {id: 1, seed: 123, params: {num_of_robots: 10, ...}}, ...], ...]

    Args:
        simulations: The simulations to be batched.
        num_cpus: The number of CPUs available.

    Returns:
        simulation_batches: The list of simulation batches.
    """
    # Initialize an empty list for each CPU
    simulation_batches = [[] for _ in range(num_cpus)]
    simulations_dict = [{'id': sim.id, 'seed': sim.seed, 'params': sim.netlogo_params}
                        for sim in simulations]

    used_cores = set()
    # Assign simulations to CPUs
    for i, simulation in enumerate(simulations_dict):
        cpu_index = i % num_cpus
        simulation_batches[cpu_index].append(simulation)
        used_cores.add(cpu_index)
    logger.info(
        f"Total number of simulations to run: {len(simulations)}. Total cores: {len(used_cores)}")

    return simulation_batches


def execute_parallel_simulations(simulations: list[Simulation], netlogo_model_path: str) -> None:
    """
    Executes the simulations in parallel using the available CPUs.

    It creates a Process for each core and runs (total simulations / number of cores) simulations
    in each, using the paramaters from each Simulation object.

    Args:
        simulations: The simulations to be executed.
        netlogo_model_path: The path to the NetLogo model.
    """
    num_cpus = get_available_cpus()
    simulation_batches = build_batches(simulations, num_cpus)

    logger.info("Setting up Simulations...")
    pbar = tqdm(total=len(simulations), desc="Simulations Progress", bar_format=get_custom_bar_format())

    q = Queue()
    for _ in range(len(simulations)):
        q.put(1)
    try:
        processes = []
        for index, batch in enumerate(simulation_batches):
            process = Process(target=batch_processor,
                              args=(batch, netlogo_model_path, index, q))
            processes.append(process)
            process.start()

        # Progress bar update
        prev_size = len(simulations) + 1
        while any(p.is_alive() for p in processes):
            size = q.qsize()
            if size < len(simulations) and size != prev_size:
                # Only update if the size has changed by more than 10%
                if prev_size - size > len(simulations) * 0.1:
                    print(' ')
                    pbar.n = len(simulations) - size
                    pbar.refresh()
                    prev_size = size

        for process in processes:
            process.join()

        q.close()
        pbar.n = len(simulations)
        pbar.refresh()
        pbar.close()
        logger.info("\nFinished all simulations.")
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
    experiments_data = get_experiment_data(scenarios)
    try:
        experiment_folder_name = get_experiment_folder()
        experiment_folder_path = os.path.join(DATA_FOLDER, experiment_folder_name)
        if not os.path.exists(experiment_folder_path):
            os.makedirs(experiment_folder_path)
    except Exception as e:
        logger.error(f"Error creating folder: {e}")

    try:
        results_file_name = "experiment_results.csv"
        data_file_name = "experiment_data.csv"
        results_file_path = os.path.join(experiment_folder_path, results_file_name)
        data_file_path = os.path.join(experiment_folder_path, data_file_name)
        experiments_results.to_csv(results_file_path)
        experiments_data.to_csv(data_file_path)
    except Exception as e:
        logger.error(f"Error saving results file: {e}")

    return {'results': experiments_results, 'data': experiments_data}


def get_experiment_data(scenarios: list[Scenario]) -> pd.DataFrame:
    """
    Returns a dataframe with the all the data from all the simulations of the scenarios.

    The dataframe contains all the parameters and results of each simulation.

    Args:
        scenarios: The scenarios to get the data from.

    Returns:
        experiments_data: The combined data of all simulations.
    """
    aggregated_data = []

    for scenario in scenarios:
        params = scenario.netlogo_params.__dict__
        info = {'name': scenario.name, 'strategy': scenario.adaptation_strategy}

        scenario_data = []
        for simulation in scenario.simulations:
            result = simulation.result.__dict__
            simulation_data = {
                'simulation_id': simulation.id,
                'simulation_seed': simulation.seed,
                'simulation_actions': simulation.actions,
                'simulation_responses': simulation.responses
            }

            scenario_data.append({**info, **params, **result, **simulation_data}),

        aggregated_data.extend(scenario_data)

    experiments_data = pd.DataFrame(aggregated_data)
    return experiments_data


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
    # TODO: add responses, no need to save robot actions to temp file
    experiments_results = save_and_return_simulation_results(scenarios)
    end_time = time.time()
    log_execution_time(start_time, end_time)
    return experiments_results
