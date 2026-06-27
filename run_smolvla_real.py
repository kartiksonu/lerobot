import torch
import time
import argparse

from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.datasets.utils import hw_to_dataset_features
from lerobot.policies.factory import make_pre_post_processors
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.policies.utils import build_inference_frame, make_robot_action
from lerobot.robots.so101_follower.config_so101_follower import SO101FollowerConfig
from lerobot.robots.so101_follower.so101_follower import SO101Follower
from lerobot.utils.utils import init_logging, log_say

def run_smolvla_real(task="Pick up the white block"):
    init_logging()

    # 1. Load Model
    model_id = "lerobot/smolvla_base"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🔄 Loading SmolVLA: {model_id} on {device}...")

    # Load model normally first
    model = SmolVLAPolicy.from_pretrained(model_id)

    # Override num_vlm_layers to use full model
    # Default is 16 layers for speed/memory efficiency
    # Setting to -1 disables layer reduction and uses all layers
    original_layers = model.config.num_vlm_layers
    model.config.num_vlm_layers = -1  # Use full model (all layers)
    print(f"📊 Overriding num_vlm_layers: {original_layers} → -1 (full model)")

    # Reinitialize the VLM component with full layers
    from lerobot.policies.smolvla.smolvlm_with_expert import SmolVLMWithExpertModel
    print("🔄 Reinitializing VLM with full layers...")
    new_vlm = SmolVLMWithExpertModel(
        model_id=model.config.vlm_model_name,
        freeze_vision_encoder=model.config.freeze_vision_encoder,
        train_expert_only=model.config.train_expert_only,
        load_vlm_weights=True,
        attention_mode=model.config.attention_mode,
        num_expert_layers=model.config.num_expert_layers,
        num_vlm_layers=-1,  # Use full model
        self_attn_every_n_layers=model.config.self_attn_every_n_layers,
        expert_width_multiplier=model.config.expert_width_multiplier,
        device=str(device),  # Use specific device
    )

    # Explicitly move all components to the correct device
    new_vlm = new_vlm.to(device)
    # Also move the VLM model and expert separately to ensure everything is on device
    if hasattr(new_vlm, 'vlm'):
        new_vlm.vlm = new_vlm.vlm.to(device)
    if hasattr(new_vlm, 'lm_expert'):
        new_vlm.lm_expert = new_vlm.lm_expert.to(device)

    model.model.vlm_with_expert = new_vlm

    # Ensure the entire model is on the correct device
    model = model.to(device)

    model.eval()

    # 2. Create Preprocessor and Postprocessor
    print("🔧 Setting up preprocessor and postprocessor...")
    preprocessor, postprocessor = make_pre_post_processors(
        model.config,
        model_id,
        preprocessor_overrides={"device_processor": {"device": str(device)}},
    )

    # 3. Configure Cameras (Using only 2 cameras: wrist and front)
    # camera1 = Ego/Wrist (WOWRobo) - mapped to camera1 for model
    # camera2 = Front (Logitech) - mapped to camera2 for model
    # Note: Disabled RealSense (top camera) to avoid connection issues
    camera_config = {
        "camera1": OpenCVCameraConfig(
            index_or_path=6, # WOWRobo (wrist camera)
            fps=30,
            width=640,
            height=480
        ),
        "camera2": OpenCVCameraConfig(
            index_or_path=0, # Logitech (front camera)
            fps=30,
            width=640,
            height=480
        )
    }

    # 4. Initialize Robot (no safety limits - using raw model outputs)
    print("🤖 Connecting to Robot and Cameras...")
    robot_cfg = SO101FollowerConfig(
        port="/dev/ttyACM0",
        id="thor_follower_arm",
        cameras=camera_config,
        max_relative_target=None  # No limiting - use model outputs directly
    )
    robot = SO101Follower(robot_cfg)
    robot.connect()
    print("✅ Connected!")

    # 5. Prepare feature mappings for dataset format conversion
    action_features = hw_to_dataset_features(robot.action_features, "action")
    obs_features = hw_to_dataset_features(robot.observation_features, "observation")
    dataset_features = {**action_features, **obs_features}

    # 6. Inference Loop
    print(f"🚀 Starting Inference for task: '{task}'")
    log_say(f"Starting task: {task}", True)
    print("Press Ctrl+C to stop\n")

    step = 0
    try:
        while True:
            step += 1
            # Get Observation from robot
            observation = robot.get_observation()

            # Build inference frame: converts observation to model format and adds task
            obs_frame = build_inference_frame(
                observation=observation,
                ds_features=dataset_features,
                device=device,
                task=task,
                robot_type="so101_follower"  # Robot type for multi-embodiment models
            )

            # Preprocess: tokenizes task, normalizes, adds batch dimension, moves to device
            obs_processed = preprocessor(obs_frame)

            # Get action from model
            with torch.inference_mode():
                action = model.select_action(obs_processed)

            # Postprocess: unnormalizes action, moves to CPU
            action = postprocessor(action)

            # Convert to robot action format
            robot_action = make_robot_action(action, dataset_features)

            # Debug: Print raw model action values occasionally
            if step % 20 == 0:
                print(f"\nStep {step}: Raw model action values:")
                for key, val in sorted(robot_action.items()):
                    print(f"  {key}: {val:.2f}")

            # Send action to robot (raw model output, no clipping or limiting)
            robot.send_action(robot_action)

            if step % 10 == 0:
                print(f"Step {step}: Executing action...")

            time.sleep(0.033)  # ~30 Hz control loop

    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    finally:
        robot.disconnect()
        print("✅ Disconnected")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SmolVLA inference on real robot")
    parser.add_argument(
        "--task",
        type=str,
        default="Pick up the white block",
        help="Task description for the robot (e.g., 'Pick up the white block')"
    )
    args = parser.parse_args()
    run_smolvla_real(task=args.task)
