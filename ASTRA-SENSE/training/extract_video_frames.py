import argparse
from pathlib import Path

import cv2


def extract_frames(video_path, output_dir, every_seconds):
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f'Unable to open video: {video_path}')

    output_dir.mkdir(parents=True, exist_ok=True)
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    frame_step = max(1, round(fps * every_seconds))
    frame_index = 0
    saved_count = 0

    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if frame_index % frame_step == 0:
            output_path = output_dir / f'video_{frame_index:08d}.jpg'
            if cv2.imwrite(str(output_path), frame):
                saved_count += 1
        frame_index += 1

    capture.release()
    return saved_count


def main():
    parser = argparse.ArgumentParser(description='Extract YOLO training frames from a video')
    parser.add_argument('video', type=Path)
    parser.add_argument('--output', type=Path, default=Path('training/dataset/images/train'))
    parser.add_argument('--every', type=float, default=0.5, help='Seconds between saved frames')
    args = parser.parse_args()

    if args.every <= 0:
        parser.error('--every must be greater than zero')
    saved_count = extract_frames(args.video, args.output, args.every)
    print(f'Saved {saved_count} frames to {args.output}')
    print('Label the saved frames before starting YOLO training.')


if __name__ == '__main__':
    main()