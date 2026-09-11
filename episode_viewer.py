"""
LeRobot dataset episode viewer (Streamlit).

Navigate episodes + metadata of a v3.0 LeRobotDataset (SO-101 / helicopter datasets).
Point it at a root folder; it auto-discovers every dataset (any subfolder with meta/info.json),
lets you pick one, scrub any episode by index, and inspect video + metadata + action/state signals.

Run:
    cd /home/ivlabs/lerobot && source .venv/bin/activate
    streamlit run episode_viewer.py
    # optional: preload a root
    streamlit run episode_viewer.py -- --root /home/ivlabs/.cache/huggingface/lerobot/helicopter
"""
from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from lerobot.datasets.lerobot_dataset import LeRobotDataset

DEFAULT_ROOT = "/home/ivlabs/.cache/huggingface/lerobot/helicopter"


# --------------------------- discovery / loading ---------------------------
def find_datasets(root: str) -> list[str]:
    """Return dataset dirs (containing meta/info.json) under `root`, including root itself."""
    root_p = Path(root).expanduser()
    if not root_p.exists():
        return []
    found = []
    if (root_p / "meta" / "info.json").is_file():
        found.append(str(root_p))
    # one and two levels deep
    for info in glob.glob(str(root_p / "*" / "meta" / "info.json")) + glob.glob(
        str(root_p / "*" / "*" / "meta" / "info.json")
    ):
        found.append(str(Path(info).parent.parent))
    return sorted(set(found))


def repo_id_from_path(path: str) -> str:
    p = Path(path)
    return f"{p.parent.name}/{p.name}"


@st.cache_resource(show_spinner="Loading dataset…")
def load_dataset(root: str):
    ds = LeRobotDataset(repo_id_from_path(root), root=root)
    info = json.load(open(Path(root) / "meta" / "info.json"))
    epm = pd.concat(
        [pd.read_parquet(p) for p in glob.glob(f"{root}/meta/episodes/**/*.parquet", recursive=True)]
    ).sort_values("episode_index").reset_index(drop=True)
    return ds, info, epm


@st.cache_data(show_spinner=False, max_entries=4096)
def get_frame(root: str, gi: int, cam: str) -> np.ndarray:
    ds = load_dataset(root)[0]
    t = ds[gi][cam]
    return (t.permute(1, 2, 0).numpy() * 255).astype("uint8")


@st.cache_data(show_spinner=False, max_entries=256)
def get_signals(root: str, from_i: int, to_i: int):
    ds = load_dataset(root)[0]
    acts, states = [], []
    for gi in range(from_i, to_i):
        item = ds[gi]
        acts.append(item["action"].numpy())
        states.append(item["observation.state"].numpy())
    return np.stack(acts), np.stack(states)


def desync_status(ep_row: pd.Series, fps: int, cams: list[str]) -> dict:
    """Return {cam: (video_frames, ok_bool)} using the same formula as the delete tool."""
    out = {}
    L = int(ep_row["length"])
    for cam in cams:
        ff = round(ep_row[f"videos/{cam}/from_timestamp"] * fps)
        tf = round(ep_row[f"videos/{cam}/to_timestamp"] * fps)
        out[cam] = (tf - ff, (tf - ff) == L)
    return out


@st.cache_data(show_spinner="Encoding MP4…", max_entries=32)
def build_mp4(root: str, from_i: int, to_i: int, fps: int, cams: list[str]) -> bytes:
    """Encode a side-by-side (cam order) H.264 mp4 for an episode, browser-playable."""
    import cv2

    tmpdir = Path(tempfile.mkdtemp())
    for k, gi in enumerate(range(from_i, to_i)):
        tiles = [cv2.cvtColor(get_frame(root, gi, c), cv2.COLOR_RGB2BGR) for c in cams]
        combo = np.hstack(tiles)
        cv2.imwrite(str(tmpdir / f"f{k:05d}.png"), combo)
    out = tmpdir / "clip.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-framerate", str(fps), "-i", str(tmpdir / "f%05d.png"),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)],
        check=True, capture_output=True,
    )
    return out.read_bytes()


# --------------------------------- UI --------------------------------------
def parse_cli_root() -> str:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=DEFAULT_ROOT)
    args, _ = ap.parse_known_args(sys.argv[1:])
    return args.root


st.set_page_config(page_title="LeRobot Episode Viewer", layout="wide")
st.title("🎬 LeRobot Episode Viewer")

