"""Train the C-ASTRA 266-class YOLO detector.

This script intentionally refuses to train when images/labels are missing.
That prevents a fake/empty model from being reported as trained.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil

from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_FILE = BASE_DIR / "training" / "dataset.yaml"
DATASET_DIR = BASE_DIR / "training" / "dataset"
BASE_MODEL = BASE_DIR.parent / "yolov8n.pt"
OUTPUT_DIR = BASE_DIR / "models"


def count_images(folder: Path) -> int:
    return sum(1 for p in folder.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"})


def verify_dataset() -> None:
    if not DATASET_FILE.exists():
        raise SystemExit(f"Dataset YAML not found: {DATASET_FILE}")

    train_images = DATASET_DIR / "images" / "train"
    val_images = DATASET_DIR / "images" / "val"
    train_labels = DATASET_DIR / "labels" / "train"
    val_labels = DATASET_DIR / "labels" / "val"

    counts = {
        "train_images": count_images(train_images),
        "val_images": count_images(val_images),
        "train_labels": len(list(train_labels.glob("*.txt"))),
        "val_labels": len(list(val_labels.glob("*.txt"))),
    }
    print("Dataset:", counts)

    if counts["train_images"] == 0 or counts["val_images"] == 0:
        raise SystemExit(
            "No train/validation images found. Add real labeled images first; "
            "the project will not claim a trained detector without them."
        )
    if counts["train_labels"] < counts["train_images"] or counts["val_labels"] < counts["val_images"]:
        raise SystemExit("Every image needs a matching YOLO .txt label file.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default=None, help="cpu, 0, 0,1, etc.; omit for auto")
    args = parser.parse_args()

    verify_dataset()

    if not BASE_MODEL.exists():
        raise SystemExit(f"Base YOLO model not found: {BASE_MODEL}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    model = YOLO(str(BASE_MODEL))

    train_kwargs = dict(
        data=str(DATASET_FILE),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=str(OUTPUT_DIR),
        name="c_astra_training",
        exist_ok=True,
    )
    if args.device:
        train_kwargs["device"] = args.device

    model.train(**train_kwargs)

    best_model = OUTPUT_DIR / "c_astra_training" / "weights" / "best.pt"
    custom_model = OUTPUT_DIR / "astronaut.pt"
    if not best_model.exists():
        raise SystemExit(f"Training completed but best.pt was not found: {best_model}")

    shutil.copy2(best_model, custom_model)
    print(f"C-ASTRA model installed: {custom_model}")


if __name__ == "__main__":
    main()
