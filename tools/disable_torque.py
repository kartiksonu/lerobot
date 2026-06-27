#!/usr/bin/env python
"""Disable torque on all motors to allow manual movement"""

from lerobot.robots.so101_follower.config_so101_follower import SO101FollowerConfig
from lerobot.robots.so101_follower.so101_follower import SO101Follower

robot_cfg = SO101FollowerConfig(
    port="/dev/ttyACM0",
    id="thor_follower_arm",
    cameras={}
    # Note: We disable torque manually, but disconnect() will also try to disable
    # This is safe - disabling twice doesn't hurt
)

print("Connecting...")
robot = SO101Follower(robot_cfg)
robot.connect()
print("✅ Connected!\n")

print("Disabling torque on all motors...")
robot.bus.disable_torque()
print("✅ Torque disabled on all motors!")
print("\nYou can now manually move the robot joints.")
print("Press Enter to disconnect...")
input()

# Disconnect (will try to disable torque again, but that's safe)
robot.disconnect()
print("✅ Disconnected")

