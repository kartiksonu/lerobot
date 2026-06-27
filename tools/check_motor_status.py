#!/usr/bin/env python
"""Check comprehensive status of all motors"""

from lerobot.robots.so101_follower.config_so101_follower import SO101FollowerConfig
from lerobot.robots.so101_follower.so101_follower import SO101Follower

def format_value(value, unit=""):
    """Format value with unit"""
    if isinstance(value, float):
        return f"{value:.2f}{unit}"
    return f"{value}{unit}"

def check_motor_status():
    robot_cfg = SO101FollowerConfig(port="/dev/ttyACM0", id="thor_follower_arm", cameras={})
    robot = SO101Follower(robot_cfg)

    print("Connecting...")
    robot.connect()
    print("✅ Connected!\n")

    # Motor name mapping (from SO101 config)
    motor_names = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]

    print("=" * 80)
    print("MOTOR STATUS REPORT")
    print("=" * 80)

    for motor_name in motor_names:
        motor_id = robot.bus.motors[motor_name].id
        print(f"\n{motor_name.upper()} (ID: {motor_id})")
        print("-" * 80)

        try:
            # Basic status
            position_norm = robot.bus.read("Present_Position", motor_name, normalize=True)
            position_raw = robot.bus.read("Present_Position", motor_name, normalize=False)
            torque_enabled = robot.bus.read("Torque_Enable", motor_name, normalize=False)
            lock = robot.bus.read("Lock", motor_name, normalize=False)
            moving = robot.bus.read("Moving", motor_name, normalize=False)

            print(f"  Position (normalized): {format_value(position_norm)}")
            print(f"  Position (raw):        {position_raw}")
            print(f"  Torque Enabled:         {'✅ YES' if torque_enabled else '❌ NO'}")
            print(f"  Lock:                   {'🔒 LOCKED' if lock else '🔓 UNLOCKED'}")
            print(f"  Moving:                 {'🟢 YES' if moving else '⚪ NO'}")

            # Try to read velocity
            try:
                velocity = robot.bus.read("Present_Velocity", motor_name, normalize=False)
                print(f"  Velocity (raw):         {velocity}")
            except Exception as e:
                print(f"  Velocity:               ❌ Error: {str(e)[:50]}")

            # Try to read load
            try:
                load = robot.bus.read("Present_Load", motor_name, normalize=False)
                print(f"  Load (raw):             {load}")
            except Exception as e:
                print(f"  Load:                   ❌ Error: {str(e)[:50]}")

            # Voltage and temperature (critical for health)
            try:
                voltage = robot.bus.read("Present_Voltage", motor_name, normalize=False)
                voltage_v = voltage / 10.0  # Typically in 0.1V units
                print(f"  Voltage:                {format_value(voltage_v, 'V')} ({voltage} raw)")
            except Exception as e:
                print(f"  Voltage:                ❌ Error: {str(e)[:50]}")

            try:
                temperature = robot.bus.read("Present_Temperature", motor_name, normalize=False)
                print(f"  Temperature:            {format_value(temperature, '°C')}")
                if temperature > 70:
                    print(f"                          ⚠️  WARNING: High temperature!")
            except Exception as e:
                print(f"  Temperature:            ❌ Error: {str(e)[:50]}")

            # Try to read current (if available for STS series)
            try:
                current = robot.bus.read("Present_Current", motor_name, normalize=False)
                print(f"  Current (raw):          {current}")
            except Exception as e:
                # Current might not be available for all models
                pass

            # Try to read status register
            try:
                status = robot.bus.read("Status", motor_name, normalize=False)
                print(f"  Status Register:       0x{status:02X}")
            except Exception as e:
                pass

        except Exception as e:
            print(f"  ❌ ERROR reading motor: {str(e)}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    # Check for issues
    issues = []
    for motor_name in motor_names:
        try:
            torque = robot.bus.read("Torque_Enable", motor_name, normalize=False)
            if not torque:
                issues.append(f"{motor_name}: Torque disabled")

            temp = robot.bus.read("Present_Temperature", motor_name, normalize=False)
            if temp > 70:
                issues.append(f"{motor_name}: High temperature ({temp}°C)")

            voltage = robot.bus.read("Present_Voltage", motor_name, normalize=False)
            voltage_v = voltage / 10.0
            if voltage_v < 10.0 or voltage_v > 14.0:
                issues.append(f"{motor_name}: Voltage out of range ({voltage_v:.1f}V)")
        except Exception:
            issues.append(f"{motor_name}: Cannot read status")

    if issues:
        print("⚠️  ISSUES DETECTED:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ All motors appear healthy")

    robot.disconnect()
    print("\n✅ Disconnected")

if __name__ == "__main__":
    check_motor_status()
