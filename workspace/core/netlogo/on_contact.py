"""
This module provides functionality for getting an adaptation strategy.

The main function in this module is called by the NetLogo simulation
to get the robot's action when it makes contact with a fallen victim.
"""

import importlib
import json
import os
import sys
import traceback
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

sys.path.append("/home/workspace/")

from typing import List, Optional

from core.utils.helper import (get_scenario_index, get_scenario_name,
                               setup_logger)
from core.utils.paths import (ROBOTS_ACTIONS_FILE_NAME,
                              SCENARIOS_TEMP_FILE_NAME, STRATEGIES_FOLDER)
from strategies.AdaptationStrategies import AdaptationStrategy, Survivor

logger = setup_logger()


class ScenarioNotFoundError(Exception):
    pass


class StrategyExecutionError(Exception):
    pass


def get_adaptation_strategy(strategy_name, strategies_folder=STRATEGIES_FOLDER):
    # type: (str, str) -> Optional[AdaptationStrategy]
    """
    Returns an instance of the specified adaptation strategy.

    Looks for a python file with the same name as the strategy in the STRATEGIES_FOLDER,
    that is a subclass of AdaptationStrategy.

    Args:
        strategy_name (str): The name of the strategy.
        strategies_folder (str): The folder containing the strategy files.
                                 Default is STRATEGIES_FOLDER form paths.py.

    Returns:
        AdaptationStrategy: An instance of the specified strategy. None if not found.
    """
    try:
        for file_name in os.listdir(strategies_folder):
            if file_name.endswith('.py') and file_name[:-3] == strategy_name:
                module = importlib.import_module('strategies.' + strategy_name)
                strategy_class = getattr(module, strategy_name)

                if issubclass(strategy_class, AdaptationStrategy):
                    strategy_instance = strategy_class()
                    return strategy_instance
    except Exception as e:
        logger.error("Error in get_adaptation_strategy: %s", e)
        traceback.print_exc()
    raise StrategyExecutionError(
        "Failed to get adaptation strategy {}".format(strategy_name))


def load_scenarios_from_temp(filename=SCENARIOS_TEMP_FILE_NAME):
    # type: (str) -> List[dict]
    """
    Loads the scenarios from the specified JSON file.

    Args:
        filename (str): The name of the file to load the scenarios from.

    Returns:
        list: A list of dictionaries containing the scenarios.
    """
    try:
        with open(filename, 'r') as file:
            scenarios = json.load(file)
    except FileNotFoundError:
        logger.error("File not found: {}".format(filename))
        raise ScenarioNotFoundError("File not found: {}".format(filename))
    except json.JSONDecodeError:
        logger.error("Error decoding JSON from file: {}".format(filename))
        raise ScenarioNotFoundError("Error decoding JSON from file: {}".format(filename))
    except Exception as e:
        logger.error("An unexpected error occurred: {}".format(e))
        raise ScenarioNotFoundError(
            "An unexpected error occurred while loading scenarios from {}".format(filename))

    for scenario in scenarios:
        if 'name' not in scenario or 'adaptation_strategy' not in scenario:
            logger.error("Invalid scenario format in file: %s", filename)
            raise ScenarioNotFoundError("Invalid scenario format in temp file")

    return scenarios


def get_current_scenario(scenario_name, active_scenarios):
    """
    Returns the scenario with the given name from the list of active scenarios.

    Args:
        scenario_name (str): The name of the scenario to find.
        active_scenarios (list): The list of active scenarios.

    Returns:
        dict: The scenario dictionary with the specified name.
    """
    for scenario in active_scenarios:
        if scenario['name'] == scenario_name:
            return scenario
    raise ScenarioNotFoundError("No matching scenario found for name {}".format(scenario_name))


def store_action(action, simulation_id):
    # type: (str, str) -> None
    """
    Stores the action taken by the robot in the `robot_actions.csv` file.

    Args:
        action (str): The action taken by the robot.
        simulation_id (str): The ID of the simulation.
    """
    file_exists = os.path.exists(ROBOTS_ACTIONS_FILE_NAME)
    try:
        with open(ROBOTS_ACTIONS_FILE_NAME, 'a') as file:
            if not file_exists or os.stat(ROBOTS_ACTIONS_FILE_NAME).st_size == 0:
                file.write("id,Action\n")
            file.write("{},{}\n".format(simulation_id, action))
    except IOError as e:
        logger.error("Failed to write to file: %s", e)


def on_survivor_contact(candidate_helper, victim, helper_victim_distance,
                        first_responder_victim_distance, simulation_id):
    # type: ( Survivor, Survivor, float, float, str) -> str
    """
    Finds the adaptation strategy and gets the robot's action.

    Finds the current scenario running in the simulation,
    gets the adaptation strategy, instantiates it and gets the robot's action.

    Args:
        candidate_helper (Survivor): The candidate helper.
        victim (Survivor): The victim.
        helper_victim_distance (float): Distance between the candidate helper and the victim.
        first_responder_victim_distance (float): Distance between the first responder
                                                 and the victim.
        simulation_id (str): The id of the simulation.

    Returns:
        str: The robot action to take.
    """
    logger.info('on_contact.py called by {}'.format(simulation_id))
    # Find the simulation's scenario
    scenario_name = get_scenario_name(simulation_id)
    active_scenarios = load_scenarios_from_temp()
    current_scenario = get_current_scenario(scenario_name, active_scenarios)

    # Find the strategy assigned to the current scenario
    strategy_name = current_scenario.get('adaptation_strategy')
    if not strategy_name:
        raise StrategyExecutionError("No adaptation strategy defined for {}".format(scenario_name))
    strategy = get_adaptation_strategy(strategy_name)

    action = strategy.get_robot_action(candidate_helper, victim, helper_victim_distance,
                                       first_responder_victim_distance)
    logger.info("Selected action: {}".format(action))
    store_action(action, simulation_id)

    return action


def main():
    """
    Called by the NetLogo model when a robot makes contact with a fallen victim.

    The Netlogo model global variables `REQUEST_STAFF_SUPPORT` and `REQUEST_BYSTANDER_SUPPORT` must
    be both be true for this to execute. Responsible for parsing command-line arguments,
    retrieving sensor data, and calling the on_survivor_contact function to get the robot's action.
    """
    try:
        parser = ArgumentParser("Get a robot action from the adaptive controller",
                                formatter_class=ArgumentDefaultsHelpFormatter)
        parser.add_argument("simulation_id")
        parser.add_argument("helper_gender")
        parser.add_argument("helper_culture")
        parser.add_argument("helper_age")
        parser.add_argument("fallen_gender")
        parser.add_argument("fallen_culture")
        parser.add_argument("fallen_age")
        parser.add_argument("helper_fallen_distance")
        parser.add_argument("staff_fallen_distance")
        arguments = parser.parse_args()
        sensor_data = vars(arguments)

        candidate_helper = Survivor(sensor_data["helper_gender"], sensor_data["helper_culture"],
                                    sensor_data["helper_age"])
        victim = Survivor(sensor_data["fallen_gender"], sensor_data["fallen_culture"],
                          sensor_data["fallen_age"])
        helper_victim_distance = float(sensor_data["helper_fallen_distance"])  # type: float
        first_responder_victim_distance = float(sensor_data["staff_fallen_distance"])  # type: float
        simulation_id = sensor_data["simulation_id"]  # type: str

        robot_action = on_survivor_contact(candidate_helper, victim, helper_victim_distance,
                                           first_responder_victim_distance, simulation_id)
        # Needed in order to return the action to netlogo
        print(robot_action)

    except Exception as e:
        logger.error("Error in on_survivor_contact: %s", e)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
