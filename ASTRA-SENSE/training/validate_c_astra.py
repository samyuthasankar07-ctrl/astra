"""Validate the installed C-ASTRA detector on the labeled validation split."""
from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL = BASE_DIR / "models" / "astronaut.pt"
DATA = BASE_DIR / "training" / "dataset.yaml"

if not MODEL.exists():
    raise SystemExit(f"C-ASTRA model not found: {MODEL}. Train it first.")
if not DATA.exists():
    raise SystemExit(f"Dataset YAML not found: {DATA}")

model = YOLO(str(MODEL))
metrics = model.val(data=str(DATA), imgsz=640, split="val", plots=True)
print("Validation complete.")
print(f"mAP50:     {float(metrics.box.map50):.4f}")
print(f"mAP50-95:  {float(metrics.box.map):.4f}")
print(f"Precision: {float(metrics.box.mp):.4f}")
print(f"Recall:    {float(metrics.box.mr):.4f}")
