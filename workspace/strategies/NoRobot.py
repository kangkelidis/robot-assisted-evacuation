from core.adaptation_strategies import AdaptationStrategy

class NoRobot(AdaptationStrategy):
    """ Randomly choose between asking for help and calling staff."""

    def __init__(self):
        super(NoRobot, self).__init__("no-robots-strategy")
        self.robot = False

    def get_robot_action(self, candidate_helper, victim, helper_victim_distance, first_responder_victim_distance):
        return self.CALL_STAFF_ROBOT_ACTION