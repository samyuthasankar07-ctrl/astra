import tkinter as tk
from utils.privacy import redact_person_label

class ObjectPanel(tk.LabelFrame):
    def __init__(self,parent):
        super().__init__(parent,text='OBJECTS',bg='#151a20',fg='#e7edf5'); self.text=tk.Text(self,height=10,bg='#0f1318',fg='#dce5ef',bd=0,font=('Consolas',9),state='disabled'); self.text.pack(fill='both',expand=True,padx=4,pady=4)
    def update(self,objects):
        lines=[]
        for o in objects:
            person_label = redact_person_label(f'Person #{o.interaction_person}') if o.interaction_person is not None else 'Person: None'
            lines.append(f'OBJECT #{o.track_id} {o.class_name}\nConfidence: {o.confidence*100:.0f}%\nPosition: ({o.center[0]:.0f},{o.center[1]:.0f}) Size: {o.bbox[2]-o.bbox[0]}x{o.bbox[3]-o.bbox[1]}\nMotion: {o.motion_state}  Direction: {o.direction}\nSpeed: {o.velocity:.1f} px/f  Track Age: {o.age}\nDistance: {o.movement_distance:.1f} px\n{person_label}\nInteraction: {o.interaction_state}\n')
        self._set('\n'.join(lines) if lines else 'No objects detected.')
    def _set(self,s):self.text.config(state='normal');self.text.delete('1.0','end');self.text.insert('end',s);self.text.config(state='disabled')
