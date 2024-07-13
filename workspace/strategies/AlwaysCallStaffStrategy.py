from src.adaptation_strategy import AdaptationStrategy


class AlwaysCallStaffStrategy(AdaptationStrategy):
    """
    Always calls for a staff member.
    """
    def get_robot_action(self, candidate_helper, victim,
                         helper_victim_distance, first_responder_victim_distance):
        return self.CALL_STAFF_ROBOT_ACTION
