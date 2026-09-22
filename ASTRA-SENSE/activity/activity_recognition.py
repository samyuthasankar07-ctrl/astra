import math
from utils.geometry import distance
class ActivityRecognizer:
    def recognize(self,p):
        if p.velocity>250:return 'RUNNING'
        if p.velocity>25:return 'WALKING'
        pose=p.pose
        if pose:
            pts=pose.get('keypoints',[])
            if len(pts)>=17:
                # COCO: shoulders 5,6; hips 11,12; knees 13,14; ankles 15,16
                sh=((pts[5][0]+pts[6][0])/2,(pts[5][1]+pts[6][1])/2)
                hp=((pts[11][0]+pts[12][0])/2,(pts[11][1]+pts[12][1])/2)
                kn=((pts[13][0]+pts[14][0])/2,(pts[13][1]+pts[14][1])/2)
                torso=distance(sh,hp); leg=distance(hp,kn)
                if torso>0 and leg<torso*0.8:return 'SITTING'
                if torso>0 and hp[1]-sh[1]<torso*0.25:return 'BENDING'
                hands=[pts[i] for i in (9,10) if i<len(pts)]
                if hands and any(distance(tuple(h),tuple(sh))>torso*0.9 for h in hands):return 'REACHING'
        return 'STATIONARY' if p.velocity<5 else 'IDLE'
