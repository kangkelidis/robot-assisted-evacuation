from __future__ import annotations

import logging
import os
import sys
import traceback
from multiprocessing import Lock
from typing import Any

from flask import Flask, request

workspace_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(workspace_path)

PORT = 5000
BASE_URL = f'http://localhost:{PORT}'

# List of scenario objects
SCENARIOS = []
# Tracks the simulation IDs that have not finished yet
UNFINISHED_SIMULATION_IDS = []

app = Flask(__name__)

lock = Lock()


@app.route('/get_unfinished_simulations', methods=['GET'])
def get_unfinished_simulations():
    """
    Returns a list of simulation IDs that have not finished yet.
    """
    return {"ids": UNFINISHED_SIMULATION_IDS}, 200


@app.route('/put_results', methods=['PUT'])
def put_results():
    """
    Updates the results of a simulation in the corresponding simulation object.
    Called when the simulation ends.
    """
    from src.simulation import Simulation
    from utils.helper import find_simulation_in, setup_logger

    # logger = setup_logger()

    data = request.json
    simulation_id = data['simulation_id']

    global UNFINISHED_SIMULATION_IDS
    UNFINISHED_SIMULATION_IDS.remove(simulation_id)

    with lock:
        simulation: Simulation = find_simulation_in(SCENARIOS, simulation_id)
        simulation.result.update(data)
        # logger.info(f"simulation data: {simulation.result.__dict__}")

    return "Results saved", 200


@app.route('/passenger_response', methods=['POST'])
def passenger_response():
    """
    Save the response of a passenger when asked to help in the corresponding simulation object.
    """
    from src.simulation import Simulation
    from utils.helper import find_simulation_in

    data = request.json
    simulation_id = data["simulation_id"]
    response = data["response"]

    with lock:
        simulation: Simulation = find_simulation_in(SCENARIOS, simulation_id)
        simulation.add_response(response)

    return "Response saved", 200


@app.route('/on_survivor_contact', methods=['POST'])
def on_survivor_contact_handler():
    """
    Called by the NetLogo model when the robot makes contact with a fallen victim.
    """
    from src.adaptation_strategy import Survivor
    from src.on_contact import on_survivor_contact
    from src.simulation import Scenario, Simulation
    from utils.helper import (find_scenario_by_name, find_simulation_in,
                              get_scenario_name, setup_logger)

    logger = setup_logger()
    data = request.json

    candidate_helper = Survivor(data["helper_gender"], data["helper_culture"], data["helper_age"])
    victim = Survivor(data["fallen_gender"], data["fallen_culture"], data["fallen_age"])
    helper_victim_distance = float(data["helper_fallen_distance"])
    first_responder_victim_distance = float(data["staff_fallen_distance"])
    simulation_id = data["simulation_id"]

    logger.debug(f'PUT /on_survivor_contact called by {simulation_id}')
    scenario_name = get_scenario_name(simulation_id)
    scenario: Scenario = find_scenario_by_name(scenario_name, SCENARIOS)
    simulation: Simulation = find_simulation_in(scenario, simulation_id)

    action = on_survivor_contact(candidate_helper, victim, helper_victim_distance,
                                 first_responder_victim_distance, scenario.adaptation_strategy)
    with lock:
        simulation.add_action(action)

    return action, 200


@app.route('/start', methods=['POST'])
def start():
    try:
        from src.load_config import load_config, load_scenarios
        from src.simulation import Scenario
        from src.simulation_manager import start_experiments
        from utils.paths import CONFIG_FILE

        data = request.json
        data_path = data["data_path"]

        config: dict[str, Any] = load_config(CONFIG_FILE)
        scenarios: list[Scenario] = load_scenarios(config)
        global SCENARIOS
        SCENARIOS = scenarios

        global UNFINISHED_SIMULATION_IDS
        for scenario in scenarios:
            for simulation in scenario.simulations:
                UNFINISHED_SIMULATION_IDS.append(simulation.id)

        # Run the experiments, and saves the results
        start_experiments(config, scenarios, data_path)
    except Exception as e:
        error_message = f"Error on server: {str(e)}\n{traceback.format_exc()}"
        return error_message, 500

    return 'ok', 200


def main():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(debug=False, port=PORT, use_reloader=False)


if __name__ == "__main__":
    main()
