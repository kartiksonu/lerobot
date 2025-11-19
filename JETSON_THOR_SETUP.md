# Jetson Thor (JetPack 7.0) Setup Guide

## Context
Standard LeRobot installation fails on Jetson Thor (JetPack 7.0, Python 3.12, CUDA 13.0).

## Why it Failed
1.  **Missing Wheels:** Official PyTorch wheels for JetPack 7.0/CUDA 13.0 are not on standard PyPI.
2.  **Resolution Error:** `uv` failed to resolve dependencies because `torchvision`/`torchaudio` wheels on the CUDA 13.0 index lack the `+cu130` suffix in their filenames, causing strict matching to fail.
3.  **Version Conflict:** LeRobot's `pyproject.toml` pinned `torch < 2.8.0`. The only working wheels for Thor are `2.9.1+`, causing `uv` to downgrade to broken/CPU versions.

## The Fix
We maintained a fork (`kartiksonu/lerobot`) to persist these environment-specific changes.

### 1. Relaxed Dependencies
Modified `pyproject.toml` to support newer PyTorch versions:
```toml
"torch>=2.2.1,<2.10.0"
"torchvision>=0.21.0,<0.25.0"
```

### 2. Manual Wheel Installation
Forced installation of the specific CUDA 13.0 binaries before installing the package:
```bash
# Create and activate venv
uv venv
source .venv/bin/activate

# Install explicit wheels
uv pip install "torch==2.9.1+cu130" "torchvision==0.24.1" "torchaudio==2.9.1" --index-url https://download.pytorch.org/whl/cu130

# Install LeRobot (editable)
uv pip install -e ".[test, aloha, pusht]"
```

## Current Status
- **PyTorch:** 2.9.1+cu130
- **CUDA:** 13.0 (Active)
- **Device:** NVIDIA Thor

