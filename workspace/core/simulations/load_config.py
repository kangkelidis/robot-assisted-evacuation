"""
Responsible for loading the JSON configuration file, checking its validity,
and creating Scenario objects.
"""

import json
import os
from typing import Any, Iterable

from core.simulations.batchrun import batch_run
from core.simulations.simulation import Scenario
from core.utils.helper import convert_dict_to_snake_case, setup_logger
from core.utils.paths import (CONFIG_FILE, EXAMPLES_FOLDER, NETLOGO_FOLDER,
                              NETLOGO_HOME, SCENARIOS_TEMP_FILE_NAME)

logger = setup_logger()

CONFIG: dict[str, Any] | None = None


def _load_json_file(config_file_path: str) -> dict[str, Any]:
    """
    Loads the JSON file and checks for errors.

    Args:
        config_file_path: The path to the JSON configuration file.

    Returns:
        config: The configuration dictionary.
    """
    try:
        with open(config_file_path, 'r') as file:
            config: dict[str, Any] = json.load(file)
    except IOError:
        raise IOError(f"Configuration file not found. Path given: {config_file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in configuration file: {config_file_path}")

    return config


def _get_params_from(config: dict[str, Any]) -> dict[str, Any]:
    """
    Gets the parameters from the configuration file and checks for required keys.

    Args:
        config: The configuration dictionary.

    Returns:
        config: The updated configuration dictionary.
    """
    # Load a saved configuration file if specified
    if config['loadConfigFrom']:
        config_file_path = os.path.join(EXAMPLES_FOLDER, config['loadConfigFrom'])
        if not config_file_path.endswith('.json'):
            config_file_path += '.json'
        logger.debug(f"Loading configuration from {config_file_path}")
        config = _load_json_file(config_file_path)

    required_keys = ['loadConfigFrom', 'netlogoModeName', 'targetScenarioForAnalysis',
                     'scenarioParams', 'simulationScenarios']
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Missing key in configuration file: {key}")

    netlogo_model_path = os.path.join(NETLOGO_HOME, NETLOGO_FOLDER, config['netlogoModeName'])
    logger.debug(f"NetLogo model path: {netlogo_model_path}")
    if not os.path.exists(netlogo_model_path):
        raise IOError(f"NetLogo model path does not exist: {netlogo_model_path}")
    config['netlogoModelPath'] = netlogo_model_path

    for scenario in config['simulationScenarios']:
        if 'name' not in scenario or not scenario['name']:
            raise ValueError("Each scenario must have a non-empty 'name' key.")

    return config


def load_config(config_file_path: str) -> dict[str, Any]:
    """
    Loads the specified JSON configuration file.

    Args:
        config_file_path: The path to the JSON configuration file.

    Returns:
        The configuration dictionary.
    """
    global CONFIG
    if CONFIG:
        return CONFIG

    config = _load_json_file(config_file_path)
    config = _get_params_from(config)

    CONFIG = config
    logger.debug('Config checked and loaded.')
    return config


def get_netlogo_model_path() -> str:
    config = load_config(CONFIG_FILE)
    return config['netlogoModelPath']


def get_target_scenario() -> str:
    config = load_config(CONFIG_FILE)
    return config['targetScenarioForAnalysis']


def _check_for_range(parameters: dict[str, Any]) -> dict[str, Any]:
    """
    Checks if a value of the parameters in JSON is a range
    and replaces it with a python range Iterable if it is.

    {"start": 1, "end": 10, "step": 1} -> range(1, 10, 1)

    Args:
        parameters: A dictionary of parameters to iterate and their respective range of values.

    Returns:
        parameters: The updated dictionary of parameters.
    """
    for key, value in parameters.items():
        if isinstance(value, dict) and 'start' in value and 'end' in value:
            parameters[key] = range(value['start'], value['end'], value.get('step', 1))

    return parameters


def _has_iterable_values(parameters: dict[str, Any]) -> bool:
    """
    Checks if a value of the parameters is iterable.

    Args:
        parameters: A dictionary of parameters to iterate and their respective range of values.

    Returns:
        True if a value is iterable, False otherwise.
    """
    _check_for_range(parameters)

    for value in parameters.values():
        if isinstance(value, Iterable) and not isinstance(value, str):
            return True

    return False


def load_scenarios(config: dict[str, Any]) -> list[Scenario]:
    """
    Creates Scenario objects from the config and saves them to a temporary file.

    Creates and returns a list of Scenario objects using the scenarioParams and
    scenario-specific parameters from the simulationScenarios
    that are 'enabled' in the config.json file.

    Args:
        config: The configuration dictionary.

    Returns:
        scenarios: A list of Scenario objects.
    """
    scenarios = []

    list_of_scenarios: list[dict[str, Any]] = config['simulationScenarios']
    for scenario_dict in list_of_scenarios:
        # Only build the scenario if it is enabled
        if scenario_dict.get('enabled', False):
            global_params = config['scenarioParams']
            scenario_obj = Scenario()
            # Scenario params override global params
            scenario_params = global_params.copy()  # Make a copy of the global_params
            scenario_params.update(scenario_dict)  # Update the copy with scenario_dict
            scenario_obj.update(scenario_params)

            if _has_iterable_values(scenario_params):
                scenario_params = convert_dict_to_snake_case(scenario_params)
                logger.debug(f"Building scenarios for {scenario_obj.name} with iterable values.")
                batch = batch_run(scenario_obj, scenario_params, scenario_params['num_of_samples'])
                scenarios.extend(batch)
            else:
                logger.debug(f'Building simulations for scenario: {scenario_obj.name}')
                scenario_obj.build_simulations()
                scenarios.append(scenario_obj)

    save_scenarios(scenarios)
    logger.debug(f"{len(scenarios)} scenarios loaded and saved to {SCENARIOS_TEMP_FILE_NAME}.")

    return scenarios

#  TODO: remove
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
