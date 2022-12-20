import pandas as pd
from typing import Dict, List

from abm_analysis import simulate_and_store, perform_analysis, WORKSPACE_FOLDER

SET_FRAME_GENERATION_COMMAND = "set ENABLE_FRAME_GENERATION {}"  # type: str
SET_FALL_LENGTH_COMMAND = "set DEFAULT_FALL_LENGTH {}"  # type: str

SET_STAFF_SUPPORT_COMMAND = "set REQUEST_STAFF_SUPPORT {}"  # type: str
SET_PASSENGER_SUPPORT_COMMAND = "set REQUEST_BYSTANDER_SUPPORT {}"  # type: str


def main():
    simulation_scenarios = {
        "no-support": [SET_FRAME_GENERATION_COMMAND.format("FALSE"),
                       SET_FALL_LENGTH_COMMAND.format(500)],
        "staff-support": [SET_FRAME_GENERATION_COMMAND.format("FALSE"),
                          SET_FALL_LENGTH_COMMAND.format(500),
                          SET_STAFF_SUPPORT_COMMAND.format("TRUE")],
        "passenger-support": [SET_FRAME_GENERATION_COMMAND.format("FALSE"),
                              SET_FALL_LENGTH_COMMAND.format(500),
                              SET_PASSENGER_SUPPORT_COMMAND.format("TRUE")],
        "adaptive-support": [SET_FRAME_GENERATION_COMMAND.format("FALSE"),
                             SET_FALL_LENGTH_COMMAND.format(500),
                             SET_PASSENGER_SUPPORT_COMMAND.format("TRUE"),
                             SET_STAFF_SUPPORT_COMMAND.format("TRUE")]
    }  # type: Dict[str, List[str]]

    results_file_name = WORKSPACE_FOLDER + "data/experiments.csv"  # type:str
    samples = 30  # type: int

    simulate_and_store(simulation_scenarios, results_file_name, samples)
    metrics = pd.DataFrame(
        [perform_analysis("adaptive-support", simulation_scenarios, results_file_name)])  # type: pd.DataFrame
    metrics.to_csv(WORKSPACE_FOLDER + "data/metrics.csv")


if __name__ == "__main__":
    main()
