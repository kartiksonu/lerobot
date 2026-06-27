import argparse
import time
import cv2
import numpy as np
import threading
from queue import Queue
try:
    import pyrealsense2 as rs
    HAS_REALSENSE = True
except ImportError:
    HAS_REALSENSE = False

# Import LeRobot classes (adjust paths if needed based on installed version)
try:
    from lerobot.robots.so101_follower.so101_follower import SO101Follower
except ImportError:
    # Fallback or try to find where it is
    import sys
    sys.path.append('/home/thor/lerobot/src')
    from lerobot.robots.so101_follower.so101_follower import SO101Follower

def get_available_cameras():
    """Detect available cameras (RealSense and USB)."""
    cameras = {}

    # Check for RealSense
    if HAS_REALSENSE:
        try:
            ctx = rs.context()
            if len(ctx.query_devices()) > 0:
                cameras['realsense'] = True
        except:
            pass

    # Check for Specific Known USB cameras
    # Priority: video0 (Logitech), video2 (WOWRobo)
    known_cameras = {
        0: "Front (Logitech)",
        2: "Ego (WOWRobo)"
    }

    # Scan indices 0-10
    for i in range(10):
        # Skip if we already found it as a "known" camera, wait, we want to add it if it works

        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                name = known_cameras.get(i, f"USB Camera {i}")
                cameras[name] = i
            cap.release()

    return cameras

class KeyboardTeleop:
    def __init__(self, robot_port, camera_indices=None):
        self.robot = SO101Follower(
            port=robot_port,
            id="thor_follower_arm",
            disable_torque_on_disconnect=True
        )
        self.camera_indices = camera_indices or {}
        self.caps = {}
        self.realsense_pipeline = None
        self.running = True

        # Current target positions (initialized after connection)
        self.targets = None

    def connect(self):
        print(f"Connecting to robot on {self.robot.port}...")
        self.robot.connect()
        print("Robot connected.")

        # Read current positions to set initial targets
        self.robot.update()
        self.targets = self.robot.sensors['present_position'].clone()
        print(f"Initial positions: {self.targets}")

        # Initialize Cameras
        for name, idx in self.camera_indices.items():
            if name == 'realsense':
                self.init_realsense()
            else:
                print(f"Opening {name} on /dev/video{idx}...")
                cap = cv2.VideoCapture(idx)

                # Set specific resolutions if known
                if "WOWRobo" in name:
                     cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                else:
                     cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

                self.caps[name] = cap

    def init_realsense(self):
        if not HAS_REALSENSE:
            return
        try:
            self.realsense_pipeline = rs.pipeline()
            config = rs.config()
            config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)
            self.realsense_pipeline.start(config)
            print("RealSense started.")
        except Exception as e:
            print(f"Failed to start RealSense: {e}")

    def run(self):
        print("\n=== Keyboard Teleoperation ===")
        print("Use number keys 1-6 to select joint.")
        print("Use W/S to increase/decrease value.")
        print("Q to quit.")

        active_joint = 0
        step_size = 50 # Encoder ticks (approx)

        while self.running:
            # 1. Capture Images
            frames = {}

            # RealSense
            if self.realsense_pipeline:
                try:
                    rs_frames = self.realsense_pipeline.wait_for_frames(timeout_ms=100)
                    color_frame = rs_frames.get_color_frame()
                    if color_frame:
                        img = np.asanyarray(color_frame.get_data())
                        frames['RealSense'] = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                except:
                    pass

            # USB Cameras
            for name, cap in self.caps.items():
                ret, frame = cap.read()
                if ret:
                    frames[name] = frame

            # 2. Display Images & Handle Input
            if frames:
                # Stack images horizontally
                # Resize to common height
                h = 360
                resized_frames = []

                # Sort frames to keep order consistent
                sorted_names = sorted(frames.keys())

                for name in sorted_names:
                    img = frames[name]
                    if img is None: continue

                    r = h / img.shape[0]
                    dim = (int(img.shape[1] * r), h)
                    resized = cv2.resize(img, dim)
                    # Add text
                    cv2.putText(resized, name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    resized_frames.append(resized)

                if resized_frames:
                    composite = np.hstack(resized_frames)
                    cv2.imshow("Teleoperation", composite)

            # Key Handling
            key = cv2.waitKey(10) & 0xFF
            if key == ord('q'):
                self.running = False
                break
            elif key >= ord('1') and key <= ord('6'):
                active_joint = key - ord('1')
                print(f"Selected Joint {active_joint + 1}")
            elif key == ord('w'):
                self.targets[active_joint] += step_size
                print(f"Joint {active_joint + 1} -> {self.targets[active_joint]}")
            elif key == ord('s'):
                self.targets[active_joint] -= step_size
                print(f"Joint {active_joint + 1} -> {self.targets[active_joint]}")

            # 3. Send Commands to Robot
            if self.targets is not None:
                self.robot.set_goal_pos(self.targets)
                self.robot.update() # Send commands and read status

        # Cleanup
        try:
            self.robot.disconnect()
        except:
            pass

        if self.realsense_pipeline:
            self.realsense_pipeline.stop()
        for cap in self.caps.values():
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot-port", default="/dev/ttyACM0")
    args = parser.parse_args()

    # Auto-detect cameras
    print("Detecting cameras...")
    available = get_available_cameras()
    print(f"Detected cameras: {available}")

    teleop = KeyboardTeleop(args.robot_port, available)
    teleop.connect()
    teleop.run()
