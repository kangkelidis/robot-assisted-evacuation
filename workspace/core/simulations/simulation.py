import math
import signal
import time
import traceback
from typing import Dict

import pandas as pd  # type: ignore
import pyNetLogo
from core.utils.helper import (convert_camelCase_to_snake_case,
                               generate_simulation_id, setup_logger,
                               timeout_exception_handler)
from core.utils.paths import *
from core.utils.video_generation import generate_video
from netlogo_commands import *
from pyNetLogo import NetLogoException

# TODO: results object, think about the structure of the results and how to save and anylyse them


class Updateable(object):
    def update(self, params):
        # type: (Dict) -> None
        """ Updates the object's parameters that are in the provided dictionary."""
        for key, value in params.items():
            attr_name = convert_camelCase_to_snake_case(key)
            if hasattr(self, attr_name):
                setattr(self, attr_name, value)


class NetLogoParams(Updateable):
    # type: () -> None
    """ Holds the NetLogo parameters for a simulation."""
    def __init__(self):
        self.num_of_samples = 30
        self.num_of_robots = 1
        self.num_of_passengers = 800
        self.num_of_staff = 10
        self.fall_length = 500
        self.fall_chance = 0.05
        self.allow_staff_support = False
        self.allow_passenger_support = False
        self.max_netlogo_ticks = 2000
        self.enable_video = False


class Scenario(Updateable):
    # type: () -> None
    """
    Represents a simulation scenario. Contains the parameters for the simulations
    and a list of the simulations objects.
    """
    def __init__(self):
        # type: () -> None
        self.name = ''
        self.description = ''
        self.netlogo_params = NetLogoParams()
        self.adaptation_strategy = None
        self.enabled = True
        self.simulations = []

    def update(self, params):
        # type: (Dict) -> None
        """ Updates the scenario's parameters and its Netlogo parameters."""
        super(Scenario, self).update(params)
        self.netlogo_params.update(params)

    def build_simulations(self, netlogo_model_path):
        # type: (str) -> None
        """ Builds the simulation objects for this scenario and saves them in a list."""
        for simulation_index in range(self.netlogo_params.num_of_samples):
            simulation = Simulation(
                self.name, simulation_index, netlogo_model_path, self.netlogo_params)
            self.simulations.append(simulation)


