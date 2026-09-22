import tkinter as tk
from tkinter import filedialog,messagebox,simpledialog
class CameraPanel(tk.Frame):
    def __init__(self,parent,app):
        super().__init__(parent,bg='#101419'); self.app=app
        self.var=tk.StringVar(); self.combo=tk.OptionMenu(self,self.var,''); self.combo.config(bg='#202831',fg='white',activebackground='#2d3945'); self.combo.pack(side='left',padx=5)
        for text,cmd in [('Rescan Cameras',app.rescan),('Add Network / Android Camera',app.add_network),('Add Video File',app.add_video),('Open Camera',app.open_selected),('Stop Camera',app.stop_selected),('Open Multi-Camera View',app.multi_view),('Saved Detections',app.open_detections),('TEST CAMERA',app.test_camera)]: tk.Button(self,text=text,command=cmd,bg='#202831',fg='white',relief='flat').pack(side='left',padx=3,pady=5)
    def refresh(self,cameras):
        menu=self.combo['menu']; menu.delete(0,'end')
        for cid,c in cameras.items(): menu.add_command(label=f'{c.name} [{cid}]',command=lambda x=cid:self.var.set(x))
        if cameras and not self.var.get():self.var.set(next(iter(cameras)))
