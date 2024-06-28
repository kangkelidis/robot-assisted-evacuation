
import os
from typing import Dict, List

import pandas as pd  # type: ignore
from core.utils.helper import (convert_camelCase_to_snake_case,
                               generate_simulation_id, setup_logger)
from core.utils.paths import (DATA_FOLDER, NETLOGO_FOLDER,
                              ROBOTS_ACTIONS_FILE_NAME, get_experiment_folder)


class Updateable(object):
    def update(self, params):
        # type: (Dict) -> None
        """ Updates the object's parameters that are in the provided dictionary."""
        for key, value in params.items():
            attr_name = convert_camelCase_to_snake_case(key)
            if hasattr(self, attr_name):
                setattr(self, attr_name, value)


class NetLogoParams(Updateable):
    """ Holds the NetLogo parameters for a simulation."""
    def __init__(self):
        self.num_of_samples = 30
        self.num_of_robots = 1
        self.num_of_passengers = 800
        self.num_of_staff = 10
        self.fall_length = 500
        self.fall_chance = 0.05
        self.allow_staff_support = True
        self.allow_passenger_support = True
        self.max_netlogo_ticks = 2000
        self.room_type = 8
        self.enable_video = False


class Result(object):
    """ Holds the results of a simulation."""
    # ? how should we handle the unsuccessful simulations?
    def __init__(self, simulation_id=None, evacuation_ticks=None,
                 evacuation_time=None, success=None):
        self.simulation_id = simulation_id
        self.evacuation_ticks = evacuation_ticks
        self.evacuation_time = evacuation_time
        self.robot_actions = []
        self.success = success

    def __str__(self):
        return "Evacuation ticks: {}, Evacuation time: {:.2f}".format(
            self.evacuation_ticks, self.evacuation_time)


class Scenario(Updateable):
    """
    Represents a simulation scenario. Contains the parameters and results for the scenario
    and a list of its simulation objects.
    """
    def __init__(self):
        # type: () -> None
        self.name = ''
        self.description = ''
        self.netlogo_params = NetLogoParams()
        self.adaptation_strategy = None
        self.enabled = True
        self.simulations = []  # type: List[Simulation]
        self.results = []  # type: List[Result]
        self.results_df = None  # type: pd.DataFrame
        self.logger = setup_logger()

    def update(self, params):
        # type: (Dict) -> None
        """ Updates the scenario's parameters and its Netlogo parameters."""
        super(Scenario, self).update(params)
        self.netlogo_params.update(params)

    def build_simulations(self):
        # type: (str) -> None
        """ Builds the simulation objects for this scenario and saves them in a list."""
        for simulation_index in range(self.netlogo_params.num_of_samples):
            simulation = Simulation(
                self.name, simulation_index, self.netlogo_params)
            self.simulations.append(simulation)

    def gather_results(self):
        # type: () -> None
        """ Gathers the results of the simulations in this scenario."""
        for simulation in self.simulations:
            simulation.get_robots_actions()
            self.results.append(simulation.result)

    def save_results(self):
        # type: () -> None
        """ Creates a dataframe with the results and saves it as a csv. """
        results_dicts = [result.__dict__ for result in self.results]
        df = pd.DataFrame(results_dicts)
        df = self.expand_robots_actions(df)
        columns_order = ['simulation_id', 'success', 'evacuation_ticks', 'evacuation_time',
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
            self.logger.error("Error creating folder: {}".format(e))

        try:
            results_file_name = self.name + "_results.csv"
            results_file_path = os.path.join(scenarios_folder_path, results_file_name)
            df.to_csv(results_file_path)
        except Exception as e:
            self.logger.error("Error saving results file: {}".format(e))

        # save params
        try:
            params_file_name = self.name + "_params.txt"
            params_file_path = os.path.join(scenarios_folder_path, params_file_name)
            with open(params_file_path, 'w') as f:
                f.write("description: {}\n".format(self.description))
                f.write("adaptation_strategy: {}\n".format(self.adaptation_strategy))
                for key, value in self.netlogo_params.__dict__.items():
                    f.write("{}: {}\n".format(key, value))
        except Exception as e:
            self.logger.error("Error saving params file: {}".format(e))

    def expand_robots_actions(self, df):
        # type: (pd.DataFrame) -> None
        """
        Turns the column containing the list of robot actions into 3 columns,
        containing the count for each action (ask-help and call-staff) and their total.
        """
        df['robot_ask_help'] = df['robot_actions'].apply(lambda x: x.count('ask-help'))
        df['robot_call_staff'] = df['robot_actions'].apply(lambda x: x.count('call-staff'))
        df['total_actions'] = df['robot_ask_help'] + df['robot_call_staff']
        df.drop('robot_actions', axis=1, inplace=True)
        return df


class Simulation(object):
    """
    A simulation object with the neccesary parameters to run a simulation in NetLogo.
    Also contains the results object created by the simulation.
    """
    def __init__(self, scenario_name, index, netlogo_params):
        # type: (str, int, NetLogoParams) -> None
        self.scenario_name = scenario_name
        self.id = generate_simulation_id(scenario_name, index)
        self.netlogo_params = netlogo_params  # type: NetLogoParams
        self.result = Result()

    def get_robots_actions(self):
        # type: () -> None
        """ Collects the robots actions from the temp file """
        robots_actions_file_path = NETLOGO_FOLDER + ROBOTS_ACTIONS_FILE_NAME
        if not os.path.exists(robots_actions_file_path):
            return
        df = pd.read_csv(robots_actions_file_path)
        actions_df = df[df['id'] == self.id]
        self.result.robot_actions.extend(actions_df['Action'].tolist())
