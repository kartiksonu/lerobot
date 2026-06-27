#!/usr/bin/env python3
"""
Dual Camera Viewer (RealSense + USB Camera)
Displays streams from both cameras side-by-side or stacked.
"""

import os
import pyrealsense2 as rs
import numpy as np
import cv2

# Set display for Jetson monitor
os.environ['DISPLAY'] = ':1'
os.environ['XAUTHORITY'] = '/run/user/1000/gdm/Xauthority'

def main():
    print("Initializing cameras...")

    # --- 1. RealSense Setup ---
    rs_ctx = rs.context()
    rs_devices = rs_ctx.query_devices()
    rs_pipeline = None

    if len(rs_devices) > 0:
        print(f"✅ Found RealSense: {rs_devices[0].get_info(rs.camera_info.name)}")
        rs_pipeline = rs.pipeline()
        rs_config = rs.config()
        rs_config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        rs_config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        rs_pipeline.start(rs_config)
    else:
        print("❌ No RealSense camera found.")

    # --- 2. USB Camera Setup ---
    # We identified it as /dev/video6 in the previous step
    # Using 640x480 @ 30fps MJPG as supported by the device
    usb_cap = cv2.VideoCapture(6) # Index 6 for /dev/video6

    if usb_cap.isOpened():
        print("✅ Found USB Camera at /dev/video6")
        # Configure USB camera
        usb_cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        usb_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        usb_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        usb_cap.set(cv2.CAP_PROP_FPS, 30)
    else:
        print("❌ Could not open USB Camera at /dev/video6")
        usb_cap = None

    if not rs_pipeline and not usb_cap:
        print("No cameras available. Exiting.")
        return

    print("\nStarting Feed... Press 'q' to quit.")

    try:
        while True:
            # --- Get RealSense Frames ---
            rs_color_image = None
            if rs_pipeline:
                frames = rs_pipeline.wait_for_frames()
                color_frame = frames.get_color_frame()
                if color_frame:
                    rs_color_image = np.asanyarray(color_frame.get_data())
                    # Add label
                    cv2.putText(rs_color_image, "RealSense", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # --- Get USB Camera Frames ---
            usb_image = None
            if usb_cap:
                ret, frame = usb_cap.read()
                if ret:
                    usb_image = frame
                    # Add label
                    cv2.putText(usb_image, "USB Camera", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # --- Combine and Display ---
            # Create a blank canvas if one camera is missing
            if rs_color_image is None and usb_image is not None:
                rs_color_image = np.zeros_like(usb_image)
            elif usb_image is None and rs_color_image is not None:
                usb_image = np.zeros_like(rs_color_image)

            if rs_color_image is not None and usb_image is not None:
                # Resize if necessary to match heights
                if rs_color_image.shape != usb_image.shape:
                    usb_image = cv2.resize(usb_image, (rs_color_image.shape[1], rs_color_image.shape[0]))

                # Stack horizontally
                combined_image = np.hstack((rs_color_image, usb_image))
                cv2.imshow('Dual Camera View', combined_image)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    finally:
        print("Closing cameras...")
        if rs_pipeline:
            rs_pipeline.stop()
        if usb_cap:
            usb_cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
