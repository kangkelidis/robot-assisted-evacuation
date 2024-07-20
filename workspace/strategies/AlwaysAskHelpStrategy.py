from src.adaptation_strategy import AdaptationStrategy, Survivor


class AlwaysAskHelpStrategy(AdaptationStrategy):
    """
    Always ask for help from a passenger.
    """
    def get_robot_action(self,
                         simulation_id: str,
                         candidate_helper: Survivor,
                         victim: Survivor,
                         helper_victim_distance: float,
                         first_responder_victim_distance: float) -> str:
        return self.ASK_FOR_HELP_ROBOT_ACTION
