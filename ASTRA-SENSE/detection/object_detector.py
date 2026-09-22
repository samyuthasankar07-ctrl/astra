from __future__ import annotations

from typing import Iterable

from .foundation_pose_adapter import FoundationPoseAdapter


class ObjectDetector:
    """Run the specialist C-ASTRA detector and the general COCO detector together.

    Person detection is intentionally excluded here because PersonDetector owns class 0.
    Detections from the specialist model are preferred when both models see the same
    object; near-duplicate boxes are suppressed with a simple IoU test.
    """

    def __init__(self, custom_model=None, general_model=None, custom_error=''):
        self.custom_model = custom_model
        self.general_model = general_model
        self.custom_error = custom_error
        self.custom_adapter = FoundationPoseAdapter(custom_model)
        self.general_adapter = FoundationPoseAdapter(general_model)
        self.ignored_classes = {"person"}

    @staticmethod
    def _iou(a, b):
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
        inter = iw * ih
        if inter <= 0:
            return 0.0
        aa = max(1, (ax2-ax1) * (ay2-ay1))
        ab = max(1, (bx2-bx1) * (by2-by1))
        return inter / float(aa + ab - inter)

    def _deduplicate(self, detections):
        result = []
        for det in sorted(detections, key=lambda d: float(d.confidence), reverse=True):
            duplicate = False
            for kept in result:
                if str(det.class_name).lower() == str(kept.class_name).lower() and self._iou(det.bbox, kept.bbox) > 0.55:
                    duplicate = True
                    break
            if not duplicate:
                result.append(det)
        return result

    def track(self, frame, conf=0.4, iou=0.5, device="cpu", imgsz=640):
        custom_detections = []
        general_detections = []

        if self.custom_model is not None:
            custom_detections = self.custom_adapter.track(frame, conf=conf, iou=iou, device=device, imgsz=imgsz)

        if self.general_model is not None:
            general_detections = self.general_adapter.track(frame, conf=conf, iou=iou, device=device, imgsz=imgsz)

        # Model class IDs are independent; class 0 is Astronaut in C-ASTRA.
        general_detections = [
            d for d in general_detections
            if str(d.class_name).lower() not in self.ignored_classes
            and getattr(d, "class_id", None) != 0
        ]
        return self._deduplicate(custom_detections + general_detections)
