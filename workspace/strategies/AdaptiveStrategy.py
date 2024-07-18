
import numpy as np
# from adaptive import analyser
from pygambit import Rational
from pygambit.nash import NashSolution
from src.adaptation_strategy import AdaptationStrategy, Survivor


class AdaptiveStrategy(AdaptationStrategy):
    """
    .
    """
    def get_robot_action(self,
                         candidate_helper: Survivor,
                         victim: Survivor,
                         helper_victim_distance: float,
                         first_responder_victim_distance: float) -> str:
        Rational(1, 2)
        NashSolution(np.array([[1, 2], [3, 4]]))
        return None
