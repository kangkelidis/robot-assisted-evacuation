class Gender:
    FEMALE, MALE = range(2)


class CulturalCluster:
    ARAB, NEAR_EAST, LATIN_AMERICA, EAST_EUROPE, LATIN_EUROPE, NORDIC, GERMANIC, AFRICAN, ANGLO, CONFUCIAN, FAR_EAST = range(
        11)


class Age:
    CHILD, ADULT, ELDERLY = range(3)


class Survivor:
    def __init__(self, gender, cultural_cluster, age):
        self.gender = int(gender)  # type: int
        self.cultural_cluster = int(cultural_cluster)  # type: int
        self.age = int(age)  # type: i