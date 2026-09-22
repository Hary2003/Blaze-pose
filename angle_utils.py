"""
Shared joint-angle math. Both MoveNet and MediaPipe extractors will
output keypoints in this same (x, y, confidence) format, so this
function doesn't care which model produced them.
"""
import numpy as np


def calculate_angle(point_a, point_b, point_c):
    """
    Calculate the angle at point_b, formed by the lines b->a and b->c.
    e.g. for knee angle: point_a=hip, point_b=knee, point_c=ankle.

    Each point is (x, y) in pixel or normalized coordinates.
    Returns angle in degrees, 0-180.
    """
    a = np.array(point_a, dtype=np.float64)
    b = np.array(point_b, dtype=np.float64)
    c = np.array(point_c, dtype=np.float64)

    ba = a - b
    bc = c - b

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    if norm_ba < 1e-8 or norm_bc < 1e-8:
        return 0.0

    cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    angle = np.degrees(np.arccos(cosine_angle))
    return float(angle)


# Standard keypoint name mapping so both extractors can output
# a common dictionary format, e.g. {"left_hip": (x, y, conf), ...}
JOINT_ANGLE_DEFINITIONS = {
    "knee_angle": ("hip", "knee", "ankle"),
    "hip_angle": ("shoulder", "hip", "knee"),
    "shoulder_angle": ("hip", "shoulder", "elbow"),
    "elbow_angle": ("shoulder", "elbow", "wrist"),
}


def compute_angle_from_keypoints(keypoints, angle_name, side="left"):
    """
    keypoints: dict like {"left_hip": (x, y, conf), "left_knee": (x, y, conf), ...}
    angle_name: one of JOINT_ANGLE_DEFINITIONS keys
    side: "left" or "right"
    Returns angle in degrees, or None if any required keypoint is missing/low-confidence.
    """
    if angle_name not in JOINT_ANGLE_DEFINITIONS:
        raise ValueError(f"Unknown angle: {angle_name}. Expected one of {list(JOINT_ANGLE_DEFINITIONS.keys())}")

    joint_a, joint_b, joint_c = JOINT_ANGLE_DEFINITIONS[angle_name]
    keys = [f"{side}_{joint_a}", f"{side}_{joint_b}", f"{side}_{joint_c}"]

    points = []
    for k in keys:
        if k not in keypoints:
            return None
        x, y, conf = keypoints[k]
        if conf < 0.3:  # confidence threshold - tune this later
            return None
        points.append((x, y))

    return calculate_angle(*points)
