from dataclasses import dataclass
from typing import List, Tuple

from .foundation_pose_adapter import FoundationPoseAdapter

@dataclass
class Detection:
    bbox:Tuple[int,int,int,int]; confidence:float; class_id:int; class_name:str; track_id:int|None=None

class PersonDetector:
    def __init__(self, model):
        self.model = model
        self.adapter = FoundationPoseAdapter(model)
    def track(self, frame, conf=0.4, iou=0.5, device='cpu') -> List[Detection]:
        if self.model is None:
            return []
        return self.adapter.track(frame, conf=conf, iou=iou, device=device, classes=[0])
