#!/bin/bash
docker rm -f evacuation-simulation

image="robot-assisted-evacuation"
args=()
for arg in "$@"; do
    if [ "$arg" == "hub" ]; then
        image="alexandroskangkelidis/robot-assisted-evacuation:v1.0"
    else
        args+=("$arg")
    fi
done

docker run --platform linux/amd64 --name evacuation-simulation -it -v "${PWD}"/workspace:/home/workspace $image "${args[@]}"
find workspace/results/frames/ -type f -exec rm {} +