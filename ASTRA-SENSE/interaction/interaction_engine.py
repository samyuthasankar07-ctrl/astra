import time
from .interaction_state import InteractionState
from .interaction_rules import infer
from utils.geometry import distance
class InteractionEngine:
    def __init__(self): self.states={}
    def update(self,persons,objects):
        now=time.time(); active=[]; seen=set()
        for p in persons:
            for o in objects:
                # Approximate hand proximity from wrist keypoints when pose exists.
                hand_d=9999.0
                if p.pose:
                    pts=p.pose.get('keypoints',[])
                    for idx in (9,10):
                        if idx<len(pts): hand_d=min(hand_d,distance(tuple(pts[idx]),o.center))
                state,score=infer(p,o,hand_d)
                key=(p.track_id,o.track_id)
                prev=self.states.get(key)
                if prev:
                    old_state=prev.state
                    hist=list(o.history)
                    if old_state == 'PUTTING_DOWN' and hand_d > 90 and o.velocity < 20:
                        state = 'RELEASED'; score = .84
                    elif old_state in ('HOLDING','CARRYING') and hand_d > 95 and o.velocity > 70:
                        state = 'THROWING' if o.velocity > 120 else 'DROPPING'; score = .88
                    elif old_state in ('HOLDING','CARRYING') and hand_d > 90 and o.velocity < 20:
                        state = 'PUTTING_DOWN'; score = .82
                    elif old_state in ('NEAR','REACHING','NONE') and hand_d < 60 and len(hist) >= 2 and hist[-1][1] < hist[-2][1] - 4:
                        state = 'PICKING_UP'; score = .80
                    elif hand_d < 70 and p.velocity < 20 and o.velocity > 10 and o.direction not in ('NONE', p.direction):
                        state = 'PULLING'; score = .68

                if state == 'NONE':
                    continue
                if getattr(p, 'confidence', 1.0) < 0.45 or getattr(o, 'confidence', 1.0) < 0.45:
                    continue
                seen.add(key)
                s=prev
                if not s: s=InteractionState(p.track_id,o.track_id,first_seen=now,last_seen=now); self.states[key]=s
                if state==s.state:s.duration=now-s.first_seen
                else:
                    # Temporal persistence prevents one-frame semantic flips.
                    s.state=state; s.first_seen=now; s.duration=0.0
                s.last_seen=now; s.score=score; s.previous_distance=distance(p.center,o.center)
                active.append(s)
        for k in list(self.states):
            if k not in seen and now-self.states[k].last_seen>1.0: del self.states[k]
        return active
