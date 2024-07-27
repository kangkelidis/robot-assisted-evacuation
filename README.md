# The Sousa Toolkit: A Socially-Aware Evaluation of Evacuation Support Systems

This project provides a container-based simulation environment for the IMPACT+ NetLogo model. The Sousa Toolkit allows users to configure and run simulations of different evacuation scenarios, analyze the results, and compare the effectiveness of various adaptation strategies.

See [Video]() showing installation and usage.

<br>

## Table of contents
- **[`Installation`](#installation-10-minutes)**
- **[`Configuration`](#configuration-options)**  
    - **[`Basic`](#basic-parameters)** 
    - **[`Scenario`](#scenario-parameters)** 
    - **[`Combinations`](#combining-parameters)** 
    - **[`Rooms`](#room-types)** 
- **[`Usage`](#usage)** 
    - **[`Results`](#results)** 
    - **[`Examples`](#examples)** 
- **[`Strategies`](#strategies)** 
    - **[`Creating New Strategies`](#creating-new-strategies)** 
- **[`Modules`](#modules)**
- **[`Help`](#help)** 
- **[`License`](#license-information)** 

<br>

## Installation (~10 minutes)

To use the Sousa Toolkit, you'll need to have Docker installed on your machine. <br>
Follow the instructions on the [Get Docker](https://docs.docker.com/get-docker/) | [Docker Docs](https://docs.docker.com/) website to install Docker.

<details>

<summary>Build docker image on your Machine (Recommended)</summary>

<br>

To build the image from source open your terminal, ensure that you are at the **robot-assisted-evacuation** directory and run:
```
chmod +x ./build-docker-container.sh

./build-docker-container.sh
```
> **_NOTE:_** Make sure docker engine is running

</details>

<details>

<summary>Download image from Docker Hub</summary>

<br>    

To download the docker image from the Docker Hub, you need to log in with a valid Docker Hub account. If you don't have an account, you can create one at [Docker Hub](https://app.docker.com/signup?).

Steps to Log In to Docker Hub:
1. Create a Docker Hub Account (if you don't have one):

    - Go to [Docker Hub](https://hub.docker.com/).
    - Click on "Sign Up" and follow the instructions to create an account.
3. Log in to Docker Hub: Open your terminal and run:
    ```
    docker login
    ```
    > **_NOTE:_** Make sure docker engine is running

    Enter your Docker Hub username and password when prompted.

Then Pull the Docker Image:
```
docker pull alexandroskangkelidis/robot-assisted-evacuation:v1.0
```
</details>

<br>

---

<br>

## Configuration Options
The [config.json](./workspace/config.json) contains parameters that can be adjusted to configure the simulations.

### Basic Parameters
| Parameter | Values | Description |
|---|---|---|
| `loadConfigFrom` | string, null | Use null to use this file  |
| `netlogoModeName` | string | The NetLogo model to be used for the simulations, must be in the src/netlogo folder |
| `targetScenarioForAnalysis` | string | The scenario that will be used for the analysis |
| `maxSimulationTime` | Any positive integer | The maximum time in seconds a simulation can run |
---

<br>

### Scenario Parameters
The `scenarioParams` section contains global parameters that are used for all simulations. These parameters can be overridden by specifying the same parameter in the `simulationScenarios` section.

| Parameter | Values | Description |
|---|---|---|
| `seed`                | 0, [-2147483648, 2147483647] | Generates the seed for simulations. Non-zero for consistent seeds, zero for random seeds. |
| `netlogo_seed`        | null, [-2147483648, 2147483647] | The actual seed to be used by NetLogo. Used to repeat a simulation. Use null to auto generate |
| `numOfSamples`        | Any positive integer | Number of simulations to run for each scenario. |
| `numOfRobots`         | Any positive integer | Number of robots. |
| `numOfPassengers`     | Any positive integer | Number passengers. |
| `numOfStaff`          | Any positive integer | Number of staff members. |
| `fallLength`          | Any positive integer | Time steps a passenger remains fallen. |
| `fallChance`          | [0.0, 100.0] | Probability that a passenger will fall during evacuation. |
| `robotPersuasionFactor` | Any number | A multiplier to the helping chance that is used to determine whether a zero-responder will accept to help a fallen victim, when asked by the robot. |
| `maxNetlogoTicks`     | Any positive integer | Maximum number of time steps the simulation can run. |
| `roomType`| [0, 8] | Type of room being simulated. |
| `enableVideo`| false / true,<br> A list of indices,<br> A positive integer | Enable video for all simulations if true or 'all'. Enable video only for the specified simulations if a list of indices is provided (e.g., [0, 2, 5]). Enable video for n random simulations if a positive integer is provided. |
| **Scenario Specific** |
| `name` | string | A name for the scenario, it is required and must be unique |
| `description` | string | A description for the scenario |
| `adaptationStrategy` | string | The name of the strategy to use, a python file containing a strategy class with the same name must be in the strategies folder. |
| `enabled` | true / false | Whether to use the scenario in the experiment. |
---

<br>

### Combining Parameters

The application has the ability to use lists and ranges to create combinations of parameters. It will automatically generate all possible combinations of the provided parameters and run `num_of_samples` simulations for each combination.

For example, given the following configuration:
```json
<!-- Use a list -->
"numOfStaff": [2, 10],

<!-- Use a range of values -->
"fallChance": {
    "start": 0.05,
    "end": 1,
    "step": 0.1
},
"num_of_samples": 5
```
The program will create combinations of numOfStaff and fallChance values, and for each combination, it will run 5 simulations.
- numOfStaff = 2 and fallChance = 0.05
- numOfStaff = 2 and fallChance = 0.15
- ...
- numOfStaff = 10 and fallChance = 0.95

For each of these combinations, the program will run the specified number of simulations (`num_of_samples`). For each combination pair, a plot will be generated comparing the impact on the number of evacuation ticks.



---
### Room Types
There are 8 different room types that the evacuation simulation can use.
The PNGs for the rooms are located in `workspace/netlogo/rooms`

| Type | Filename                                         |
|------|--------------------------------------------------|
| 0    | room_square_2doors_up_down.png                   |
| 1    | room_square_4doors_main_down.png                 |
| 2    | room_square_2doors_left_right.png                |
| 3    | room_square_4doors_main_left.png                 |
| 4    | room_rectangle_2doors_left_right.png             |
| 5    | room_rectangle_2doors_up_down.png                |
| 6    | room_rectangle_4doors_main_down.png              |
| 7    | room_rectangle_4doors_main_left.png              |
| 8    | room_square_2doors_left_right_barriers.png       |

<br>

---

<br>

## Usage

To start the application, ensure that you are at **robot-assisted-evacuation** directory and run:
```
./run-container.sh
```
> **_NOTE:_**
>Make sure you use the `chmod +x` command to add execute permissions to the file and avoid the "permission denied" error.

If you downloaded the image from Docker Hub instead of building it locally, add `hub` after the script name. For example:
```
./run-container.sh hub
```

To only analysis the results of an experiment saved in a folder use:
```
./run-container.sh [hub] --analyse FOLDER
``` 
Replace FOLDER with the folder name, located in the results directory.
<br>

If you modify any part of the code you might need to rebuild the docker image before running it, run:
```
./build-docker-image.sh
```
or just run:
```
./build-and-run.sh
```

<br>

### Results

The application generates a `results` folder to store the output of the simulations. Each experiment's results are stored in a subfolder named using a timestamp. This subfolder contains the following:

1. **Data Folder**: Contains CSV files with detailed results and metrics:
    - `experiment_data.csv`: Contains all the results and information for each simulation.
    - `scenario_metrics.csv`: Contains the metrics for each scenario.
    - `scenario_processed_data.csv`: Contains the evacuation ticks per scenario.
    - `strategy_metrics.csv`: Contains the metrics for each strategy.
    - `strategy_processed_data.csv`: Contains the evacuation ticks per strategy.

2. **Img Folder**: Contains various plots:
    - Violin plots for each scenario.
    - Violin plots for each strategy.
    - Robots actions plot.
    - Plots for each pair of parameter combinations against the evacuation ticks.

3. **Video Folder**: Contains any videos created during the simulations.

4. **Config File**: `config.json` contains the configurations used to create the experiment.

5. **Hypothesis Test File**: `hypothesis_test.txt` contains the results of the statistical analysis.

if you need to delete all the results folders run:
```
./clear-results.sh
```

#### Examples
The `examples` folder contains several example simulation experiment that demonstrate the capabilities of the Sousa Toolkit.

<br>

---

<br>

## Strategies

The application includes basic predefined strategies for the SAR robot. Each strategy defines the robot's action when encountering a fallen victim:
- **`RandomStrategy.py`**: Randomly chooses between asking for help from a passenger or calling for staff assistance.
- **`OptimalStrategy.py`**: A baseline strategy, uses the help matrix from the IMPACT+ model to predict if a zero responder will accept to offer help.
- **`AlwaysCallStaffStrategy.py`**: Always calls for a staff member to assist the victim.
- **`AlwaysAskHelpStrategy.py`**: Always asks for help from a passenger.

Each strategy is defined in a python file saved in the `strategies` folder and inherits from the `AdaptationStrategy` base class in `adaptation_strategy.py` file.

### Creating New Strategies

To create a new strategy, follow these steps:

1. **Create a New Python File**: In the strategies folder, create a new Python file. The name of the file (minus the .py extension) will be the name of the strategy. For example, if you want to create a strategy named `NewStrategy`, create a file named `NewStrategy.py` in the strategies folder.

2. **Import the Base Class**: In your new strategy file, import the `AdaptationStrategy` base class from `adaptation_strategy.py`.
```python
from src.adaptation_strategy import AdaptationStrategy, Survivor
```
3. **Define the Strategy Class**: Create a new class with exactly the same name as the strategy and file name. This class should inherit from `AdaptationStrategy`.
```python
class NewStrategy(AdaptationStrategy):
    def get_robot_action(self,
                         simulation_id: str,
                         candidate_helper: Survivor,
                         victim: Survivor,
                         helper_victim_distance: float,
                         first_responder_victim_distance: float) -> str:
        # Implement the logic for the strategy here
        pass
```
4. **Implement the get_robot_action Method**: The `get_robot_action` method should contain the logic for how the robots will behave during the evacuation. This method will be called each time the robot encounters a fallen victim and must decide between asking for help from a nearby zero responder or a member of staff.
```python
def get_robot_action(self,
                     simulation_id: str,
                     candidate_helper: Survivor,
                     victim: Survivor,
                     helper_victim_distance: float,
                     first_responder_victim_distance: float) -> str:
    # Example logic for the new strategy
    if helper_victim_distance < first_responder_victim_distance:
        return self.ASK_FOR_HELP_ROBOT_ACTION
    else:
        return self.CALL_STAFF_ROBOT_ACTION
```
5. **Using the Strategy**: To use a strategy, simply specify the name of the strategy in the `adaptationStrategy` field of a scenario in the `config.json` file:
```json
{
    "name": "new-strategy",
    "description": "A new Strategy.",
    "adaptationStrategy": "NewStrategy",
    "enabled": true
}
```

<br>

---

<br>

## Modules

An overview of the main modules. 

- **`simulation.py`**: Defines the classes and functions necessary for executing the NetLogo model simulations.
- **`simulation_manager.py`**: Manages the parallel execution of simulations in NetLogo.
- **`server.py`**: A simple flask server, used to communicate with the NetLogo simulations. 
- **`results_analysis.py`**: Responsible for analysing and plotting the results of the simulation experiments.
- **`load_config.py`**: Responsible for loading and checking the JSON configuration file.
- **`batch_run.py`**: Contains a methods to run a scenario using a different combination of parameters.
- **`adaptation_strategy.py`**: Contains the base class for adaptation strategies, which are used in the simulation to determine the robot's actions.


<br>

---

<br>

## Help

Feel free to open an issue if something is not working as expected.

[![GitHub Issues](https://img.shields.io/badge/GitHub-Issues-green?logo=github)](https://github.com/alekosomegas/robot-assisted-evacuation/issues)

<br>

---

<br>

## License Information

This project is licensed under the terms of the MIT license. Please refer to [LICENSE](LICENSE) for the full 
terms.

As with all Docker images, these may contain other software which may be under other licenses (such as Bash, etc. from 
the base distribution, along with any direct or indirect dependencies of the primary software being contained). 
It is the image user’s responsibility to ensure that any use of this image complies with any relevant licenses for all 
software contained within.

<br>
<p align="right"><a href="#top"><img src="https://cdn-icons-png.flaticon.com/512/892/892692.png" height="40px"></a></p>