# ---- sidebar: pick root + dataset + episode ----
with st.sidebar:
    st.header("Dataset")
    root_input = st.text_input("Root folder (dataset or parent)", value=parse_cli_root())
    datasets = find_datasets(root_input)
    if not datasets:
        st.error("No dataset (meta/info.json) found under this path.")
        st.stop()
    ds_choice = st.selectbox(
        "Dataset", datasets, format_func=lambda p: Path(p).name, index=len(datasets) - 1
    )

ds, info, epm = load_dataset(ds_choice)
fps = info["fps"]
cams = [k for k, v in info["features"].items() if v["dtype"] == "video"]
total = info["total_episodes"]

# dataset-level desync summary
desync_eps = [
    int(r["episode_index"])
    for _, r in epm.iterrows()
    if not all(ok for _, ok in desync_status(r, fps, cams).values())
]

with st.sidebar:
    st.divider()
    st.metric("Episodes", total)
    st.metric("Frames", info["total_frames"])
    st.metric("FPS", fps)
    st.caption(f"Cameras: {', '.join(c.split('.')[-1] for c in cams)}")
    if desync_eps:
        st.warning(f"⚠️ {len(desync_eps)} desynced: {desync_eps}")
    else:
        st.success("✓ No desynced episodes")
    st.divider()
    st.header("Episode")
    ep = st.number_input("Index", min_value=0, max_value=total - 1, value=0, step=1)
    c1, c2 = st.columns(2)
    if c1.button("◀ Prev", use_container_width=True) and ep > 0:
        ep -= 1
    if c2.button("Next ▶", use_container_width=True) and ep < total - 1:
        ep += 1

# ---- selected episode ----
row = epm[epm["episode_index"] == ep].iloc[0]
from_i, to_i = int(row["dataset_from_index"]), int(row["dataset_to_index"])
length = int(row["length"])
task = row["tasks"][0] if isinstance(row["tasks"], (list, np.ndarray)) else row["tasks"]
dstat = desync_status(row, fps, cams)
is_desynced = not all(ok for _, ok in dstat.values())

st.subheader(f"Episode {ep}  ·  {length} frames (~{length/fps:.1f}s)"
             + ("   🔴 DESYNCED" if is_desynced else "   🟢 clean"))
st.caption(f"Task: *{task}*")

tab_scrub, tab_video, tab_meta, tab_sig = st.tabs(["🖼 Scrub", "▶ Video", "📋 Metadata", "📈 Signals"])

with tab_scrub:
    f = st.slider("Frame", 0, length - 1, 0)
    gi = from_i + f
    cols = st.columns(len(cams))
    for col, cam in zip(cols, cams):
        col.image(get_frame(ds_choice, gi, cam), caption=cam.split(".")[-1], use_container_width=True)
    st.caption(f"global frame index {gi}  ·  t={f/fps:.2f}s")

with tab_video:
    if st.button("Build & play MP4 (top | wrist)"):
        st.video(build_mp4(ds_choice, from_i, to_i, fps, cams))
        st.download_button(
            "⬇ Download MP4",
            build_mp4(ds_choice, from_i, to_i, fps, cams),
            file_name=f"episode_{ep}.mp4",
            mime="video/mp4",
        )
    else:
        st.info("Click to encode this episode (cached after first build).")

with tab_meta:
    left, right = st.columns(2)
    with left:
        st.write("**Episode metadata**")
        st.json({
            "episode_index": ep,
            "length": length,
            "seconds": round(length / fps, 2),
            "global_frame_range": [from_i, to_i],
            "task": task,
        })
    with right:
        st.write("**Video segment check** (video frames vs length)")
        st.table(pd.DataFrame([
            {"camera": c.split(".")[-1], "length": length, "video_frames": vf,
             "status": "OK" if ok else "DESYNC"}
            for c, (vf, ok) in dstat.items()
        ]))
    st.write("**Per-episode brightness** (stored stats, mean over channels ×255)")
    bright = {}
    for c in cams:
        key = f"stats/{c}/mean"
        if key in row and row[key] is not None:
            bright[c.split(".")[-1]] = round(float(np.mean(row[key])) * 255, 1)
    st.write(bright)

with tab_sig:
    acts, states = get_signals(ds_choice, from_i, to_i)
    st.write("**Action** (6-DoF)")
    st.line_chart(pd.DataFrame(acts, columns=[f"a{i}" for i in range(acts.shape[1])]))
    st.write("**Observation.state** (6-DoF)")
    st.line_chart(pd.DataFrame(states, columns=[f"s{i}" for i in range(states.shape[1])]))
