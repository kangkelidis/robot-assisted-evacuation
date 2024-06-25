import json
import tempfile

from netlogo_commands import *
from paths import CONFIG_FILE
from utils import convert_camel_case_to_snake_case

with open(CONFIG_FILE, 'r') as config_file:
    config = json.load(config_file)

NETLOGO_MODEL = config['netlogoModelPath']

class SimulationParameters(object):
    def __init__(self):
        self.name = ''
        self.description = ''
        self.id = ''
        self.num_of_samples = 30
        self.num_of_robots = 1
        self.num_of_passengers = 800
        self.num_of_staff = 10
        self.fall_length = 500
        self.fall_chance = 0.05
        self.allow_staff_support = False
        self.allow_passenger_support = False
        self.adaptation_strategy = None
        self.max_netlogo_ticks = 2000
        self.enable_video = False
        self.enabled = True


    def update(self, scenarioParams):
        for key, value in scenarioParams.items():
            attr_name = convert_camel_case_to_snake_case(key)
            if hasattr(self, attr_name):
                setattr(self, attr_name, value)

    
    def execute_commands(self, netlogo_link):
        netlogo_link.command(SET_SIMULATION_ID_COMMAND.format(self.id))
        netlogo_link.command(SET_NUM_OF_ROBOTS_COMMAND.format(self.num_of_robots))
        netlogo_link.command(SET_NUM_OF_PASSENGERS_COMMAND.format(self.num_of_passengers))
        netlogo_link.command(SET_NUM_OF_STAFF_COMMAND.format(self.num_of_staff))
        netlogo_link.command(SET_FALL_LENGTH_COMMAND.format(self.fall_length))
        netlogo_link.command(SET_FALL_CHANCE_COMMAND.format(self.fall_chance))
        netlogo_link.command(SET_STAFF_SUPPORT_COMMAND.format("TRUE" if self.allow_staff_support else "FALSE"))
        netlogo_link.command(SET_PASSENGER_SUPPORT_COMMAND.format("TRUE" if self.allow_passenger_support else "FALSE"))
        netlogo_link.command(SET_FRAME_GENERATION_COMMAND.format("TRUE" if self.enable_video else "FALSE"))
    
    def __str__(self):
        return str(self.__dict__)
    


# TODO: add only active ones
def load_scenarios():
    scenarios = []

    for scenario in config['simulationScenarios']:
        scenario_params = SimulationParameters()
        scenario_params.update(config['simulationParameters'])
        scenario_params.update(scenario)

        scenarios.append(scenario_params)

    save_senarios(scenarios)

    return scenarios


# store the scenarios in a temp json
def save_senarios(scenarios):
    temp_file_path = "netlogo/scenarios_temp.json"
    with open(temp_file_path, 'w') as temp_file:
        scenarios_dict = [scenario.__dict__ for scenario in scenarios]
        json.dump(scenarios_dict, temp_file)


def load_scenarios_from_temp(filename="scenarios_temp.json"):
    """Loads the scenarios from the specified JSON file."""
    with open(filename, 'r') as file:
        scenarios = json.load(file)
    return scenarios