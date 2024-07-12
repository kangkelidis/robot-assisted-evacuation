"""
This module contains the base class for adaptation strategies.
"""


from enum import Enum, auto


class Gender(Enum):
    """
    Enum for Survivor gender.
    """
    FEMALE = 0
    MALE = 1


class CulturalCluster(Enum):
    """
    Enum for cultural cluster.
    """
    ARAB = 0
    NEAR_EAST = 1
    LATIN_AMERICA = 2
    EAST_EUROPE = 3
    LATIN_EUROPE = 4
    NORDIC = 5
    GERMANIC = 6
    AFRICAN = 7
    ANGLO = 8
    CONFUCIAN = 9
    FAR_EAST = 10


class Age(Enum):
    """
    Enum for age.
    """
    CHILD = 0
    ADULT = 1
    ELDERLY = 2


class Survivor:
    """
    Class representing a survivor.

    Attributes:
        gender: The gender of the survivor.
        cultural_cluster: The cultural cluster of the survivor.
        age: The age of the survivor.
    """
    def __init__(self, gender: int, cultural_cluster: int, age: int) -> None:
        self.gender = int(gender)
        self.cultural_cluster = int(cultural_cluster)
        self.age = int(age)


# TODO: Turn to Singleton, so the server will always use the same object,
#       unless we want a new class for each scenario
class AdaptationStrategy(object):
    """
    Base class for adaptation strategies.

    The get_robot_action method should be overridden and implemented by the subclasses.

    Attributes:
        ASK_FOR_HELP_ROBOT_ACTION: The robot action to ask for help.
        CALL_STAFF_ROBOT_ACTION: The robot action to call staff.
    """

    ASK_FOR_HELP_ROBOT_ACTION = "ask-help"
    CALL_STAFF_ROBOT_ACTION = "call-staff"

    def get_robot_action(self, candidate_helper: Survivor, victim: Survivor,
                         helper_victim_distance: float,
                         first_responder_victim_distance: float) -> str:
        """
        Gets the robot action based on the candidate helper, victim, and distances.

        During the simulation, if the robot encounters a fallen victim,
        the Netlogo model will execute the `on_contact.py` file,
        which in turn will call this function to determine the robot action.

        Args:
            candidate_helper: The candidate helper.
            victim: The victim.
            helper_victim_distance: Distance between the candidate helper and the victim.
            first_responder_victim_distance: Distance between the first responder and
                                                     the victim.

        Returns:
            The robot action to take.
        """
        raise NotImplementedError("Subclasses must override get_robot_action")
