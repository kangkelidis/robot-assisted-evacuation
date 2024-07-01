#!/bin/bash
docker rm -f evacuation-simulation
docker run --platform linux/amd64 --name evacuation-simulation -it -v "${PWD}"/workspace:/home/workspace robot-assisted-evacuation
find workspace/results/frames/ -type f -exec rm {} +
python workspace/core/utils/cleanup.py