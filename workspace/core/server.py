import sys

from flask import Flask, jsonify, request

sys.path.append("/home/workspace/")
# from core.Scenario import get_adaptation_strategy
# from core.Survivor import Survivor

app = Flask(__name__)


@app.route('/on_survivor_contact', methods=['POST'])
def on_survivor_contact():
    data = request.json
    print(data)
    # candidate_helper = Survivor(data["helper_gender"], data["helper_culture"], data["helper_age"])
    # victim = Survivor(data["fallen_gender"], data["fallen_culture"], data["fallen_age"])
    # helper_victim_distance = float(data["helper_fallen_distance"])
    # first_responder_victim_distance = float(data["staff_fallen_distance"])
    # simulation_id = data["simulation_id"]

    # adaptation_strategy = get_adaptation_strategy(simulation_id.split("_")[0])
    # robot_action = adaptation_strategy.get_robot_action(candidate_helper, victim, helper_victim_distance, first_responder_victim_distance)

    # return jsonify({"robot_action": robot_action})
    return "ok"

if __name__ == "__main__":
    app.run(debug=True, port=5000)