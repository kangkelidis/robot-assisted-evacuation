import json
import os
import random
import sys
import unittest
from unittest.mock import ANY, MagicMock, mock_open, patch

workspace_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(workspace_path)
strategy_path = os.path.join(workspace_path, 'strategies')

from core.netlogo.on_contact import (ScenarioNotFoundError,
                                     StrategyExecutionError,
                                     get_adaptation_strategy,
                                     get_current_scenario,
                                     load_scenarios_from_temp, main,
                                     on_survivor_contact, store_action)
from core.utils.paths import ROBOTS_ACTIONS_FILE_NAME

from workspace.src.adaptation_strategy import AdaptationStrategy, Survivor


class TestOnContactHelperFunctions(unittest.TestCase):
    def setUp(self):
        self.active_scenarios = [
            {'name': 'scenario1', 'adaptation_strategy': 'RandomStrategy'},
            {'name': 'scenario2', 'adaptation_strategy': 'RandomStrategy'}]
        self.bad_scenarios = [{'adaptation_strategy': 'RandomStrategy'},
                              {'name2': 'Scenario2', 'adaptation_strategy1': 'RandomStrategy'}]

    def test_get_adaptation_strategy_valid(self):
        # Test get_adaptation_strategy with a valid strategy name
        strategy_instance = get_adaptation_strategy('RandomStrategy', strategy_path)
        assert isinstance(strategy_instance, AdaptationStrategy)

    def test_get_adaptation_strategy_invalid(self):
        # Test get_adaptation_strategy with an invalid strategy name
        with self.assertRaises(StrategyExecutionError):
            get_adaptation_strategy('NonExistentStrategy', strategy_path)

    def test_load_scenarios_from_temp_valid(self):
        # Test load_scenarios_from_temp with a valid filename
        mock_file_content = json.dumps(self.active_scenarios)
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            scenarios = load_scenarios_from_temp("dummy_file.json")
            self.assertEqual(scenarios, self.active_scenarios)

    def test_load_scenarios_from_temp_invalid(self):
        # Test load_scenarios_from_temp with an invalid filename
        # Test the function raises ScenarioNotFoundError when the file does not exist
        with patch("builtins.open", side_effect=IOError):
            with self.assertRaises(ScenarioNotFoundError):
                load_scenarios_from_temp("nonexistent_file.json")

        # Test the function raises ScenarioNotFoundError when the file does not contain proper data
        mock_file_content = json.dumps(self.bad_scenarios)
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            with self.assertRaises(ScenarioNotFoundError):
                load_scenarios_from_temp("dummy_file.json")

    def test_get_current_scenario_found(self):
        # Test that the correct scenario is returned when it exists.
        scenario_name = 'scenario2'
        expected_scenario = {'name': 'scenario2', 'adaptation_strategy': 'RandomStrategy'}
        result = get_current_scenario(scenario_name, self.active_scenarios)
        self.assertEqual(result, expected_scenario)

    def test_get_current_scenario_not_found(self):
        # Test that ScenarioNotFoundError is raised when the scenario does not exist.
        scenario_name = 'nonexistent_scenario'
        with self.assertRaises(ScenarioNotFoundError):
            get_current_scenario(scenario_name, self.active_scenarios)

    def test_store_action(self):
        # Test store_action function for successful action storage
        action = "call-help"
        simulation_id = "scenario1_1"
        expected_file_content = "id,Action\nscenario1_1,call-help\n"

        store_action(action, simulation_id)
        # Verify the content written to the file
        file_path = os.path.join(os.getcwd(), ROBOTS_ACTIONS_FILE_NAME)
        with open(ROBOTS_ACTIONS_FILE_NAME, 'r') as file:
            content = file.read()
        try:
            self.assertEqual(content, expected_file_content)
        finally:
            os.remove(file_path)


class TestOnSurvivorContact(unittest.TestCase):
    def setUp(self):
        self.candidate_helper = Survivor(gender=0, cultural_cluster=0, age=0)
        self.victim = Survivor(gender=0, cultural_cluster=0, age=0)
        self.helper_victim_distance = 1.414
        self.first_responder_victim_distance = 2.0
        self.simulation_id = "scenario1_1"
        self.expected_actions = [AdaptationStrategy.ASK_FOR_HELP_ROBOT_ACTION,
                                 AdaptationStrategy.CALL_STAFF_ROBOT_ACTION]

    def test_on_survivor_contact_success(self):
        # Test the successful execution of on_survivor_contact
        with patch('core.netlogo.on_contact.get_scenario_name') as mock_get_scenario_name, \
             patch('core.netlogo.on_contact.load_scenarios_from_temp') as mock_load_scenarios, \
             patch('core.netlogo.on_contact.get_current_scenario') as mock_get_current_scenario, \
             patch(
                 'core.netlogo.on_contact.get_adaptation_strategy') as mock_get_adaptation_strategy:

            # Setup mocks
            mock_get_scenario_name.return_value = "scenario1"
            mock_load_scenarios.return_value = [
                {'name': "scenario1", 'adaptation_strategy': "RandomStrategy"}]
            mock_get_current_scenario.return_value = {
                'name': "scenario1", 'adaptation_strategy': "RandomStrategy"}
            strategy_instance = MagicMock()
            strategy_instance.get_robot_action.return_value = random.choice(self.expected_actions)
            mock_get_adaptation_strategy.return_value = strategy_instance

            # Execute the test
            action = on_survivor_contact(self.candidate_helper, self.victim,
                                         self.helper_victim_distance,
                                         self.first_responder_victim_distance,
                                         self.simulation_id)

            # Remove the temp file created by the function
            file_path = os.path.join(os.getcwd(), ROBOTS_ACTIONS_FILE_NAME)
            os.remove(file_path)
            self.assertIn(action, self.expected_actions)

    def test_main_in_on_contact(self):
        # Test the main function in on_contact.py
        simulated_args = ['on_contact.py', 'sim1', '0', '0', '0', '0', '0', '0', '2.4', '1.2']

        with patch('sys.argv', simulated_args), \
                patch('core.netlogo.on_contact.on_survivor_contact') as mock_on_survivor_contact, \
                patch('builtins.print') as mock_print:

            mock_on_survivor_contact.return_value = random.choice(self.expected_actions)
            main()

            # Assert there is only one print call and it is in the expected actions
            self.assertEqual(len(mock_print.call_args_list), 1,
                             "Expected 'print' to be called exactly once.")
            printed_output = mock_print.call_args_list[0][0][0]
            self.assertIn(printed_output, self.expected_actions,
                          "Printed output '{}' not in expected actions.".format(printed_output))


if __name__ == '__main__':
    unittest.main()
