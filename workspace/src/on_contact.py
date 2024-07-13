"""
This module provides functionality for getting an adaptation strategy.

The main function in this module is called by the NetLogo simulation
to get the robot's action when it makes contact with a fallen victim.
"""

from src.adaptation_strategy import AdaptationStrategy, Survivor
from utils.helper import setup_logger

logger = setup_logger()


def on_survivor_contact(candidate_helper: Survivor,
                        victim: Survivor,
                        helper_victim_distance: float,
                        first_responder_victim_distance: float,
                        strategy: AdaptationStrategy) -> str:
    """
    Calls the adaptation strategy get_robot_action and returns the action.

    Args:
        candidate_helper: The candidate helper.
        victim: The victim.
        helper_victim_distance: Distance between the candidate helper and the victim.
        first_responder_victim_distance: Distance between the first responder
                                                 and the victim.
        strategy: The adaptation strategy to use.

    Returns:
        The robot action to take.
    """

    if strategy is None:
        raise ValueError("No adaptation strategy provided.")

    action = strategy.get_robot_action(candidate_helper, victim, helper_victim_distance,
                                       first_responder_victim_distance)
    logger.debug(f"Selected action: {action}")

    return action
