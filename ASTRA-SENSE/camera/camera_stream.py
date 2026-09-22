import cv2, threading, time
from config import CAMERA_WIDTH,CAMERA_HEIGHT,FRAME_QUEUE_SIZE,RECONNECT_DELAY
from utils.logger import get_logger
class CameraStream:
    def __init__(self, source, camera_id, name, depth_source=None):
        self.source=source; self.camera_id=camera_id; self.name=name; self.depth_source=depth_source; self.cap=None; self.depth_cap=None; self.lock=threading.Lock(); self.frame=None; self.depth_frame=None; self.last_frame_time=0; self.running=False; self.thread=None; self.stop_event=threading.Event(); self.logger=get_logger('camera')
        self.error=''
    def _open(self):
        self.cap=cv2.VideoCapture(self.source)
        if isinstance(self.source,int):
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,CAMERA_WIDTH); self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT,CAMERA_HEIGHT)
        if self.depth_source is not None:
            self.depth_cap=cv2.VideoCapture(self.depth_source)
            if not self.depth_cap.isOpened():
                self.depth_cap.release(); self.depth_cap=None
        return bool(self.cap and self.cap.isOpened())
    def start(self):
        if self.running:return True
        if not self._open(): self.error='Unable to open camera'; self.release(); return False
        self.running=True; self.stop_event.clear(); self.thread=threading.Thread(target=self._loop,name=f'capture-{self.camera_id}',daemon=True); self.thread.start(); return True
    def _loop(self):
        failures=0
        while not self.stop_event.is_set():
            try:
                if not self.cap or not self.cap.isOpened():
                    self.running=False; break
                ret,frame=self.cap.read()
                if ret and frame is not None and frame.size>0:
                    depth=None
                    if self.depth_cap is not None:
                        depth_ret, depth= self.depth_cap.read()
                        if not depth_ret: depth=None
                    with self.lock:self.frame=frame; self.depth_frame=depth; self.last_frame_time=time.time()
                    failures=0
                else:
                    failures+=1
                    if failures>=10:
                        self.error='Frame could not be read'; self.running=False; break
                    time.sleep(0.05)
            except Exception as e:
                self.logger.exception('Camera %s capture failure: %s',self.camera_id,e); self.error='Camera capture error'; self.running=False; break
        self.release()
    def read(self):
        with self.lock:return None if self.frame is None else self.frame.copy()
    def read_depth(self):
        with self.lock:return None if self.depth_frame is None else self.depth_frame.copy()
    def release(self):
        cap=self.cap; self.cap=None
        if cap is not None:
            try:cap.release()
            except Exception: self.logger.debug("camera release cleanup failed", exc_info=True)
        depth_cap=self.depth_cap; self.depth_cap=None
        if depth_cap is not None:
            try:depth_cap.release()
            except Exception: self.logger.debug("depth release cleanup failed", exc_info=True)
    def stop(self):
        self.stop_event.set(); self.running=False
        if self.thread and self.thread is not threading.current_thread(): self.thread.join(timeout=2)
        self.release(); self.thread=None
    def is_running(self): return self.running
