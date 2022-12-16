docker rm -f evacuation-simulation
docker run -dit --name evacuation-simulation -v results:/home/results robot-assisted-evacuation