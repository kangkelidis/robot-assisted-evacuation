docker rm -f evacuation-simulation
docker run --platform linux/amd64 --name evacuation-simulation -v "${PWD}"/workspace:/home/workspace robot-assisted-evacuation
rm -rf workspace/results/frames/*
python workspace/core/utils/cleanup.py