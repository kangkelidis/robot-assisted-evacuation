from core.adaptation_strategies import AdaptationStrategy

class ProSelf(AdaptationStrategy):
    """ Randomly choose between asking for help and calling staff."""

    def __init__(self):
        super(ProSelf, self).__init__("always-ask-for-staff-help-strategy")

    def get_robot_action(self, candidate_helper, victim, helper_victim_distance, first_responder_victim_distance):
        return self.CALL_STAFF_ROBOT_ACTION