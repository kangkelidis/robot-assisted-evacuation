docker rm -f evacuation-simulation
# docker run --name evacuation-simulation -v "${PWD}"/workspace:/home/workspace robot-assisted-evacuation
docker run --platform linux/amd64 --name evacuation-simulation -v "${PWD}"/workspace:/home/workspace robot-assisted-evacuation
# Deleting content from the frame directory
rm -rf workspace/frames/*
python workspace/cleanup.py
