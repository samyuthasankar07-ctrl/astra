import tkinter as tk
class EventPanel(tk.LabelFrame):
    def __init__(self,parent):
        super().__init__(parent,text='LIVE EVENTS',bg='#151a20',fg='#e7edf5'); self.text=tk.Text(self,height=8,bg='#0f1318',fg='#dce5ef',bd=0,font=('Consolas',9),state='disabled'); self.text.pack(fill='both',expand=True,padx=4,pady=4)
    def add(self,events):
        if not events:return
        self.text.config(state='normal')
        for e in events:
            import time
            self.text.insert('end',f'{time.strftime("%H:%M:%S",time.localtime(e["timestamp"]))}  {e["description"]}\n')
        self.text.see('end'); self.text.config(state='disabled')
