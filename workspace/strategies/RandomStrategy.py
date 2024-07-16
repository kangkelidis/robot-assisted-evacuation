import random

from src.adaptation_strategy import AdaptationStrategy, Survivor


class RandomStrategy(AdaptationStrategy):
    """
    Randomly choose between asking for help and calling staff.
    """
    def get_robot_action(self,
                         candidate_helper: Survivor,
                         victim: Survivor,
                         helper_victim_distance: float,
                         first_responder_victim_distance: float) -> str:
        if random.random() < 0.5:
            return self.ASK_FOR_HELP_ROBOT_ACTION
        else:
            return self.CALL_STAFF_ROBOT_ACTION
