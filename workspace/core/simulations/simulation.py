"""
This module defines the classes and functions necessary for executing the Netlogo model simulations.

Classes:
- Updateable: A base class that provides a method to update object attributes.
- NetLogoParams: Stores the parameters required to configure and run a simulation.
- Result: Holds the results of a single simulation, including metrics such as evacuation ticks.
- Scenario: Represents a simulation scenario, encapsulating the parameters, simulations,
            and results associated with it.
- Simulation: Encapsulates the details necessary to run a single simulation within a scenario.
"""

import os

import pandas as pd  # type: ignore
from core.utils.helper import (convert_camelCase_to_snake_case,
                               generate_simulation_id, setup_logger)
from core.utils.paths import (DATA_FOLDER, NETLOGO_FOLDER,
                              ROBOTS_ACTIONS_FILE_NAME, get_experiment_folder)


class Updateable(object):
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


class NetLogoParams(Updateable):
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


class Result(Updateable):
    """
    Holds the results of a simulation.

    Attributes:
    - seed: The seed used for the simulation.
    - simulation_id: Combines the scenario name and the simulation number.
    - evacuation_ticks: The number of ticks it took to evacuate the room.
    - evacuation_time: The time it took to execute the simulation.
    - robot_actions: A list of the actions performed by the robots.
    - success: Whether the simulation was successful (finished on time and no errors).
    """
    # ? how should we handle the unsuccessful simulations?
    def __init__(self, seed: int = 0, simulation_id: str = '', evacuation_ticks: int | None = None,
                 evacuation_time: float | None = None, success: bool = False, robot_actions: list[str] = []) -> None:
        self.simulation_id = simulation_id
        self.evacuation_ticks = evacuation_ticks
        self.evacuation_time = evacuation_time
        self.robot_actions: list[str] = robot_actions
        self.success = success
        self.seed = seed

    def __str__(self):
        return (f"Evacuation ticks: {self.evacuation_ticks}, "
                f"Evacuation time: {self.evacuation_time:.2f}, "
                f"Seed: {self.seed}")


class Scenario(Updateable):
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
        self.adaptation_strategy = None
        self.enabled = True
        self.simulations: list[Simulation] = []
        self.results: list[Result] = []
        self.results_df: pd.DataFrame | None = None
        self.logger = setup_logger()

    def update(self, params: dict) -> None:
        super().update(params)
        self.netlogo_params.update(params)

    # TODO: refactor this method
    def copy(self) -> 'Scenario':
        new_scenario = Scenario()
        new_scenario.name = self.name
        new_scenario.description = self.description
        new_scenario.adaptation_strategy = self.adaptation_strategy
        new_scenario.enabled = self.enabled
        new_scenario.simulations = self.simulations[:]
        new_scenario.results = self.results[:]
        new_scenario.results_df = self.results_df
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

    def gather_results(self) -> None:
        """
        Gathers the results of the simulations in this scenario.
        Also collects the robots actions from the temp file.
        """
        for simulation in self.simulations:
            # TODO: delete this line
            simulation.get_robots_actions()
            self.results.append(simulation.result)

    def save_results(self) -> None:
        """
        Creates a dataframe with the results and saves it as a csv.
        """
        results_dicts = [result.__dict__ for result in self.results]
        df = pd.DataFrame(results_dicts)
        df = self.expand_robots_actions(df)
        columns_order = ['simulation_id', 'seed', 'success', 'evacuation_ticks', 'evacuation_time',
                         'robot_ask_help', 'robot_call_staff', 'total_actions']
        self.results_df = df[columns_order]

        try:
            experiment_folder_name = get_experiment_folder()
            experiment_folder_path = os.path.join(DATA_FOLDER, experiment_folder_name)
            if not os.path.exists(experiment_folder_path):
                os.makedirs(experiment_folder_path)

            scenarios_folder_path = os.path.join(experiment_folder_path, 'scenarios')
            if not os.path.exists(scenarios_folder_path):
                os.makedirs(scenarios_folder_path)
        except Exception as e:
            self.logger.error(f"Error creating folder: {e}")

        try:
            results_file_name = self.name + "_results.csv"
            results_file_path = os.path.join(scenarios_folder_path, results_file_name)
            self.results_df.to_csv(results_file_path)
        except Exception as e:
            self.logger.error(f"Error saving results file: {e}")

        # save params
        try:
            params_file_name = self.name + "_params.txt"
            params_file_path = os.path.join(scenarios_folder_path, params_file_name)
            with open(params_file_path, 'w') as f:
                f.write(f"description: {self.description}\n")
                f.write(f"adaptation_strategy: {self.adaptation_strategy}\n")
                for key, value in self.netlogo_params.__dict__.items():
                    f.write(f"{key}: {value}\n")
        except Exception as e:
            self.logger.error(f"Error saving params file: {e}")

    def expand_robots_actions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Turns the column containing the list of robot actions into 3 columns,
        containing the count for each action (ask-help and call-staff) and their total.

        Args:
            df: A DataFrame containing the results of the scenario.

        Returns:
            df: A DataFrame with the expanded columns.
        """
        df['robot_ask_help'] = df['robot_actions'].apply(lambda x: x.count('ask-help'))
        df['robot_call_staff'] = df['robot_actions'].apply(lambda x: x.count('call-staff'))
        df['total_actions'] = df['robot_ask_help'] + df['robot_call_staff']
        df.drop('robot_actions', axis=1, inplace=True)

        return df


class Simulation(Updateable):
    """
    A simulation object with the neccesary parameters to run a simulation in NetLogo.
    Also contains the results object created by the simulation.
    """
    def __init__(self, scenario_name: str, index: int, netlogo_params: NetLogoParams) -> None:
        self.scenario_name = scenario_name
        self.id = generate_simulation_id(scenario_name, index)
        self.netlogo_params = netlogo_params
        self.result = Result()
        self.seed = self.generate_seed(index)
        self.netlogo_seed = None
        # TODO: add them to the Resul
        self.actions = []
        self.responses = []

    # TODO: delete this method
    def get_robots_actions(self) -> None:
        """
        Collects the robots actions from the temp file and appends them to the robot_actions list.
        """
        robots_actions_file_path = NETLOGO_FOLDER + ROBOTS_ACTIONS_FILE_NAME
        if not os.path.exists(robots_actions_file_path):
            return
        df = pd.read_csv(robots_actions_file_path)
        actions_df = df[df['id'] == self.id]
        self.result.robot_actions.extend(actions_df['Action'].tolist())

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
            seed: int = (self.netlogo_params.seed * (index + 1)) % 2147483647
            return seed
        return 0
