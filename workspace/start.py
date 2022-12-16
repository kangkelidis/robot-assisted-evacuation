import pandas as pd
from typing import Dict, List

from abm_analysis import simulate_and_store, perform_analysis


def main():
    set_staff_support_command = "set REQUEST_STAFF_SUPPORT {}"  # type: str
    simulation_scenarios = {
        "no-support": [],
        "staff-support": [set_staff_support_command.format("TRUE")],
    }  # type: Dict[str, List[str]]

    results_file_name = "/home/workspace/data/experiments.csv"  # type:str
    samples = 1  # type: int

    simulate_and_store(simulation_scenarios, results_file_name, samples)
    metrics = pd.DataFrame(
        [perform_analysis("staff-support", simulation_scenarios, results_file_name)])  # type: pd.DataFrame
    metrics.to_csv("/home/workspace/data/metrics.csv")


if __name__ == "__main__":
    main()
