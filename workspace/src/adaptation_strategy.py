"""
This module contains the base class for adaptation strategies.
"""

import importlib
import os
import traceback
from enum import Enum
from typing import Optional, Self

from utils.helper import setup_logger
from utils.paths import STRATEGIES_FOLDER

logger = setup_logger()


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

    @staticmethod
    def get_strategy(strategy_name: str,
                     strategies_folder: str = STRATEGIES_FOLDER) -> Optional['AdaptationStrategy']:
        """
        Returns an instance of the specified adaptation strategy.

        Looks for a python file with the same name as the strategy in the strategies_folder,
        that is a subclass of AdaptationStrategy.

        Args:
            strategy_name: The name of the strategy.
            strategies_folder: The folder containing the strategy files.
                                    Default is STRATEGIES_FOLDER form paths.py.

        Returns:
            An instance of the specified strategy. None if not found.
        """
        try:
            for file_name in os.listdir(strategies_folder):
                if file_name.endswith('.py') and file_name[:-3] == strategy_name:
                    module = importlib.import_module('strategies.' + strategy_name)
                    strategy_class = getattr(module, strategy_name)

                    if issubclass(strategy_class, AdaptationStrategy):
                        strategy_instance = strategy_class()
                        return strategy_instance
        except Exception as e:
            logger.error(f"Error in get_adaptation_strategy: {e}")
            traceback.print_exc()
        raise FileNotFoundError(f"Failed to get adaptation strategy {strategy_name}")

    def get_robot_action(self,
                         candidate_helper: Survivor,
                         victim: Survivor,
                         helper_victim_distance: float,
                         first_responder_victim_distance: float) -> str:
        """
        Gets the robot action based on the candidate helper, victim, and distances.

        During the simulation, if the robot encounters a fallen victim,
        the NetLogo model will call this function to determine the robot's action.

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

    def __str__(self):
        return self.__class__.__name__
