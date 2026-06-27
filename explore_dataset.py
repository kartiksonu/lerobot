import torch
import matplotlib.pyplot as plt
from lerobot.datasets.lerobot_dataset import LeRobotDataset
import numpy as np

# Global variables/Hyperparameters
DATASET_REPO_ID = "sapanostic/so101_offline_eval"
EPISODE_INDEX = 5  # Change this to access different episodes
OUTPUT_PLOT_FILE = f"episode_{EPISODE_INDEX}_joints.png"

def main():
    print(f"Loading dataset: {DATASET_REPO_ID}...")

    # Load the dataset
    dataset = LeRobotDataset(repo_id=DATASET_REPO_ID)

    if EPISODE_INDEX >= dataset.num_episodes:
        print(f"Error: Episode index {EPISODE_INDEX} is out of bounds (max {dataset.num_episodes - 1})")
        return

    # Access the specific episode
    print(f"\n--- Accessing Episode {EPISODE_INDEX} ---")

    episode_meta = dataset.meta.episodes[EPISODE_INDEX]
    start_frame = episode_meta['dataset_from_index']
    end_frame = episode_meta['dataset_to_index']

    print(f"Episode {EPISODE_INDEX} frame range: {start_frame} to {end_frame}")
    print(f"Task: {episode_meta['tasks']}")

    # Extract observation state (joint positions)
    # We'll collect them into a list then convert to numpy/tensor

    # The dataset can be sliced directly if supported, but let's iterate to be safe with the current understanding
    # or use range indexing if dataset supports it.
    # dataset[start_frame:end_frame] might work if implemented, but let's loop to be robust.

    print("Extracting joint values...")
    joint_values = []

    # Efficiently load frames
    # dataset[i] returns a dict for frame i

    # Note: iterating through dataset one by one might be slow for large episodes,
    # but for ~200 frames it's fine.
    # A faster way if the dataset supports slicing: dataset.hf_dataset.select(range(start_frame, end_frame))
    # But hf_dataset returns dict of lists, which is easier.

    # Using hf_dataset directly for speed if available
    if hasattr(dataset, 'hf_dataset'):
        # hf_dataset is a Hugging Face dataset object
        # We can slice it directly
        episode_slice = dataset.hf_dataset[start_frame:end_frame]

        # 'observation.state' will be a list of lists (or tensors if transformed)
        obs_state = episode_slice['observation.state']

        # Convert to numpy
        if isinstance(obs_state[0], torch.Tensor):
             joint_values = torch.stack(obs_state).numpy()
        else:
             joint_values = np.array(obs_state)

    else:
        # Fallback to iteration
        for i in range(start_frame, end_frame):
            frame = dataset[i]
            state = frame['observation.state']
            if isinstance(state, torch.Tensor):
                state = state.numpy()
            joint_values.append(state)
        joint_values = np.array(joint_values)

    print(f"Joint values shape: {joint_values.shape}")

    # Get joint names
    joint_names = dataset.features['observation.state']['names']
    print(f"Joint names: {joint_names}")

    # Plotting
    print(f"Plotting to {OUTPUT_PLOT_FILE}...")
    plt.figure(figsize=(12, 8))

    num_joints = joint_values.shape[1]

    for i in range(num_joints):
        plt.plot(joint_values[:, i], label=joint_names[i])

    plt.title(f"Joint Space Values for Episode {EPISODE_INDEX}")
    plt.xlabel("Frame Index (within episode)")
    plt.ylabel("Joint Position")
    plt.legend()
    plt.grid(True)

    plt.savefig(OUTPUT_PLOT_FILE)
    print(f"Plot saved successfully to {OUTPUT_PLOT_FILE}")

if __name__ == "__main__":
    main()
