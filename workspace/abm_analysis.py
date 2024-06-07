import math
import time
import traceback
import pandas as pd
import signal
import random
import pyNetLogo

from pyNetLogo import NetLogoException
from multiprocessing import Pool, Process, Queue, cpu_count
from typing import List, Tuple, Dict, Optional

from abm_video_generation import generate_video
from utils import setup_logger, timeout_exception_handler, get_available_cpus
from netlogo_commands import *
from config import *

# Set up the signal handler for the timeout exception
signal.signal(signal.SIGALRM, timeout_exception_handler)
logger = setup_logger()

class SimulationResult(object):
    def __init__(self, simulation_id, time):
        self.simulation_id = simulation_id  # type: str
        self.time = int(time)  # type: int
        if "_" not in simulation_id:
            raise ValueError("Simulation id does not contain the scenario name (no '_').")
        self.scenario = simulation_id.split("_")[0]  # type: str


def get_netlogo_report(simulation_id):
    # type: (str) -> Optional[pd.DataFrame]
    """Runs the Netlogo simulation and returns the results for the count commands."""

    TIME_LIMIT_SECONDS = 120  # type: int
    MAX_RETRIES = 2

    metrics_dataframe = None
    for i in range(MAX_RETRIES):
        try:
            logger.debug("Starting reporter for %s, attempt no. %i", simulation_id, i)
            signal.alarm(TIME_LIMIT_SECONDS)

            start_time = time.time()
            metrics_dataframe = netlogo_link.repeat_report(
                netlogo_reporter=[TURTLE_PRESENT_REPORTER, EVACUATED_REPORTER, DEAD_REPORTER],
                reps=MAX_NETLOGO_TICKS)  # type: pd.DataFrame
            endtime = time.time()

            logger.info("%s simulation completed on attempt n.%i. Execution time was %.2f seconds", simulation_id, i+1, endtime-start_time)
            signal.alarm(0)
            break
        except Exception as e:
            logger.error("Exception in %s attempt no.%i: %s", simulation_id, i, e)
            signal.alarm(0)
    
    return metrics_dataframe


def setup_simulation(simulation_id, post_setup_commands):
    # type: (str, List[str]) -> None

    logger.info("id:{} starting simulation".format(simulation_id))
    current_seed = netlogo_link.report(SEED_SIMULATION_REPORTER)  # type:str
    netlogo_link.command("setup")
    netlogo_link.command(SET_SIMULATION_ID_COMMAND.format(simulation_id))

    # netlogo_link.command(SET_GROUP_IDENTIFYING_PERCENTAGE_COMMAND.format(GROUP_IDENTIFYING_PERCENTAGE))
    # netlogo_link.command(SET_REDUCE_HELPING_CHANCE_COMMAND.format(REDUCE_HELPING_CHANCE))
    # netlogo_link.command(SET_BOOST_HELPING_CHANCE_COMMAND.format(BOOST_HELPING_CHANCE))

    logger.debug('id: {} completed setup'.format(simulation_id))

    if len(post_setup_commands) > 0:
        for post_setup_command in post_setup_commands:
            netlogo_link.command(post_setup_command)
            logger.debug("id:{} seed:{} {} executed".format(simulation_id, current_seed, post_setup_command))
    else:
        logger.debug("id:{} seed:{} no post-setup commands".format(simulation_id, current_seed))
    
    logger.info('id: {} completed commands'.format(simulation_id))


def run_simulation(simulation_id, post_setup_commands):
    # type: (str, List[str]) -> SimulationResult
    try:
        setup_simulation(simulation_id, post_setup_commands)

        metrics_dataframe = get_netlogo_report(simulation_id)

        if metrics_dataframe is None:
            logger.error("id:{} metrics_dataframe is None. The simulation did not return any results.".format(simulation_id))
            # TODO: think how to handle this case
            return SimulationResult(simulation_id, 0)
        
        evacuation_finished = metrics_dataframe[
            metrics_dataframe[TURTLE_PRESENT_REPORTER] == metrics_dataframe[DEAD_REPORTER]]
        evacuation_time = evacuation_finished.index.min()  # type: float

        # TODO: think how to handle this case
        if math.isnan(evacuation_time):
            metrics_dataframe.to_csv("data/nan_df.csv")
            logger.warning("DEBUG!!! info to data/nan_df.csv")
            # simulation did not finish on time, use max time/ticks
            evacuation_time = MAX_NETLOGO_TICKS

        if GENERATE_VIDEO:
            generate_video(simulation_id=simulation_id)

        return SimulationResult(simulation_id, evacuation_time)
    except NetLogoException as e:
        logger.error("id:{} NetLogo exception: {}".format(simulation_id, e))
        traceback.print_exc()
    except Exception as e:
        logger.error("id:{} Exception: {}".format(simulation_id, e))
        traceback.print_exc() 

    return SimulationResult(simulation_id, 0)


