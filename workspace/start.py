import pandas as pd
from typing import Dict, List

from abm_analysis import simulate_and_store, perform_analysis, WORKSPACE_FOLDER


def main():
    set_frame_generation_command = "set ENABLE_FRAME_GENERATION {}"  # type: str
    set_staff_support_command = "set REQUEST_STAFF_SUPPORT {}"  # type: str
    set_passenger_support_command = "set REQUEST_BYSTANDER_SUPPORT {}"  # type: str

    simulation_scenarios = {
        # "no-support": [],
        # "staff-support": [set_staff_support_command.format("TRUE")],
        "passenger-support": [set_frame_generation_command.format("FALSE"),
                              set_passenger_support_command.format("TRUE")],
        "adaptive-support": [set_frame_generation_command.format("FALSE"),
                             set_passenger_support_command.format("TRUE"),
                             set_staff_support_command.format("TRUE")]
    }  # type: Dict[str, List[str]]

    results_file_name = WORKSPACE_FOLDER + "data/experiments.csv"  # type:str
    samples = 30  # type: int

    simulate_and_store(simulation_scenarios, results_file_name, samples)
    metrics = pd.DataFrame(
        [perform_analysis("adaptive-support", simulation_scenarios, results_file_name)])  # type: pd.DataFrame
    metrics.to_csv(WORKSPACE_FOLDER + "data/metrics.csv")


if __name__ == "__main__":
    main()
