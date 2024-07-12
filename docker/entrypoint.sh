#!/bin/bash
# Activate the Conda environment
source /opt/conda/etc/profile.d/conda.sh
conda activate robot-assisted-evacuation
exec python -u /home/workspace/server.py &
exec python -u /home/workspace/start.py "$@"