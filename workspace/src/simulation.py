"""
This module defines the classes and functions necessary for executing the NetLogo model simulations.

Classes:
- Updatable: A base class that provides a method to update object attributes.
- NetLogoParams: Stores the parameters required to configure and run a simulation.
- Result: Holds the results of a single simulation, including metrics such as evacuation ticks.
- Scenario: Represents a simulation scenario, encapsulating the parameters, simulations,
            and results associated with it.
- Simulation: Encapsulates the details necessary to run a single simulation within a scenario.
"""
from __future__ import annotations

import copy
import os
import random
from typing import Optional

import pandas as pd  # type: ignore
from src.adaptation_strategy import AdaptationStrategy
from utils.helper import (convert_camelCase_to_snake_case,
                          generate_simulation_id, setup_logger)
from utils.paths import DATA_FOLDER, NETLOGO_FOLDER, get_experiment_folder


class Updatable(object):
    def update(self, params: dict) -> None:
        """
        Updates the object's parameters that are in the provided dictionary.

        Args:
            params: A dictionary containing the parameters to update.
        """
        for key, value in params.items():
            attr_name = convert_camelCase_to_snake_case(key)
            if hasattr(self, attr_name):
                setattr(self, attr_name, value)


class NetLogoParams(Updatable):
    """
    Holds the NetLogo parameters for a simulation.

    Attributes:
    - seed: The seed for the simulation.
    - num_of_samples: The number of simulations to run.
    - num_of_robots: The number of robots in the simulation.
    - num_of_passengers: The number of passengers in the simulation.
    - num_of_staff: The number of staff in the simulation.
    - fall_length: The number of ticks of fall lasts in the simulation.
    - fall_chance: The chance of a fall happening in the simulation.
    - allow_staff_support: Whether staff can support passengers.
    - allow_passenger_support: Whether passengers can support each other.
    - max_netlogo_ticks: The maximum number of NetLogo ticks to run the simulation.
    - room_type: The type of room in the simulation.
    - enable_video: Whether to enable video recording of the simulation.
    """
    def __init__(self):
        self.seed = 0
        self.num_of_samples = 30
        self.num_of_robots = 1
        self.num_of_passengers = 800
        self.num_of_staff = 10
        self.fall_length = 500
        self.fall_chance = 0.05
        self.max_netlogo_ticks = 2000
        self.room_type = 8
        self.enable_video = False


class Result(Updatable):
    """
    Holds the results of a simulation.

    Attributes:
    - seed: The seed used for the simulation.
    - evacuation_ticks: The number of ticks it took to evacuate the room.
    - evacuation_time: The time it took to execute the simulation.
    - robot_actions: A list of the actions performed by the robots.
    - success: Whether the simulation was successful (finished on time and no errors).
    """
    # ? how should we handle the unsuccessful simulations?
    def __init__(self,
                 netlogo_seed: int = 0,
                 evacuation_ticks: Optional[int] = None,
                 evacuation_time: Optional[float] = None,
                 success: bool = False,
                 ) -> None:
        self.evacuation_ticks = evacuation_ticks
        self.evacuation_time = evacuation_time
        self.robot_actions: list[str] = []
        self.robot_responses: list[str] = []
        self.success = success
        self.netlogo_seed = netlogo_seed

    def __str__(self):
        return (f"Evacuation ticks: {self.evacuation_ticks}, "
                f"Evacuation time: {self.evacuation_time:.2f}, "
                f"Seed: {self.netlogo_seed}")


class Scenario(Updatable):
    """
    Represents a simulation scenario. Contains the parameters and results for the scenario
    and a list of its simulation objects.

    Attributes:
    - name: The name of the scenario.
    - description: A description of the scenario.
    - netlogo_params: The NetLogo parameters for the scenario.
    - adaptation_strategy: The name of the adaptation strategy to use in the scenario.
    - enabled: Whether to run the scenario's simulations.
    - simulations: A list of Simulation objects for the scenario.
    - results: A list of Result objects for the scenario.
    - results_df: A DataFrame containing the results of the scenario.
    - logger: A logger object for logging messages.
    """
    def __init__(self) -> None:
        self.name = ''
        self.description = ''
        self.netlogo_params = NetLogoParams()
        self.adaptation_strategy: Optional[AdaptationStrategy] = None
        self.enabled = True
        self.simulations: list[Simulation] = []
        self.results: list[Result] = []
        self.logger = setup_logger()

    def update(self, params: dict) -> None:
        super().update(params)
        self.netlogo_params.update(params)
        self.adaptation_strategy = AdaptationStrategy.get_strategy(
            params.get('adaptation_strategy'))

    def duplicate(self) -> 'Scenario':
        new_scenario = Scenario()
        new_scenario.description = self.description
        new_scenario.adaptation_strategy = self.adaptation_strategy
        new_scenario.enabled = self.enabled
        new_scenario.simulations = self.simulations[:]
        new_scenario.results = self.results[:]
        new_scenario.netlogo_params.update(self.netlogo_params.__dict__)
        return new_scenario

    def build_simulations(self) -> None:
        """
        Builds the simulation objects for this scenario and saves them in a list.
        """
        for simulation_index in range(self.netlogo_params.num_of_samples):
            simulation = Simulation(self.name, simulation_index, self.netlogo_params)
            self.simulations.append(simulation)
        self.logger.debug(f"Finished building simulations for scenario: {self.name}. "
                          f"Size of list: {len(self.simulations)}")

    def get_data(self) -> pd.DataFrame:
        params = self.netlogo_params.__dict__
        info = {'scenario': self.name, 'strategy': self.adaptation_strategy}

        scenario_data = []
        for simulation in self.simulations:
            result = simulation.result.__dict__

            scenario_data.append({"simulation_id": simulation.id, **info, **params, **result})

        return pd.DataFrame(scenario_data)


class Simulation(Updatable):
    """
    A simulation object with the necessary parameters to run a simulation in NetLogo.
    Also contains the results object created by the simulation.
    """
    def __init__(self, scenario_name: str, index: int, netlogo_params: NetLogoParams) -> None:
        self.scenario_name = scenario_name
        self.id = generate_simulation_id(scenario_name, index)
        self.netlogo_params = netlogo_params
        self.result: Result = Result()
        self.seed = self.generate_seed(index)
        self.netlogo_seed = None

    def generate_seed(self, index) -> None:
        """
        Generates a seed for the simulation based on the netlogo_params seed and index.

        Each simulation round will have the same seed, unless the netlogo_params seed is 0.
        Simulations in batch runs will behave the way.
        The seed number must be an integer in the range -2147483648 to 2147483647.

        Args:
            index: The index of the simulation.

        Returns:
            seed: An integer seed for the simulation.
        """
        #  use the netlogo random-seed if 0
        if self.netlogo_params.seed != 0:
            # Generate a seed based on the netlogo_params seed and the index
            random.seed(self.netlogo_params.seed * (index + 1))
            while True:
                seed: int = random.randint(-2147483647, 2147483646)
                if seed != 0:
                    break
            return seed
        return 0

    def add_action(self, action: str) -> None:
        self.result.robot_actions.append(action)

    def add_response(self, response: str) -> None:
        self.result.robot_responses.append(response)
