"""
Runs MediaPipe Pose on a video file.
Outputs one row per frame: timestamp, inference time, all keypoints,
and the computed joint angle you specify.

Usage:
    python mediapipe_extractor.py test_clips/knee_extension.mp4 knee_angle left
"""
import os
import sys
import time
import cv2
import numpy as np
import pandas as pd
import mediapipe as mp

from angle_utils import compute_angle_from_keypoints

# Keypoints to track (aligned with MoveNet's 17 keypoints)
KEYPOINT_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]

mp_pose = mp.solutions.pose

# Mapping of common keypoint names to MediaPipe PoseLandmark enum
MEDIAPIPE_LANDMARK_MAP = {
    "nose": mp_pose.PoseLandmark.NOSE,
    "left_eye": mp_pose.PoseLandmark.LEFT_EYE,
    "right_eye": mp_pose.PoseLandmark.RIGHT_EYE,
    "left_ear": mp_pose.PoseLandmark.LEFT_EAR,
    "right_ear": mp_pose.PoseLandmark.RIGHT_EAR,
    "left_shoulder": mp_pose.PoseLandmark.LEFT_SHOULDER,
    "right_shoulder": mp_pose.PoseLandmark.RIGHT_SHOULDER,
    "left_elbow": mp_pose.PoseLandmark.LEFT_ELBOW,
    "right_elbow": mp_pose.PoseLandmark.RIGHT_ELBOW,
    "left_wrist": mp_pose.PoseLandmark.LEFT_WRIST,
    "right_wrist": mp_pose.PoseLandmark.RIGHT_WRIST,
    "left_hip": mp_pose.PoseLandmark.LEFT_HIP,
    "right_hip": mp_pose.PoseLandmark.RIGHT_HIP,
    "left_knee": mp_pose.PoseLandmark.LEFT_KNEE,
    "right_knee": mp_pose.PoseLandmark.RIGHT_KNEE,
    "left_ankle": mp_pose.PoseLandmark.LEFT_ANKLE,
    "right_ankle": mp_pose.PoseLandmark.RIGHT_ANKLE,
}


def load_model(model_complexity=1):
    """
    model_complexity: 0 = Lite, 1 = Full, 2 = Heavy.
    Default is 1 (Full) for balanced speed and accuracy.
    """
    return mp_pose.Pose(
        static_image_mode=False,
        model_complexity=model_complexity,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )


def run_inference(pose_detector, frame_rgb):
    start = time.perf_counter()
    results = pose_detector.process(frame_rgb)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return results, elapsed_ms


def landmarks_to_dict(results, frame_width, frame_height):
    result = {}
    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark
        for name, lm_enum in MEDIAPIPE_LANDMARK_MAP.items():
            lm = landmarks[lm_enum]
            result[name] = (
                float(lm.x * frame_width),
                float(lm.y * frame_height),
                float(lm.visibility),
            )
    else:
        for name in KEYPOINT_NAMES:
            result[name] = (0.0, 0.0, 0.0)
    return result


def process_video(video_path, angle_name="knee_angle", side="left", model_complexity=1):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video file: {video_path}")

    pose_detector = load_model(model_complexity=model_complexity)
    rows = []
    frame_idx = 0

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, _ = frame.shape

            results, inference_ms = run_inference(pose_detector, frame_rgb)
            kp_dict = landmarks_to_dict(results, w, h)
            angle = compute_angle_from_keypoints(kp_dict, angle_name, side)

            row = {"frame": frame_idx, "inference_ms": inference_ms, "angle": angle}
            for name in KEYPOINT_NAMES:
                x, y, conf = kp_dict[name]
                row[f"{name}_x"] = x
                row[f"{name}_y"] = y
                row[f"{name}_conf"] = conf
            rows.append(row)
            frame_idx += 1
    finally:
        cap.release()
        pose_detector.close()

    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mediapipe_extractor.py <video_path> [angle_name] [side]")
        print("Example: python mediapipe_extractor.py test_clips/knee_extension.mp4 knee_angle left")
        sys.exit(1)

    video_path = sys.argv[1]
    angle_name = sys.argv[2] if len(sys.argv) > 2 else "knee_angle"
    side = sys.argv[3] if len(sys.argv) > 3 else "left"

    os.makedirs("outputs", exist_ok=True)
    df = process_video(video_path, angle_name, side)
    out_path = f"outputs/mediapipe_{angle_name}.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} frames to {out_path}")
    if len(df) > 0 and "inference_ms" in df:
        mean_ms = df['inference_ms'].mean()
        fps = 1000 / mean_ms if mean_ms > 0 else 0
        print(f"Mean inference time: {mean_ms:.2f} ms ({fps:.1f} fps)")
