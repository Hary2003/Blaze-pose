"""
Runs MoveNet (Lightning variant, from TF-Hub) on a video file.
Outputs one row per frame: timestamp, inference time, all keypoints,
and the computed joint angle you specify.

Usage:
    python movenet_extractor.py test_clips/knee_extension.mp4 knee_angle left
"""
import os
import sys
import time
import cv2
import numpy as np
import pandas as pd
import tensorflow as tf
import tensorflow_hub as hub

from angle_utils import compute_angle_from_keypoints

# MoveNet's 17 keypoints, in the order the model outputs them
MOVENET_KEYPOINT_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]

# Lightning = faster, less accurate. Thunder = slower, more accurate.
# Test both eventually - start with Lightning since it's the on-device candidate.
MODEL_URL = "https://tfhub.dev/google/movenet/singlepose/lightning/4"
INPUT_SIZE = 192  # Lightning uses 192x192; Thunder uses 256x256


def load_model():
    model = hub.load(MODEL_URL)
    return model.signatures["serving_default"]


def run_inference(movenet, frame):
    img = tf.image.resize_with_pad(np.expand_dims(frame, axis=0), INPUT_SIZE, INPUT_SIZE)
    img = tf.cast(img, dtype=tf.int32)

    start = time.perf_counter()
    outputs = movenet(img)
    elapsed_ms = (time.perf_counter() - start) * 1000

    # shape: (1, 1, 17, 3) -> (y, x, confidence) normalized 0-1
    keypoints = outputs["output_0"].numpy()[0, 0, :, :]
    return keypoints, elapsed_ms


def keypoints_to_dict(keypoints, frame_width, frame_height):
    result = {}
    for i, name in enumerate(MOVENET_KEYPOINT_NAMES):
        y, x, conf = keypoints[i]
        result[name] = (float(x * frame_width), float(y * frame_height), float(conf))
    return result


def process_video(video_path, angle_name="knee_angle", side="left"):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video file: {video_path}")

    movenet = load_model()
    rows = []
    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape

        keypoints, inference_ms = run_inference(movenet, frame_rgb)
        kp_dict = keypoints_to_dict(keypoints, w, h)
        angle = compute_angle_from_keypoints(kp_dict, angle_name, side)

        row = {"frame": frame_idx, "inference_ms": inference_ms, "angle": angle}
        for name in MOVENET_KEYPOINT_NAMES:
            x, y, conf = kp_dict[name]
            row[f"{name}_x"] = x
            row[f"{name}_y"] = y
            row[f"{name}_conf"] = conf
        rows.append(row)
        frame_idx += 1

    cap.release()
    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python movenet_extractor.py <video_path> [angle_name] [side]")
        print("Example: python movenet_extractor.py test_clips/knee_extension.mp4 knee_angle left")
        sys.exit(1)

    video_path = sys.argv[1]
    angle_name = sys.argv[2] if len(sys.argv) > 2 else "knee_angle"
    side = sys.argv[3] if len(sys.argv) > 3 else "left"

    os.makedirs("outputs", exist_ok=True)
    df = process_video(video_path, angle_name, side)
    out_path = f"outputs/movenet_{angle_name}.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} frames to {out_path}")
    if len(df) > 0 and "inference_ms" in df:
        mean_ms = df['inference_ms'].mean()
        fps = 1000 / mean_ms if mean_ms > 0 else 0
        print(f"Mean inference time: {mean_ms:.2f} ms ({fps:.1f} fps)")
