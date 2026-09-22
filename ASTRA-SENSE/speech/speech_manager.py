import threading,queue,time
from config import SPEECH_ENABLED,SPEECH_COOLDOWN,SPEECH_VOLUME,SPEECH_RATE
class SpeechManager:
    def __init__(self,enabled=SPEECH_ENABLED):
        self.enabled=enabled; self.q=queue.Queue(maxsize=20); self.stop_event=threading.Event(); self.last={}; self.engine=None
        if enabled:
            try:
                import pyttsx3
                self.engine=pyttsx3.init(); self.engine.setProperty('volume',SPEECH_VOLUME); self.engine.setProperty('rate',SPEECH_RATE)
            except Exception:self.engine=None; self.enabled=False
        self.thread=threading.Thread(target=self._worker,daemon=True,name='tts-worker'); self.thread.start()
    def announce(self,text,key=None):
        if not self.enabled or self.engine is None:return
        k=key or text; now=time.time()
        if now-self.last.get(k,0)<SPEECH_COOLDOWN:return
        self.last[k]=now
        try:self.q.put_nowait(text)
        except queue.Full: self.q.full()
    def _worker(self):
        while not self.stop_event.is_set():
            try:text=self.q.get(timeout=.2)
            except queue.Empty:continue
            try:self.engine.say(text); self.engine.runAndWait()
            except Exception:self.enabled=False
            finally:self.q.task_done()
    def stop(self):
        self.stop_event.set()
        if self.thread is not threading.current_thread():self.thread.join(timeout=2)
        try:
            if self.engine:self.engine.stop()
        except Exception: self.engine=None
