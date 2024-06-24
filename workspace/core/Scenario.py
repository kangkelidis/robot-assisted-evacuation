import importlib
import os
import pyNetLogo
import traceback
import signal
import math
import time

from pyNetLogo import NetLogoException

from utils.netlogo_commands import *
from utils.utils import setup_logger, timeout_exception_handler
from core.adaptation_strategies import AdaptationStrategy
from core.abm_video_generation import generate_video
from core.paths import *
from config import *

class Scenario():
    instance_count = {}

    def __init__(self, name, adaptation_strategy, options):
        if name not in Scenario.instance_count:
            Scenario.instance_count[name] = 1
        else:
            Scenario.instance_count[name] += 1

        self.name = name
        self.adaptation_strategy = adaptation_strategy
        self.options = options
        self.id = name + '_' + str(Scenario.instance_count[name])

        self.logger = setup_logger()
        self.netlogo_link = None
        self.results = None


    def apply_options(self):
        """ Commands to change the model"""
        if self.options['video']:
            self.netlogo_link.command(ENABLE_FRAME_GENERATION_COMMAND)
        
        if not self.adaptation_strategy.robot:
            self.netlogo_link.command(SET_ENABLE_ROBOTS_COMMAND.format("FALSE"))
            self.logger.info('remove robots. ID: {}'.format(self.id))
        

    def initialise_netlogo_link(self):
        # type: () -> None
        self.logger.debug("Initializing NetLogo")

        self.netlogo_link = pyNetLogo.NetLogoLink(netlogo_home=NETLOGO_HOME,
                                            netlogo_version=NETLOGO_VERSION,
                                            gui=False)  # type: pyNetLogo.NetLogoLink
        self.netlogo_link.load_model(NETLOGO_MODEL)


    def setup_simulation(self):
        self.initialise_netlogo_link()
        self.logger.info("id:{} starting simulation".format(self.id))
        current_seed = self.netlogo_link.report(SEED_SIMULATION_REPORTER)  # type:str
        self.netlogo_link.command("setup")
        self.netlogo_link.command(SET_SIMULATION_ID_COMMAND.format(self.id))
        self.apply_options()
        self.logger.debug('id: {} completed setup'.format(self.id))


    def get_netlogo_report(self):
        """Runs the Netlogo simulation and returns the results for the count commands."""

        signal.signal(signal.SIGALRM, timeout_exception_handler)
        TIME_LIMIT_SECONDS = 120  # type: int
        MAX_RETRIES = 2

        metrics_dataframe = None
        for i in range(MAX_RETRIES):
            try:
                self.logger.debug("Starting reporter for %s, attempt no. %i", self.id, i)
                signal.alarm(TIME_LIMIT_SECONDS)

                start_time = time.time()
                metrics_dataframe = self.netlogo_link.repeat_report(
                    netlogo_reporter=[TURTLE_PRESENT_REPORTER, EVACUATED_REPORTER, DEAD_REPORTER],
                    reps=MAX_NETLOGO_TICKS)  # type: pd.DataFrame
                endtime = time.time()

                self.logger.info("%s simulation completed on attempt n.%i. Execution time was %.2f seconds", self.id, i+1, endtime-start_time)
                signal.alarm(0)
                break
            except Exception as e:
                self.logger.error("Exception in %s attempt no.%i: %s", self.id, i+1, e)
                traceback.print_exc()
                signal.alarm(0)
        
        return metrics_dataframe


    def run(self):
        try:
            self.setup_simulation()

            metrics_dataframe = self.get_netlogo_report()

            if metrics_dataframe is None:
                self.logger.error("id:{} metrics_dataframe is None. The simulation did not return any results.".format(self.id))
                # TODO: think how to handle this case
                return
            
            evacuation_finished = metrics_dataframe[
                metrics_dataframe[TURTLE_PRESENT_REPORTER] == metrics_dataframe[DEAD_REPORTER]]
            evacuation_time = evacuation_finished.index.min()  # type: float

            # TODO: think how to handle this case
            if math.isnan(evacuation_time):
                metrics_dataframe.to_csv(DATA_FOLDER + "nan_df.csv")
                self.logger.warning("DEBUG!!! info to {}nan_df.csv".format(DATA_FOLDER))
                # simulation did not finish on time, use max time/ticks)
                evacuation_time = MAX_NETLOGO_TICKS

            if self.options['video']:
                generate_video(simulation_id=self.id)

            self.results = evacuation_time
        except NetLogoException as e:
            self.logger.error("id:{} NetLogo exception: {}".format(self.id, e))
            traceback.print_exc()
        except Exception as e:
            self.logger.error("id:{} Exception: {}".format(self.id, e))
            traceback.print_exc() 

            

def is_valid_scenario(scenario):
    """ Checks that scenatrios in config.py are in the correct format."""

    if not isinstance(scenario, dict): 
        return False
    if 'strategy_name' not in scenario or 'options' not in scenario: 
        return False
    options = scenario['options']
    if not isinstance(options, dict): 
        return False
    # TODO: does it work if False? should be ok if does not exist no?
    if 'video' not in options:
        return False
    return True


def get_simulation_scenarios():
    """ Loads the adaptation strategy from the config file."""
    assert isinstance(SIMULATION_SCENARIOS, list), "SIMULATION_SCENARIOS must be a list"

    scenarios = []
    for scenario in SIMULATION_SCENARIOS:
        if is_valid_scenario(scenario):
            scenario_name = scenario['strategy_name']
            options = scenario['options']
            strategy = get_adaptation_strategy(scenario_name)
            for _ in range(NUM_SAMPLES):
                scenarios.append(Scenario(scenario_name, strategy, options))
    
    return scenarios


def get_adaptation_strategy(strategy_name):
    for file_name in os.listdir(STRATEGIES_FOLDER):
        if file_name[:-3] == strategy_name:
            module = importlib.import_module('strategies.' + strategy_name)
            strategy_class = getattr(module, strategy_name)

            if issubclass(strategy_class, AdaptationStrategy):
                strategy_instance = strategy_class()
                return strategy_instance
   
    return None

