"""ASTRA-SENSE dependency/model smoke test."""
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

print("Checking Python imports...")
import cv2
import numpy as np
import torch
from ultralytics import YOLO

print("OpenCV:", cv2.__version__)
print("NumPy:", np.__version__)
print("Torch:", torch.__version__)
print("Ultralytics:", __import__("ultralytics").__version__)

for name in ("yolov8n.pt", "yolov8n-pose.pt", "astronaut.pt"):
    p = BASE / "models" / name
    if not p.exists():
        p = BASE.parent / name
    print(f"{name}: {'OK' if p.exists() else 'MISSING'}")

# Load models; this catches corrupt/incompatible .pt files without opening a camera.
YOLO(str(BASE / "models" / "astronaut.pt"))
from config import C_ASTRA_CLASS_COUNT, C_ASTRA_FALLBACK_MODEL_PATH, C_ASTRA_MODEL_PATH
c_astra_path = C_ASTRA_MODEL_PATH if C_ASTRA_MODEL_PATH.exists() else C_ASTRA_FALLBACK_MODEL_PATH
c_astra = YOLO(str(c_astra_path))
if len(c_astra.names) != C_ASTRA_CLASS_COUNT:
    raise RuntimeError(f"Expected {C_ASTRA_CLASS_COUNT} C-ASTRA classes, got {len(c_astra.names)}")
print(f"C-ASTRA model load: OK ({c_astra_path})")
print("SMOKE TEST PASSED")
