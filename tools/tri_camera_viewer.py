#!/usr/bin/env python3
"""
Tri-Camera Viewer (RealSense + WOWRobo USB + Logitech BRIO)
Displays streams from all three cameras.
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
        # rs_config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30) # Optional depth
        rs_pipeline.start(rs_config)
    else:
        print("❌ No RealSense camera found.")

    # --- 2. WOWRobo USB Camera Setup (/dev/video6) ---
    wow_cap = cv2.VideoCapture(6)
    if wow_cap.isOpened():
        print("✅ Found WOWRobo Camera at /dev/video6")
        wow_cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        wow_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        wow_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        wow_cap.set(cv2.CAP_PROP_FPS, 30)
    else:
        print("❌ Could not open WOWRobo Camera at /dev/video6")
        wow_cap = None

    # --- 3. Logitech BRIO Setup (/dev/video0) ---
    logi_cap = cv2.VideoCapture(0)
    if logi_cap.isOpened():
        print("✅ Found Logitech BRIO at /dev/video0")
        logi_cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        logi_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        logi_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        logi_cap.set(cv2.CAP_PROP_FPS, 30)
    else:
        print("❌ Could not open Logitech BRIO at /dev/video0")
        logi_cap = None

    if not rs_pipeline and not wow_cap and not logi_cap:
        print("No cameras available. Exiting.")
        return

    print("\nStarting Feed... Press 'q' to quit.")

    try:
        while True:
            frames_to_show = []

            # --- Get RealSense Frames ---
            if rs_pipeline:
                frames = rs_pipeline.wait_for_frames()
                color_frame = frames.get_color_frame()
                if color_frame:
                    rs_image = np.asanyarray(color_frame.get_data())
                    # Resize to common viewing height (e.g., 480px high) to keep window manageable
                    rs_image = cv2.resize(rs_image, (640, 360))
                    cv2.putText(rs_image, "RealSense", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    frames_to_show.append(rs_image)

            # --- Get WOWRobo Frames ---
            if wow_cap:
                ret, frame = wow_cap.read()
                if ret:
                    # Resize for display
                    frame = cv2.resize(frame, (640, 360))
                    cv2.putText(frame, "WOWRobo", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    frames_to_show.append(frame)

            # --- Get Logitech Frames ---
            if logi_cap:
                ret, frame = logi_cap.read()
                if ret:
                    # Resize for display
                    frame = cv2.resize(frame, (640, 360))
                    cv2.putText(frame, "Logitech BRIO", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    frames_to_show.append(frame)

            # --- Combine and Display ---
            if frames_to_show:
                # Stack all available frames horizontally
                combined_image = np.hstack(frames_to_show)
                cv2.imshow('Tri-Camera View', combined_image)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    finally:
        print("Closing cameras...")
        if rs_pipeline:
            rs_pipeline.stop()
        if wow_cap:
            wow_cap.release()
        if logi_cap:
            logi_cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()


