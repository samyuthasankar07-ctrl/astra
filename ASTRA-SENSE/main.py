# pyright: reportMissingImports=false
import sys,time,threading,queue,traceback
from pathlib import Path
import cv2
import numpy as np
from config import *
from utils.logger import get_logger
from utils.fps import FPSCounter
from camera.camera_detector import scan_local
from camera.camera_manager import CameraManager
from detection.person_detector import PersonDetector
from detection.object_detector import ObjectDetector
from detection.pose_detector import PoseDetector
from tracking.person_tracker import PersonTracker
from tracking.object_tracker import ObjectTracker
from activity.activity_recognition import ActivityRecognizer
from interaction.interaction_engine import InteractionEngine
from context.context_engine import ContextEngine
from context.analysis_types import FrameAnalysisResult
from speech.speech_manager import SpeechManager
from utils.geometry import iou
from data.detection_store import save_detection

logger=get_logger()

class ModelBundle:
    def __init__(self):
        self.yolo=None
        self.object_model=None
        self.general_object_model=None
        self.foundation_pose=None
        self.pose=None
        self.error_foundation_pose=''
        self.error_pose=''
        self.error_object=''
        self.error_c_astra=''
        self.device=self._device()
        self._load()
    def _model_path(self, filename, fallback=None):
        filenames = (filename, fallback) if fallback else (filename,)
        for candidate in filenames:
            if not candidate:
                continue
            for path in (MODEL_DIR / candidate, BASE_DIR.parent / candidate):
                if path.exists():
                    return str(path)
        return filename
    def _device(self):
        if DEVICE!='auto':return DEVICE
        try:
            import torch
            return 'cuda' if torch.cuda.is_available() else 'cpu'
        except Exception:return 'cpu'
    def _load(self):
        try:
            from ultralytics import YOLO
            # General COCO detector remains available for common objects
            # (bottle, laptop, scissors, backpack, chair, etc.).
            self.yolo=YOLO(self._model_path(GENERAL_OBJECT_MODEL_FILENAME))
            self.general_object_model=self.yolo

        except Exception as e:
            self.error_object='MODEL NOT AVAILABLE'
            logger.exception('General YOLO load failed: %s',e)
        try:
            from ultralytics import YOLO
            object_path = C_ASTRA_MODEL_PATH
            if not Path(object_path).exists() and not C_ASTRA_MODEL_FROM_ENV:
                object_path = C_ASTRA_FALLBACK_MODEL_PATH
            if not Path(object_path).exists():
                raise FileNotFoundError(f'C-ASTRA model not found: {C_ASTRA_MODEL_PATH}')
            model = YOLO(str(object_path))
            names = getattr(model, 'names', {})
            if len(names) != C_ASTRA_CLASS_COUNT:
                raise ValueError(f'C-ASTRA model exposes {len(names)} classes; expected {C_ASTRA_CLASS_COUNT}')
            self.object_model = model
        except Exception as e:
            self.object_model=None
            self.error_c_astra='C-ASTRA MODEL NOT AVAILABLE'
            self.error_object=self.error_c_astra
            logger.exception('C-ASTRA load failed: %s',e)
        try:
            from ultralytics import YOLO
            self.pose=YOLO(self._model_path('yolov8n-pose.pt'))
        except Exception as e:self.error_pose='MODEL NOT AVAILABLE'; logger.exception('Pose load failed: %s',e)
        self._load_foundation_pose()
    def _load_foundation_pose(self):
        if not FOUNDATION_POSE_MESH_PATH:
            self.error_foundation_pose='MODEL DATA NOT CONFIGURED'
            return
        try:
            from estimater import FoundationPose  # type: ignore[import-not-found]
            from learning.training.predict_score import ScorePredictor  # type: ignore[import-not-found]
            from learning.training.predict_pose_refine import PoseRefinePredictor  # type: ignore[import-not-found]
            import trimesh  # type: ignore[import-not-found]
            mesh=trimesh.load(str(FOUNDATION_POSE_MESH_PATH), force='mesh')
            debug_dir=Path(FOUNDATION_POSE_DEBUG_DIR); debug_dir.mkdir(parents=True, exist_ok=True)
            self.foundation_pose=FoundationPose(model_pts=np.asarray(mesh.vertices),model_normals=np.asarray(mesh.vertex_normals),mesh=mesh,scorer=ScorePredictor(),refiner=PoseRefinePredictor(),debug=0,debug_dir=str(debug_dir))
        except Exception as e:
            self.error_foundation_pose=f'UNAVAILABLE: {type(e).__name__}'
            logger.exception('Official FoundationPose load failed: %s',e)

