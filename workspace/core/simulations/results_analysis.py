"""
Results Analysis Module

This module is responsible for analyzing and plotting the results of the simulation experiments.

Using https://www.stat.ubc.ca/~rollin/stats/ssize/n2.html
And https://www.statology.org/pooled-standard-deviation-calculator/
function to calculate Cohen's d for independent samples
Inspired by: https://machinelearningmastery.com/effect-size-measures-in-python/
"""

import matplotlib  # type: ignore

matplotlib.use('Agg')
from typing import List

import matplotlib.pyplot as plt  # type: ignore
import numpy as np
import pandas as pd  # type: ignore
import seaborn as sns  # type: ignore
import statsmodels.api as sm
from core.simulations.load_config import load_target_scenario
from core.utils.helper import (get_experiment_folder, get_scenario_index,
                               get_scenario_name, setup_logger)
from core.utils.paths import DATA_FOLDER, IMAGE_FOLDER
from scipy.stats import mannwhitneyu

PLOT_STYLE = 'seaborn-darkgrid'
EXPERIMENT_FOLDER_NAME = get_experiment_folder()

logger = setup_logger()


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


def test_hypothesis(first_scenario_column, second_scenario_column,
                    results_dataframe, alternative="two-sided"):
    # type: (str, str, pd.DataFrame, str) -> None

    first_scenario_data = results_dataframe[first_scenario_column].values  # type: List[int]
    first_scenario_mean = np.mean(first_scenario_data).item()  # type:float
    first_scenario_stddev = np.std(first_scenario_data).item()  # type:float

    second_scenario_data = results_dataframe[second_scenario_column].values  # type: List[float]
    second_scenario_mean = np.mean(second_scenario_data).item()  # type:float
    second_scenario_stddev = np.std(second_scenario_data).item()  # type:float

    print("{}->mean = {} std = {} len={}".format(first_scenario_column, first_scenario_mean,
                                                 first_scenario_stddev, len(first_scenario_data)))
    print("{}->mean = {} std = {} len={}".format(second_scenario_column, second_scenario_mean,
                                                 second_scenario_stddev, len(second_scenario_data)))
    print("Recommended Sample size: {}".format(
        calculate_sample_size(first_scenario_mean, second_scenario_mean, first_scenario_stddev,
                              second_scenario_stddev)))

    null_hypothesis = (
        "MANN-WHITNEY RANK TEST: The distribution of {} times is THE SAME as the "
        "distribution of {} times".format(first_scenario_column, second_scenario_column)
    )

    alternative_hypothesis = (
        "ALTERNATIVE HYPOTHESIS: the distribution underlying {} is stochastically {} "
        "than the distribution underlying {}".format(
            first_scenario_column, alternative, second_scenario_column
        )
    )

    threshold = 0.05  # type:float
    u, p_value = mannwhitneyu(x=first_scenario_data, y=second_scenario_data,
                              alternative=alternative)
    print("U={} , p={}".format(u, p_value))

    hypothesis_file_path = DATA_FOLDER + EXPERIMENT_FOLDER_NAME + "/hypothesis_tests.txt"
    if p_value > threshold:
        print("FAILS TO REJECT NULL HYPOTHESIS: {}".format(null_hypothesis))
        # save the results
        with open(hypothesis_file_path, "a") as f:
            f.write("FAILS TO REJECT NULL HYPOTHESIS: {}\n".format(null_hypothesis))
            f.write(alternative_hypothesis)
            f.write("\n")
    else:
        print("REJECT NULL HYPOTHESIS: {}".format(null_hypothesis))
        print(alternative_hypothesis)
        # save the results
        with open(hypothesis_file_path, "a") as f:
            f.write("REJECT NULL HYPOTHESIS: {}\n".format(null_hypothesis))
            f.write(alternative_hypothesis)
            f.write("\n")


def get_metrics(experiment_results):
    # type: (pd.DataFrame) -> pd.DataFrame
    """ Returns the metrics of the experiment results."""
    metrics_df = experiment_results.describe()
    print(metrics_df)
    return metrics_df


def plot_results(experiment_results):
    # type: (pd.DataFrame) -> None
    """ Plots the results of the experiment."""
    plt.style.use(PLOT_STYLE)
    plt_path = IMAGE_FOLDER + EXPERIMENT_FOLDER_NAME + "/violin_plot"
    _ = sns.violinplot(data=experiment_results, order=None).set_title("title")
    plt.savefig(plt_path + ".png", bbox_inches='tight', pad_inches=0)
    plt.savefig(plt_path + ".eps", bbox_inches='tight', pad_inches=0)
    plt.clf()


def process_data(experiment_results):
    # type: (pd.DataFrame) -> pd.DataFrame
    """
    Processes the data from the experiment results in order to plot them.
    It combines the simulation evacuation ticks for each scenario sample in a row and
    has each scenario as a column.
    """
    # Split 'simulation_id' to extract the scenario name and simulation number
    experiment_results['scenario'] = experiment_results['simulation_id'].apply(get_scenario_name)
    experiment_results['sim_indx'] = experiment_results['simulation_id'].apply(get_scenario_index)
    # Pivot the DataFrame using 'simulation_number' as the new index
    processed_data = experiment_results.pivot(
        index='sim_indx', columns='scenario', values='evacuation_ticks')

    processed_data_path = DATA_FOLDER + EXPERIMENT_FOLDER_NAME + "/processed_data.csv"
    processed_data.to_csv(processed_data_path)

    metrics = get_metrics(processed_data)
    metrics_path = DATA_FOLDER + EXPERIMENT_FOLDER_NAME + "/metrics.csv"
    metrics.to_csv(metrics_path)
    return processed_data


def perform_analysis(experiment_results):
    # type: (pd.DataFrame) -> None
    """ Performs the analysis of the experiment results."""
    logger.info("Performing analysis.")
    processed_data = process_data(experiment_results)
    plot_results(processed_data)

    target_scenario = load_target_scenario()
    scenarios = processed_data.columns.tolist()
    if target_scenario in scenarios:
        for alternative_scenario in scenarios:
            if alternative_scenario != target_scenario:
                test_hypothesis(first_scenario_column=target_scenario,
                                second_scenario_column=alternative_scenario,
                                results_dataframe=processed_data,
                                alternative="less")
    else:
        logger.error(
            "Cannot test_hypothesis. Target scenario for analysis not in simulationScenarios, " +
            "check targetScenarioForAnalysis in config.json.")
        raise Exception('targetScenarioForAnalysis not in simulationScenarios')
