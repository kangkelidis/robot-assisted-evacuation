# The Sousa Toolkit: A Socially-Aware Evaluation of Evacuation Support Systems

A short description of the container. What is this for, who is this for, why should someone 
continue to read this README.

## Install and Setup

List any prerequisities, setup options and configuation details.

* [Install Docker on your machine.](https://docs.docker.com/get-docker/)
* Then, either run the pre-built image we’ve provided on Docker Hub, or build the image yourself from the source code.
* This container was tested on 18.09.1 (for example)

## Usage

List all parameters.


### Configuration Options
The config.json contains parameters that can be adjusted by the user.

`scenarioParams` contains global parameters that are used for all simulations. These  parameters can be overridden by specifying the same parameter in the `simulationScenarios` .

- `numOfSamples`: The number of simulations to run for each scenario.
- `numOfRobots`: The number of robots.
- `numOfPassengers`: The number of passengers.
- `numOfStaff`: The number of staff members.
- `fallLength`: The number of time steps a passenger remains fallen.
- `fallChance`: The probability that a passenger will fall during the evacuation. [0-100]
- `allowStaffSupport`: Whether staff members can provide support to passengers.
- `allowPassengerSupport`: Whether passengers can provide support to each other.
- `maxNetlogoTicks`: The maximum number of time steps the simulation can run.
- `roomType`: The type of room being simulated. [0-8]
- `enableVideo`: Whether to generate a gif video of the simulation.


#### Room Types
The PNGs for the rooms are located in `core/netlogo/rooms`

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




## Working Together

Include information such as:

* Where to Get Help
* Where to File Issues
* Image Updates
* Maintained By

# License Information

This project is licensed under the terms of the MIT license. Please refer to [LICENSE](LICENSE) for the full 
terms.

As with all Docker images, these may contain other software which may be under other licenses (such as Bash, etc. from 
the base distribution, along with any direct or indirect dependencies of the primary software being contained). 
It is the image user’s responsibility to ensure that any use of this image complies with any relevant licenses for all 
software contained within.