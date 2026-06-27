import time
import argparse
import cv2
import numpy as np
import rerun as rr
from lerobot.robots.so101_follower.so101_follower import SO101Follower

def main(args):
    # 1. Initialize Rerun
    print(f"Initializing Rerun (Hosting on 0.0.0.0:{args.port})...")
    rr.init("lerobot_live_viz", spawn=False)
    rr.serve(open_browser=False, web_port=args.port, ws_port=args.ws_port)

    # 2. Connect to Robot
    print(f"Connecting to Robot on {args.robot_port}...")
    robot = SO101Follower(
        port=args.robot_port,
        id="thor_follower_arm",
        disable_torque_on_disconnect=True
    )
    robot.connect()
    print("Robot connected.")

    # 3. Connect to Cameras
    cameras = {}
    camera_configs = [
        {"name": "Front (Logitech)", "path": "/dev/video0", "width": 1920, "height": 1080},
        {"name": "Ego (WOWRobo)", "path": "/dev/video2", "width": 1920, "height": 1080},
    ]

    for conf in camera_configs:
        path = conf["path"]
        # Extract index from /dev/videoX
        try:
            idx = int(path.replace("/dev/video", ""))
            cap = cv2.VideoCapture(idx)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, conf["width"])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, conf["height"])
            if cap.isOpened():
                print(f"Connected to {conf['name']} at {path}")
                cameras[conf["name"]] = cap
            else:
                print(f"Failed to open {conf['name']} at {path}")
        except Exception as e:
            print(f"Error opening {path}: {e}")

    print("\nStarting Visualization Loop...")
    print(f"Open https://app.rerun.io/ or a local rerun viewer and connect to: ws://10.0.0.103:{args.ws_port}")
    print(f"Or open http://10.0.0.103:{args.port} in your browser (if on same network).")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            loop_start = time.perf_counter()

            # Read Robot State
            robot.update()
            present_position = robot.sensors['present_position']
            present_velocity = robot.sensors['present_velocity']

            # Log Robot State
            for i, pos in enumerate(present_position):
                rr.log(f"robot/position/joint_{i+1}", rr.Scalar(pos.item()))
            for i, vel in enumerate(present_velocity):
                rr.log(f"robot/velocity/joint_{i+1}", rr.Scalar(vel.item()))

            # Read and Log Cameras
            for name, cap in cameras.items():
                ret, frame = cap.read()
                if ret:
                    # OpenCV is BGR, Rerun expects RGB
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    rr.log(f"cameras/{name}", rr.Image(rgb))

            # Maintain FPS
            dt = time.perf_counter() - loop_start
            sleep_time = max(0, (1.0 / args.fps) - dt)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        robot.disconnect()
        for cap in cameras.values():
            cap.release()
        rr.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot-port", default="/dev/ttyACM0")
    parser.add_argument("--port", type=int, default=9090, help="Web viewer port")
    parser.add_argument("--ws-port", type=int, default=9087, help="Web socket port")
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()
    main(args)






