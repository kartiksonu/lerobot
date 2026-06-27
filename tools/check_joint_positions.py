#!/usr/bin/env python
"""Check current joint positions and calibration status"""

from lerobot.robots.so101_follower.config_so101_follower import SO101FollowerConfig
from lerobot.robots.so101_follower.so101_follower import SO101Follower

robot_cfg = SO101FollowerConfig(port="/dev/ttyACM0", id="thor_follower_arm", cameras={})
robot = SO101Follower(robot_cfg)

print("Connecting...")
robot.connect()
print("✅ Connected!\n")

# Get current observation
obs = robot.get_observation()

print("Current Joint Positions (Normalized):")
print("-" * 50)
for key in sorted(obs.keys()):
    if key.endswith(".pos"):
        motor_name = key.replace(".pos", "")
        value = obs[key]
        print(f"{motor_name:20s}: {value:8.2f}")

print("\n" + "=" * 50)
print("Calibration Status:")
print("-" * 50)

# Check if joints are at limits
at_limits = []
for motor_name in robot.bus.motors:
    pos = obs[f"{motor_name}.pos"]
    if abs(pos) >= 99.9:  # Close to -100 or +100
        at_limits.append((motor_name, pos))
        print(f"⚠️  {motor_name:20s}: {pos:8.2f} (AT LIMIT!)")
    else:
        print(f"✅ {motor_name:20s}: {pos:8.2f} (OK)")

if at_limits:
    print(f"\n⚠️  WARNING: {len(at_limits)} joint(s) at calibration limits!")
    print("   These joints may cause erratic behavior.")
    print("   Consider moving them to center position or recalibrating.")
else:
    print("\n✅ All joints within safe ranges")

robot.disconnect()

