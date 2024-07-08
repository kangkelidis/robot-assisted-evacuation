"""
Responsible for loading the JSON configuration file, checking its validity,
and creating Scenario objects.
"""

import json
import os
from typing import Any

from core.simulations.simulation import Scenario
from core.utils.helper import setup_logger
from core.utils.paths import (CONFIG_FILE, NETLOGO_FOLDER, NETLOGO_HOME,
                              SCENARIOS_TEMP_FILE_NAME)

logger = setup_logger()

CONFIG: dict[str, Any] | None = None


def load_config(config_file_path: str) -> dict[str, Any]:
    """
    Loads the JSON configuration file and checks for the following keys:

    - netlogoModeName
    - targetScenarioForAnalysis
    - scenarioParams
    - simulationScenarios

    Then the scenarios are loaded and returned as a dictionary.

    Args:
        config_file_path: The path to the JSON configuration file.

    Returns:
        The configuration dictionary.
    """
    global CONFIG
    if CONFIG:
        return CONFIG
    try:
        with open(config_file_path, 'r') as file:
            config: dict[str, Any] = json.load(file)
    except IOError:
        raise IOError(f"Configuration file not found. Path given: {config_file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in configuration file: {config_file_path}")

    required_keys = ['netlogoModeName', 'targetScenarioForAnalysis', 'scenarioParams',
                     'simulationScenarios']
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Missing key in configuration file: {key}")

    for scenario in config['simulationScenarios']:
        if 'name' not in scenario or not scenario['name']:
            raise ValueError("Each scenario must have a non-empty 'name' key.")

    netlogo_model_path = os.path.join(NETLOGO_HOME, NETLOGO_FOLDER, config['netlogoModeName'])
    logger.debug("NetLogo model path: {}".format(netlogo_model_path))
    if not os.path.exists(netlogo_model_path):
        raise IOError(f"NetLogo model path does not exist: {netlogo_model_path}")
    config['netlogoModelPath'] = netlogo_model_path

    CONFIG = config
    logger.debug('Config checked and loaded. Loading Scenarios...')
    return config


def load_netlogo_model_path() -> str:
    config = load_config(CONFIG_FILE)
    return config['netlogoModelPath']


def load_target_scenario() -> str:
    config = load_config(CONFIG_FILE)
    return config['targetScenarioForAnalysis']


def load_scenarios() -> list[Scenario]:
    """
    Loads the config file, creates Scenario objects and saves them to a temporary file.

    Creates and returns a list of Scenario objects using the scenarioParams and
    scenario-specific parameters from the simulationScenarios
    that are 'enabled' in the config.json file.

    Returns:
        scenarios: A list of Scenario objects.
    """
    config = load_config(CONFIG_FILE)
    scenarios = []

    for scenario_dict in config['simulationScenarios']:
        # Only build the scenario if it is enabled
        if scenario_dict.get('enabled', False):
            global_params = config['scenarioParams']
            scenario_obj = Scenario()
            # Scenario params override global params
            params_to_update = global_params.copy()  # Make a copy of the global_params
            params_to_update.update(scenario_dict)  # Update the copy with scenario_dict
            scenario_obj.update(params_to_update)
            logger.debug(f'Building simulations for scenario: {scenario_obj.name}')
            scenario_obj.build_simulations()
            scenarios.append(scenario_obj)

    save_scenarios(scenarios)
    logger.debug(f"{len(scenarios)} scenarios loaded and saved to {SCENARIOS_TEMP_FILE_NAME}.")

    return scenarios


def save_scenarios(scenarios: list[Scenario]) -> None:
    """Saves the scenarios to a temporary file, so that they can be accessed by on_contact.py.

    Args:
        scenarios: A list of Scenario objects.
    """
    try:
        temp_file_path = NETLOGO_FOLDER + SCENARIOS_TEMP_FILE_NAME
        with open(temp_file_path, 'w') as temp_file:
            scenarios_dict = [{
                'name': scenario.name,
                'adaptation_strategy': scenario.adaptation_strategy}
                for scenario in scenarios]
            json.dump(scenarios_dict, temp_file)
    except IOError as e:
        logger.error(f"Failed to write to file: {e}")
    except TypeError as e:
        logger.error(f"Type error during serialization: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
