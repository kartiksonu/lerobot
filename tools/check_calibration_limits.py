#!/usr/bin/env python
"""Check if motors at limits are due to calibration issues"""

import json
from lerobot.robots.so101_follower.config_so101_follower import SO101FollowerConfig
from lerobot.robots.so101_follower.so101_follower import SO101Follower

def check_calibration_limits():
    # Load calibration
    calib_path = "/home/thor/.cache/huggingface/lerobot/calibration/robots/so101_follower/thor_follower_arm.json"
    try:
        with open(calib_path, 'r') as f:
            calib = json.load(f)
    except FileNotFoundError:
        print(f"❌ Calibration file not found: {calib_path}")
        return

    print("=" * 80)
    print("CALIBRATION LIMIT ANALYSIS")
    print("=" * 80)

    # Connect to robot
    robot_cfg = SO101FollowerConfig(port="/dev/ttyACM0", id="thor_follower_arm", cameras={})
    robot = SO101Follower(robot_cfg)

    print("Connecting...")
    robot.connect()
    print("✅ Connected!\n")

    # Get current observation
    obs = robot.get_observation()

    motor_names = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]

    print("Motor Status vs Calibration Ranges:")
    print("-" * 80)

    issues = []

    for motor_name in motor_names:
        # Get normalized position
        norm_pos = obs.get(f"{motor_name}.pos", 0.0)

        # Get raw position
        try:
            raw_pos = robot.bus.read("Present_Position", motor_name, normalize=False)
        except Exception as e:
            print(f"❌ {motor_name}: Cannot read raw position: {e}")
            continue

        # Get calibration
        motor_calib = calib.get(motor_name, {})
        range_min = motor_calib.get('range_min', 0)
        range_max = motor_calib.get('range_max', 4095)
        homing_offset = motor_calib.get('homing_offset', 0)

        # Calculate what normalized position should be
        # Normalized = (Raw - Homing_Offset - Range_Min) / (Range_Max - Range_Min) * 200 - 100
        # Or simpler: the calibration defines the mapping

        # Check if at limit
        is_at_limit = abs(norm_pos) >= 99.0

        # Calculate percentage through calibration range
        if range_max > range_min:
            range_size = range_max - range_min
            position_in_range = raw_pos - range_min
            percent_through = (position_in_range / range_size) * 100
        else:
            percent_through = 50.0  # Unknown

        print(f"\n{motor_name.upper()}:")
        print(f"  Normalized position: {norm_pos:.2f}")
        print(f"  Raw position:        {raw_pos}")
        print(f"  Calibration range:   {range_min} to {range_max} (size: {range_max - range_min})")
        print(f"  Homing offset:       {homing_offset}")
        print(f"  Position in range:   {percent_through:.1f}%")

        if is_at_limit:
            if norm_pos >= 99.0:
                print(f"  ⚠️  AT UPPER LIMIT (normalized: {norm_pos:.2f})")
                # Check if raw position is actually at range_max
                if raw_pos >= range_max - 10:  # Within 10 units of max
                    print(f"     → Raw position ({raw_pos}) is at/near calibration max ({range_max})")
                    print(f"     → This is a CALIBRATION ISSUE: range_max may be too low")
                    issues.append(f"{motor_name}: At upper limit, raw={raw_pos}, calib_max={range_max}")
                else:
                    print(f"     → Raw position ({raw_pos}) is NOT at calibration max ({range_max})")
                    print(f"     → This is a CALIBRATION ISSUE: mapping is incorrect")
                    issues.append(f"{motor_name}: At normalized limit but raw not at calib max")
            else:  # norm_pos <= -99.0
                print(f"  ⚠️  AT LOWER LIMIT (normalized: {norm_pos:.2f})")
                # Check if raw position is actually at range_min
                if raw_pos <= range_min + 10:  # Within 10 units of min
                    print(f"     → Raw position ({raw_pos}) is at/near calibration min ({range_min})")
                    print(f"     → This is a CALIBRATION ISSUE: range_min may be too high")
                    issues.append(f"{motor_name}: At lower limit, raw={raw_pos}, calib_min={range_min}")
                else:
                    print(f"     → Raw position ({raw_pos}) is NOT at calibration min ({range_min})")
                    print(f"     → This is a CALIBRATION ISSUE: mapping is incorrect")
                    issues.append(f"{motor_name}: At normalized limit but raw not at calib min")
        else:
            print(f"  ✅ Within safe range")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if issues:
        print("⚠️  CALIBRATION ISSUES DETECTED:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n💡 SOLUTION:")
        print("   1. Manually move the affected motors to center positions")
        print("   2. Recalibrate: uv run lerobot-calibrate --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=thor_follower_arm")
        print("   3. Ensure motors are in middle of their physical range during calibration")
    else:
        print("✅ No calibration issues detected")
        print("   Motors at limits are physically at their mechanical limits")
        print("   Manually move them away from limits before running inference")

    robot.disconnect()

if __name__ == "__main__":
    check_calibration_limits()
