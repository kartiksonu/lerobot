#!/usr/bin/env python3
"""
Simple RealSense Viewer using OpenCV
Displays color and depth streams from RealSense camera
"""

import os
import pyrealsense2 as rs
import numpy as np
import cv2

# Set display for Jetson monitor
os.environ['DISPLAY'] = ':1'
os.environ['XAUTHORITY'] = '/run/user/1000/gdm/Xauthority'

def main():
    # Check if camera is available first
    ctx = rs.context()
    devices = ctx.query_devices()
    if len(devices) == 0:
        print("ERROR: No RealSense camera detected!")
        print("Please check:")
        print("  1. Camera USB cable is connected")
        print("  2. Camera is powered on")
        print("  3. Try unplugging and replugging the camera")
        return

    print(f"Found {len(devices)} camera(s)")
    for dev in devices:
        print(f"  - {dev.get_info(rs.camera_info.name)} (SN: {dev.get_info(rs.camera_info.serial_number)})")

    # Configure streams
    pipeline = rs.pipeline()
    config = rs.config()

    # Enable color and depth streams
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    # Start streaming
    print("Starting RealSense camera...")
    pipeline.start(config)

    print("Camera started! Press 'q' to quit, 's' to save frame")
    print("Window should appear on Jetson monitor: 'RealSense Viewer (Color | Depth)'")

    try:
        while True:
            # Wait for frames
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()

            if not depth_frame or not color_frame:
                continue

            # Convert images to numpy arrays
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            # Apply colormap on depth image
            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.03),
                cv2.COLORMAP_JET
            )

            # Stack images horizontally
            images = np.hstack((color_image, depth_colormap))

            # Display images
            cv2.imshow('RealSense Viewer (Color | Depth)', images)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                cv2.imwrite('/tmp/realsense_color.png', color_image)
                cv2.imwrite('/tmp/realsense_depth.png', depth_colormap)
                print("Saved frames to /tmp/realsense_*.png")

    finally:
        # Stop streaming
        pipeline.stop()
        cv2.destroyAllWindows()
        print("Camera stopped")

if __name__ == "__main__":
    main()
