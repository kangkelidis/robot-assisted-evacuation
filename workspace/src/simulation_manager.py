"""
This module, manages the parallel execution of simulations in NetLogo.

It provides functionality to run simulations and save the results.
It uses the pyNetLogo library, to configure simulation parameters and retrieve simulation results.
"""

import signal
import time
from multiprocessing import Pool, Process, Queue
from typing import Any, Optional

import pandas as pd  # type: ignore
import pyNetLogo
import requests
from pyNetLogo import NetLogoException
from src.load_config import get_max_time
from src.server import BASE_URL
from src.simulation import NetLogoParams, Result, Scenario, Simulation
from tqdm import tqdm  # type: ignore
from utils.helper import (PBar, TimeoutException, get_available_cpus,
                          print_dots, setup_logger, timeout_handler)
from utils.netlogo_commands import *
from utils.paths import *
from utils.video_generation import generate_video

logger = setup_logger()

SIMULATION_TIMEOUT = get_max_time()


def execute_commands(simulation_id: str,
                     netlogo_params: NetLogoParams,
                     netlogo_link: pyNetLogo.NetLogoLink) -> None:
    """
    Executes NetLogo commands to setup global model parameters in NetLogo.

    Each parameter is mapped to a NetLogo command and executed.
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
        SET_ROBOT_PERSUASION_FACTOR: netlogo_params.robot_persuasion_factor,
        SET_FRAME_GENERATION_COMMAND: "TRUE" if netlogo_params.enable_video else "FALSE",
        SET_ROOM_ENVIRONMENT_TYPE: netlogo_params.room_type
    }

    try:
        for command, value in commands.items():
            netlogo_link.command(command.format(value))
            logger.debug(f"{simulation_id}: Executed {command.format(value)}")

    except Exception as e:
        logger.error(f"Commands failed for id: {simulation_id}. Exception: {e}")
    logger.debug(f"Commands executed for id: {simulation_id}")


def setup_simulation(simulation_id: str,
                     simulation_seed: int,
                     simulation_params: NetLogoParams,
                     netlogo_link: pyNetLogo.NetLogoLink) -> int:
    """
    Prepares the simulation.

    Clears the environment in NetLogo, executes the commands using the parameters provided
    and calls the set-up function of the NetLogo model.

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
    execute_commands(simulation_id, simulation_params, netlogo_link)

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


