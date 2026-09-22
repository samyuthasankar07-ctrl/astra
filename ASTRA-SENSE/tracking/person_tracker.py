import time
from utils.geometry import center,distance,direction,iou
from .track_state import TrackState
class PersonTracker:
    def __init__(self, history_length=30): self.states={}; self.history_length=history_length
    def _match_existing_track(self, bbox, center_point, incoming_track_id=None):
        best_tid = None
        best_score = 0.0
        for tid, state in self.states.items():
            if incoming_track_id is not None and tid == incoming_track_id:
                return tid
            iou_score = iou(bbox, state.bbox)
            size = max(30.0, 0.5 * ((state.bbox[2]-state.bbox[0]) + (state.bbox[3]-state.bbox[1])))
            dist = distance(center_point, state.center)
            score = iou_score * 2.0 - (dist / max(size, 1.0)) * 0.5
            if iou_score > 0.15 or dist < size:
                if score > best_score:
                    best_score = score
                    best_tid = tid
        return best_tid
    def update(self,detections):
        now=time.time(); seen=set()
        for d in detections:
            if d.track_id is None: continue
            c=center(d.bbox)
            target_tid = d.track_id if d.track_id in self.states else self._match_existing_track(d.bbox, c, d.track_id)
            old=self.states.get(target_tid)
            if old:
                step=distance(old.center,c); dt=max(now-old.last_seen,1/30)
                old.previous_center=old.center; old.center=c; old.bbox=d.bbox; old.confidence=d.confidence; old.velocity=step/max(dt,1e-3); old.motion_state='FAST MOVING' if old.velocity>120 else 'MOVING' if old.velocity>5 else 'STATIONARY'; old.direction=direction(c[0]-old.previous_center[0],c[1]-old.previous_center[1]); old.movement_distance+=step; old.age+=1; old.last_seen=now; old.history.append(c)
            else:
                s=TrackState(d.track_id,'person',d.confidence,d.bbox,c,c,last_seen=now); s.history.append(c); self.states[d.track_id]=s
            seen.add(target_tid)
        for tid in list(self.states):
            if tid not in seen and now-self.states[tid].last_seen>1.5: del self.states[tid]
        return list(self.states.values())
