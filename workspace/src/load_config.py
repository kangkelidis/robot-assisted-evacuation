"""
Responsible for loading the JSON configuration file, checking its validity,
and creating Scenario objects.
"""

import copy
import json
import os
from typing import Any, Iterable

import numpy as np  # type: ignore
from src.batch_run import batch_run
from src.simulation import Scenario
from utils.helper import convert_dict_to_snake_case, setup_logger
from utils.paths import CONFIG_FILE, NETLOGO_FOLDER, NETLOGO_HOME

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
    # Load a saved json configuration file from the provided path
    if config['loadConfigFrom']:
        config_file_path = config['loadConfigFrom']
        if not config_file_path.endswith('.json'):
            config_file_path += '.json'
        logger.debug(f"Loading configuration from {config_file_path}")
        config = _load_json_file(config_file_path)

    required_keys = ['loadConfigFrom', 'netlogoModelName', 'targetScenarioForAnalysis',
                     'scenarioParams', 'simulationScenarios']
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Missing key in configuration file: {key}")

    netlogo_model_path = os.path.join(NETLOGO_HOME, NETLOGO_FOLDER, config['netlogoModelName'])
    if not os.path.exists(netlogo_model_path):
        raise IOError(f"NetLogo model path does not exist: {netlogo_model_path}")
    config['netlogoModelPath'] = netlogo_model_path

    scenario_names = set()
    for scenario in copy.deepcopy(config['simulationScenarios']):
        if not scenario['enabled']:
            config['simulationScenarios'].remove(scenario)
            continue

        if 'name' not in scenario or not scenario['name']:
            raise ValueError("Each scenario must have a non-empty 'name' key.")

        # Check for duplicate scenario names
        if scenario['name'] in scenario_names:
            raise ValueError(f"Duplicate scenario name found: {scenario['name']}")
        else:
            scenario_names.add(scenario['name'])

    if not scenario_names:
        raise ValueError("No enabled scenarios found in configuration file.")

    if config['targetScenarioForAnalysis'] not in scenario_names:
        logger.warning(f"CAUTION: Target scenario for analysis not found in simulation scenarios: "
                       f"{config['targetScenarioForAnalysis']}")

    # remove comments
    config.pop('')

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


def get_max_time() -> int:
    """
    Returns the maximum simulation time from the configuration file.
    If not found, returns 120.
    """
    config = load_config(CONFIG_FILE)
    try:
        return int(config['maxSimulationTime'])
    except Exception:
        return 120


def get_netlogo_model_path() -> str:
    config = load_config(CONFIG_FILE)
    return config['netlogoModelPath']


def get_target_scenario() -> str:
    config = load_config(CONFIG_FILE)
    return config['targetScenarioForAnalysis']


def _check_for_range(parameters: dict[str, Any]) -> dict[str, Any]:
    """
    Checks if a value of the parameters in JSON is a range
    and replaces it with a list if it is.

    Using numpy.arange to work with floats and integers.
    {"start": 1, "end": 10, "step": 1} -> range(1, 10, 1)

    Args:
        parameters: A dictionary of parameters to iterate and their respective range of values.

    Returns:
        parameters: The updated dictionary of parameters.
    """
    for key, value in parameters.items():
        if isinstance(value, dict) and 'start' in value and 'end' in value:
            # TODO: float numbers precision is not working properly, 0.450000000002
            parameters[key] = np.arange(value['start'], value['end'], value.get('step', 1)).tolist()
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
    Creates Scenario objects from the config.

    Creates and returns a list of Scenario objects using the scenarioParams and
    scenario-specific parameters from the simulationScenarios
    that are 'enabled' in the config.

    Args:
        config: The configuration dictionary.

    Returns:
        scenarios: A list of Scenario objects.
    """
    scenarios = []

    list_of_scenarios: list[dict[str, Any]] = config['simulationScenarios']
    for scenario_dict in list_of_scenarios:
        global_params: dict[str, Any] = config['scenarioParams']
        scenario_obj = Scenario()
        # Scenario params override global params
        scenario_params = {**global_params, **scenario_dict}
        scenario_params = convert_dict_to_snake_case(scenario_params)
        # no need for it as all scenarios in the list are enabled
        scenario_params.pop('enabled')
        scenario_obj.update(scenario_params)

        if _has_iterable_values(scenario_params):
            logger.debug(f"Building scenarios for {scenario_obj.name} with iterable values.")
            batch = batch_run(scenario_obj, scenario_params, scenario_params['num_of_samples'])
            scenarios.extend(batch)
        else:
            logger.debug(f'Building simulations for scenario: {scenario_obj.name}')
            scenario_obj.build_simulations()
            scenarios.append(scenario_obj)

    logger.debug(f"{len(scenarios)} scenarios loaded from config.")

    return scenarios
