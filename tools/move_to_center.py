#!/usr/bin/env python
"""Move robot to center/safe position when stuck"""

import time
from lerobot.robots.so101_follower.config_so101_follower import SO101FollowerConfig
from lerobot.robots.so101_follower.so101_follower import SO101Follower

def move_to_center():
    robot_cfg = SO101FollowerConfig(port="/dev/ttyACM0", id="thor_follower_arm", cameras={})
    robot = SO101Follower(robot_cfg)

    print("Connecting...")
    robot.connect()
    print("✅ Connected!\n")

    # Get current positions
    obs = robot.get_observation()
    print("Current positions:")
    current_positions = {}
    for motor_name in ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]:
        key = f"{motor_name}.pos"
        pos = obs.get(key, 0.0)
        current_positions[motor_name] = pos
        print(f"  {motor_name:20s}: {pos:8.2f}")

    print("\nTarget center positions:")
    # Target positions (middle of range, safe positions)
    target_positions = {
        "shoulder_pan": 0.0,
        "shoulder_lift": 0.0,
        "elbow_flex": 0.0,
        "wrist_flex": 0.0,
        "wrist_roll": 0.0,
        "gripper": 10.0,  # Slightly open
    }

    for motor_name, target in target_positions.items():
        current = current_positions[motor_name]
        diff = abs(target - current)
        print(f"  {motor_name:20s}: {target:8.2f} (current: {current:8.2f}, diff: {diff:8.2f})")

    print("\n⚠️  Moving robot to center positions in 2 seconds...")
    print("   Press Ctrl+C to cancel...")
    try:
        time.sleep(2)
    except KeyboardInterrupt:
        print("\n❌ Cancelled")
        robot.disconnect()
        return

    print("\nMoving to center positions (gradually)...")

    # Move gradually in steps
    num_steps = 50
    for step in range(num_steps):
        progress = (step + 1) / num_steps
        action = {}

        for motor_name in target_positions.keys():
            current = current_positions[motor_name]
            target = target_positions[motor_name]
            # Interpolate between current and target
            intermediate = current + (target - current) * progress
            action[f"{motor_name}.pos"] = intermediate

        try:
            robot.send_action(action)
            if step % 10 == 0:
                print(f"  Step {step+1}/{num_steps}...")
            time.sleep(0.05)  # Small delay between steps
        except Exception as e:
            print(f"  ⚠️  Error at step {step+1}: {e}")
            break

    # Final check
    print("\nFinal positions:")
    obs = robot.get_observation()
    for motor_name in target_positions.keys():
        key = f"{motor_name}.pos"
        final_pos = obs.get(key, 0.0)
        target = target_positions[motor_name]
        diff = abs(final_pos - target)
        status = "✅" if diff < 5.0 else "⚠️"
        print(f"  {status} {motor_name:20s}: {final_pos:8.2f} (target: {target:8.2f})")

    print("\n✅ Movement complete!")
    robot.disconnect()

if __name__ == "__main__":
    move_to_center()