def initialise_netlogo_link():
    # type: () -> None
    logger.debug("Initializing NetLogo")
    global netlogo_link

    netlogo_link = pyNetLogo.NetLogoLink(netlogo_home=NETLOGO_HOME,
                                         netlogo_version=NETLOGO_VERSION,
                                         gui=False)  # type: pyNetLogo.NetLogoLink
    netlogo_link.load_model(NETLOGO_MODEL_FILE)


def build_simulation_pool(experiment_configurations, samples):
    # type: (Dict[str, List[str]], int) -> List[Dict[str, List[str]]]
    """ Takes each simulation scenario and creates a pool of all simulations."""

    simulations_pool = []  # type: List[Dict[str, List[str]]]
    for experiment_name, experiment_commands in experiment_configurations.items():
        for simulation_index in range(samples):
            simulations_pool.append({"simulation_id": "{}_{}".format(experiment_name, simulation_index),
                                    "post_setup_commands": experiment_commands})
    return simulations_pool


def simulation_processor(simulations_results_queue, simulation_parameters):
    try:
        initialise_netlogo_link() 
        result = run_simulation(**simulation_parameters)
    except Exception as e:
        logger.error("Exception in simulation_processor: %s", e)
        result = SimulationResult(simulation_parameters["simulation_id"], 0)

    simulations_results_queue.put(result)


def execute_parallel_simulations(simulations_pool):
    # type: (List[Dict[str, List[str]]]) -> List[SimulationResult]
    """ Runs each simulations in the simulation_pool in parallel using multiprocessing."""
    
    # Using multiprocessing.Queue to allow for inter-process communication and store the results
    simulations_results_queue = Queue() # type: Queue
    simulations_results = []  # type: List[SimulationResult]

    num_cpus = get_available_cpus()
    random.shuffle(simulations_pool) 

    logger.info("Total number of simulations to run: %i.", len(simulations_pool))
    try:
        while simulations_pool:
            processes = []
            for _ in range(num_cpus):
                if simulations_pool:  
                    simulation_parameters = simulations_pool.pop()
                    process = Process(target=simulation_processor, args=(simulations_results_queue, simulation_parameters))
                    processes.append(process)
                    process.start()
                    logger.debug("Started process %s. Remaining simulations: %s", process.pid, len(simulations_pool))
            
            for process in processes:
                try:
                    process.join()
                except Exception as e:
                    logger.error("Exception in joining process: %s", e)
                    traceback.print_exc()
                    process.terminate()

                logger.debug("Process %s terminated.", process.pid)
            logger.info("All processes in current batch finished. Remaining simulations: %s", len(simulations_pool))
        logger.info("Finished all simulations. Successful results Queue size: %s", simulations_results_queue.qsize()) 

        while not simulations_results_queue.empty():
            simulation_result = simulations_results_queue.get() # type: SimulationResult
            simulations_results.append(simulation_result) # type: List[SimulationResult]

    except Exception as e:
        logger.error("Exception in parallel simulation")
        print(e)
        traceback.print_exc()

    return simulations_results


def extract_evacuation_times(results):
    # type: (List[SimulationResult]) -> Dict[str, List[int]]
    """ Extracts the evacuation times from the results and groups them by scenario name."""

    simulation_times = {}  # type: Dict[str, List[int]]
    for result in results:
        if result.scenario in simulation_times:
            simulation_times[result.scenario].append(result.time)
        else:
            simulation_times[result.scenario] = [result.time]
    return simulation_times


def start_experiments(experiment_configurations, results_file, samples):
    # type: (Dict[str, List[str]], str, int) -> None
    start_time = time.time()  # type: float

    simulations_pool = build_simulation_pool(experiment_configurations, samples) # type: List[Dict[str, List[str]]]
    results = execute_parallel_simulations(simulations_pool) # type: List[SimulationResult]
    experiment_data = extract_evacuation_times(results) # type: Dict[str, List[int]]

    end_time = time.time()  # type: float
    logger.info("Simulation finished after {} seconds".format(end_time - start_time))

    # TODO: make sure the experiment_data has the same length for all scenarios
    try:
        experiment_results = pd.DataFrame(experiment_data)  # type:pd.DataFrame
        experiment_results.to_csv(results_file)
        logger.debug("Data written to {}".format(results_file))
    except Exception as e:
        logger.warning("Error writing data to file. Experiment data: {}. \n{}".format(experiment_data, e))


def simulate_and_store(simulation_scenarios, results_file_name, samples):
    # type: (Dict[str, List[str]],str, int) -> None

    updated_simulation_scenarios = {scenario_name: commands
                                    for scenario_name, commands in
                                    simulation_scenarios.iteritems()}  # type: Dict[str, List[str]]
    start_experiments(updated_simulation_scenarios, results_file_name, samples)

