#!/bin/bash
export DISPLAY=:1
export XAUTHORITY=/run/user/1000/gdm/Xauthority

# Ensure we are in the right directory
cd /home/thor/lerobot

# Activate virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    source .venv/bin/activate
fi

echo "Starting LeRobot Rerun Visualization..."
echo "Web Viewer: http://10.0.0.103:9090"
echo "WS Endpoint: ws://10.0.0.103:9087"

python tools/visualize_robot.py "$@"






