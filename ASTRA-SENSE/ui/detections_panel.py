import tkinter as tk
from tkinter import ttk, messagebox

from data.detection_store import list_detections, delete_detection, delete_all_detections, update_detection_summary, get_detection


class DetectionsPanel(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title('ASTRA-SENSE Saved Detections')
        self.geometry('900x500')
        self.configure(bg='#101419')
        self.parent = parent

        toolbar = tk.Frame(self, bg='#101419')
        toolbar.pack(fill='x', padx=8, pady=(8, 4))

        tk.Button(toolbar, text='Refresh', command=self.refresh_list, bg='#1f2d37', fg='white', activebackground='#33495e').pack(side='left')
        tk.Button(toolbar, text='Delete Selected', command=self.delete_selected, bg='#3a1f1f', fg='white', activebackground='#5b2a2a').pack(side='left', padx=(8, 0))
        tk.Button(toolbar, text='Delete All Data', command=self.delete_all_data, bg='#5a1717', fg='white', activebackground='#7a2222').pack(side='left', padx=(8, 0))
        tk.Button(toolbar, text='Save Edit', command=self.save_selected, bg='#1f3a2e', fg='white', activebackground='#285740').pack(side='left', padx=(8, 0))

        cols = ('id', 'time', 'camera', 'people', 'objects', 'interactions', 'summary')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=18)
        for col in cols:
            self.tree.heading(col, text=col.replace('_', ' ').title())
            self.tree.column(col, width=100, anchor='center')
        self.tree.column('summary', width=280, anchor='w')
        self.tree.pack(fill='both', expand=True, padx=8, pady=(0, 8))

        self.tree.bind('<<TreeviewSelect>>', self.load_selected)

        editor = tk.LabelFrame(self, text='Edit selected record', bg='#101419', fg='#e8edf5', padx=8, pady=8)
        editor.pack(fill='x', padx=8, pady=(0, 8))

        tk.Label(editor, text='Summary:', bg='#101419', fg='#dfe7f1').grid(row=0, column=0, sticky='w', padx=(0, 8), pady=(0, 6))
        self.summary_var = tk.StringVar()
        self.summary_entry = tk.Entry(editor, textvariable=self.summary_var, width=100, bg='#0d1217', fg='#e7edf5', insertbackground='white')
        self.summary_entry.grid(row=0, column=1, sticky='ew', padx=(0, 8))

        self.details_text = tk.Text(editor, height=8, bg='#0d1217', fg='#e7edf5', insertbackground='white')
        self.details_text.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=(0, 8), pady=(8, 0))

        editor.grid_columnconfigure(1, weight=1)
        editor.grid_rowconfigure(1, weight=1)

        self.refresh_list()

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in list_detections():
            self.tree.insert('', 'end', values=(
                row['id'],
                row['created_at'],
                row['camera_name'] or row['camera_id'] or 'N/A',
                row['person_count'],
                row['object_count'],
                row['interaction_count'],
                row['summary'],
            ))

    def load_selected(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        row_id = self.tree.item(sel[0], 'values')[0]
        record = get_detection(int(row_id))
        if not record:
            return
        self.summary_var.set(record['summary'])
        self.details_text.delete('1.0', 'end')
        self.details_text.insert('1.0', record['details'] or '')

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('Delete', 'Select a record first.')
            return
        row_id = self.tree.item(sel[0], 'values')[0]
        delete_detection(int(row_id))
        self.refresh_list()
        self.summary_var.set('')
        self.details_text.delete('1.0', 'end')

    def delete_all_data(self):
        if not list_detections(limit=1):
            messagebox.showinfo('Delete All Data', 'There is no saved data to delete.')
            return
        confirmed = messagebox.askyesno(
            'Delete All Data',
            'Delete all saved detection data? This cannot be undone.',
            icon='warning',
            parent=self,
        )
        if not confirmed:
            return
        delete_all_detections()
        self.refresh_list()
        self.summary_var.set('')
        self.details_text.delete('1.0', 'end')

    def save_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('Save', 'Select a record first.')
            return
        row_id = self.tree.item(sel[0], 'values')[0]
        summary = self.summary_var.get().strip() or 'Updated detection'
        details = self.details_text.get('1.0', 'end').strip()
        update_detection_summary(int(row_id), summary, details)
        self.refresh_list()
