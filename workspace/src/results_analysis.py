"""
Results Analysis Module

This module is responsible for analyzing and plotting the results of the simulation experiments.

Using https://www.stat.ubc.ca/~rollin/stats/ssize/n2.html
And https://www.statology.org/pooled-standard-deviation-calculator/
function to calculate Cohen's d for independent samples
Inspired by: https://machinelearningmastery.com/effect-size-measures-in-python/
"""

import os
import textwrap

import matplotlib  # type: ignore

matplotlib.use('Agg')
from typing import List

import matplotlib.pyplot as plt  # type: ignore
import numpy as np
import pandas as pd  # type: ignore
import seaborn as sns  # type: ignore
import statsmodels.api as sm
from scipy.stats import mannwhitneyu
from src.load_config import get_target_scenario
from utils.helper import (get_experiment_folder, get_scenario_index,
                          setup_logger)
from utils.paths import DATA_FOLDER, IMAGE_FOLDER

PLOT_STYLE = 'seaborn-v0_8-darkgrid'
EXPERIMENT_FOLDER_NAME = ""

logger = setup_logger()


def cohen_d_from_metrics(mean_1: float, mean_2: float, std_dev_1: float, std_dev_2: float) -> float:
    """
    Calculate Cohen's d effect size from the means and standard deviations of two samples.

    Cohen's d is a measure of the standardized difference between two means. It is calculated as the
    difference between the two means divided by the pooled standard deviation.

    Args:
        mean_1: The mean of the first sample.
        mean_2: The mean of the second sample.
        std_dev_1: The standard deviation of the first sample.
        std_dev_2: The standard deviation of the second sample.

    Returns:
        The Cohen's d effect size.
    """
    pooled_std_dev = np.sqrt((std_dev_1 ** 2 + std_dev_2 ** 2) / 2)
    return (mean_1 - mean_2) / pooled_std_dev


def calculate_sample_size(mean_1: float, mean_2: float, std_dev_1: float, std_dev_2: float,
                          alpha: float = 0.05, power: float = 0.8) -> float:
    """
    Calculates the recommended sample size for a two-sample test.

    This function uses the `statsmodels` library to calculate the recommended sample size based on
    the provided means, standard deviations, alpha level, and desired power.

    Args:
        mean_1: The mean of the first sample.
        mean_2: The mean of the second sample.
        std_dev_1: The standard deviation of the first sample.
        std_dev_2: The standard deviation of the second sample.
        alpha: The desired alpha level (type I error rate). Defaults to 0.05.
        power: The desired statistical power. Defaults to 0.8.

    Returns:
        The recommended sample size for each group.
    """
    analysis = sm.stats.TTestIndPower()  # type: sm.stats.TTestIndPower
    effect_size = cohen_d_from_metrics(mean_1, mean_2, std_dev_1, std_dev_2)
    result = analysis.solve_power(effect_size=effect_size,
                                  alpha=alpha,
                                  power=power,
                                  alternative="two-sided")
    return result


