#!/usr/bin/env python
"""Check wrist_roll calibration and suggest fixes"""

import json
from lerobot.robots.so101_follower.config_so101_follower import SO101FollowerConfig
from lerobot.robots.so101_follower.so101_follower import SO101Follower

# Load calibration
calib_path = "/home/thor/.cache/huggingface/lerobot/calibration/robots/so101_follower/thor_follower_arm.json"
with open(calib_path, 'r') as f:
    calib = json.load(f)

wrist_calib = calib.get("wrist_roll", {})
print("Current wrist_roll calibration:")
print(f"  range_min: {wrist_calib.get('range_min')}")
print(f"  range_max: {wrist_calib.get('range_max')}")
print(f"  homing_offset: {wrist_calib.get('homing_offset')}")
print()

# Connect and check current position
robot_cfg = SO101FollowerConfig(port="/dev/ttyACM0", id="thor_follower_arm", cameras={})
robot = SO101Follower(robot_cfg)
robot.connect()

obs = robot.get_observation()
wrist_pos_norm = obs.get("wrist_roll.pos", 0)
print(f"Current wrist_roll normalized position: {wrist_pos_norm:.2f}")

# Read raw position
raw_pos = robot.bus.read("Present_Position", "wrist_roll", normalize=False)
print(f"Current wrist_roll raw position: {raw_pos}")

# Calculate what normalized position should be at center
range_min = wrist_calib.get('range_min', 0)
range_max = wrist_calib.get('range_max', 4095)
center_raw = (range_min + range_max) / 2
print(f"\nCenter raw position: {center_raw:.0f}")

# Check if wrist is at an extreme
if abs(wrist_pos_norm) >= 90:
    print(f"\n⚠️  PROBLEM: wrist_roll is at extreme position ({wrist_pos_norm:.2f})")
    print("   This causes the model to rotate 180° to reach other orientations.")
    print("\n💡 SOLUTION:")
    print("   1. Manually rotate wrist_roll to center position (normalized ~0)")
    print("   2. Or recalibrate with wrist_roll at center")
    print("   3. Or add logic to choose shortest rotation path")
else:
    print(f"\n✅ wrist_roll is in reasonable range ({wrist_pos_norm:.2f})")

robot.disconnect()

