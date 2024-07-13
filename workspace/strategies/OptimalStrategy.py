
import random

from src.adaptation_strategy import (AdaptationStrategy, Age, CulturalCluster,
                                     Gender, Survivor)


class OptimalStrategy(AdaptationStrategy):
    """
    Rows represent the helper's characteristics:

    Rows 0 and 1: Male adult and elderly from the ingroup, respectively.
    Rows 2 and 3: Male adult and elderly from the outgroup, respectively.
    Rows 4 and 5: Female adult and elderly from the ingroup, respectively.
    Rows 6 and 7: Female adult and elderly from the outgroup, respectively.
    Columns represent the fallen person's characteristics:

    Columns 0, 1, and 2: Male child, adult, and elderly, respectively.
    Columns 3, 4, and 5: Female child, adult, and elderly, respectively.

    ingroup is either in the same culture group or have formed a link(part of a group)
    in the simulation.
"""
    help_matrix: list[list[float]] = [
        [0.3, 0.15, 0.3, 0.4, 0.3, 0.4],
        [0.15, 0.075, 0.15, 0.2, 0.15, 0.2],
        [0.252, 0.126, 0.252, 0.336, 0.252, 0.336],
        [0.126, 0.063, 0.126, 0.168, 0.126, 0.168],
        [0.15, 0.075, 0.15, 0.2, 0.15, 0.2],
        [0.075, 0.0375, 0.075, 0.1, 0.075, 0.1],
        [0.126, 0.063, 0.126, 0.168, 0.126, 0.168],
        [0.063, 0.0315, 0.063, 0.084, 0.063, 0.084]
    ]

    """

    """
    # TODO: as the number of passengers decreases,
    # the probability of asking for staff help should increase
    def get_robot_action(self, candidate_helper, victim,
                         helper_victim_distance, first_responder_victim_distance):
        if first_responder_victim_distance < helper_victim_distance:
            return self.CALL_STAFF_ROBOT_ACTION

        row: int = 0
        #  Females are at row 4 to 7, males at 0-3
        if candidate_helper.gender == Gender.FEMALE.value:
            row += 4
        # outgroup is at row 2-3 and 6-7, ingroup at 0-1 and 4-5
        if candidate_helper.cultural_cluster != victim.cultural_cluster:
            row += 2
        # Elderly are at row 1, 3, 5, 7
        if candidate_helper.age == Age.ELDERLY.value:
            row += 1

        col: int = 0
        if victim.gender == Gender.FEMALE.value:
            col += 3
        if victim.age == Age.ADULT.value:
            col += 1
        if victim.age == Age.ELDERLY.value:
            col += 2

        helping_chance: float = self.help_matrix[row][col]
        if helping_chance > 0.2:
            return self.ASK_FOR_HELP_ROBOT_ACTION
        else:
            return self.CALL_STAFF_ROBOT_ACTION