class CameraProcessor:
    def __init__(self,info,stream,models,result_queue):
        self.info=info; self.stream=stream; self.models=models; self.q=result_queue; self.stop_event=threading.Event(); self.fps=FPSCounter(); self.person_tracker=PersonTracker(HISTORY_LENGTH); self.object_tracker=ObjectTracker(); self.activity=ActivityRecognizer(); self.interaction=InteractionEngine(); self.context=ContextEngine(); self.person_detector=PersonDetector(models.yolo) if models.yolo else None; self.object_detector=ObjectDetector(models.object_model, models.general_object_model, models.error_c_astra) if (models.object_model or models.general_object_model) else None; self.pose_detector=PoseDetector(models.pose) if models.pose else None; self.thread=threading.Thread(target=self._loop,daemon=True,name=f'processor-{info.camera_id}'); self.last_result=None; self.frame_count=0
    def start(self):self.thread.start()
    def stop(self):self.stop_event.set(); self.thread.join(timeout=2)
    def _associate_pose(self,persons,poses):
        from utils.geometry import iou
        for p in persons:
            best=None; score=0
            for pose in poses:
                if pose.get('bbox'):
                    s=iou(p.bbox,pose['bbox'])
                    if s>score:score=s;best=pose
            if best:p.pose=best
    def _foundation_pose_update(self,frame,objects):
        depth=self.stream.read_depth()
        if self.models.foundation_pose is None or depth is None or FOUNDATION_POSE_INTRINSICS is None:
            return 'WAITING FOR RGB-D/INTRINSICS'
        rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        K=np.asarray(FOUNDATION_POSE_INTRINSICS,dtype=np.float32).reshape(3,3)
        for obj in objects:
            x1,y1,x2,y2=map(int,obj.bbox)
            object_mask=np.zeros(depth.shape[:2],dtype=np.uint8)
            object_mask[max(0,y1):min(object_mask.shape[0],y2),max(0,x1):min(object_mask.shape[1],x2)]=1
            try:
                if obj.foundation_pose is None:
                    obj.foundation_pose=self.models.foundation_pose.register(K=K,rgb=rgb,depth=depth,ob_mask=object_mask,iteration=5)
                else:
                    obj.foundation_pose=self.models.foundation_pose.track_one(rgb=rgb,depth=depth,K=K,iteration=2)
            except Exception:
                logger.exception('FoundationPose inference failed for object %s',obj.track_id)
                return 'ERROR'
        return 'RUNNING'
    def _loop(self):
        while not self.stop_event.is_set():
            frame=self.stream.read()
            if frame is None: time.sleep(.01); continue
            self.frame_count+=1; self.fps.tick()
            persons=[]; objects=[]; interactions=[]; contexts=[]; activities=[]; statuses={'camera':'ONLINE','frame':'RECEIVING','device':self.models.device,'yolo':'RUNNING' if self.person_detector else 'MODEL NOT AVAILABLE','c_astra':'RUNNING' if self.models.object_model else (self.models.error_c_astra or 'C-ASTRA MODEL NOT AVAILABLE'),'objects':'RUNNING' if self.object_detector else (self.models.error_object or 'MODEL NOT AVAILABLE'),'foundation_pose':self.models.error_foundation_pose or ('READY' if self.models.foundation_pose else 'MODEL NOT AVAILABLE'),'pose':'RUNNING' if self.pose_detector else 'MODEL NOT AVAILABLE','tracking':'WAITING FOR DETECTIONS','activity':'WAITING FOR DETECTIONS','interaction':'RUNNING','context':'RUNNING'}
            try:
                if self.person_detector and self.frame_count%max(1,DETECTION_INTERVAL)==0:
                    persons=self.person_tracker.update(self.person_detector.track(frame,CONFIDENCE_THRESHOLD,IOU_THRESHOLD,self.models.device)); statuses['tracking']='RUNNING'
                    objects=self.object_tracker.update(self.object_detector.track(frame,CONFIDENCE_THRESHOLD,IOU_THRESHOLD,self.models.device,IMAGE_SIZE)) if self.object_detector else []
                    statuses['foundation_pose']=self._foundation_pose_update(frame,objects)
                    if self.pose_detector:
                        self._associate_pose(persons,self.pose_detector.detect(frame,CONFIDENCE_THRESHOLD,self.models.device)); statuses['pose']='RUNNING'
                    for p in persons:p.activity=self.activity.recognize(p); activities.append({'person_id':p.track_id,'activity':p.activity,'method':'RULE-BASED'}); statuses['activity']='RUNNING'
                    interactions=self.interaction.update(persons,objects)
                    for i in interactions:
                        o=next((x for x in objects if x.track_id==i.object_id),None)
                        if o:o.interaction_person=i.person_id;o.interaction_state=i.state
                    contexts=self.context.generate(persons,objects,interactions)
                    statuses['tracking']='RUNNING' if persons or objects else 'WAITING FOR DETECTIONS'
                annotated=frame.copy(); self._draw(annotated,persons,objects,interactions)
                if not self.models.object_model:
                    cv2.putText(annotated, self.models.error_c_astra or 'C-ASTRA MODEL NOT AVAILABLE', (10, 28), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 80, 255), 2)
                events=[]
                if self.last_result:
                    old={(i.person_id,i.object_id,i.state) for i in self.last_result.interactions}; new={(i.person_id,i.object_id,i.state) for i in interactions}
                    for p,o,s in new-old:
                        obj=next((x for x in objects if x.track_id==o),None); events.append({'timestamp':time.time(),'description':f'Person #{p} {s} {obj.class_name} #{o}' if obj else f'Person #{p} {s} object #{o}'})
                result=FrameAnalysisResult(self.info.camera_id,self.info.name,time.time(),annotated,persons,objects,interactions,activities,contexts,events,self.fps.value(),statuses)
                self.last_result=result
                try:
                    save_detection(
                        self.info.camera_id,
                        self.info.name,
                        persons,
                        objects,
                        interactions,
                        summary=f'{self.info.name} | {len(persons)} people | {len(objects)} objects | {len(interactions)} interactions',
                        details=str({
                            'camera_id': self.info.camera_id,
                            'camera_name': self.info.name,
                            'fps': round(self.fps.value(), 2),
                            'persons': [p.__dict__ for p in persons],
                            'objects': [o.__dict__ for o in objects],
                            'interactions': [i.__dict__ for i in interactions],
                        })
                    )
                except Exception:
                    logger.exception('Auto-save detection failed for camera %s', self.info.camera_id)
                try:self.q.put_nowait(result)
                except queue.Full:
                    try:self.q.get_nowait()
                    except queue.Empty: self.q.get_nowait if False else None
                    try:self.q.put_nowait(result)
                    except queue.Full: self.q.full()
            except Exception as e:
                logger.exception('Processor error %s: %s',self.info.camera_id,e)
                statuses['detection']='ERROR'; statuses['error']='Processing error; see log'
                result=FrameAnalysisResult(self.info.camera_id,self.info.name,time.time(),frame,[],[],[],[],[],[{'timestamp':time.time(),'description':'AI processing error; see log'}],self.fps.value(),statuses)
                try:self.q.put_nowait(result)
                except queue.Full:self.q.full()
    def _draw(self,frame,persons,objects,interactions):
        for p in persons:
            x1,y1,x2,y2=p.bbox; cv2.rectangle(frame,(x1,y1),(x2,y2),(80,220,120),2); cv2.putText(frame,f'PERSON #{p.track_id} {p.confidence*100:.0f}% {p.activity}',(x1,max(18,y1-8)),cv2.FONT_HERSHEY_SIMPLEX,.5,(80,220,120),2)
            if p.pose:
                pts=p.pose['keypoints']
                for x,y in pts:
                    cv2.circle(frame,(int(x),int(y)),3,(255,255,255),-1)
                for a,b in [(5,6),(5,7),(7,9),(6,8),(8,10),(5,11),(6,12),(11,12),(11,13),(13,15),(12,14),(14,16)]:
                    if a<len(pts) and b<len(pts):cv2.line(frame,tuple(map(int,pts[a])),tuple(map(int,pts[b])),(255,255,255),2)
        for o in objects:
            x1,y1,x2,y2=o.bbox; cv2.rectangle(frame,(x1,y1),(x2,y2),(230,170,60),2); cv2.putText(frame,f'{o.class_name.upper()} #{o.track_id} {o.confidence*100:.0f}% {o.interaction_state}',(x1,max(18,y1-8)),cv2.FONT_HERSHEY_SIMPLEX,.45,(230,170,60),2)
        for i in interactions:
            o=next((x for x in objects if x.track_id==i.object_id),None); p=next((x for x in persons if x.track_id==i.person_id),None)
            if o and p: cv2.line(frame,tuple(map(int,p.center)),tuple(map(int,o.center)),(255,220,80),2)

if __name__ == "__main__":
    from ui.main_window import run
    run()
