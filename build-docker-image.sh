#!/bin/bash
cd docker || exit
docker buildx build --platform linux/amd64 --tag robot-assisted-evacuation . # > build_output.txt 2>&1