import torch
import numpy as np
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.model.kinematics import RobotKinematics
import argparse
from pathlib import Path

# Global variables/Hyperparameters
DATASET_REPO_ID = "sapanostic/so101_offline_eval"
URDF_PATH = "lerobot/urdfs/so101_new_calib.urdf"

def export_joints(episode_index: int, output_file: str):
    print(f"Loading dataset: {DATASET_REPO_ID}...")
    dataset = LeRobotDataset(repo_id=DATASET_REPO_ID)

    episode_meta = dataset.meta.episodes[episode_index]
    start_frame = episode_meta['dataset_from_index']
    end_frame = episode_meta['dataset_to_index']

    print(f"Extracting episode {episode_index} (frames {start_frame}-{end_frame})...")
    episode_slice = dataset.hf_dataset[start_frame:end_frame]
    obs_state = episode_slice['observation.state']

    if isinstance(obs_state[0], torch.Tensor):
         joint_values = torch.stack(obs_state).numpy()
    else:
         joint_values = np.array(obs_state)

    # Reorder based on URDF if needed
    # Standard order: ['shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper']
    # Dataset order: ['shoulder_pan.pos', 'shoulder_lift.pos', 'elbow_flex.pos', 'wrist_flex.pos', 'wrist_roll.pos', 'gripper.pos']
    # They match 1:1 usually.

    print(f"Saving {len(joint_values)} frames to {output_file}...")
    np.save(output_file, joint_values)
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", type=int, default=5)
    parser.add_argument("--out", type=str, default="so101_joint_to_crt/data/episode_5_joints.npy")
    args = parser.parse_args()

    export_joints(args.episode, args.out)
