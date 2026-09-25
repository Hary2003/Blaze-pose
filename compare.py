"""
Compares MoveNet vs MediaPipe output on the same video.
Run the two extractors first, then this.

Usage:
    python compare.py knee_angle
    python compare.py knee_angle 10 25   # optional: specify still frame range (start, end)
"""
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt


def load_results(angle_name):
    """
    Loads all available model extraction CSVs for the given angle_name.
    Recognizes MoveNet, MediaPipe Full, MediaPipe Lite, etc.
    """
    models = {}
    
    movenet_path = f"outputs/movenet_{angle_name}.csv"
    if os.path.exists(movenet_path):
        models["MoveNet Lightning"] = pd.read_csv(movenet_path)

    mediapipe_path = f"outputs/mediapipe_{angle_name}.csv"
    if os.path.exists(mediapipe_path):
        models["MediaPipe Full"] = pd.read_csv(mediapipe_path)

    mediapipe_lite_path = f"outputs/mediapipe_lite_{angle_name}.csv"
    if os.path.exists(mediapipe_lite_path):
        models["MediaPipe Lite"] = pd.read_csv(mediapipe_lite_path)

    mediapipe_heavy_path = f"outputs/mediapipe_heavy_{angle_name}.csv"
    if os.path.exists(mediapipe_heavy_path):
        models["MediaPipe Heavy"] = pd.read_csv(mediapipe_heavy_path)

    if not models:
        raise FileNotFoundError(
            f"No extracted outputs found in 'outputs/' for angle '{angle_name}'.\n"
            f"Please run at least one extractor first:\n"
            f"  python movenet_extractor.py <video_path> {angle_name} <side>\n"
            f"  python mediapipe_extractor.py <video_path> {angle_name} <side> [0|1]"
        )

    return models


def print_speed_comparison(models):
    print("\n=== INFERENCE SPEED ===")
    for name, df in models.items():
        if df.empty or "inference_ms" not in df:
            print(f"{name}: No frame timing data available.")
            continue
        mean_ms = df["inference_ms"].mean()
        fps = (1000 / mean_ms) if mean_ms > 0 else 0
        print(f"{name:20}: {mean_ms:.2f} ms/frame avg  ({fps:.1f} fps)")
    print("(Note: Measured on local host CPU. Relative speed difference remains informative.)")


def print_stability(models, still_frame_range=None):
    """
    Stability = how much the angle wobbles when the person should be
    roughly still (e.g. holding the bottom or top of a rep).
    Pass still_frame_range=(start, end) once you've picked a still segment
    by eye from the angle-over-time plot.
    """
    print("\n=== STABILITY (angle std-dev over a still segment) ===")
    if still_frame_range is None:
        print("No still_frame_range given yet — look at the plot, pick a")
        print("segment where the person is holding still, then re-run with")
        print("still_frame_range=(start_frame, end_frame) or CLI:")
        print("  python compare.py <angle_name> <start_frame> <end_frame>")
        return

    start, end = still_frame_range
    for name, df in models.items():
        segment = df[(df["frame"] >= start) & (df["frame"] <= end)]["angle"].dropna()
        if len(segment) > 1:
            print(f"{name:20}: std-dev = {segment.std():.2f} degrees "
                  f"(lower = more stable, n={len(segment)} frames)")
        elif len(segment) == 1:
            print(f"{name:20}: only 1 valid angle in frame range [{start}, {end}]")
        else:
            print(f"{name:20}: no valid angles found in frame range [{start}, {end}]")


def plot_angle_comparison(models, angle_name):
    os.makedirs("outputs", exist_ok=True)
    plt.figure(figsize=(12, 5))
    
    style_map = {
        "MoveNet Lightning": {"color": "#ff7f0e", "linestyle": "--", "alpha": 0.8},
        "MediaPipe Full":    {"color": "#1f77b4", "linestyle": "-",  "alpha": 0.8},
        "MediaPipe Lite":    {"color": "#2ca02c", "linestyle": "-.", "alpha": 0.8},
        "MediaPipe Heavy":   {"color": "#9467bd", "linestyle": ":",  "alpha": 0.8},
    }

    for name, df in models.items():
        st = style_map.get(name, {"linestyle": "-", "alpha": 0.7})
        plt.plot(df["frame"], df["angle"], label=name, **st)

    plt.xlabel("Frame")
    plt.ylabel(f"{angle_name} (degrees)")
    plt.title(f"{angle_name}: Model Comparison ({', '.join(models.keys())})")
    plt.legend()
    plt.grid(alpha=0.3)
    out_path = f"outputs/{angle_name}_comparison.png"
    plt.savefig(out_path, dpi=120)
    plt.close()
    print(f"\nSaved plot to {out_path}")
    print("Look at this to:")
    print("  1. Sanity-check models are tracking the same movement pattern")
    print("  2. Spot a 'still' segment to plug into print_stability()")
    print("  3. Eyeball where models disagree most")


if __name__ == "__main__":
    angle_name = sys.argv[1] if len(sys.argv) > 1 else "knee_angle"

    still_frame_range = None
    if len(sys.argv) >= 4:
        try:
            still_frame_range = (int(sys.argv[2]), int(sys.argv[3]))
        except ValueError:
            pass

    models = load_results(angle_name)
    print_speed_comparison(models)
    print_stability(models, still_frame_range=still_frame_range)
    plot_angle_comparison(models, angle_name)

