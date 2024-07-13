#!/bin/bash
source /opt/conda/etc/profile.d/conda.sh
conda activate robot-assisted-evacuation

# RE to hide logs from Java
PATTERN="(INFO|WARNING|Warning:)|[A-Z][a-z]{2} [0-9]{1,2}, [0-9]{4} [0-9]{1,2}:[0-9]{2}:[0-9]{2} (AM|PM)"

exec python -u /home/workspace/server.py 2>&1 | grep -Ev "$PATTERN" &
exec python -u /home/workspace/start.py "$@" 2>&1 | grep -Ev "$PATTERN"