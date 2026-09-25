# Test Clips Directory

This directory stores test video clips used for pose estimation benchmarking (e.g. MoveNet vs MediaPipe BlazePose Lite/Full).

## Note on Video Binaries
Video files (`*.mp4`, `*.webm`, `*.mov`, etc.) are ignored by `.gitignore` to keep the repository lightweight and prevent large binary bloat.

To run benchmarks locally:
1. Place exercise video files in this folder (e.g. `arm-circles.mp4`, `knee_extension.mp4`).
2. Run extraction commands:
   ```bash
   # MediaPipe Pose Lite
   python mediapipe_extractor.py test_clips/<video_name>.mp4 <joint_angle> <side> 0

   # MoveNet Lightning
   python movenet_extractor.py test_clips/<video_name>.mp4 <joint_angle> <side>
   ```
3. Run comparison:
   ```bash
   python compare.py <joint_angle>
   ```
