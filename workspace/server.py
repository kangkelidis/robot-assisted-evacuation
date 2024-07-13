from __future__ import annotations

import importlib
import json
import logging
import os
import sys
from typing import Optional

from core.simulations.simulation import Result, Scenario, Simulation
from core.utils.helper import get_scenario_name, setup_logger
from core.utils.paths import (NETLOGO_FOLDER, ROBOTS_ACTIONS_FILE_NAME,
                              SCENARIOS_TEMP_FILE_NAME, STRATEGIES_FOLDER)
from flask import Flask, request
# sys.path.append("/home/workspace/")
from strategies.AdaptationStrategies import AdaptationStrategy, Survivor

logger = setup_logger()

app = Flask(__name__)

SCENARIOS = []
class ScenarioNotFoundError(Exception):
    pass


class StrategyExecutionError(Exception):
    pass


def get_adaptation_strategy(strategy_name: str,
                            strategies_folder: str = STRATEGIES_FOLDER
                            ) -> Optional[AdaptationStrategy]:
    """
    Returns an instance of the specified adaptation strategy.

    Looks for a python file with the same name as the strategy in the STRATEGIES_FOLDER,
    that is a subclass of AdaptationStrategy.

    Args:
        strategy_name: The name of the strategy.
        strategies_folder: The folder containing the strategy files.
                                 Default is STRATEGIES_FOLDER form paths.py.

    Returns:
        AdaptationStrategy: An instance of the specified strategy. None if not found.
    """
    try:
        for file_name in os.listdir(strategies_folder):
            if file_name.endswith('.py') and file_name[:-3] == strategy_name:
                module_path = f'strategies.{strategy_name}'
                module = importlib.import_module(module_path)
                strategy_class = getattr(module, strategy_name)

                if issubclass(strategy_class, AdaptationStrategy):
                    strategy_instance = strategy_class()
                    return strategy_instance
    except Exception as e:
        logger.error(f"Error in get_adaptation_strategy: {e}")

    raise StrategyExecutionError(
        f"Failed to get adaptation strategy {strategy_name}")


def load_scenarios_from_temp(filename: str = SCENARIOS_TEMP_FILE_NAME) -> list[dict]:
    """
    Loads the scenarios from the specified JSON file.

    Args:
        filename: The name of the file to load the scenarios from.

    Returns:
        A list of dictionaries containing the scenarios.
    """
    try:
        filename = NETLOGO_FOLDER + filename
        with open(filename, 'r') as file:
            scenarios = json.load(file)
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        raise ScenarioNotFoundError(f"File not found: {filename}")
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from file: {filename}")
        raise ScenarioNotFoundError(f"Error decoding JSON from file: {filename}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise ScenarioNotFoundError(
            f"An unexpected error occurred while loading scenarios from {filename}")

    for scenario in scenarios:
        if 'name' not in scenario or 'adaptation_strategy' not in scenario:
            logger.error(f"Invalid scenario format in file: {filename}")
            raise ScenarioNotFoundError("Invalid scenario format in temp file")

    return scenarios


def get_current_scenario(scenario_name: str,
                         active_scenarios: list[dict[str, str]]
                         ) -> dict[str, str]:
    """
    Returns the scenario with the given name from the list of active scenarios.

    Args:
        scenario_name: The name of the scenario to find.
        active_scenarios: The list of active scenarios.

    Returns:
        The scenario dictionary with the specified name.
    """
    for scenario in active_scenarios:
        if scenario['name'] == scenario_name:
            return scenario
    raise ScenarioNotFoundError(f"No matching scenario found for name {scenario_name}")


def store_action(action: str, simulation_id: str) -> None:
    """
    Stores the action taken by the robot in the `robot_actions.csv` file.

    Args:
        action: The action taken by the robot.
        simulation_id: The ID of the simulation.
    """
    file_path = NETLOGO_FOLDER + ROBOTS_ACTIONS_FILE_NAME
    file_exists = os.path.exists(file_path)
    try:
        with open(file_path, 'a') as file:
            if not file_exists or os.stat(file_path).st_size == 0:
                file.write("id,Action\n")
            file.write(f"{simulation_id},{action}\n")
    except IOError as e:
        logger.error(f"Failed to write to file: {e}")


