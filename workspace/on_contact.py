import logging
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

sys.path.append("/home/workspace/")
from core.Scenario import get_adaptation_strategy
from core.Survivor import Survivor
from utils.utils import setup_logger

logger = setup_logger()

def on_survivor_contact(
    candidate_helper: Survivor,
    victim: Survivor,
    helper_victim_distance: float,
    first_responder_victim_distance: float,
    simulation_id: str
) -> str:

    """ Only gets called during adaptive-support scenario. Called by Netlogo model and returns the robot's action.
    Either asks for help from a survivor or calls staff. If the former, the survivor's decision whether to help on not 
    is determined by offer-help? in the IMPACT model. If he helps, the victim gets a speed bonus. 
    The optimal output would be the prediction of the offer-help? output.
    If an adaptation strategy is defined in config.py, it will be used. Otherwise, the strategy is determined by the simulation_id."""

    adaptation_strategy = get_adaptation_strategy(simulation_id.split("_")[0])

    return adaptation_strategy.get_robot_action(candidate_helper, victim, helper_victim_distance,
                                                          first_responder_victim_distance)

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
    main()
