# Experiment Log: Model Verification & Inference Readiness

## 1. Model Verification
**Goal**: Confirm that the models installed/downloaded match our expectations for the Thor + RealSense + SO-ARM101 setup.

### Installed Models
- **SmolVLA**: Installed via `lerobot` (native).
- **OpenPi (Pi0.5)**: Cloned to `/home/thor/openpi`.
- **Groot N1.5**: Cloned to `/home/thor/Isaac-GR00T`.

### Verification Status
- [x] **SmolVLA**: Pretrained weights present.
- [x] **Groot**: Weights downloaded. **Code installed & operational**.
    - Venv created at `/home/thor/Isaac-GR00T/.venv`.
    - Flash Attention compiled (Pending Arch Fix).
    - Torch 2.9.1+cu130 verified.
    - LeRobot & Feetech drivers linked.
    - Metadata patched (`new_embodiment` added with `webcam` key).

## 2. Inference Readiness
**Goal**: Determine if we can run "Pick up the white block" type commands *now* with the current hardware.

### Hardware Capability
- **Robot**: SO-ARM101 (Joint control ready).
- **Camera**: RealSense D435i (RGB-D ready).
- **Compute**: Jetson Thor (CUDA 13.0).

### Readiness Checks & Gaps

#### **A. Groot N1.5 (Operational)**
- **Status**: **Blocked by CUDA Architecture Mismatch (Flash Attention)**.
- **Setup**:
    - Server: Hosted locally on Thor.
    - Client: Connects to Robot & Camera.

**Running Instructions (Once Fixed):**

**Terminal 1: Policy Server**
(This loads the model and waits for requests)
```bash
cd /home/thor/Isaac-GR00T
source .venv/bin/activate
python scripts/inference_service.py \
    --model_path nvidia/GR00T-N1.5-3B \
    --server \
    --data_config so100 \
    --embodiment_tag new_embodiment
```

**Terminal 2: Robot Client**
(This connects to hardware and sends images to server)
```bash
cd /home/thor/Isaac-GR00T
source .venv/bin/activate
# Note: Camera key 'webcam' matches the metadata config we injected
PYTHONPATH=.:gr00t/eval:/home/thor/librealsense/build/Release python examples/SO-100/eval_lerobot.py \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=thor_follower_arm \
    --robot.cameras="{ webcam: {type: intelrealsense, serial_number_or_name: '844212071286', fps: 30, width: 640, height: 480}}" \
    --policy_host=localhost \
    --lang_instruction="Pick up the white block"
```

#### **B. SmolVLA (Backup)**
- **Status**: Installed, but requires config tweaks for single camera.

#### **C. OpenPi (Skipped)**
- **Status**: Not prioritized.

## 3. Conclusion & Next Steps
We have successfully deployed the **Groot N1.5** stack on the Jetson Thor. The environment handles the complex intersection of:
-   Bleeding-edge Torch (2.9.1)
-   RealSense Drivers (Patched via PYTHONPATH)
-   Feetech Motor Control
-   Decord (Mocked)

**Critical Blocker:**
The system crashes at runtime with `CUDA error: no kernel image is available`.
**Cause:** `flash-attn` was compiled without explicit architecture flags for Jetson Thor (Blackwell/Orin).

## Appendix: Pending Tasks
To resolve the CUDA error, run the following command block to rebuild Flash Attention correctly (~2 hours):

```bash
# 1. Restore Torch (if overwritten)
uv pip install "torch==2.9.1+cu130" "torchvision==0.24.1" "torchaudio==2.9.1" --index-url https://download.pytorch.org/whl/cu130

# 2. Rebuild Flash Attention with Correct Arch
export MAX_JOBS=2
export TORCH_CUDA_ARCH_LIST="8.7 9.0"
export CUDA_HOME=/usr/local/cuda
uv pip install "flash-attn>=2.5.9,<3.0.0" --no-build-isolation --no-deps --no-cache --force-reinstall
```
