import matplotlib

matplotlib.use('Agg')

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from config import DATA_FOLDER, IMAGE_FOLDER
from scipy.stats import mannwhitneyu

PLOT_STYLE = 'seaborn-darkgrid'

# Using https://www.stat.ubc.ca/~rollin/stats/ssize/n2.html
# And https://www.statology.org/pooled-standard-deviation-calculator/


# function to calculate Cohen's d for independent samples
# Inspired by: https://machinelearningmastery.com/effect-size-measures-in-python/

def cohen_d_from_metrics(mean_1, mean_2, std_dev_1, std_dev_2):
    # type: (float, float, float, float) -> float
    pooled_std_dev = np.sqrt((std_dev_1 ** 2 + std_dev_2 ** 2) / 2)
    return (mean_1 - mean_2) / pooled_std_dev


def calculate_sample_size(mean_1, mean_2, std_dev_1, std_dev_2, alpha=0.05, power=0.8):
    # type: (float, float, float, float, float, float) -> float
    analysis = sm.stats.TTestIndPower()  # type: sm.stats.TTestIndPower
    effect_size = cohen_d_from_metrics(mean_1, mean_2, std_dev_1, std_dev_2)
    result = analysis.solve_power(effect_size=effect_size,
                                  alpha=alpha,
                                  power=power,
                                  alternative="two-sided")
    return result


def get_dataframe(csv_file):
    # type: (str) -> pd.DataFrame
    results_dataframe = pd.read_csv(csv_file, index_col=[0])  # type: pd.DataFrame
    results_dataframe = results_dataframe.dropna()

    return results_dataframe


def plot_results(csv_file, samples_in_title=False):
    # type: (str, bool) -> None
    file_description = Path(csv_file).stem  # type: str
    results_dataframe = get_dataframe(csv_file)  # type: pd.DataFrame

    print(results_dataframe.describe())

    title = ""
    order = None

    if samples_in_title:
        title = "{} samples".format(len(results_dataframe))
    _ = sns.violinplot(data=results_dataframe, order=order).set_title(title)
    plt.savefig(IMAGE_FOLDER + file_description + "_violin_plot.png",
                bbox_inches='tight', pad_inches=0)
    plt.savefig(IMAGE_FOLDER + file_description + "_violin_plot.eps", bbox_inches='tight',
                pad_inches=0)
    plt.show()
    plt.clf()

    _ = sns.stripplot(data=results_dataframe, order=order, jitter=True).set_title(title)
    plt.savefig(IMAGE_FOLDER + file_description + "_strip_plot.png",
                bbox_inches='tight', pad_inches=0)
    plt.savefig(IMAGE_FOLDER + file_description + "_strip_plot.eps",
                bbox_inches='tight', pad_inches=0)
    plt.show()


def test_hypothesis(first_scenario_column, second_scenario_column, csv_file, alternative="two-sided"):
    # type: (str, str, str, str) -> None
    print("CURRENT ANALYSIS: Analysing file {}".format(csv_file))
    results_dataframe = get_dataframe(csv_file)  # type: pd.DataFrame

    first_scenario_data = results_dataframe[first_scenario_column].values  # type: List[float]
    first_scenario_mean = np.mean(first_scenario_data).item()  # type:float
    first_scenario_stddev = np.std(first_scenario_data).item()  # type:float

    second_scenario_data = results_dataframe[second_scenario_column].values  # type: List[float]
    second_scenario_mean = np.mean(second_scenario_data).item()  # type:float
    second_scenario_stddev = np.std(second_scenario_data).item()  # type:float

    print("{}-> mean = {} std = {} len={}".format(first_scenario_column, first_scenario_mean,
                                                  first_scenario_stddev, len(first_scenario_data)))
    print("{}-> mean = {} std = {} len={}".format(second_scenario_column, second_scenario_mean,
                                                  second_scenario_stddev, len(second_scenario_data)))
    print("Recommended Sample size: {}".format(
        calculate_sample_size(first_scenario_mean, second_scenario_mean, first_scenario_stddev,
                              second_scenario_stddev)))

    null_hypothesis = "MANN-WHITNEY RANK TEST: " + \
                      "The distribution of {} times is THE SAME as the distribution of {} times".format(
                          first_scenario_column, second_scenario_column)  # type: str
    alternative_hypothesis = "ALTERNATIVE HYPOTHESIS: the distribution underlying {} is stochastically {} than the " \
                             "distribution underlying {}".format(first_scenario_column, alternative,
                                                                 second_scenario_column)  # type:str

    threshold = 0.05  # type:float
    u, p_value = mannwhitneyu(x=first_scenario_data, y=second_scenario_data, alternative=alternative)
    print("U={} , p={}".format(u, p_value))
    if p_value > threshold:
        print("FAILS TO REJECT NULL HYPOTHESIS: {}".format(null_hypothesis))
        # save the results
        with open(DATA_FOLDER + "hypothesis_tests.txt", "a") as f:
            f.write("FAILS TO REJECT NULL HYPOTHESIS: {}\n".format(null_hypothesis))
            f.write(alternative_hypothesis)
            f.write("\n")
    else:
        print("REJECT NULL HYPOTHESIS: {}".format(null_hypothesis))
        print(alternative_hypothesis)
        # save the results
        with open(DATA_FOLDER + "hypothesis_tests.txt", "a") as f:
            f.write("REJECT NULL HYPOTHESIS: {}\n".format(null_hypothesis))
            f.write(alternative_hypothesis)
            f.write("\n")


def get_current_file_metrics(simulation_scenarios, current_file):
    # type: (Dict[str, List[str]], str) -> Dict[str, float]
    results_dataframe = get_dataframe(current_file)  # type: pd.DataFrame
    metrics_dict = {}  # type: Dict[str, float]

    for scenario in simulation_scenarios.keys():
        metrics_dict["{}_mean".format(scenario)] = results_dataframe[scenario].mean()
        metrics_dict["{}_std".format(scenario)] = results_dataframe[scenario].std()
        metrics_dict["{}_median".format(scenario)] = results_dataframe[scenario].median()
        metrics_dict["{}_min".format(scenario)] = results_dataframe[scenario].min()
        metrics_dict["{}_max".format(scenario)] = results_dataframe[scenario].max()

    return metrics_dict


def perform_analysis(target_scenario, simulation_scenarios, current_file):
    # type: (str, Dict[str, List[str]], str) -> Dict[str, float]

    plt.style.use(PLOT_STYLE)
    plot_results(csv_file=current_file)
    current_file_metrics = get_current_file_metrics(simulation_scenarios, current_file)  # type: Dict[str, float]
    # current_file_metrics["fall_length"] = fall_length

    for alternative_scenario in simulation_scenarios.keys():
        if alternative_scenario != target_scenario:
            test_hypothesis(first_scenario_column=target_scenario,
                            second_scenario_column=alternative_scenario,
                            alternative="less",
                            csv_file=current_file)

    return current_file_metrics