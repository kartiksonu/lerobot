#!/usr/bin/env python
"""Test motor connectivity and activation by moving each motor a small amount"""

import time
from lerobot.robots.so101_follower.config_so101_follower import SO101FollowerConfig
from lerobot.robots.so101_follower.so101_follower import SO101Follower

def test_motor_movement():
    robot_cfg = SO101FollowerConfig(port="/dev/ttyACM0", id="thor_follower_arm", cameras={})
    robot = SO101Follower(robot_cfg)

    print("Connecting...")
    robot.connect()
    print("✅ Connected!\n")

    # Motor name mapping
    motor_names = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]

    # Very small movement amount (normalized units)
    # For joints: 1.0 unit is a very small movement
    # For gripper: 2.0 units is a very small movement
    movement_amount = {
        "shoulder_pan": 1.0,
        "shoulder_lift": 1.0,
        "elbow_flex": 1.0,
        "wrist_flex": 1.0,
        "wrist_roll": 1.0,
        "gripper": 2.0,  # Gripper needs slightly more to be detectable
    }

    print("=" * 80)
    print("MOTOR MOVEMENT TEST")
    print("=" * 80)
    print("This will move each motor a very small amount to verify connectivity.\n")

    # Get initial positions
    print("Reading initial positions...")
    initial_obs = robot.get_observation()
    initial_positions = {}
    for motor_name in motor_names:
        key = f"{motor_name}.pos"
        initial_positions[motor_name] = initial_obs.get(key, 0.0)
        print(f"  {motor_name}: {initial_positions[motor_name]:.2f}")
    print()

    results = {}

    for motor_name in motor_names:
        motor_id = robot.bus.motors[motor_name].id
        print(f"Testing {motor_name.upper()} (ID: {motor_id})...")

        try:
            # Get current position
            current_pos = initial_positions[motor_name]
            move_amount = movement_amount[motor_name]

            # Check if motor is at limit
            is_at_limit = False
            if motor_name == "gripper":
                is_at_limit = (current_pos >= 99.0)
            else:
                is_at_limit = (abs(current_pos) >= 99.0)

            # Calculate target position (small movement)
            if motor_name == "gripper":
                if is_at_limit:
                    # At upper limit, move down
                    target_pos = max(0.0, current_pos - move_amount)
                else:
                    # Move slightly open (positive direction)
                    target_pos = min(100.0, current_pos + move_amount)
            else:
                # Joints: check which limit
                if current_pos >= 99.0:
                    # At upper limit, move down
                    target_pos = max(-100.0, current_pos - move_amount)
                elif current_pos <= -99.0:
                    # At lower limit, move up
                    target_pos = min(100.0, current_pos + move_amount)
                else:
                    # Not at limit, move in positive direction
                    target_pos = min(100.0, current_pos + move_amount)

            move_dir = "+" if target_pos > current_pos else "-"
            move_abs = abs(target_pos - current_pos)
            limit_note = " [AT LIMIT]" if is_at_limit else ""
            print(f"  Current: {current_pos:.2f} → Target: {target_pos:.2f} (move: {move_dir}{move_abs:.2f}){limit_note}")

            # Send movement command
            action = {f"{motor_name}.pos": target_pos}
            robot.send_action(action)

            # Wait for movement
            time.sleep(0.3)

            # Read new position (with error handling)
            try:
                obs = robot.get_observation()
                new_pos = obs.get(f"{motor_name}.pos", current_pos)
            except Exception as e:
                print(f"  ⚠️  WARNING: Could not read position after movement: {e}")
                results[motor_name] = "⚠️  READ_ERROR"
                continue

            actual_movement = new_pos - current_pos

            print(f"  New position: {new_pos:.2f} (moved: {actual_movement:+.2f})")

            # Check if motor actually moved
            if is_at_limit and abs(actual_movement) < 0.1:
                # Motor is at limit and can't move - this is expected
                print(f"  ⚠️  AT LIMIT: Motor is at limit and cannot move further")
                results[motor_name] = "⚠️  AT_LIMIT"
            elif abs(actual_movement) >= 0.1:  # At least 0.1 units of movement
                print(f"  ✅ SUCCESS: Motor responded and moved")
                results[motor_name] = "✅ PASS"
            else:
                print(f"  ⚠️  WARNING: Motor may not have moved (movement < 0.1 units)")
                results[motor_name] = "⚠️  WEAK"

            # Move back to original position
            print(f"  Returning to original position ({current_pos:.2f})...")
            action = {f"{motor_name}.pos": current_pos}
            robot.send_action(action)
            time.sleep(0.3)

            # Verify return (with error handling)
            try:
                obs = robot.get_observation()
                final_pos = obs.get(f"{motor_name}.pos", current_pos)
                if abs(final_pos - current_pos) < 1.0:
                    print(f"  ✅ Returned to {final_pos:.2f}")
                else:
                    print(f"  ⚠️  Position after return: {final_pos:.2f} (expected: {current_pos:.2f})")
            except Exception as e:
                print(f"  ⚠️  WARNING: Could not verify return position: {e}")

        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            results[motor_name] = "❌ FAIL"

        print()
        time.sleep(0.2)  # Small delay between motors

    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for motor_name in motor_names:
        status = results.get(motor_name, "❌ NOT TESTED")
        print(f"  {motor_name:20s}: {status}")

    all_passed = all("✅" in results.get(name, "") for name in motor_names)
    if all_passed:
        print("\n✅ All motors responded successfully!")
    else:
        print("\n⚠️  Some motors had issues. Check the details above.")

    # Disconnect with error handling (motors may have stopped responding)
    print("\nDisconnecting...")
    try:
        robot.disconnect()
        print("✅ Disconnected")
    except Exception as e:
        print(f"⚠️  Error during disconnect: {e}")
        print("   Motors may have stopped responding. Try power cycling the robot.")
        # Try to disconnect bus directly without disabling torque
        try:
            robot.bus.disconnect(disable_torque=False)
        except:
            pass

if __name__ == "__main__":
    test_motor_movement()
