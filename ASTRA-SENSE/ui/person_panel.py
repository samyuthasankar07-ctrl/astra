import tkinter as tk
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.privacy import redact_person_label

class PersonPanel(tk.LabelFrame):
    def __init__(self,parent):
        super().__init__(parent,text='PEOPLE',bg='#151a20',fg='#e7edf5'); self.text=tk.Text(self,height=10,bg='#0f1318',fg='#dce5ef',bd=0,font=('Consolas',9),state='disabled'); self.text.pack(fill='both',expand=True,padx=4,pady=4)
    def update(self,persons):
        lines=[]
        for p in persons:
            obj=f'{p.interaction_state} / {p.interaction_person}' if p.interaction_state!='NONE' else 'NONE'
            label = redact_person_label(f'PERSON #{p.track_id}')
            lines.append(f'{label}\nConfidence: {p.confidence*100:.0f}%\nPosition: ({p.center[0]:.0f},{p.center[1]:.0f})\nVelocity: {p.velocity:.1f} px/f\nDirection: {p.direction}\nMotion: {p.motion_state}\nActivity: {p.activity}\nPose: {"DETECTED" if p.pose else "NOT AVAILABLE"}\nInteraction: {obj}\n')
        self._set('\n'.join(lines) if lines else 'No people detected.')
    def _set(self,s):self.text.config(state='normal');self.text.delete('1.0','end');self.text.insert('end',s);self.text.config(state='disabled')

if __name__ == '__main__':
    from ui.main_window import run
    run()
