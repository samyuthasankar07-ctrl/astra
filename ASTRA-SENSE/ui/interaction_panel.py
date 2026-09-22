import tkinter as tk
from utils.privacy import redact_person_label

class InteractionPanel(tk.LabelFrame):
    def __init__(self,parent):
        super().__init__(parent,text='INTERACTIONS',bg='#151a20',fg='#e7edf5'); self.lbl=tk.Label(self,text='No active interactions.',justify='left',anchor='nw',bg='#0f1318',fg='#dce5ef',font=('Consolas',9)); self.lbl.pack(fill='both',expand=True,padx=4,pady=4)
    def update(self,ints,objects):
        m={o.track_id:o for o in objects}; lines=[]
        for i in ints:
            if i.object_id not in m or i.state in ('NONE','NEAR'):
                continue
            person_label = redact_person_label(f'Person #{i.person_id}')
            lines.append(f'{person_label} → {i.state} → {m[i.object_id].class_name} #{i.object_id} ({i.duration:.1f}s)')
        self.lbl.config(text='\n'.join(lines) if lines else 'No active interactions.')
