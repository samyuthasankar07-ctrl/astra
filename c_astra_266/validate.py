from ultralytics import YOLO
from pathlib import Path
import argparse
p=argparse.ArgumentParser()
p.add_argument("--weights",required=True)
a=p.parse_args()
root=Path(__file__).resolve().parent
model=YOLO(a.weights)
print(model.val(data=str(root/"dataset.yaml"),split="test"))