def test_hypothesis(first_scenario_column: str,
                    second_scenario_column: str,
                    results_dataframe: pd.DataFrame,
                    alternative: str = "two-sided") -> None:
    """
    Perform a Mann-Whitney U test to compare the distributions of two samples.

    This function calculates the means, standard deviations, and recommended sample sizes for the
    two samples, then performs a Mann-Whitney U test to determine if the distributions are
    significantly different. The results are printed to the console and also saved to a file.

    Args:
        first_scenario_column: The name of the column containing the first sample.
        second_scenario_column: The name of the column containing the second sample.
        results_dataframe: The DataFrame containing the sample data.
        alternative: The alternative hypothesis, either "two-sided", "less", or "greater".
                     Defaults to "two-sided".
    """

    first_scenario_data = results_dataframe[first_scenario_column].values  # type: List[int]
    first_scenario_mean = np.mean(first_scenario_data).item()  # type:float
    first_scenario_stddev = np.std(first_scenario_data).item()  # type:float

    second_scenario_data = results_dataframe[second_scenario_column].values  # type: List[float]
    second_scenario_mean = np.mean(second_scenario_data).item()  # type:float
    second_scenario_stddev = np.std(second_scenario_data).item()  # type:float

    logger.info("{}->mean = {} std = {} len={}".format(
        first_scenario_column, first_scenario_mean,
        first_scenario_stddev, len(first_scenario_data)))
    logger.info("{}->mean = {} std = {} len={}".format(
        second_scenario_column, second_scenario_mean,
        second_scenario_stddev, len(second_scenario_data)))
    logger.info("Recommended Sample size: {}".format(
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
    logger.info("U={} , p={}".format(u, p_value))

    hypothesis_file_path = DATA_FOLDER + EXPERIMENT_FOLDER_NAME + "/hypothesis_tests.txt"
    if p_value > threshold:
        logger.info("FAILS TO REJECT NULL HYPOTHESIS: {}".format(null_hypothesis))
        # save the results
        with open(hypothesis_file_path, "a") as f:
            f.write("FAILS TO REJECT NULL HYPOTHESIS: {}\n".format(null_hypothesis))
            f.write(alternative_hypothesis)
            f.write("\n")
    else:
        logger.info("REJECT NULL HYPOTHESIS: {}".format(null_hypothesis))
        logger.info(alternative_hypothesis)
        # save the results
        with open(hypothesis_file_path, "a") as f:
            f.write("REJECT NULL HYPOTHESIS: {}\n".format(null_hypothesis))
            f.write(alternative_hypothesis)
            f.write("\n")


def get_metrics(experiment_results: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the metrics of the experiment results.

    Args:
        experiment_results: The DataFrame containing the experiment results.

    Returns:
        The DataFrame containing the description of the results.
    """
    metrics_df = experiment_results.describe()
    logger.info("\n%s\n", metrics_df)
    return metrics_df


def plot_results(data_for_violin: pd.DataFrame) -> None:
    """
    Plots the results of the experiment.

    Args:
        data_for_violin: The DataFrame containing the experiment result data.
    """
    plt.style.use(PLOT_STYLE)
    plt_path = IMAGE_FOLDER + EXPERIMENT_FOLDER_NAME + "/violin_plot"
    ax = sns.violinplot(data=data_for_violin, order=None)
    ax.set_title("Scenarios Comparison")
    locs = ax.get_xticks()
    labels = [textwrap.fill(label.get_text(), 12) for label in ax.get_xticklabels()]
    ax.xaxis.set_major_locator(plt.FixedLocator(locs))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    plt.savefig(plt_path + ".png", bbox_inches='tight', pad_inches=0)
    plt.savefig(plt_path + ".eps", bbox_inches='tight', pad_inches=0)
    plt.clf()


def process_data(experiment_data: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the data from the experiment results in order to plot them.

    It combines the simulation evacuation ticks from each scenario sample in a row and
    has each scenario as a column.

    Args:
        experiment_data: DataFrame with all simulations' data.

    Returns:
        processed_data: DataFrame with ticks grouped by scenario.
    """
    # Split 'simulation_id' to extract the simulation number
    experiment_data['sim_index'] = experiment_data['simulation_id'].apply(get_scenario_index)
    # Pivot the DataFrame using 'sim_index' as the new index
    processed_data = experiment_data.pivot(
        index='sim_index', columns='scenario', values='evacuation_ticks')

    processed_data_path = DATA_FOLDER + EXPERIMENT_FOLDER_NAME + "/processed_data.csv"
    processed_data.to_csv(processed_data_path)

    metrics = get_metrics(processed_data)
    metrics_path = DATA_FOLDER + EXPERIMENT_FOLDER_NAME + "/metrics.csv"
    metrics.to_csv(metrics_path)
    return processed_data


def plot_num_of_robots(experiment_data: pd.DataFrame) -> None:
    """
    Plots the number of robots in the simulation.

    Args:
        experiment_data (pd.DataFrame): The DataFrame containing the experiment data.
    """
    plt.style.use(PLOT_STYLE)
    plt_path = IMAGE_FOLDER + EXPERIMENT_FOLDER_NAME + "/num_of_robots"
    ax = sns.lineplot(
        data=experiment_data, x='num_of_robots', y='evacuation_ticks', hue='num_of_staff')
    ax.set_title("Evacuation Ticks vs Number of Robots")
    plt.savefig(plt_path + ".png", bbox_inches='tight', pad_inches=0)
    plt.clf()


def plot_comparisons(experiment_data: pd.DataFrame) -> None:
    """
    Plots the comparisons between differences in the dataFrame.

    Checks the dataFrame for columns that have different values and plots combinations.

    Example:
        - If the data has under num_robots values 1 and 2, the function will plot the difference
          between the evacuation_ticks for those values.

    Args:
        experiment_data: The DataFrame containing the experiment data.
    """
    columns_to_check = ['strategy', 'num_of_robots', 'num_of_passengers',
                        'num_of_staff', 'fall_length', 'fall_chance', 'room_type']

    # Check for columns with different values
    # if there are multiple non-unique values, plot a line with a different color for each value
    multivalue_columns = []
    for column in columns_to_check:
        unique_values = experiment_data[column].unique()
        if len(unique_values) > 1:
            multivalue_columns.append(column)
            plt.style.use(PLOT_STYLE)
            plt_path = IMAGE_FOLDER + EXPERIMENT_FOLDER_NAME + f"/{column}_comparison.png"
            ax = sns.lineplot(data=experiment_data, x=column, y='evacuation_ticks')
            first_value = experiment_data[column].iloc[0]
            num_samples = (experiment_data[column] == first_value).sum()
            ax.set_title(f"Evacuation Ticks vs {column}. Sample size: {num_samples}")
            plt.savefig(plt_path, bbox_inches='tight', pad_inches=0)
            plt.clf()

    # Plot a line for each non-unique value
    if len(multivalue_columns) > 1:
        long_format_data = pd.DataFrame(columns=['category', 'value', 'evacuation_ticks'])
        
        for column in multivalue_columns:
            temp_df = experiment_data[[column, 'evacuation_ticks']].copy()
            temp_df['category'] = column
            temp_df.rename({column: 'value'}, axis=1, inplace=True)
            long_format_data = pd.concat([long_format_data, temp_df], ignore_index=True)

        # Plot
        plt.style.use(PLOT_STYLE)
        plt_path = IMAGE_FOLDER + EXPERIMENT_FOLDER_NAME + "/combined_comparison.png"
        ax = sns.lineplot(data=long_format_data, x='value', y='evacuation_ticks', hue='category')
        ax.set_title("Evacuation Ticks Comparison")
        plt.savefig(plt_path, bbox_inches='tight', pad_inches=0)
        plt.clf()


def setup_result_folders() -> None:
    """
    Makes sure the necessary folders are created for the analysis.
    """
    if not os.path.exists(IMAGE_FOLDER + EXPERIMENT_FOLDER_NAME):
        os.makedirs(IMAGE_FOLDER + EXPERIMENT_FOLDER_NAME)


def perform_analysis(experiment_folder_name: str) -> None:
    """
    Performs the analysis of the experiment results.

    Args:
        experiment_results: path to the CSV file containing the experiment results.
    """
    global EXPERIMENT_FOLDER_NAME
    EXPERIMENT_FOLDER_NAME = experiment_folder_name
    setup_result_folders()
    file_path = DATA_FOLDER + experiment_folder_name + "/experiment_data.csv"
    experiment_data = pd.read_csv(file_path)
    processed_data = process_data(experiment_data)

    plot_results(processed_data)

    plot_comparisons(experiment_data)

    target_scenario = get_target_scenario()
    scenarios = processed_data.columns.to_list()
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