def _run_netlogo_model(netlogo_link: pyNetLogo.NetLogoLink, max_netlogo_ticks,
                       time_limit: int = SIMULATION_TIMEOUT) -> int | None:
    """
    Runs the NetLogo model with a time limit and returns the number of ticks it took for the
    evacuation to finish. If the evacuation does not finish or exceeds the time limit,
    it returns None.

    Args:
        netlogo_link: The NetLogo link object.
        max_netlogo_ticks: The maximum number of ticks to run the model.
        time_limit: The time limit in seconds for running the model.

    Returns:
        evacuation_ticks: The number of ticks it took for the evacuation to finish, or None.
    """
    evacuation_ticks = None
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(time_limit)
        ticks = 0
        while not netlogo_link.report(EVACUATION_FINISHED_REPORTER) and ticks < max_netlogo_ticks:
            netlogo_link.command('go')
            ticks += 1
        evacuation_ticks = ticks if ticks < max_netlogo_ticks else None
        signal.alarm(0)
    except TimeoutException:
        logger.warning("Simulation timed out!")
    except NetLogoException as e:
        logger.error(f"NetLogo exception: {e}")
    # ! cannot catch the exception in the java environment
    except BaseException as e:
        logger.error(f"Exception: {e}")
    finally:
        signal.alarm(0)
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
    evacuation_ticks: Optional[int] = _run_netlogo_model(netlogo_link,
                                                         simulation_params.max_netlogo_ticks)
    endtime = time.time()
    evacuation_time = round(endtime - start_time, 2)

    success: bool = evacuation_ticks is not None and \
        evacuation_ticks < simulation_params.max_netlogo_ticks
    return Result(netlogo_seed=current_seed,
                  evacuation_ticks=evacuation_ticks,
                  evacuation_time=evacuation_time,
                  success=success)


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
        q: The queue to track the progress of the simulations.
    """
    netlogo_link = initialise_netlogo_link(netlogo_model_path)

    for simulation in simulation_batch:
        result = run_simulation(simulation['id'],
                                simulation['seed'],
                                simulation['params'],
                                netlogo_link)
        # update the queue to indicate that the simulation has finished to the progress bar
        q.get()
        # Convert result object to dict excluding keys that start with robot_ as they are
        # updated from the server. ie 'robot_actions', 'robot_responses', 'robot_contacts'
        data = {key: value for key, value in result.__dict__.items()
                if not key.startswith('robot_')}
        data['simulation_id'] = simulation['id']

        url = BASE_URL + "/put_results"
        requests.put(url, json=data)
        logger.debug(f"Simulation id: {simulation['id']} finished. - Result: {result}.")

    logger.debug(f"Finished batch {index + 1}")
    netlogo_link.kill_workspace()


def build_batches(simulations: list[Simulation], num_cpus: int) -> list[list[dict[str, Any]]]:
    """
    Builds batches of simulations to be executed in parallel.

    It splits the list of simulations into batches and creates a list of dictionaries
    containing the simulation id, seed and parameters for each simulation in each batch.
    Objects are not passed by reference to the Process, but by value. This is why the
    simulations are converted to dictionaries.

    [[ {id: 1, seed: 123, params: {num_of_robots: 10, ...}}, ...], ...]

    Args:
        simulations: The simulations to be batched.
        num_cpus: The number of CPUs available.

    Returns:
        simulation_batches: The list of simulation batches.
    """
    # Initialize an empty list for each CPU
    simulation_batches: list[list] = [[] for _ in range(num_cpus)]
    simulations_dict = [{'id': sim.id, 'seed': sim.seed, 'params': sim.netlogo_params}
                        for sim in simulations]

    used_cores = set()
    # Assign simulations to CPUs
    for i, simulation in enumerate(simulations_dict):
        cpu_index = i % num_cpus
        simulation_batches[cpu_index].append(simulation)
        used_cores.add(cpu_index)
    # remove empty lists
    simulation_batches = [batch for batch in simulation_batches if batch]
    total_bathes_len = sum(len(batch) for batch in simulation_batches)
    logger.info(
        f"Total number of simulations to run: {total_bathes_len}. Total cores: {len(used_cores)}")
    return simulation_batches


def execute_parallel_simulations(simulations: list[Simulation], netlogo_model_path: str) -> None:
    """
    Executes the simulations in parallel using the available CPUs.

    It creates a Process for each core and runs (total simulations / number of cores) simulations
    in each, using the parameters from each Simulation object.

    Args:
        simulations: The simulations to be executed.
        netlogo_model_path: The path to the NetLogo model.
    """
    num_cpus = get_available_cpus()
    simulation_batches = build_batches(simulations, num_cpus)
    logger.info(f"Setting up {len(simulations)} Simulations")
    # Create a queue to track the progress of the simulations
    q = Queue()
    for _ in simulations:
        q.put(1)
    try:
        processes = []
        for index, batch in enumerate(simulation_batches):
            process = Process(target=batch_processor,
                              args=(batch, netlogo_model_path, index, q))
            processes.append(process)
            process.start()
            logger.debug(f"Started batch {index + 1} with {len(batch)} simulations, "
                         f"on processes: {process.pid}. {[sim['id'] for sim in batch]}")
        # used to track the progress of the simulations
        prev_size = len(simulations) + 1
        # used to print dots while waiting for the setting up to finish
        dot = 0
        pbar: PBar = PBar()
        while any(p.is_alive() for p in processes):
            size = q.qsize()

            # print dots while waiting for the setting up to finish
            if size == len(simulations):
                dot = print_dots(dot, len(simulations))

            # update the progress bar
            if size < len(simulations) and size != prev_size:
                prev_size = pbar.update(len(simulations), size, prev_size)

        for process in processes:
            process.join()

        q.close()
        pbar.close(len(simulations), size)
        logger.info(f"\nFinished {len(simulations) - size} simulations.")
    except Exception as e:
        logger.error(f"Exception in parallel simulation: {e}")


def build_simulation_pool(scenarios: list[Scenario]) -> list[Simulation]:
    """
    Combines all simulations from the provided scenarios into a list.

    Args:
        scenarios: The scenarios to be combined.

    Returns:
        simulations_pool: The list of all simulations.
    """
    simulations_pool = []
    for scenario in scenarios:
        logger.debug(
            f"Adding simulations for: {scenario.name}. List size {len(scenario.simulations)}")
        simulations_pool.extend(scenario.simulations)
    return simulations_pool


def video_worker(args: tuple) -> None:
    """
    Worker function to generate videos in parallel.

    Args:
        args: A tuple containing the simulation id and the path to save the video.
    """
    simulation_id, video_folder_path = args
    try:
        generate_video(simulation_id, video_folder_path)
    except Exception as e:
        logger.error(f"Error generating video for {simulation_id}. {e}")


def save_simulations_results(scenarios: list[Scenario], experiment_folder: dict) -> None:
    """
    Gather the results from each simulation and saves a csv for each scenario, in their
    respective folder under the current experiment folder.
    Then it combines all the results in a single dataFrame and saves it as a csv.

    Args:
        scenarios: The scenarios to get the results from.
        experiment_folder: A dictionary containing the paths in the experiment folder.
    """
    data_folder_path = experiment_folder['data']
    video_folder_path = experiment_folder['video']

    simulations_with_video: list[str] = []
    # Combine all the results
    experiments_data = pd.DataFrame()
    for scenario in scenarios:
        simulations_with_video.extend(scenario.simulation_ids_with_video)
        scenario_data = scenario.get_data()
        experiments_data = pd.concat(
            [experiments_data, scenario_data], ignore_index=True)

    # Save the data
    try:
        data_path = f"{data_folder_path}/{RESULTS_CSV_FILE_NAME}"
        experiments_data.to_csv(data_path)
    except Exception as e:
        logger.error(f"Error saving results file: {e}")

    # save potential videos
    if simulations_with_video:
        logger.info(f"Generating videos for {simulations_with_video}")
        args_list = [(simulation_id, video_folder_path) for simulation_id in simulations_with_video]
        with Pool(processes=get_available_cpus()) as pool:
            pool.map(video_worker, args_list)


def log_execution_time(start_time: float, end_time: float) -> None:
    minutes, seconds = divmod(end_time - start_time, 60)
    logger.info(f"Experiment finished after {int(minutes)} minutes and {seconds:.2f} seconds")


def update_simulations_pool(simulations_pool) -> list[Simulation]:
    """
    Queries the server for the list of unfinished simulations
    and updates the next iteration of the simulations pool.

    Args:
        simulations_pool: The previous iteration of the simulations pool.

    Returns:
        new_pool: The updated simulations pool.
    """
    responses = requests.get(BASE_URL + "/get_unfinished_simulations")
    data = responses.json()
    unfinished_simulations = data['ids']
    unfinished_simulations = set(unfinished_simulations)

    new_pool = []
    for simulation in simulations_pool:
        if simulation.id in unfinished_simulations:
            new_pool.append(simulation)

    if len(new_pool) != len(simulations_pool) and len(new_pool) != 0:
        logger.warning(f"An error prevented {len(unfinished_simulations)} simulations to execute. "
                       f"Trying again...")

    return new_pool


def start_experiments(config: dict[str, Any],
                      scenarios: list[Scenario],
                      experiment_folder: dict[str, str]) -> None:
    """
    Starts the simulations for the provided scenarios.

    It runs the simulations in parallel and saves the result in their respective Scenario objects.
    Then it combines all the results and saves them in a csv file.
    Finally, it returns the results for further analysis.

    Args:
        config: The configuration parameters for the simulations.
        scenarios: The scenarios to be executed.
        experiment_folder: A dictionary containing the paths in the experiment folder.
    """
    start_time = time.time()

    netlogo_model_path: str = config.get('netlogoModelPath', NETLOGO_FOLDER + "model.nlogo")
    simulations_pool = build_simulation_pool(scenarios)
    current_pool = simulations_pool[:]
    # Run the simulations until all are finished
    while current_pool:
        execute_parallel_simulations(current_pool, netlogo_model_path)
        current_pool = update_simulations_pool(simulations_pool)

    save_simulations_results(scenarios, experiment_folder)
    end_time = time.time()
    log_execution_time(start_time, end_time)
