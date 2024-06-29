"""
This module contains the base class for adaptation strategies.
"""


class Gender:
    """
    Enum for Survivor gender.
    """
    FEMALE, MALE = range(2)


class CulturalCluster:
    """
    Enum for cultural cluster.
    """
    ARAB, NEAR_EAST, LATIN_AMERICA, EAST_EUROPE, LATIN_EUROPE, NORDIC, GERMANIC, AFRICAN, ANGLO, \
        CONFUCIAN, FAR_EAST = (range(11))


class Age:
    """
    Enum for age.
    """
    CHILD, ADULT, ELDERLY = range(3)


class Survivor:
    """
    Class representing a survivor.

    Attributes:
        gender (int): The gender of the survivor.
        cultural_cluster (int): The cultural cluster of the survivor.
        age (int): The age of the survivor.
    """
    def __init__(self, gender, cultural_cluster, age):
        self.gender = int(gender)  # type: int
        self.cultural_cluster = int(cultural_cluster)  # type: int
        self.age = int(age)  # type: int


class AdaptationStrategy(object):
    """
    Base class for adaptation strategies.

    The get_robot_action method should be overridden and implemented by the subclasses.

    Attributes:
        ASK_FOR_HELP_ROBOT_ACTION (str): The robot action to ask for help.
        CALL_STAFF_ROBOT_ACTION (str): The robot action to call staff.
    """

    ASK_FOR_HELP_ROBOT_ACTION = "ask-help"
    CALL_STAFF_ROBOT_ACTION = "call-staff"

    def get_robot_action(self, candidate_helper, victim, helper_victim_distance,
                         first_responder_victim_distance):
        # type: (Survivor, Survivor, float, float) -> str
        """
        Gets the robot action based on the candidate helper, victim, and distances.

        During the simulation, if the robot encounters a fallen victim,
        the Netlogo model will execute the `on_contact.py` file,
        which in turn will call this function to determine the robot action.

        Args:
            candidate_helper (Survivor): The candidate helper.
            victim (Survivor): The victim.
            helper_victim_distance (float): Distance between the candidate helper and the victim.
            first_responder_victim_distance (float): Distance between the first responder and
                                                     the victim.

        Returns:
            str: The robot action to take.
        """
        raise NotImplementedError("Subclasses must override get_robot_action")
