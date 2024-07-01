#!/bin/bash
cd docker || exit
docker buildx build --platform linux/amd64 --tag robot-assisted-evacuation .