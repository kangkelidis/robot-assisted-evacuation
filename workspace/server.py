from __future__ import annotations

import importlib
import json
import logging
import os
import sys
import traceback
from typing import Any, Optional

from flask import Flask, request
# sys.path.append("/home/workspace/")
# from src.adaptation_strategy import AdaptationStrategy, Survivor
# from src.on_contact import on_survivor_contact
# from src.simulation import Result, Scenario, Simulation
# from src.simulation_manager import start_experiments
# from utils.cleanup import cleanup_workspace
# from utils.helper import (find_scenario_by_name, find_simulation_in,
#                           get_scenario_name, setup_folders, setup_logger)
from utils.paths import (CONFIG_FILE, NETLOGO_FOLDER, STRATEGIES_FOLDER,
                         WORKSPACE_FOLDER)

# logger = setup_logger()

app = Flask(__name__)

# List of scenario objects
SCENARIOS = []


@app.route('/put_results', methods=['POST'])
def put_results():
    from src.simulation import Result, Scenario, Simulation
    from utils.helper import get_scenario_name
    data = request.json
    results = Result(**data)
    simulation_id = results.simulation_id
    scenario_name = get_scenario_name(simulation_id)
    scenario: Scenario = next((s for s in SCENARIOS if s.name == scenario_name), None)
    simulation: Simulation = next((s for s in scenario.simulations if s.id == simulation_id), None)
    simulation.result = results

    return "Results received"


@app.route('/passenger_response', methods=['POST'])
def passenger_response():
    from src.simulation import Scenario
    from utils.helper import get_scenario_name
    data = request.json
    simulation_id = data["simulation_id"]
    response = data["response"]

    scenario_name: str = get_scenario_name(simulation_id)
    scenario: Scenario = next((s for s in SCENARIOS if s.name == scenario_name), None)
    simulation = next((s for s in scenario.simulations if s.id == simulation_id), None)
    simulation.responses.append(response)

    return "Response received"


@app.route('/on_survivor_contact', methods=['POST'])
def on_survivor_contact_handler():
    from src.adaptation_strategy import Survivor
    from src.on_contact import on_survivor_contact
    from src.simulation import Scenario, Simulation
    from utils.helper import (find_scenario_by_name, find_simulation_in,
                              get_scenario_name, setup_logger)

    logger = setup_logger()
    """
    Called by the NetLogo model when the robot makes contact with a fallen victim.
    """
    data = request.json

    candidate_helper = Survivor(data["helper_gender"], data["helper_culture"], data["helper_age"])
    victim = Survivor(data["fallen_gender"], data["fallen_culture"], data["fallen_age"])
    helper_victim_distance = float(data["helper_fallen_distance"])
    first_responder_victim_distance = float(data["staff_fallen_distance"])
    simulation_id = data["simulation_id"]

    logger.debug(f'on_contact.py called by {simulation_id}')
    scenario_name = get_scenario_name(simulation_id)
    scenario: Scenario = find_scenario_by_name(scenario_name, SCENARIOS)
    simulation: Simulation = find_simulation_in(scenario, simulation_id)

    action = on_survivor_contact(candidate_helper, victim, helper_victim_distance,
                                 first_responder_victim_distance, scenario.adaptation_strategy)
    # TODO: sort action out in the class
    simulation.actions.append(action)
    return action


@app.route('/run', methods=['GET'])
def run():
    from src.load_config import load_config, load_scenarios
    from src.results_analysis import perform_analysis
    from src.simulation import Scenario
    from src.simulation_manager import start_experiments
    from utils.helper import setup_logger

    logger = setup_logger()
    logger.info("******* ==Starting Experiment== *******")
    config: dict[str, Any] = load_config(CONFIG_FILE)
    scenarios: list[Scenario] = load_scenarios(config)
    global SCENARIOS
    SCENARIOS = scenarios
    experiments_results = start_experiments(config, scenarios)
    # perform_analysis(experiments_results)
    logger.info("******* ==Experiment Finished== *******\n")

    return 'Experiment finished'


def main():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(debug=False, port=5000)


if __name__ == "__main__":
    main()
