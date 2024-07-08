"""
This module contains the base class for adaptation strategies.
"""


from enum import Enum, auto


class Gender(Enum):
    """
    Enum for Survivor gender.
    """
    FEMALE = auto()
    MALE = auto()


class CulturalCluster(Enum):
    """
    Enum for cultural cluster.
    """
    ARAB = auto()
    NEAR_EAST = auto()
    LATIN_AMERICA = auto()
    EAST_EUROPE = auto()
    LATIN_EUROPE = auto()
    NORDIC = auto()
    GERMANIC = auto()
    AFRICAN = auto()
    ANGLO = auto()
    CONFUCIAN = auto()
    FAR_EAST = auto()


class Age(Enum):
    """
    Enum for age.
    """
    CHILD = auto()
    ADULT = auto()
    ELDERLY = auto()


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
