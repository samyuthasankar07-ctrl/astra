import time
from utils.geometry import center,distance,direction,iou
from .track_state import TrackState
class ObjectTracker:
    def __init__(self): self.states={}; self.next_id=-1
    def _match_existing_track(self, bbox, center_point, incoming_track_id=None):
        best_tid = None
        best_score = 0.0
        for tid, state in self.states.items():
            if incoming_track_id is not None and tid == incoming_track_id:
                return tid
            iou_score = iou(bbox, state.bbox)
            size = max(20.0, 0.5 * ((state.bbox[2]-state.bbox[0]) + (state.bbox[3]-state.bbox[1])))
            dist = distance(center_point, state.center)
            score = iou_score * 2.0 - (dist / max(size, 1.0)) * 0.5
            if iou_score > 0.10 or dist < size:
                if score > best_score:
                    best_score = score
                    best_tid = tid
        return best_tid
    def update(self,detections):
        now=time.time(); seen=set()
        for d in detections:
            c=center(d.bbox)
            key = d.track_id if d.track_id in self.states else self._match_existing_track(d.bbox, c, d.track_id)
            if key is None:
                key = d.track_id if d.track_id is not None else self.next_id
                if d.track_id is None:
                    self.next_id -= 1
            old=self.states.get(key)
            if old:
                step=distance(old.center,c); dt=max(now-old.last_seen,1/30)
                old.previous_center=old.center; old.center=c; old.bbox=d.bbox; old.confidence=d.confidence; old.velocity=step/dt; old.motion_state='FAST MOVING' if old.velocity>120 else 'MOVING' if old.velocity>5 else 'STATIONARY'; old.direction=direction(c[0]-old.previous_center[0],c[1]-old.previous_center[1]); old.movement_distance+=step; old.age+=1; old.last_seen=now
            else:
                old=TrackState(key,d.class_name,d.confidence,d.bbox,c,c,last_seen=now); old.history.append(c); self.states[key]=old
            old.class_name=d.class_name; old.history.append(c); seen.add(key)
        for tid in list(self.states):
            if tid not in seen and now-self.states[tid].last_seen>1.5: del self.states[tid]
        return list(self.states.values())
