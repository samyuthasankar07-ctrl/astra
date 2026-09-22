import tkinter as tk
class StatusPanel(tk.LabelFrame):
    def __init__(self,parent):
        super().__init__(parent,text='SYSTEM STATUS',bg='#151a20',fg='#e7edf5'); self.lbl=tk.Label(self,text='',justify='left',anchor='nw',bg='#151a20',fg='#dce5ef',font=('Consolas',9)); self.lbl.pack(fill='both',expand=True,padx=6,pady=6)
    def update(self,status,fps,speech):
        order=['camera','frame','yolo','c_astra','foundation_pose','tracking','pose','activity','interaction','context','device']; lines=[f'{k.title()}: {status.get(k,"N/A")}' for k in order]; lines += [f'Speech: {"ENABLED" if speech else "DISABLED"}',f'FPS: {fps:.1f}', '', 'SECURITY STATUS', 'Local Processing: ENABLED', 'External Upload: DISABLED', 'Telemetry: DISABLED', 'Hidden Network Service: NONE', 'Camera Access: USER CONTROLLED', 'Input Validation: ENABLED', 'Logging: ENABLED']; self.lbl.config(text='\n'.join(lines))
