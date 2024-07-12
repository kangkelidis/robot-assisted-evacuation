"""
A method to run a scenario using a different comninbation of parameters.

Should take a scenario, a dictionary of parameteres to iterate and their respective range of values,
and number of samples to run each combination of parameters.

Note:
Inspired by the butch_run method in Mesa's BatchRunner class.
https://github.com/projectmesa/mesa
"""

import itertools
import os
import sys
from typing import Any, Iterable, Mapping, Union

ParametersType = Mapping[str, Union[Any, Iterable[Any]]]

workspace_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(workspace_path)

from core.simulations.simulation import Scenario
from core.utils.helper import setup_logger

logger = setup_logger()


def _get_scenario_name(scenario: Scenario, kwargs: dict[str, Any]) -> str:
    """
    Returns a name for the scenario based on the parameters.

    Args:
        scenario: The scenario to run.
        kwargs: A dictionary of parameters to iterate and their respective range of values.

    Returns:
        A name for the scenario based on the parameters.
    """
    name = scenario.name + "--" + ''.join(
        [f"+{key}={value}" for key, value in kwargs.items()])
    name = name.replace("_", "-")
    return name


def _build_kwargs(parameters: ParametersType) -> list[dict[str, Any]]:
    """
    Build a list of dictionaries with all the different combinations of parameters.

    Args:
        parameters: A dictionary of parameters to iterate and their respective range of values.

    Returns:
        A list of dictionaries with different combinations of parameters.
    """
    # Holds lists of tuples, where each tuple is a parameter name its value
    parameter_list: list[list[tuple[str, Any]]] = []
    for param, values in parameters.items():
        if isinstance(values, Iterable) and not isinstance(values, str):
            all_values: list[tuple[str, Any]] = [(param, value) for value in values]
            parameter_list.append(all_values)

    all_kwargs: Iterable[tuple[tuple[str, Any]]] = itertools.product(*parameter_list)
    kwargs_list: list[dict[str, Any]] = [dict(kwargs) for kwargs in all_kwargs]
    return kwargs_list


def batch_run(scenario: Scenario, parameters: ParametersType, num_samples: int) -> list[Scenario]:
    """
    Creates a list of scenarios with different combinations of parameters.

    Example:
        batch_run(scenario, {num_of_robots: range(1, 11)}, 5) will run the scenario 50 times.
        - 5 times with num_of_robots equal to 1, 5 times equal to 2 ...

        batch_run(scenario, {num_of_robots: range(1, 11), num_of_staff: [2, 10]}, 5)
        will run the scenario 100 times.
        - 5 times with num_of_robots equal to 1, num_of_staff equal = 2,
        - 5 times with num_of_robots equal to 1, num_of_staff equal = 10,
        - 5 times with num_of_robots equal to 2, num_of_staff equal = 2...

    Args:
        scenario: The scenario to run.
        parameters: A dictionary of parameters to iterate and their respective range of values.
        num_samples: The number of samples to run each combination of parameters.

    Returns:
        Scenrios: A list of scenarios with different combinations of parameters.
    """
    keys = list(parameters.keys())
    # check that every key is in the scenario
    for key in keys:
        if not (hasattr(scenario, key) or hasattr(scenario.netlogo_params, key)):
            raise ValueError(f"Parameter {key} not in scenario")

    scenarios: list[Scenario] = []
    kwargs_list: list[dict[str, Any]] = _build_kwargs(parameters)

    for kwargs in kwargs_list:
        new_scenario = scenario.copy()
        new_scenario.name = _get_scenario_name(scenario, kwargs)
        new_scenario.netlogo_params.num_of_samples = num_samples

        for key, value in kwargs.items():
            if hasattr(new_scenario, key):
                setattr(new_scenario, key, value)
            else:
                setattr(new_scenario.netlogo_params, key, value)

        new_scenario.build_simulations()
        scenarios.append(new_scenario)

    logger.info(f"Expanded scenario {scenario.name} to {len(scenarios)} scenarios.")

    return scenarios
