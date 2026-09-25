# BlazePose vs MoveNet Pose Detection & Joint Angle POC

A benchmarking and evaluation framework comparing **Google MoveNet (SinglePose Lightning)** and **Google MediaPipe (BlazePose)** for automated exercise tracking, joint angle calculation, and form analysis.

---

## Architecture Overview

```
phyx-poc/
│
├── angle_utils.py               # Shared joint-angle trigonometry & landmark mapping
├── movenet_extractor.py         # MoveNet Lightning video inference pipeline
├── mediapipe_extractor.py       # MediaPipe Pose video inference pipeline (Lite, Full, Heavy)
├── compare.py                   # Speed, stability (jitter std-dev), and multi-model visual comparison
├── requirements.txt             # Pinned dependencies (Python 3.11)
├── benchmark_report.html        # Interactive standalone HTML benchmark dashboard
├── benchmark_6_videos_report.md # 6-video batch benchmark report & analysis
├── model_performance_armcycle.md# 3-way pose model comparison report on arm circles
│
├── test_clips/                  # Video inputs for pose tracking (video binaries ignored in git)
│   └── README.md
└── outputs/                     # Extracted CSV logs, comparison plots, and batch datasets
    ├── batch_6_videos/          # 6-video multi-model datasets and individual plots
    └── ...
```

---

## Benchmark Reports & Analysis

Comprehensive benchmarks across multiple movement types are available:
- **Interactive Web Dashboard**: Open [benchmark_report.html](benchmark_report.html) in any web browser for a responsive, interactive visual report with interactive comparison metrics.
- **6-Video Batch Benchmark**: See [benchmark_6_videos_report.md](benchmark_6_videos_report.md) for full analysis of 8,730 frames comparing MoveNet Lightning, MediaPipe Lite, and MediaPipe Full across 6 diverse movement categories.
- **Arm Circles Detailed Evaluation**: See [model_performance_armcycle.md](model_performance_armcycle.md) for detailed evaluation on rotational movements, latency distribution, and self-occlusions.


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

### 2. Extract Pose Keypoints with MediaPipe (Full & Lite)
```bash
# Full model (model_complexity=1, default)
python mediapipe_extractor.py test_clips/armcycle.webm shoulder_angle right 1

# Lite model (model_complexity=0, ultra-fast for mobile)
python mediapipe_extractor.py test_clips/armcycle.webm shoulder_angle right 0
```
- Full saves to `outputs/mediapipe_<angle_name>.csv`
- Lite saves to `outputs/mediapipe_lite_<angle_name>.csv`

### 3. Compare Speed, Stability, & Track Curves
```bash
# Automatically detects all extracted models (MoveNet, MediaPipe Full, MediaPipe Lite)
python compare.py shoulder_angle

# Or compute stability over a stationary hold frame range (start_frame end_frame)
python compare.py shoulder_angle 46 70
```
Outputs:
- **Inference Speed**: Average latency (ms/frame) and FPS across all extracted models.
- **Angle Stability**: Standard deviation in degrees over the stationary segment (lower = less jitter).
- **Comparison Curve**: Multi-model overlay plot saved to `outputs/<angle_name>_comparison.png`.


---

## Supported Joint Angles

Defined in `angle_utils.py`:
- `knee_angle`: Hip – Knee – Ankle
- `hip_angle`: Shoulder – Hip – Knee
- `shoulder_angle`: Hip – Shoulder – Elbow
- `elbow_angle`: Shoulder – Elbow – Wrist

Supports both `left` and `right` sides.
