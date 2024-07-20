from src.adaptation_strategy import AdaptationStrategy, Survivor


class AlwaysCallStaffStrategy(AdaptationStrategy):
    """
    Always calls for a staff member.
    """
    def get_robot_action(self,
                         simulation_id: str,
                         candidate_helper: Survivor,
                         victim: Survivor,
                         helper_victim_distance: float,
                         first_responder_victim_distance: float) -> str:
        return self.CALL_STAFF_ROBOT_ACTION
