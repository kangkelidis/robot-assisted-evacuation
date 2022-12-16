docker rm -f evacuation-simulation
docker run --name evacuation-simulation -v "${PWD}"/results:/home/results robot-assisted-evacuation