def on_survivor_contact(candidate_helper: Survivor,
                        victim: Survivor,
                        helper_victim_distance: float,
                        first_responder_victim_distance: float,
                        simulation_id: str) -> str:
    """
    Finds the adaptation strategy and gets the robot's action.

    Finds the current scenario running in the simulation,
    gets the adaptation strategy, instantiates it and gets the robot's action.

    Args:
        candidate_helper: The candidate helper.
        victim: The victim.
        helper_victim_distance: Distance between the candidate helper and the victim.
        first_responder_victim_distance: Distance between the first responder
                                                 and the victim.
        simulation_id: The id of the simulation.

    Returns:
        The robot action to take.
    """
    logger.debug(f'on_contact.py called by {simulation_id}')
    # Find the simulation's scenario
    scenario_name = get_scenario_name(simulation_id)
    active_scenarios = load_scenarios_from_temp()
    current_scenario = get_current_scenario(scenario_name, active_scenarios)

    # Find the strategy assigned to the current scenario
    strategy_name = current_scenario.get('adaptation_strategy')
    if not strategy_name:
        raise StrategyExecutionError(f"No adaptation strategy defined for {scenario_name}")
    strategy = get_adaptation_strategy(strategy_name)

    action = strategy.get_robot_action(candidate_helper, victim, helper_victim_distance,
                                       first_responder_victim_distance)
    logger.debug(f"Selected action: {action}")
    store_action(action, simulation_id)

    return action

# @app.route('/finished', methods=['POST'])
# def finished():
#     data = request.json
#     simulation_id = data["simulation_id"]
#     ticks = data["ticks"]
#     scenario_name = get_scenario_name(simulation_id)
#     scenario: Scenario = next((s for s in SCENARIOS if s.name == scenario_name), None)
#     simulation: Simulation = next((s for s in scenario.simulations if s.id == simulation_id), None)
#     r: Result = simulation.result
#     r.evacuation_ticks = ticks
#     r.simulation_id = simulation_id
#     r.success = True
#     return "Simulation finished"


@app.route('/put_results', methods=['POST'])
def put_results():
    data = request.json
    results = Result(**data)
    simulation_id = results.simulation_id
    scenario_name = get_scenario_name(simulation_id)
    scenario: Scenario = next((s for s in SCENARIOS if s.name == scenario_name), None)
    simulation: Simulation = next((s for s in scenario.simulations if s.id == simulation_id), None)
    simulation.result = results

    return "Results received"

@app.route('/passenger_response', methods=['POST'])
def passenger_response():
    data = request.json
    simulation_id = data["simulation_id"]
    response = data["response"]

    scenario_name: str = get_scenario_name(simulation_id)
    scenario: Scenario = next((s for s in SCENARIOS if s.name == scenario_name), None)
    simulation = next((s for s in scenario.simulations if s.id == simulation_id), None)
    simulation.responses.append(response)

    return "Response received"


@app.route('/on_survivor_contact', methods=['POST'])
def handler():
    data = request.json

    candidate_helper = Survivor(data["helper_gender"], data["helper_culture"], data["helper_age"])
    victim = Survivor(data["fallen_gender"], data["fallen_culture"], data["fallen_age"])
    helper_victim_distance = float(data["helper_fallen_distance"])
    first_responder_victim_distance = float(data["staff_fallen_distance"])
    simulation_id = data["simulation_id"]

    action = on_survivor_contact(candidate_helper, victim, helper_victim_distance,
                                 first_responder_victim_distance, simulation_id)
    scenario_name: str = get_scenario_name(simulation_id)
    scenario: Scenario = next((s for s in SCENARIOS if s.name == scenario_name), None)
    simulation = next((s for s in scenario.simulations if s.id == simulation_id), None)
    simulation.actions.append(action)
    return action


@app.route('/run', methods=['GET'])
def run():
    import traceback
    from typing import Any

    from core.simulations.load_config import load_config, load_scenarios
    from core.simulations.results_analysis import perform_analysis
    from core.simulations.simulation import Scenario
    from core.simulations.simulation_manager import start_experiments
    from core.utils.cleanup import cleanup_workspace
    from core.utils.helper import setup_folders, setup_logger
    from core.utils.paths import CONFIG_FILE, WORKSPACE_FOLDER
    logger = setup_logger()
    try:
        logger.info("******* ==Starting Experiment== *******")
        setup_folders()

        config: dict[str, Any] = load_config(CONFIG_FILE)
        scenarios: list[Scenario] = load_scenarios(config)
        global SCENARIOS
        SCENARIOS = scenarios
        experiments_results = start_experiments(config, scenarios)

        perform_analysis(experiments_results)

        logger.info("******* ==Experiment Finished== *******\n")
    except Exception as e:
        logger.critical(f"Error in main: {e}")
        traceback.print_exc()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt: Cleaning up workspace.")
    finally:
        cleanup_workspace(WORKSPACE_FOLDER)

    return 'ok'


if __name__ == "__main__":
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(debug=False, port=5000)
