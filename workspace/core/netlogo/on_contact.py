import importlib
import json
import os
import sys
import traceback
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

sys.path.append("/home/workspace/")

from core.utils.helper import get_scenario_name, setup_logger
from core.utils.paths import (SCENARIOS_TEMP_FILE_RELATIVE_PATH,
                              STRATEGIES_FOLDER)
from strategies.AdaptationStrategies import AdaptationStrategy, Survivor

logger = setup_logger()


class ScenarioNotFoundError(Exception):
    pass


class StrategyExecutionError(Exception):
    pass


def get_adaptation_strategy(strategy_name):
    # type: (str) -> AdaptationStrategy | None
    """
    Returns an instance of the specified adaptation strategy.
    Looks for a python file with the same name as the strategy in the STRATEGIES_FOLDER,
    that is a subclass of AdaptationStrategy.
    """
    try:
        for file_name in os.listdir(STRATEGIES_FOLDER):
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


def load_scenarios_from_temp(filename='scenarios_temp.json'):
    """Loads the scenarios from the specified JSON file."""
    try:
        with open(filename, 'r') as file:
            scenarios = json.load(file)
        return scenarios
    except IOError:
        logger.error("File not found or can't be opened: %s", filename)
    except ValueError:
        logger.error("Error decoding JSON from file: %s", filename)
    except Exception as e:
        logger.error("An unexpected error occurred: %s", str(e))
    raise ScenarioNotFoundError("Failed to load scenarios from temp")


def get_current_scenario(scenario_name, active_scenarios):
    """ Returns the scenario with the given name from the list of active scenarios."""
    for scenario in active_scenarios:
        if scenario['name'] == scenario_name:
            return scenario
    raise ScenarioNotFoundError("No matching scenario found for name {}".format(scenario_name))


def on_survivor_contact(candidate_helper, victim, helper_victim_distance,
                        first_responder_victim_distance, simulation_id):
    # type: ( Survivor, Survivor, float, float, str) -> str
    """
    This function is called by the Netlogo model when a robot makes contact with a fallen victim
    and the simulation uses an adaptive strategy (staff_support and passenger_support are true).
    The function return the outcome of the adaptive strategy for the robot.
    Either to ask help from a staff member or from a nearby passenger.
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
    return action


def main():
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
        # Needed in otder to return to netlogo
        print(robot_action)

    except Exception as e:
        logger.error("Error in on_survivor_contact: %s", e)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
