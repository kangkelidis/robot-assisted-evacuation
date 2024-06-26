
class Gender:
    FEMALE, MALE = range(2)


class CulturalCluster:
    ARAB, NEAR_EAST, LATIN_AMERICA, EAST_EUROPE, LATIN_EUROPE, NORDIC, GERMANIC, AFRICAN, ANGLO, \
        CONFUCIAN, FAR_EAST = (range(11))


class Age:
    CHILD, ADULT, ELDERLY = range(3)


class Survivor:
    def __init__(self, gender, cultural_cluster, age):
        self.gender = int(gender)  # type: int
        self.cultural_cluster = int(cultural_cluster)  # type: int
        self.age = int(age)  # type: int


class AdaptationStrategy(object):
    """
    Base class for adaptation strategies.
    The get_robot_action method should be overridden and implemented by the subclasses.
    """

    def __init__(self):
        # type: (str) -> None
        self.ASK_FOR_HELP_ROBOT_ACTION = "ask-help"  # type:str
        self.CALL_STAFF_ROBOT_ACTION = "call-staff"  # type:str

    def get_robot_action(self, candidate_helper, victim, helper_victim_distance,
                         first_responder_victim_distance):
        # type: (Survivor, Survivor, float, float) -> str
        pass
