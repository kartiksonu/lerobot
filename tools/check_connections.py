import sys
import os
import glob
import pyrealsense2 as rs
import serial.tools.list_ports

def check_arm_connection():
    print("--- Checking Arm Connection ---")
    # Check for ttyACM devices
    ports = glob.glob('/dev/ttyACM*')
    if not ports:
        print("❌ No /dev/ttyACM* ports found.")
        print("   Is the arm plugged in via USB?")
        print("   Try unplugging and replugging the USB cable.")
        return False

    print(f"✅ Found potential arm ports: {ports}")

    # Optional: Try to identify specifically if possible, but presence is a good start
    # We assume /dev/ttyACM0 is the arm based on previous context
    target_port = '/dev/ttyACM0'
    if target_port in ports:
        print(f"✅ {target_port} is present (Expected Arm Port).")
        return True
    else:
        print(f"⚠️ {target_port} not found, but other ports exist. Arm might be on {ports[0]}.")
        return True

def check_realsense_connection():
    print("\n--- Checking RealSense Connection ---")
    try:
        ctx = rs.context()
        devices = ctx.query_devices()

        if len(devices) == 0:
            print("❌ No RealSense devices detected.")
            print("   Is the camera plugged in?")
            print("   Try unplugging and replugging the USB cable.")
            return False

        print(f"✅ Found {len(devices)} RealSense device(s):")
        for dev in devices:
            name = dev.get_info(rs.camera_info.name)
            serial = dev.get_info(rs.camera_info.serial_number)
            fw = dev.get_info(rs.camera_info.firmware_version)
            usb_type = dev.get_info(rs.camera_info.usb_type_descriptor)
            print(f"   - {name}")
            print(f"     Serial:   {serial}")
            print(f"     Firmware: {fw}")
            print(f"     USB Type: {usb_type}")

            if "3." not in usb_type:
                print("     ⚠️ WARNING: Camera connected via USB 2.X. Performance may be limited. Use a USB 3.0 port/cable if possible.")

        return True

    except Exception as e:
        print(f"❌ Error checking RealSense: {e}")
        return False

def main():
    arm_ok = check_arm_connection()
    cam_ok = check_realsense_connection()

    print("\n--- Summary ---")
    if arm_ok and cam_ok:
        print("✅ Both Arm and Camera are connected!")
    else:
        print("⚠️ Issues detected. See details above.")

if __name__ == "__main__":
    main()
