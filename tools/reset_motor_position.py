#!/usr/bin/env python3
"""
Attempt to reset motor position counter via software.
Tries: mode switch, power cycle via torque toggle, and position limit reset.
"""

import time
import scservo_sdk as scs

PORT = "/dev/ttyACM0"
BAUDRATE = 1_000_000
MOTOR_ID = 4

# STS3215 register addresses
OPERATING_MODE = 33
TORQUE_ENABLE = 40
LOCK = 55
PRESENT_POSITION = 56
MIN_POSITION_LIMIT = 9
MAX_POSITION_LIMIT = 11

def main():
    port = scs.PortHandler(PORT)
    packet = scs.PacketHandler(0)  # Protocol 0 for STS series

    if not port.openPort():
        print(f"Failed to open {PORT}")
        return
    port.setBaudRate(BAUDRATE)

    def read_pos():
        val, _, _ = packet.read2ByteTxRx(port, MOTOR_ID, PRESENT_POSITION)
        return val

    def read_reg(addr, size=1):
        if size == 1:
            val, _, _ = packet.read1ByteTxRx(port, MOTOR_ID, addr)
        else:
            val, _, _ = packet.read2ByteTxRx(port, MOTOR_ID, addr)
        return val

    def write_reg(addr, val, size=1):
        # Unlock EEPROM first
        packet.write1ByteTxRx(port, MOTOR_ID, LOCK, 0)
        time.sleep(0.01)
        if size == 1:
            packet.write1ByteTxRx(port, MOTOR_ID, addr, val)
        else:
            packet.write2ByteTxRx(port, MOTOR_ID, addr, val)
        time.sleep(0.01)

    print(f"Motor ID {MOTOR_ID}")
    print(f"Initial Position: {read_pos()}")
    print(f"Operating Mode: {read_reg(OPERATING_MODE)}")
    print(f"Min Limit: {read_reg(MIN_POSITION_LIMIT, 2)}")
    print(f"Max Limit: {read_reg(MAX_POSITION_LIMIT, 2)}")

    print("\n--- Attempting Reset Methods ---\n")

    # Method 1: Disable torque
    print("1. Disabling torque...")
    write_reg(TORQUE_ENABLE, 0)
    time.sleep(0.1)
    print(f"   Position after: {read_pos()}")

    # Method 2: Switch to wheel mode (1) then back to position mode (0)
    print("2. Switching Operating Mode: Position -> Wheel -> Position...")
    write_reg(OPERATING_MODE, 1)  # Wheel mode
    time.sleep(0.2)
    print(f"   Position in wheel mode: {read_pos()}")
    write_reg(OPERATING_MODE, 0)  # Back to position mode
    time.sleep(0.2)
    print(f"   Position after mode switch: {read_pos()}")

    # Method 3: Reset position limits to full range
    print("3. Resetting position limits to 0-4095...")
    write_reg(MIN_POSITION_LIMIT, 0, 2)
    write_reg(MAX_POSITION_LIMIT, 4095, 2)
    time.sleep(0.1)
    print(f"   Position after limit reset: {read_pos()}")

    # Method 4: Try writing Goal_Position to center
    print("4. Writing Goal_Position to 2048...")
    write_reg(TORQUE_ENABLE, 1)  # Enable torque
    time.sleep(0.05)
    packet.write2ByteTxRx(port, MOTOR_ID, 42, 2048)  # Goal_Position = 42
    time.sleep(1.0)
    print(f"   Position after goal write: {read_pos()}")
    write_reg(TORQUE_ENABLE, 0)

    final_pos = read_pos()
    print(f"\n=== Final Position: {final_pos} ===")
    if 0 <= final_pos <= 4095:
        print("✓ Position is now in valid range!")
    else:
        print("✗ Position still out of range. Physical reset required.")

    port.closePort()

if __name__ == "__main__":
    main()
