from ultralytics import YOLO
from pathlib import Path
import argparse
p=argparse.ArgumentParser()
p.add_argument("--model",default="yolov8n.pt")
p.add_argument("--epochs",type=int,default=30)
p.add_argument("--imgsz",type=int,default=512)
p.add_argument("--batch",type=int,default=16)
a=p.parse_args()
data=Path(__file__).resolve().parent/"dataset.yaml"
model=YOLO(a.model)
model.train(data=str(data),epochs=a.epochs,imgsz=a.imgsz,batch=a.batch,project=str(Path(__file__).resolve().parent/"runs"),name="c_astra_266")
