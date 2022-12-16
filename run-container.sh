docker rm -f evacuation-simulation
docker run --name evacuation-simulation -v "${PWD}"/workspace:/home/workspace robot-assisted-evacuation