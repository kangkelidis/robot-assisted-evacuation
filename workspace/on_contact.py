import logging
import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from typing import Dict

ASK_FOR_HELP_ROBOT_ACTION = "ask-help"  # type:str
CALL_STAFF_ROBOT_ACTION = "call-staff"  # type:str


class Gender:
    FEMALE, MALE = range(2)


class CulturalCluster:
    ARAB, NEAR_EAST, LATIN_AMERICA, EAST_EUROPE, LATIN_EUROPE, NORDIC, GERMANIC, AFRICAN, ANGLO, CONFUCIAN, FAR_EAST = range(
        11)


class Age:
    CHILD, ADULT, ELDERLY = range(3)


class Survivor:
    def __init__(self, gender, cultural_cluster, age):
        # type: (str, str, str) -> None

        self.gender = int(gender)  # type: int
        self.cultural_cluster = int(cultural_cluster)  # type: int
        self.age = int(age)  # type: int


def on_survivor_contact(candidate_helper, victim, helper_victim_distance, first_responder_victim_distance):
    # type: ( Survivor, Survivor, float, float) -> str

    robot_action = CALL_STAFF_ROBOT_ACTION

    if helper_victim_distance < first_responder_victim_distance and \
            candidate_helper.gender == Gender.MALE and candidate_helper.age == Age.ADULT:
        robot_action = ASK_FOR_HELP_ROBOT_ACTION

    return robot_action


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
    sensor_data = vars(arguments)  # type:Dict[str, str]

    candidate_helper = Survivor(sensor_data["helper_gender"], sensor_data["helper_culture"], sensor_data["helper_age"])
    victim = Survivor(sensor_data["fallen_gender"], sensor_data["fallen_culture"], sensor_data["fallen_age"])
    helper_victim_distance = float(sensor_data["helper_fallen_distance"])  # type: float
    first_responder_victim_distance = float(sensor_data["staff_fallen_distance"])  # type: float

    robot_action = on_survivor_contact(candidate_helper, victim, helper_victim_distance,
                                       first_responder_victim_distance)  # type:str
    print(robot_action)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    # logging.basicConfig(level=logging.INFO)

    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

    main()
