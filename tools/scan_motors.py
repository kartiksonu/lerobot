import sys
import glob
import serial
from scservo_sdk import *

# Settings
DEVICENAME = '/dev/ttyACM0'
BAUDRATE = 1000000  # Default for SO-ARM101
PROTOCOL_VERSION = 1.0

def scan_motors():
    print(f"Opening port {DEVICENAME} at {BAUDRATE} baud...")

    portHandler = PortHandler(DEVICENAME)
    packetHandler = PacketHandler(PROTOCOL_VERSION)

    if portHandler.openPort():
        print("Succeeded to open the port")
    else:
        print("Failed to open the port")
        return

    if portHandler.setBaudRate(BAUDRATE):
        print("Succeeded to change the baudrate")
    else:
        print("Failed to change the baudrate")
        return

    print("Scanning for motors (ID 1-6)...")
    found_motors = []

    for id in range(1, 7):
        model_number, result, error = packetHandler.ping(portHandler, id)
        if result == COMM_SUCCESS:
            print(f"[ID:{id:03d}] ping successful. Model Number: {model_number}")
            found_motors.append(id)
        else:
            print(f"[ID:{id:03d}] ping failed. Error: {packetHandler.getRxPacketError(error)}")

    print(f"\nFound {len(found_motors)} motors: {found_motors}")

    portHandler.closePort()

if __name__ == "__main__":
    scan_motors()
