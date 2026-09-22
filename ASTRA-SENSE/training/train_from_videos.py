import argparse
from pathlib import Path
import shutil

import cv2
from ultralytics import YOLO


BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / 'training' / 'video_dataset'
OUTPUT_DIR = BASE_DIR / 'models'


def extract_frames(video_path, image_dir, every_seconds):
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f'Unable to open video: {video_path}')

    image_dir.mkdir(parents=True, exist_ok=True)
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    frame_step = max(1, round(fps * every_seconds))
    frame_index = 0
    saved = 0

    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if frame_index % frame_step == 0:
            output_path = image_dir / f'{video_path.stem}_{frame_index:08d}.jpg'
            if cv2.imwrite(str(output_path), frame):
                saved += 1
        frame_index += 1

    capture.release()
    return saved


def require_labels(image_dir, label_dir):
    label_dir.mkdir(parents=True, exist_ok=True)
    images = list(image_dir.glob('*.jpg'))
    missing = [image for image in images if not (label_dir / f'{image.stem}.txt').exists()]
    if missing:
        raise RuntimeError(
            f'{len(missing)} frames in {image_dir} have no matching labels in {label_dir}. '
            'Label all extracted frames before training. Example: ' 
            f'{image_dir.name}/image_000001.jpg -> {label_dir.name}/image_000001.txt'
        )


def write_dataset_yaml(dataset_file):
    dataset_file.write_text(
        'path: ' + str(DATASET_DIR).replace('\\', '/') + '\n'
        'train: images/train\n'
        'val: images/val\n\n'
        'names:\n'
        '  0: person\n'
        '  1: astronaut\n'
        '  2: helmet\n',
        encoding='utf-8',
    )


def main():
    parser = argparse.ArgumentParser(description='Extract and train YOLO data from separate videos')
    parser.add_argument('--train-video', type=Path, required=True)
    parser.add_argument('--val-video', type=Path, required=True)
    parser.add_argument('--every', type=float, default=0.5, help='Seconds between extracted frames')
    parser.add_argument('--epochs', type=int, default=100)
    args = parser.parse_args()

    if args.every <= 0 or args.epochs <= 0:
        parser.error('--every and --epochs must be greater than zero')

    train_images = DATASET_DIR / 'images' / 'train'
    val_images = DATASET_DIR / 'images' / 'val'
    train_labels = DATASET_DIR / 'labels' / 'train'
    val_labels = DATASET_DIR / 'labels' / 'val'
    for folder in (DATASET_DIR, train_images, val_images, train_labels, val_labels):
        folder.mkdir(parents=True, exist_ok=True)
    train_count = extract_frames(args.train_video, train_images, args.every)
    val_count = extract_frames(args.val_video, val_images, args.every)
    print(f'Extracted {train_count} training frames and {val_count} validation frames.')
    require_labels(train_images, train_labels)
    require_labels(val_images, val_labels)

    dataset_file = DATASET_DIR / 'dataset.yaml'
    write_dataset_yaml(dataset_file)
    model = YOLO(str(BASE_DIR.parent / 'yolov8n.pt'))
    model.train(
        data=str(dataset_file),
        epochs=args.epochs,
        imgsz=640,
        batch=8,
        project=str(OUTPUT_DIR),
        name='video_object_training',
        exist_ok=True,
    )
    best_model = OUTPUT_DIR / 'video_object_training' / 'weights' / 'best.pt'
    custom_model = OUTPUT_DIR / 'astronaut.pt'
    if best_model.exists():
        shutil.copyfile(best_model, custom_model)
        print(f'Updated application model: {custom_model}')


if __name__ == '__main__':
    main()