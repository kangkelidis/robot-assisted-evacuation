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
from typing import Any, Dict, Iterable, List

workspace_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(workspace_path)

from core.simulations.load_config import save_scenarios
from core.simulations.simulation import NetLogoParams, Scenario


def _get_scenario_name(scenario, kwargs):
    # type: (Scenario, Dict[str, Any]) -> str
    """
    Returns a name for the scenario based on the parameters.

    Args:
        scenario: The scenario to run.
        kwargs: A dictionary of parameters to iterate and their respective range of values.

    Returns:
        str: A name for the scenario based on the parameters.
    """
    name = scenario.name + "-" + ''.join(
        ["{}{}".format(key, value) for key, value in kwargs.iteritems()])
    name = name.replace("_", "-")
    return name


def batch_run(scenario, parameters, num_samples):
    # type: (Scenario, Dict[str, Any | Iterable[Any]], int) -> List[Scenario]
    """
    Run a scenario with different combinations of parameters.

    batch_run(scenario, {num_of_robots: range(1, 11)}, 5) will run the scenario 50 times.
    - 5 times with num_of_robots equal to 1, 5 times equal to 2 ...

    batch_run(scenario, {num_of_robots: range(1, 10], num_of_staff: [2, 10]}, 5)
    will run the scenario 100 times.
    - 5 times with num_of_robots equal to 1, num_of_staff equal = 2,
    - 5 times with num_of_robots equal to 1, num_of_staff equal = 10,
    - 5 times with num_of_robots equal to 2, num_of_staff equal = 2...

    Args:
        scenario: The scenario to run.
        parameters: A dictionary of parameters to iterate and their respective range of values.
                    Single, or multiple values for each parameter name.
        num_samples: The number of samples to run each combination of parameters.

    Returns:
        Scenrios: A list of scenarios with different combinations of parameters.
    """

    keys = list(parameters.keys())
    # check that every key is in the scenario
    for key in keys:
        if not (hasattr(scenario, key) or hasattr(scenario.netlogo_params, key)):
            raise ValueError("Parameter {} not in scenario".format(key))

    scenarios = []
    parameter_list = []
    for param, values in parameters.items():
        if not isinstance(values, Iterable):
            # A single value for the parameter
            all_values = [(param, values)]
        else:
            all_values = [(param, value) for value in values]

        parameter_list.append(all_values)
    all_kwargs = itertools.product(*parameter_list)
    kwargs_list = [dict(kwargs) for kwargs in all_kwargs]

    for kwargs in kwargs_list:
        print(kwargs)
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

    print("Generated {} scenarios".format(len(scenarios)))
    save_scenarios(scenarios)

    return scenarios


if __name__ == "__main__":
    sc = Scenario()
    sc.name = "test"
    sc.adaptation_strategy = "RandomStrategy"
    batch_run(sc, {"num_of_robots": range(1, 11)}, 5)
    batch_run(sc, {"num_of_robots": range(1, 11), "num_of_staff": [2, 10]}, 5)
    batch_run(sc, {"num_of_robots": range(1, 11), "num_of_staff": [2, 10], "room_type": 1}, 5)
