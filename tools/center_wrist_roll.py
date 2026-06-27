#!/usr/bin/env python
"""Move wrist_roll to center position (normalized ~0)"""

from lerobot.robots.so101_follower.config_so101_follower import SO101FollowerConfig
from lerobot.robots.so101_follower.so101_follower import SO101Follower
import time

robot_cfg = SO101FollowerConfig(port="/dev/ttyACM0", id="thor_follower_arm", cameras={})
robot = SO101Follower(robot_cfg)

print("Connecting...")
robot.connect()
print("✅ Connected!\n")

# Get current position
obs = robot.get_observation()
current_wrist = obs.get("wrist_roll.pos", 0)
print(f"Current wrist_roll position: {current_wrist:.2f}")

if abs(current_wrist) < 5.0:
    print("✅ wrist_roll is already centered!")
    robot.disconnect()
    exit(0)

print(f"\nMoving wrist_roll to center (target: 0.0)...")
print("This will move gradually to avoid sudden movements.\n")

# Move gradually to center
target = 0.0
step_size = 2.0  # Move 2 units at a time
steps = int(abs(current_wrist) / step_size) + 1

for i in range(steps):
    # Calculate intermediate target
    progress = (i + 1) / steps
    intermediate_target = current_wrist * (1 - progress)

    action = {"wrist_roll.pos": intermediate_target}
    robot.send_action(action)

    # Check actual position
    obs = robot.get_observation()
    actual_pos = obs.get("wrist_roll.pos", 0)

    print(f"Step {i+1}/{steps}: Target={intermediate_target:.2f}, Actual={actual_pos:.2f}")
    time.sleep(0.1)

# Final check
obs = robot.get_observation()
final_pos = obs.get("wrist_roll.pos", 0)
print(f"\n✅ Final wrist_roll position: {final_pos:.2f}")

if abs(final_pos) < 10.0:
    print("✅ wrist_roll is now centered! Safe to run inference.")
else:
    print(f"⚠️  wrist_roll is still at {final_pos:.2f}. May need manual adjustment.")

robot.disconnect()

