import numpy as np
class PoseDetector:
    def __init__(self, model): self.model=model
    def detect(self, frame, conf=0.4, device='cpu'):
        results=self.model(frame, conf=conf, device=device, verbose=False)
        out=[]
        if not results or results[0].keypoints is None:return out
        r=results[0]
        boxes=r.boxes.xyxy.cpu().numpy().tolist() if r.boxes is not None else []
        pts=r.keypoints.xy.cpu().numpy()
        kconf=r.keypoints.conf.cpu().numpy() if r.keypoints.conf is not None else np.ones(pts.shape[:2])
        for i,p in enumerate(pts):
            out.append({'bbox':tuple(map(int,boxes[i])) if i<len(boxes) else None,'keypoints':p.tolist(),'confidence':float(kconf[i].mean()) if i<len(kconf) else 0.0})
        return out
