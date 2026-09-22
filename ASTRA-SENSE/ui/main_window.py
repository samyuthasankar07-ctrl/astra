import tkinter as tk
from tkinter import messagebox,simpledialog,filedialog
import cv2,time,threading,queue
from PIL import Image,ImageTk
from camera.camera_detector import scan_local
from camera.camera_manager import CameraManager
from camera.network_camera import safe_url_for_log
from main import ModelBundle,CameraProcessor
from config import C_ASTRA_CLASS_COUNT
from speech.speech_manager import SpeechManager
from .camera_panel import CameraPanel
from .person_panel import PersonPanel
from .object_panel import ObjectPanel
from .interaction_panel import InteractionPanel
from .context_panel import ContextPanel
from .event_panel import EventPanel
from .status_panel import StatusPanel
from .detections_panel import DetectionsPanel
from utils.logger import get_logger
from utils.privacy import redact_event_description

class MainWindow:
    def __init__(self,root):
        self.root=root; root.title('ASTRA-SENSE — AI Human Activity & Object Interaction Monitoring'); root.geometry('1500x900'); root.configure(bg='#101419'); self.logger=get_logger('ui'); self.manager=CameraManager(); self.models=ModelBundle(); self.results=queue.Queue(maxsize=3); self.processors={}; self.latest={}; self.speech=SpeechManager(); self.events_seen=set()
        tk.Label(root,text='ASTRA-SENSE',font=('Segoe UI',24,'bold'),bg='#101419',fg='#f3f6fa').pack(anchor='w',padx=15,pady=(12,0)); tk.Label(root,text='AI Human Activity & Object Interaction Monitoring',font=('Segoe UI',10),bg='#101419',fg='#91a0af').pack(anchor='w',padx=17)
        self.camera_bar=CameraPanel(root,self); self.camera_bar.pack(fill='x',padx=10,pady=8)
        body=tk.Frame(root,bg='#101419'); body.pack(fill='both',expand=True,padx=10)
        self.video=tk.Label(body,text='Select a camera and click OPEN CAMERA',bg='#080b0e',fg='#82909e',font=('Segoe UI',14)); self.video.pack(side='left',fill='both',expand=True,padx=(0,8))
        right=tk.Frame(body,bg='#101419',width=420); right.pack(side='right',fill='y'); right.pack_propagate(False)
        self.people=PersonPanel(right); self.people.pack(fill='x',pady=3); self.objects=ObjectPanel(right); self.objects.pack(fill='x',pady=3); self.interactions=InteractionPanel(right); self.interactions.pack(fill='x',pady=3); self.context=ContextPanel(right); self.context.pack(fill='x',pady=3); self.status=StatusPanel(right); self.status.pack(fill='both',expand=True,pady=3)
        self.events=EventPanel(root); self.events.pack(fill='x',padx=10,pady=(6,10)); self.detections_panel=None; self.rescan(); self.root.after(30,self.ui_tick); self.root.protocol('WM_DELETE_WINDOW',self.close)
    def rescan(self):
        try:self.manager.set_local(scan_local()); self.camera_bar.refresh(self.manager.cameras)
        except Exception as e:self.logger.exception('Scan failed: %s',e); messagebox.showerror('Camera Scan','Unable to scan cameras. See data/logs/astra_sense.log')
    def add_network(self):
        name=simpledialog.askstring('Network Camera','Camera Name:',parent=self.root)
        url=simpledialog.askstring('Network Camera','Stream URL (http/https/rtsp):',parent=self.root)
        if not name or not url:return
        try:cid=self.manager.add_network(name,url); self.camera_bar.refresh(self.manager.cameras); self.camera_bar.var.set(cid)
        except Exception as e:messagebox.showerror('Invalid camera URL',str(e))
    def add_video(self):
        path=filedialog.askopenfilename(parent=self.root,filetypes=[('Video files','*.mp4 *.avi *.mov *.mkv *.m4v *.wmv')])
        if path:
            try:cid=self.manager.add_video(path); self.camera_bar.refresh(self.manager.cameras); self.camera_bar.var.set(cid)
            except Exception as e:messagebox.showerror('Invalid video',str(e))
    def open_selected(self):
        cid=self.camera_bar.var.get()
        if not cid:return
        self.stop_selected()
        stream=self.manager.open(cid)
        if not stream:messagebox.showerror('Camera Error','Unable to open camera. Check permissions, availability, URL, or whether another application is using it.');return
        p=CameraProcessor(self.manager.cameras[cid],stream,self.models,self.results); self.processors[cid]=p; p.start()
    def stop_selected(self):
        cid=self.camera_bar.var.get()
        if cid in self.processors:
            self.processors[cid].stop(); del self.processors[cid]
        self.manager.stop(cid); self.video.config(image='',text='Camera stopped.')
    def ui_tick(self):
        try:
            while True:
                r=self.results.get_nowait(); self.latest[r.camera_id]=r
                if r.camera_id==self.camera_bar.var.get():self.render(r)
                for e in r.events:
                    description = redact_event_description(e['description'])
                    key=(r.camera_id,description)
                    if key not in self.events_seen:self.events_seen.add(key); self.events.add([{'timestamp': e.get('timestamp'), 'description': description}]); self.speech.announce(description,key=str(key))
        except queue.Empty: self.results.empty()
        self.root.after(30,self.ui_tick)
    def render(self,r):
        rgb=cv2.cvtColor(r.frame,cv2.COLOR_BGR2RGB); im=Image.fromarray(rgb); im.thumbnail((980,700)); photo=ImageTk.PhotoImage(im); self.video.config(image=photo,text=''); self.video.image=photo; self.people.update(r.persons); self.objects.update(r.objects); self.interactions.update(r.interactions,r.objects); self.context.update(r.contexts); self.status.update(r.system_status,r.fps,self.speech.enabled)
        if self.detections_panel is not None and self.detections_panel.winfo_exists():
            pass
    def multi_view(self):MultiCameraWindow(self)
    def open_detections(self):
        if self.detections_panel is None or not self.detections_panel.winfo_exists():
            self.detections_panel = DetectionsPanel(self.root)
        else:
            self.detections_panel.focus_set()
    def test_camera(self):
        checks=[]
        import importlib.util
        for n in ['Python','OpenCV','NumPy','Ultralytics','Torch','Tkinter','TTS']:
            mod={'Python':None,'OpenCV':'cv2','NumPy':'numpy','Ultralytics':'ultralytics','Torch':'torch','Tkinter':'tkinter','TTS':'pyttsx3'}[n]
            try:
                if mod:__import__(mod)
                checks.append(f'[✓] {n}')
            except Exception as e:checks.append(f'[✗] {n}: {type(e).__name__}')
        checks += [f'[✓] YOLO' if self.models.yolo else '[✗] YOLO: MODEL NOT AVAILABLE',f'[✓] C-ASTRA ({C_ASTRA_CLASS_COUNT} classes)' if self.models.object_model else f'[✗] {self.models.error_c_astra or "C-ASTRA MODEL NOT AVAILABLE"}',f'[✓] Pose' if self.models.pose else '[✗] Pose: MODEL NOT AVAILABLE', '[✓] Camera scan complete']
        messagebox.showinfo('ASTRA-SENSE SYSTEM CHECK','\n'.join(checks),parent=self.root)
    def close(self):
        for p in list(self.processors.values()):p.stop()
        self.manager.stop_all(); self.speech.stop(); self.root.destroy()

