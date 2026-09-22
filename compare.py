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
    movenet_path = f"outputs/movenet_{angle_name}.csv"
    mediapipe_path = f"outputs/mediapipe_{angle_name}.csv"

    if not os.path.exists(movenet_path):
        raise FileNotFoundError(
            f"Could not find MoveNet output at '{movenet_path}'.\n"
            f"Please run the MoveNet extractor first:\n"
            f"  python movenet_extractor.py <video_path> {angle_name} <side>"
        )
    if not os.path.exists(mediapipe_path):
        raise FileNotFoundError(
            f"Could not find MediaPipe output at '{mediapipe_path}'.\n"
            f"Please run the MediaPipe extractor first:\n"
            f"  python mediapipe_extractor.py <video_path> {angle_name} <side>"
        )

    movenet_df = pd.read_csv(movenet_path)
    mediapipe_df = pd.read_csv(mediapipe_path)
    return movenet_df, mediapipe_df


def print_speed_comparison(movenet_df, mediapipe_df):
    print("\n=== INFERENCE SPEED ===")
    for name, df in [("MoveNet", movenet_df), ("MediaPipe", mediapipe_df)]:
        if df.empty or "inference_ms" not in df:
            print(f"{name}: No frame timing data available.")
            continue
        mean_ms = df["inference_ms"].mean()
        fps = (1000 / mean_ms) if mean_ms > 0 else 0
        print(f"{name}: {mean_ms:.2f} ms/frame avg  ({fps:.1f} fps)")
    print("(Remember: this is on your laptop, not the target Android device.")
    print(" Relative speed difference between models is still informative,")
    print(" but absolute fps will be different/lower on-device.)")


def print_stability(movenet_df, mediapipe_df, still_frame_range=None):
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
    for name, df in [("MoveNet", movenet_df), ("MediaPipe", mediapipe_df)]:
        segment = df[(df["frame"] >= start) & (df["frame"] <= end)]["angle"].dropna()
        if len(segment) > 1:
            print(f"{name}: std-dev = {segment.std():.2f} degrees "
                  f"(lower = more stable, n={len(segment)} frames)")
        elif len(segment) == 1:
            print(f"{name}: only 1 valid angle in frame range [{start}, {end}]")
        else:
            print(f"{name}: no valid angles found in frame range [{start}, {end}]")


def plot_angle_comparison(movenet_df, mediapipe_df, angle_name):
    os.makedirs("outputs", exist_ok=True)
    plt.figure(figsize=(12, 5))
    plt.plot(movenet_df["frame"], movenet_df["angle"], label="MoveNet", alpha=0.8)
    plt.plot(mediapipe_df["frame"], mediapipe_df["angle"], label="MediaPipe", alpha=0.8)
    plt.xlabel("Frame")
    plt.ylabel(f"{angle_name} (degrees)")
    plt.title(f"{angle_name}: MoveNet vs MediaPipe")
    plt.legend()
    plt.grid(alpha=0.3)
    out_path = f"outputs/{angle_name}_comparison.png"
    plt.savefig(out_path, dpi=120)
    plt.close()
    print(f"\nSaved plot to {out_path}")
    print("Look at this to:")
    print("  1. Sanity-check both models are tracking the same movement pattern")
    print("  2. Spot a 'still' segment to plug into print_stability()")
    print("  3. Eyeball where the two models disagree most")


if __name__ == "__main__":
    angle_name = sys.argv[1] if len(sys.argv) > 1 else "knee_angle"

    # Support optional CLI still frame range: python compare.py knee_angle 40 70
    still_frame_range = None
    if len(sys.argv) >= 4:
        try:
            still_frame_range = (int(sys.argv[2]), int(sys.argv[3]))
        except ValueError:
            pass

    movenet_df, mediapipe_df = load_results(angle_name)
    print_speed_comparison(movenet_df, mediapipe_df)

    # You can pass still_frame_range directly here or via CLI
    # e.g., still_frame_range=(40, 70)
    print_stability(movenet_df, mediapipe_df, still_frame_range=still_frame_range)

    plot_angle_comparison(movenet_df, mediapipe_df, angle_name)
