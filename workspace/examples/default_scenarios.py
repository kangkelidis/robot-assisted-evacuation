"""
This module creates the default Scenarios for the simulation.
"""

from typing import List

from core.simulations.load_config import save_scenarios
from core.simulations.simulation import Scenario

scenarioParams = {
    'num_of_samples': 30,
    'num_of_robots': 1,
    'num_of_passengers': 800,
    'num_of_staff': 10,
    'fall_length': 500,
    'fall_chance': 0.05,
    'allow_staff_support': True,
    'allow_passenger_support': True,
    'max_netlogo_ticks': 2000,
    'room_type': 8,
    'enable_video': False
}

simulationParams = [
    {
        "name": "no-support",
        "description": "There are no SAR robots in the simulation.",
        "numOfRobots": 0,
        "allowStaffSupport": False,
        "allowPassengerSupport": False,
        "adaptationStrategy": None,
        "enabled": True
    },
    {
        "name": "staff-support",
        "description": "The SAR always asks help from a staff member.",
        "allowPassengerSupport": False,
        "adaptationStrategy": None,
        "enabled": True
    },
    {
        "name": "passenger-support",
        "description": "The SAR always asks help from a passenger.",
        "allowStaffSupport": False,
        "adaptationStrategy": None,
        "enabled": True
    },
    {
        "name": "adaptive-support",
        "description": "The SAR will use its adaptation strategy to " +
                       "decide whether to ask help from a passenger or a staff member.",
        "adaptationStrategy": "RandomStrategy",
        "enableVideo": True,
        "enabled": True
    }
]


def get_default_experiment_scenarios() -> List[Scenario]:
    """
    Returns the list of default scenarios.

    Returns:
        scenarios: A list of scenarios.
    """
    scenarios = []

    for simulationParam in simulationParams:
        scenario = Scenario()
        scenario.update(scenarioParams)
        scenario.update(simulationParam)
        scenario.build_simulations()
        scenarios.append(scenario)

    save_scenarios(scenarios)
    return scenarios