class MultiCameraWindow(tk.Toplevel):
    def __init__(self,app):
        super().__init__(app.root); self.app=app; self.title('ASTRA-SENSE — Multi-Camera View'); self.geometry('1200x800'); self.configure(bg='#101419'); self.tiles={}; self.after(100,self.update_tiles)
    def update_tiles(self):
        for w in self.winfo_children():w.destroy()
        active=list(self.app.latest.values())
        for idx,r in enumerate(active):
            f=tk.Frame(self,bg='#0b0f13',bd=1,relief='solid'); f.grid(row=idx//2,column=idx%2,sticky='nsew',padx=4,pady=4); self.grid_rowconfigure(idx//2,weight=1); self.grid_columnconfigure(idx%2,weight=1)
            tk.Label(f,text=f'{r.camera_name} | {r.camera_id} | {r.fps:.1f} FPS | {len(r.persons)} people | {len(r.objects)} objects',bg='#202831',fg='white').pack(fill='x'); im=Image.fromarray(cv2.cvtColor(r.frame,cv2.COLOR_BGR2RGB)); im.thumbnail((560,360)); ph=ImageTk.PhotoImage(im); lab=tk.Label(f,image=ph,bg='#080b0e'); lab.image=ph; lab.pack(fill='both',expand=True); tk.Label(f,text=f'Status: {r.system_status.get("camera")} | Detection: {r.system_status.get("yolo")}',bg='#0b0f13',fg='#cbd5df').pack(fill='x')
        self.after(300,self.update_tiles)

def run():
    root=tk.Tk(); MainWindow(root); root.mainloop()
