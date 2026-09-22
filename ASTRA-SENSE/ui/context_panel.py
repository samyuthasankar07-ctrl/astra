import tkinter as tk
class ContextPanel(tk.LabelFrame):
    def __init__(self,parent):
        super().__init__(parent,text='CONTEXT',bg='#151a20',fg='#e7edf5'); self.lbl=tk.Label(self,text='No context available.',justify='left',anchor='nw',bg='#0f1318',fg='#dce5ef',font=('Consolas',9),wraplength=380); self.lbl.pack(fill='both',expand=True,padx=4,pady=4)
    def update(self,contexts):self.lbl.config(text='\n'.join(contexts) if contexts else 'No context available.')
