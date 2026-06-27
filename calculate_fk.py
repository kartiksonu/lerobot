import torch
import numpy as np
import matplotlib.pyplot as plt
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.model.kinematics import RobotKinematics
import argparse
from pathlib import Path

# Global variables/Hyperparameters
DATASET_REPO_ID = "sapanostic/so101_offline_eval"
URDF_PATH = "lerobot/urdfs/so101_new_calib.urdf"
TARGET_FRAME = "gripper_frame_link"

def calculate_fk_for_episode(episode_index: int, output_plot: str = None):
    print(f"Loading dataset: {DATASET_REPO_ID}...")
    dataset = LeRobotDataset(repo_id=DATASET_REPO_ID)

    if episode_index >= dataset.num_episodes:
        print(f"Error: Episode index {episode_index} is out of bounds (max {dataset.num_episodes - 1})")
        return

    print(f"\n--- Processing Episode {episode_index} ---")
    episode_meta = dataset.meta.episodes[episode_index]
    start_frame = episode_meta['dataset_from_index']
    end_frame = episode_meta['dataset_to_index']
    print(f"Frame range: {start_frame} to {end_frame}")

    # Load URDF and initialize kinematics
    print(f"Loading Kinematics from {URDF_PATH}...")
    if not Path(URDF_PATH).exists():
        raise FileNotFoundError(f"URDF file not found at {URDF_PATH}")

    kinematics = RobotKinematics(
        urdf_path=URDF_PATH,
        target_frame_name=TARGET_FRAME
    )
    print(f"Joint names in URDF: {kinematics.joint_names}")

    # Extract joint values from dataset
    print("Extracting joint values...")
    # Use hf_dataset for efficiency
    episode_slice = dataset.hf_dataset[start_frame:end_frame]
    obs_state = episode_slice['observation.state'] # List of lists or tensors

    # Convert to numpy array of shape (num_frames, num_joints)
    if isinstance(obs_state[0], torch.Tensor):
         joint_values = torch.stack(obs_state).numpy()
    else:
         joint_values = np.array(obs_state)

    # Map dataset features to URDF joints
    # Dataset features: shoulder_pan.pos, shoulder_lift.pos, ...
    # URDF joints: shoulder_pan, shoulder_lift, ...
    # We need to ensure order matches kinematics.joint_names

    dataset_joint_names = dataset.features['observation.state']['names']
    print(f"Dataset joint names: {dataset_joint_names}")

    # Create a mapping from URDF joint name to dataset column index
    joint_indices = []
    for urdf_joint in kinematics.joint_names:
        # Try to find corresponding dataset feature
        # Heuristic: dataset name starts with urdf name
        match = None
        for i, ds_name in enumerate(dataset_joint_names):
            if ds_name == urdf_joint or ds_name == f"{urdf_joint}.pos":
                match = i
                break

        if match is None:
            print(f"Warning: Could not find dataset feature for URDF joint '{urdf_joint}'")
            # If gripper is missing or named differently, handle it.
            # In SO-ARM100, gripper might be 'gripper' in URDF but 'gripper.pos' in dataset.
            # If it's a dummy or fixed joint in URDF it wouldn't appear in joint_names.
            # 'gripper_frame_link' is fixed to 'gripper_link'.
            # 'gripper' joint exists in URDF.
        else:
            joint_indices.append(match)

    if len(joint_indices) != len(kinematics.joint_names):
        print("Error: Mismatch in number of joints found.")
        print(f"URDF joints ({len(kinematics.joint_names)}): {kinematics.joint_names}")
        print(f"Found indices: {joint_indices}")
        return

    # Reorder joint values to match URDF expectation
    ordered_joint_values = joint_values[:, joint_indices]

    # Compute FK for all frames
    print("Computing Forward Kinematics...")
    ee_positions = []

    # Ensure joint values are float64 for placo compatibility
    ordered_joint_values = ordered_joint_values.astype(np.float64)

    for i in range(len(ordered_joint_values)):
        joints_deg = ordered_joint_values[i]
        # RobotKinematics expects degrees?
        # Checking kinematics.py:
        # forward_kinematics(self, joint_pos_deg: np.ndarray) -> np.ndarray
        # Yes, it expects degrees.
        # But wait, does the dataset store degrees or radians?
        # lerobot dataset usually stores radians?
        # SO100 config says `use_degrees=True` or `False`.
        # Let's check the values.
        # From previous output: "shoulder_pan.pos": 37.3457
        # 37 radians is impossible (multiple revolutions). 37 degrees is plausible.
        # It seems the dataset is in degrees.

        tf_matrix = kinematics.forward_kinematics(joints_deg)
        # Extract translation (x, y, z)
        translation = tf_matrix[:3, 3]
        ee_positions.append(translation)

    ee_positions = np.array(ee_positions)
    print(f"Computed FK for {len(ee_positions)} frames.")
    print(f"End Effector Position shape: {ee_positions.shape}")
    print("First frame EE position (x, y, z):", ee_positions[0])

    if output_plot:
        print(f"Plotting trajectory to {output_plot}...")
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        ax.plot(ee_positions[:, 0], ee_positions[:, 1], ee_positions[:, 2], label='EE Trajectory')
        ax.scatter(ee_positions[0, 0], ee_positions[0, 1], ee_positions[0, 2], color='green', label='Start')
        ax.scatter(ee_positions[-1, 0], ee_positions[-1, 1], ee_positions[-1, 2], color='red', label='End')

        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Z (m)')
        ax.set_title(f'End Effector Trajectory - Episode {episode_index}')
        ax.legend()

        plt.savefig(output_plot)
        print(f"Plot saved to {output_plot}")

    return ee_positions

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate FK for a given episode")
    parser.add_argument("--episode", type=int, default=5, help="Episode index to process")
    parser.add_argument("--plot", type=str, default="ee_trajectory.png", help="Output plot filename")

    args = parser.parse_args()

    calculate_fk_for_episode(args.episode, args.plot)
