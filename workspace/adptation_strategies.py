import random

from survivor import Age, CulturalCluster, Gender, Survivor


class AdaptationStrategy(object):
    """ Base class for adaptation strategies. get_robot_action method should be overridden and implemented by the subclasses."""

    def __init__(self):
        # type: (str) -> None
        self.ASK_FOR_HELP_ROBOT_ACTION = "ask-help"  # type:str
        self.CALL_STAFF_ROBOT_ACTION = "call-staff"  # type:str
        
    def get_robot_action(self, candidate_helper, victim, helper_victim_distance, first_responder_victim_distance):
        # type: (Survivor, Survivor, float, float) -> str
        pass
    
class StrategyA(AdaptationStrategy):
    """ If the potential helper is closer to the victim than the first responder (staff member) and
        the is an adult male, ask for his help. Otherwise, call the staff. """    

    # TODO: To optimise it, could take into account how more efficient a staff member is compared to a bystander and determine the distance cuttoff accordingly.
    def get_robot_action(self, candidate_helper, victim, helper_victim_distance, first_responder_victim_distance):
        robot_action = self.CALL_STAFF_ROBOT_ACTION

        if helper_victim_distance < first_responder_victim_distance and \
                candidate_helper.gender == Gender.MALE and candidate_helper.age == Age.ADULT:
            robot_action = self.ASK_FOR_HELP_ROBOT_ACTION

        return robot_action

class StrategyB(AdaptationStrategy):
    """ Randomly choose between asking for help and calling staff."""

    def get_robot_action(self, candidate_helper, victim, helper_victim_distance, first_responder_victim_distance):
        if random.random() < 0.5:
            return self.ASK_FOR_HELP_ROBOT_ACTION
        else:
            return self.CALL_STAFF_ROBOT_ACTION

class StrategyC(AdaptationStrategy):
    """ The potential helper has an X% chance to have a group identity, there is a Y% chance the robot will predict it correctly.
        Then it asks for help. If it predics wrong, it calls the staff. 
        Similarly, If the potential helper has an individual identity (1-X%), there is a Y% chance the robot will predict it correctly
        and call for staff. Or 1-Y% it predicts wrong and it asks for help."""
    GROUP_IDENTIFYING_PERCENTAGE = 0.8
    IDENTITY_PREDICTION_ACCURANCY = 0.9

    def get_robot_action(self, candidate_helper, victim, helper_victim_distance, first_responder_victim_distance):
        if helper_victim_distance < first_responder_victim_distance and \
                        candidate_helper.gender == Gender.MALE and candidate_helper.age == Age.ADULT:
                    return self.ASK_FOR_HELP_ROBOT_ACTION

        if random.random() < GROUP_IDENTIFYING_PERCENTAGE:
            if random.random() < IDENTITY_PREDICTION_ACCURANCY:
                return self.ASK_FOR_HELP_ROBOT_ACTION # correctly identified group identity
            else:
                return self.CALL_STAFF_ROBOT_ACTION # erroneusly identified individual identity
        else:
            if random.random() < IDENTITY_PREDICTION_ACCURANCY:
                return self.CALL_STAFF_ROBOT_ACTION # correctly identified individual identity
            else:
                return self.ASK_FOR_HELP_ROBOT_ACTION # erroneusly identified individual identity
    
        """ This is the same as saying P(H) = P(G)*P(A) + (1-P(G)) * (1-P(A))
            where P(H) is the probability of asking for help, P(G) is the probability of having a group identity 
            and P(A) is the probability of the robot predicting the identity correctly.
            P(H) = P(G)*P(A) + 1 - P(G) - P(A) + P(G)*P(A) = 2*P(G)*P(A) - P(G) - P(A) + 1
            P(H) = 2*0.8*0.9 - 0.8 - 0.9 + 1 = 0.74
            P(H) = 0.8*0.9 + 0.2*0.1 = 0.74"""
        # if random.random() < GROUP_IDENTIFYING_PERCENTAGE * IDENTITY_PREDICTION_ACCURANCY + (1 - GROUP_IDENTIFYING_PERCENTAGE) * (1 - IDENTITY_PREDICTION_ACCURANCY):
        #     return self.ASK_FOR_HELP_ROBOT_ACTION
        # else:
        #     return self.CALL_STAFF_ROBOT_ACTION


class StrategyD(AdaptationStrategy):
    """ Predictor is always correct. P(A) = 1. """


    GROUP_IDENTIFYING_PERCENTAGE  = 0.8
    def get_robot_action(self, candidate_helper, victim, helper_victim_distance, first_responder_victim_distance):
        if random.random() < GROUP_IDENTIFYING_PERCENTAGE:
            return self.ASK_FOR_HELP_ROBOT_ACTION
        else:
            return self.CALL_STAFF_ROBOT_ACTION

# Strategies to be used in the simulation. sDon't use _ in the name of the strategy (_ used to separate the strategy name from the sample id)
adaptation_strategies = {
    "A": StrategyA(),
    "B": StrategyB(),
    "C": StrategyC(),
    "D": StrategyD()
}