class Simulation(object):
    # type: (str, int, str, NetLogoParams) -> None
    """
    A simulation object that runs a single simulation in NetLogo.
    Contains the logic to setup and run the simulation. Also contains the results of the simulation.
    """
    def __init__(self, scenario_name, index, netlogo_model_path, netlogo_params):
        self.scenario_name = scenario_name
        self.id = generate_simulation_id(scenario_name, index)
        self.logger = setup_logger()
        self.netlogo_model_path = netlogo_model_path
        self.netlogo_link = None
        self.netlogo_params = netlogo_params  # type: NetLogoParams
        self.results = None

    def initialise_netlogo_link(self):
        # type: (str) -> pyNetLogo.NetLogoLink
        """ Initialises the NetLogo link and loads the model."""
        netlogo_link = pyNetLogo.NetLogoLink(netlogo_home=NETLOGO_HOME,
                                             netlogo_version=NETLOGO_VERSION, gui=False)
        netlogo_link.load_model(self.netlogo_model_path)
        self.netlogo_link = netlogo_link

    def execute_comands(self):
        # type: () -> None
        """ Executes commands to setup the parameters in NetLogo."""
        commands = {
            SET_SIMULATION_ID_COMMAND: self.id,
            SET_NUM_OF_ROBOTS_COMMAND: self.netlogo_params.num_of_robots,
            SET_NUM_OF_PASSENGERS_COMMAND: self.netlogo_params.num_of_passengers,
            SET_NUM_OF_STAFF_COMMAND: self.netlogo_params.num_of_staff,
            SET_FALL_LENGTH_COMMAND: self.netlogo_params.fall_length,
            SET_FALL_CHANCE_COMMAND: self.netlogo_params.fall_chance,
            SET_STAFF_SUPPORT_COMMAND: "TRUE" if self.netlogo_params.allow_staff_support
            else "FALSE",
            SET_PASSENGER_SUPPORT_COMMAND: "TRUE" if self.netlogo_params.allow_passenger_support
            else "FALSE",
            SET_FRAME_GENERATION_COMMAND: "TRUE" if self.netlogo_params.enable_video else "FALSE"
        }
        try:
            for command, value in commands.items():
                self.netlogo_link.command(command.format(value))
                self.logger.debug("Executed %s", command.format(value))

        except Exception as e:
            self.logger.error("Commands failed for id: {}. Exception: {}".format(self.id, e))
            traceback.print_exc()
        self.logger.debug("Commands executed for id: {}".format(self.id))

    def setup_simulation(self):
        # type: () -> None
        """
        Sets up the simulation in NetLogo.
        Clears the environment, executes the commands and sets up the simulation.
        """
        self.logger.debug(
            'Setting up simulation for id: {}. netlogo_link: {}'.format(self.id, self.netlogo_link))
        self.netlogo_link.command('clear')
        self.logger.debug('Cleared environment for id: {}'.format(self.id))
        self.execute_comands()
        self.netlogo_link.command('setup')
        self.logger.info("Setup completed for id: {}".format(self.id))

    # TODO: retry if max_netlogo_ticks is reached, see what the metrics df looks like
    def get_netlogo_report(self):
        # type: () -> pd.DataFrame
        """
        Runs the simulation and returns the results.
        If the simulation is unsucessful, it tries again.
        """
        signal.signal(signal.SIGALRM, timeout_exception_handler)
        TIME_LIMIT_SECONDS = 120
        MAX_RETRIES = 2

        metrics_dataframe = None
        for i in range(MAX_RETRIES):
            try:
                signal.alarm(TIME_LIMIT_SECONDS)
                start_time = time.time()
                self.logger.info("Starting reporter for %s, attempt no. %i", self.id, i + 1)
                metrics_dataframe = self.netlogo_link.repeat_report(
                    netlogo_reporter=[TURTLE_PRESENT_REPORTER, EVACUATED_REPORTER, DEAD_REPORTER],
                    reps=self.netlogo_params.max_netlogo_ticks)  # type: pd.DataFrame
                self.netlogo_link.kill_workspace()
                endtime = time.time()
                self.logger.info(
                    "%s simulation completed on attempt n.%i. Execution time was %.2f seconds",
                    self.id, i + 1, endtime - start_time)
                signal.alarm(0)
                if metrics_dataframe is not None:
                    break
            except Exception as e:
                self.logger.error("Exception in %s attempt no.%i: %s", self.id, i + 1, e)
                signal.alarm(0)
        return metrics_dataframe

    def run(self):
        # type: () -> None
        """ Runs the simulation."""
        try:
            self.logger.debug("Initialising NetLogo link for simulation %s. model path: %s",
                              self.id, self.netlogo_model_path)
            self.initialise_netlogo_link()
            self.setup_simulation()
            metrics_dataframe = self.get_netlogo_report()

            if metrics_dataframe is None:
                self.logger.error("Simulation %s failed. Did not return any results", self.id)

            evacuation_finished = metrics_dataframe[
                metrics_dataframe[TURTLE_PRESENT_REPORTER] == metrics_dataframe[DEAD_REPORTER]]
            evacuation_time = evacuation_finished.index.min()  # type: float

            # TODO: think how to handle this case
            if math.isnan(evacuation_time):
                metrics_dataframe.to_csv(DATA_FOLDER + "nan_df.csv")
                self.logger.warning("DEBUG!!! info to {}nan_df.csv".format(DATA_FOLDER))
                # simulation did not finish on time, use max time/ticks)
                evacuation_time = self.netlogo_params.max_netlogo_ticks

            if self.netlogo_params.enable_video:
                generate_video(simulation_id=self.id)

        except NetLogoException as e:
            self.logger.error("id:{} NetLogo exception: {}".format(self.id, e))
            traceback.print_exc()
        except Exception as e:
            self.logger.error("id:{} Exception: {}".format(self.id, e))
            traceback.print_exc()
