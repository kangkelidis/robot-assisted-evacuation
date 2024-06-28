"""
Responsible for loading the JSON configuration file, checking its validity,
and creating the Scenario objects.
"""

import json
import os
from typing import Dict, List

from core.simulations.simulation import Scenario
from core.utils.helper import setup_logger
from core.utils.paths import (CONFIG_FILE, NETLOGO_FOLDER, NETLOGO_HOME,
                              SCENARIOS_TEMP_FILE_NAME)

logger = setup_logger()

CONFIG = None


def load_config(config_file_path):
    # type: (str) -> Dict
    """
    The JSON configuration file is loaded and checked for the following keys:

    - netlogoModeName           (str)
    - targetScenarioForAnalysis (str)
    - scenarioParams            (dict)
    - simulationScenarios       (list[dict])

    Then the scenarios are loaded and returned as a dictionary.
    """
    global CONFIG
    if CONFIG:
        return CONFIG
    try:
        with open(config_file_path, 'r') as file:
            config = json.load(file)
    except IOError:
        raise IOError(
            "Configuration file not found. Path given: {}".format(config_file_path))
    except json.JSONDecodeError:
        raise ValueError(
            "Invalid JSON format in configuration file: {}".format(config_file_path))

    required_keys = ['netlogoModeName', 'targetScenarioForAnalysis', 'scenarioParams',
                     'simulationScenarios']
    for key in required_keys:
        if key not in config:
            raise KeyError("Missing key in configuration file: {}".format(key))

    for scenario in config['simulationScenarios']:
        if 'name' not in scenario or not scenario['name']:
            raise ValueError("Each scenario must have a non-empty 'name' key.")

    netlogo_model_path = os.path.join(NETLOGO_HOME, NETLOGO_FOLDER, config['netlogoModeName'])
    logger.debug("NetLogo model path: {}".format(netlogo_model_path))
    if not os.path.exists(netlogo_model_path):
        raise IOError(
            "NetLogo model path does not exist: {}".format(netlogo_model_path))
    config['netlogoModelPath'] = netlogo_model_path

    CONFIG = config
    logger.info('Config checked and loaded. Loading Scenarios...')
    return config


def load_netlogo_model_path():
    # type: () -> str
    config = load_config(CONFIG_FILE)
    return config['netlogoModelPath']


def load_target_scenario():
    # type: () -> str
    config = load_config(CONFIG_FILE)
    return config['targetScenarioForAnalysis']


def load_scenarios():
    # type: () -> List[Scenario]
    """
    Creates and returns a list of Scenario objects. They are created using
    the scenarioParams and scenario specific params from
    the simulationScenarios that are 'enabled', in the config.json file.
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
            logger.info('Building simulations for scenario: {}'.format(scenario_obj.name))
            scenario_obj.build_simulations()
            scenarios.append(scenario_obj)

    save_scenarios(scenarios)
    logger.debug("{} scenarios loaded and saved to {}.".format(len(scenarios),
                                                               SCENARIOS_TEMP_FILE_NAME))
    return scenarios


def save_scenarios(scenarios):
    """ Saves the scenarios to a temporary file. To be read by on_contact.py."""
    try:
        temp_file_path = NETLOGO_FOLDER + SCENARIOS_TEMP_FILE_NAME
        with open(temp_file_path, 'w') as temp_file:
            scenarios_dict = [{
                'name': scenario.name,
                'adaptation_strategy': scenario.adaptation_strategy}
                for scenario in scenarios]
            json.dump(scenarios_dict, temp_file)
    except IOError as e:
        logger.error("Failed to write to file: %s", e)
    except TypeError as e:
        logger.error("Type error during serialization: %s", e)
    except Exception as e:
        logger.error("Unexpected error: %s", e)
