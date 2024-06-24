from core.adaptation_strategies import AdaptationStrategy

class ProGroup(AdaptationStrategy):
    """ Randomly choose between asking for help and calling staff."""

    def __init__(self):
        super(ProGroup, self).__init__("always-ask-for-victims-help-strategy")

    def get_robot_action(self, candidate_helper, victim, helper_victim_distance, first_responder_victim_distance):
        return self.ASK_FOR_HELP_ROBOT_ACTION