from src.adaptation_strategy import AdaptationStrategy


class AlwaysAskHelpStrategy(AdaptationStrategy):
    """
    Always ask for help from a passenger.
    """
    def get_robot_action(self, candidate_helper, victim,
                         helper_victim_distance, first_responder_victim_distance):
        return self.ASK_FOR_HELP_ROBOT_ACTION
