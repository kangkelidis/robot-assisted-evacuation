import logging
import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from typing import Dict

ASK_FOR_HELP_ROBOT_ACTION = "ask-help"  # type:str
CALL_STAFF_ROBOT_ACTION = "call-staff"  # type:str


def on_survivor_contact(sensor_data):
    # type: ( Dict[str, str]) -> str

    return CALL_STAFF_ROBOT_ACTION


def main():
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
    sensor_data = vars(arguments)  # type:Dict

    robot_action = on_survivor_contact(sensor_data)  # type:str
    print(robot_action)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    # logging.basicConfig(level=logging.INFO)

    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

    main()
