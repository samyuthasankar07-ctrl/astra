from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Sequence, Tuple


@dataclass
class Detection:
    bbox: Tuple[int, int, int, int]
    confidence: float
    class_id: int
    class_name: str
    track_id: int | None = None


class FoundationPoseAdapter:
    def __init__(self, model=None, device: str = 'cpu'):
        self.model = model
        self.device = device
        self.available = model is not None

    @staticmethod
    def _as_tuple(value: Sequence[float] | Iterable[float], fallback=(0, 0, 0, 0)) -> Tuple[int, int, int, int]:
        values = list(value)
        if len(values) < 4:
            return tuple(int(x) for x in fallback)
        return tuple(int(round(v)) for v in values[:4])

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except Exception:
            return default

    @classmethod
    def _coerce_result(cls, raw_result: Any) -> List[Detection]:
        detections: List[Detection] = []

        if raw_result is None:
            return detections

        if isinstance(raw_result, dict):
            items = raw_result.get('detections') or raw_result.get('results') or raw_result.get('objects') or []
        elif isinstance(raw_result, (list, tuple)):
            items = raw_result
        else:
            items = getattr(raw_result, 'detections', None) or getattr(raw_result, 'results', None) or getattr(raw_result, 'objects', None) or []

        if not items:
            return detections

        for item in items:
            boxes = getattr(item, 'boxes', None)
            if boxes is not None:
                xyxy = boxes.xyxy.cpu().tolist() if getattr(boxes, 'xyxy', None) is not None else []
                confidences = boxes.conf.cpu().tolist() if getattr(boxes, 'conf', None) is not None else []
                class_ids = boxes.cls.cpu().tolist() if getattr(boxes, 'cls', None) is not None else []
                track_ids = boxes.id.cpu().tolist() if getattr(boxes, 'id', None) is not None else [None] * len(xyxy)
                names = getattr(item, 'names', {})
                for index, bbox in enumerate(xyxy):
                    class_id = int(class_ids[index]) if index < len(class_ids) else 0
                    class_name = str(names.get(class_id, class_id)) if isinstance(names, dict) else str(class_id)
                    track_id = track_ids[index] if index < len(track_ids) else None
                    detections.append(Detection(cls._as_tuple(bbox), cls._safe_float(confidences[index] if index < len(confidences) else 0.0), class_id, class_name, int(track_id) if track_id is not None else None))
                continue
            if isinstance(item, dict):
                bbox = item.get('bbox') or item.get('box') or item.get('xyxy') or (0, 0, 0, 0)
                conf = item.get('confidence') or item.get('score') or 0.0
                class_id = item.get('class_id') if item.get('class_id') is not None else item.get('class') or 0
                class_name = item.get('class_name') or item.get('label') or 'object'
                track_id = item.get('track_id')
                detections.append(Detection(cls._as_tuple(bbox), cls._safe_float(conf), int(class_id), str(class_name), int(track_id) if track_id is not None else None))
                continue

            if hasattr(item, 'bbox') or hasattr(item, 'box') or hasattr(item, 'xyxy'):
                bbox = getattr(item, 'bbox', None) or getattr(item, 'box', None) or getattr(item, 'xyxy', None) or (0, 0, 0, 0)
                conf = getattr(item, 'confidence', None)
                if conf is None:
                    conf = getattr(item, 'score', None)
                if conf is None:
                    conf = 0.0
                class_id = getattr(item, 'class_id', None)
                if class_id is None:
                    class_id = getattr(item, 'class', 0)
                class_name = getattr(item, 'class_name', None) or getattr(item, 'label', None) or 'object'
                track_id = getattr(item, 'track_id', None)
                detections.append(Detection(cls._as_tuple(bbox), cls._safe_float(conf), int(class_id), str(class_name), int(track_id) if track_id is not None else None))

        return detections

    def predict(self, frame, conf=0.4, device='cpu', classes=None):
        if self.model is None:
            return []

        try:
            result = self.model(frame, conf=conf, device=device, classes=classes)
        except TypeError:
            try:
                result = self.model(frame, conf_threshold=conf, device=device, classes=classes)
            except TypeError:
                result = self.model(frame, conf=conf, device=device)
        except Exception:
            return []

        return self._coerce_result(result)

    def track(self, frame, conf=0.4, iou=0.5, device='cpu', classes=None, imgsz=640):
        if self.model is None:
            return []

        try:
            result = self.model.track(frame, conf=conf, iou=iou, device=device, classes=classes, imgsz=imgsz, persist=True)
        except TypeError:
            try:
                result = self.model.track(frame, conf_threshold=conf, iou=iou, device=device, classes=classes, imgsz=imgsz, persist=True)
            except TypeError:
                result = self.model.track(frame, conf=conf, iou=iou, device=device)
        except Exception:
            return []

        return self._coerce_result(result)
