#!/bin/bash
export DISPLAY=:1
export XAUTHORITY=/run/user/1000/gdm/Xauthority

# Ensure we are in the right directory or use absolute paths
cd /home/thor/lerobot

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    source .venv/bin/activate
fi

echo "Starting Teleoperation with Camera Feed..."
echo "Robot Port: /dev/ttyACM0"
echo "Searching for Cameras..."

python tools/teleoperate_with_camera.py
