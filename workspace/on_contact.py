import importlib
import json
import logging
import os
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

# from typing import Dict # <-  TODO: crashed the program, perhaps becouse it is called from netlogo?
from adptation_strategies import AdaptationStrategy, adaptation_strategies
from paths import WORKSPACE_FOLDER
from survivor import Survivor
from utils import load_adaptation_strategy, setup_logger

logger = setup_logger()

def get_adaptation_strategy(strategy_name):
    for file_name in os.listdir(WORKSPACE_FOLDER + "strategies/"):
        logger.info('strategy file name: {}'.format(file_name))
        if file_name[:-3] == strategy_name:
            module = importlib.import_module('strategies.' + strategy_name)
            strategy_class = getattr(module, strategy_name)

            if issubclass(strategy_class, AdaptationStrategy):
                strategy_instance = strategy_class()
                return strategy_instance
            
def load_scenarios_from_temp(filename="scenarios_temp.json"):
    """Loads the scenarios from the specified JSON file."""
    logger.info('loading')
    with open(filename, 'r') as file:
        scenarios = json.load(file)
    return scenarios

def on_survivor_contact(candidate_helper, victim, helper_victim_distance, first_responder_victim_distance, simulation_id):
    # type: ( Survivor, Survivor, float, float, str) -> str

    """ Only gets called during adaptive-support scenario. Called by Netlogo model and returns the robot's action.
    Either asks for help from a survivor or calls staff. If the former, the survivor's decision whether to help on not 
    is determined by offer-help? in the IMPACT model. If he helps, the victim gets a speed bonus. 
    The optimal output would be the prediction of the offer-help? output.
    If an adaptation strategy is defined in config.py, it will be used. Otherwise, the strategy is determined by the simulation_id."""
    
    scenario_name = simulation_id.split("_")[0]  # type: str
    logger.info('Simulation id : {}'.format(simulation_id))
    with open("output.txt", "a") as file:
        file.write("Scenario name: {}\n".format(scenario_name))
        file.write("simulation_id: {}\n".format(simulation_id))

    scenario = None
    # load scenarios from temporary files
    
    scnarios = load_scenarios_from_temp()

    for scenario in scnarios:
        logger.info('scenario name: {}'.format(scenario['name']))
        if scenario['name'] == scenario_name:
            scenario = scenario
            break
    if scenario:
        strategy_name = scenario['adaptation_strategy']
        with open("output.txt", "a") as file:
            file.write("strategy name: {}\n".format(strategy_name))
        strategy = get_adaptation_strategy(strategy_name)


        if strategy:
            # create a text file in the current working directory
            with open("output.txt", "a") as file:
                file.write("Hello, world!")

            action = strategy.get_robot_action(candidate_helper, victim, helper_victim_distance,
                                                          first_responder_victim_distance)
            logger.info("Selected action: {}".format(action))
            return action

def main():
    try:
        parser = ArgumentParser("Get a robot action from the adaptive controller",
                                formatter_class=ArgumentDefaultsHelpFormatter)  # type: ArgumentParser
        parser.add_argument("simulation_id")
        parser.add_argument("helper_gender")
        parser.add_argument("helper_culture")
        parser.add_argument("helper_age")
        parser.add_argument("fallen_gender")
        parser.add_argument("fallen_culture")
        parser.add_argument("fallen_age")
        parser.add_argument("helper_fallen_distance")
        parser.add_argument("staff_fallen_distance")
        arguments = parser.parse_args()
        sensor_data = vars(arguments)  # type:Dict[str, str]
         
        candidate_helper = Survivor(sensor_data["helper_gender"], sensor_data["helper_culture"], sensor_data["helper_age"])
        victim = Survivor(sensor_data["fallen_gender"], sensor_data["fallen_culture"], sensor_data["fallen_age"])
        helper_victim_distance = float(sensor_data["helper_fallen_distance"])  # type: float
        first_responder_victim_distance = float(sensor_data["staff_fallen_distance"])  # type: float
        simulation_id = sensor_data["simulation_id"]  # type: str

        robot_action = on_survivor_contact(candidate_helper, victim, helper_victim_distance,
                                        first_responder_victim_distance,simulation_id)  # type:str
        # To return to netlogo
        print(robot_action) 

    except Exception as e:
        # This runs in a shell from netlogo, not sure if logging works here
        logging.error("Error in on_survivor_contact: %s", e)


if __name__ == "__main__":
    logger.info('on cantact called')
    with open("output.txt", "w") as file:
        file.write("on contact\n")
    main()
