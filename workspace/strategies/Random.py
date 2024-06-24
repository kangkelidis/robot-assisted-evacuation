from core.adaptation_strategies import AdaptationStrategy

import random

class Random(AdaptationStrategy):
    """ Randomly choose between asking for help and calling staff."""

    def __init__(self):
        super(Random, self).__init__("random-strategy")

    def get_robot_action(self, candidate_helper, victim, helper_victim_distance, first_responder_victim_distance):
        if random.random() < 0.5:
            return self.ASK_FOR_HELP_ROBOT_ACTION
        else:
            return self.CALL_STAFF_ROBOT_ACTION