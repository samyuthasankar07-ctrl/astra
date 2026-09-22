from dataclasses import dataclass
from pathlib import Path
from .camera_stream import CameraStream
from .network_camera import validate_url
from config import SUPPORTED_VIDEO_EXTENSIONS, FOUNDATION_POSE_DEPTH_SOURCE

@dataclass
class CameraInfo:
    camera_id:str; name:str; source:object; type:str; status:str='OFFLINE'

class CameraManager:
    def __init__(self): self.cameras={}; self.streams={}
    def set_local(self,items):
        for x in items:self.cameras[x['id']]=CameraInfo(x['id'],x['name'],x['source'],x['type'])
    def add_network(self,name,url):
        safe=validate_url(url); idx=sum(1 for c in self.cameras.values() if c.type=='network'); cid=('android:' if 'android' in name.lower() else 'network:')+str(idx)
        self.cameras[cid]=CameraInfo(cid,name,safe,'network'); return cid
    def add_video(self,path):
        p=Path(path).expanduser().resolve()
        if not p.is_file() or p.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS: raise ValueError('Unsupported or invalid video file')
        cid=f'video:{len([c for c in self.cameras.values() if c.type=="video"])}'; self.cameras[cid]=CameraInfo(cid,p.as_posix(),str(p),'video'); return cid
    def open(self,cid):
        if cid not in self.cameras:return None
        info=self.cameras[cid]
        stream=CameraStream(info.source,cid,info.name,FOUNDATION_POSE_DEPTH_SOURCE)
        if not stream.start():return None
        self.streams[cid]=stream; info.status='ONLINE'; return stream
    def stop(self,cid):
        s=self.streams.pop(cid,None)
        if s:s.stop()
        if cid in self.cameras:self.cameras[cid].status='OFFLINE'
    def stop_all(self):
        for cid in list(self.streams):self.stop(cid)
