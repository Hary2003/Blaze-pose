# BlazePose vs MoveNet Pose Detection & Joint Angle POC

A benchmarking and evaluation framework comparing **Google MoveNet (SinglePose Lightning)** and **Google MediaPipe (BlazePose)** for automated exercise tracking, joint angle calculation, and form analysis.

---

## Architecture Overview

```
phyx-poc/
│
├── angle_utils.py          # Shared joint-angle trigonometry & landmark mapping
├── movenet_extractor.py    # MoveNet Lightning video inference pipeline
├── mediapipe_extractor.py  # MediaPipe Pose video inference pipeline
├── compare.py              # Speed, stability (jitter std-dev), and visual plot comparison
├── requirements.txt        # Pinned dependencies (Python 3.11)
│
├── test_clips/             # Video inputs for pose tracking
│   └── knee_extension.mp4
└── outputs/                # Extracted CSV logs & comparison plots
    ├── movenet_knee_angle.csv
    ├── mediapipe_knee_angle.csv
    └── knee_angle_comparison.png
```

---

## Setup & Installation

> **Note:** Requires **Python 3.11** (TensorFlow 2.15 and MediaPipe 0.10.9 provide wheels up to Python 3.11).

```bash
# Clone the repository
git clone https://github.com/Hary2003/Blaze-pose.git
cd Blaze-pose

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Running the Pipelines

### 1. Extract Pose Keypoints with MoveNet
```bash
python movenet_extractor.py test_clips/knee_extension.mp4 knee_angle right
```
Logs 17 keypoint coordinates, per-frame inference duration, and computed joint angle to `outputs/movenet_knee_angle.csv`.

### 2. Extract Pose Keypoints with MediaPipe
```bash
python mediapipe_extractor.py test_clips/knee_extension.mp4 knee_angle right
```
Logs MediaPipe landmarks mapped to the exact same 17-keypoint schema, inference duration, and computed joint angle to `outputs/mediapipe_knee_angle.csv`.

### 3. Compare Speed, Stability, & Track Curves
```bash
# Generate comparison plot and speed benchmark
python compare.py knee_angle

# Or compute stability over a stationary hold frame range (start_frame end_frame)
python compare.py knee_angle 46 70
```
Outputs:
- **Inference Speed**: Average latency (ms/frame) and FPS.
- **Angle Stability**: Standard deviation in degrees over the stationary segment (lower = less jitter).
- **Comparison Curve**: Saved to `outputs/knee_angle_comparison.png`.

---

## Supported Joint Angles

Defined in `angle_utils.py`:
- `knee_angle`: Hip – Knee – Ankle
- `hip_angle`: Shoulder – Hip – Knee
- `shoulder_angle`: Hip – Shoulder – Elbow
- `elbow_angle`: Shoulder – Elbow – Wrist

Supports both `left` and `right` sides.
