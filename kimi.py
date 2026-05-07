
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
import re
from datetime import datetime
from pathlib import Path
import threading

try:
    from PyPDF2 import PdfMerger, PdfReader
except ImportError:
    print("PyPDF2 not found, installing...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'PyPDF2'])
    from PyPDF2 import PdfMerger, PdfReader

# Set appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class PDFMergeApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("EffCorp PDF Merger Pro")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # Data
        self.pdf_files = []  # List of dicts: {'path': str, 'name': str, 'pages': int}
        self.drag_start_index = None
        
        # Default output folder
        self.default_output = os.path.join(os.path.expanduser("~"), "Effcorp_Output")
        self.output_folder = ctk.StringVar(value=self.default_output)
        
        # Ensure default output exists
        os.makedirs(self.default_output, exist_ok=True)
        
        self._build_ui()
        self._setup_drag_drop()
        
    def _build_ui(self):
        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        
        # ===== HEADER =====
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(header, text="📄 EffCorp PDF Merger", 
                            font=ctk.CTkFont(size=28, weight="bold"))
        title.grid(row=0, column=0, sticky="w")
        
        subtitle = ctk.CTkLabel(header, text="Drag & drop to reorder • Merge with one click", 
                               font=ctk.CTkFont(size=13), text_color="gray")
        subtitle.grid(row=1, column=0, sticky="w", pady=(2, 0))
        
        # ===== TOOLBAR =====
        toolbar = ctk.CTkFrame(main_frame)
        toolbar.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        toolbar.grid_columnconfigure(1, weight=1)
        
        # Browse Button
        self.btn_browse = ctk.CTkButton(toolbar, text="➕ Add PDF Files", 
                                       font=ctk.CTkFont(size=13, weight="bold"),
                                       width=150, height=40,
                                       command=self._browse_files)
        self.btn_browse.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        # Output folder selection
        out_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        out_frame.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        out_frame.grid_columnconfigure(1, weight=1)
        
        out_label = ctk.CTkLabel(out_frame, text="Output:", font=ctk.CTkFont(size=12))
        out_label.grid(row=0, column=0, padx=(0, 5))
        
        self.entry_output = ctk.CTkEntry(out_frame, textvariable=self.output_folder,
                                        font=ctk.CTkFont(size=12))
        self.entry_output.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.btn_out_browse = ctk.CTkButton(out_frame, text="📁", width=40, height=32,
                                           command=self._browse_output)
        self.btn_out_browse.grid(row=0, column=2, padx=(5, 10))
        
        # ===== FILE LIST =====
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)
        
        # List header
        list_header = ctk.CTkFrame(list_frame, fg_color=("gray85", "gray25"), height=35)
        list_header.grid(row=0, column=0, sticky="ew", padx=2, pady=(2, 0))
        list_header.grid_propagate(False)
        list_header.grid_columnconfigure(1, weight=1)
        
        headers = [("#", 50), ("Filename", 400), ("Pages", 80), ("Size", 100), ("Action", 100)]
        for i, (text, width) in enumerate(headers):
            lbl = ctk.CTkLabel(list_header, text=text, font=ctk.CTkFont(size=12, weight="bold"))
            lbl.grid(row=0, column=i, padx=5, pady=5)
            
        # Scrollable frame for files
        self.scroll_frame = ctk.CTkScrollableFrame(list_frame)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self.scroll_frame.grid_columnconfigure(1, weight=1)
        
        # Empty state label
        self.empty_label = ctk.CTkLabel(self.scroll_frame, 
                                       text="No files added yet\nClick 'Add PDF Files' or drag & drop PDFs here",
                                       font=ctk.CTkFont(size=14), text_color="gray")
        self.empty_label.grid(row=0, column=0, columnspan=5, pady=50)
        
        # ===== BOTTOM ACTIONS =====
        bottom = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom.grid(row=3, column=0, padx=10, pady=(10, 15), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)
        
        # Stats
        self.lbl_stats = ctk.CTkLabel(bottom, text="0 files | 0 pages", 
                                     font=ctk.CTkFont(size=12), text_color="gray")
        self.lbl_stats.grid(row=0, column=0, sticky="w")
        
        # Action buttons
        btn_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")
        
        self.btn_clear = ctk.CTkButton(btn_frame, text="🗑️ Clear All", 
                                      font=ctk.CTkFont(size=12),
                                      width=120, height=38,
                                      fg_color="transparent", border_width=2,
                                      command=self._clear_all)
        self.btn_clear.grid(row=0, column=0, padx=5)
        
        self.btn_merge = ctk.CTkButton(btn_frame, text="🔀 Merge PDFs", 
                                      font=ctk.CTkFont(size=14, weight="bold"),
                                      width=180, height=45,
                                      command=self._merge_pdfs)
        self.btn_merge.grid(row=0, column=1, padx=(10, 0))
        
        # Progress bar (hidden initially)
        self.progress = ctk.CTkProgressBar(main_frame, mode="determinate")
        self.progress.set(0)
        self.progress.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.progress.grid_remove()
        
        self.lbl_progress = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=12))
        self.lbl_progress.grid(row=5, column=0, pady=(0, 5))
        
    def _setup_drag_drop(self):
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self._on_drop)
        
    def _on_drop(self, event):
        files = self.tk.splitlist(event.data)
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        if pdf_files:
            self._add_files(pdf_files)
        else:
            messagebox.showwarning("Invalid Files", "Please drop only PDF files.")
            
    def _browse_files(self):
        files = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if files:
            self._add_files(files)
            
    def _browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
            
    def _get_file_size(self, path):
        size = os.path.getsize(path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def _get_page_count(self, path):
        try:
            reader = PdfReader(path)
            return len(reader.pages)
        except Exception:
            return 0
            
    def _add_files(self, file_paths):
        added = 0
        for path in file_paths:
            path = os.path.normpath(path)
            if any(f['path'] == path for f in self.pdf_files):
                continue
                
            name = os.path.basename(path)
            pages = self._get_page_count(path)
            size = self._get_file_size(path)
            
            self.pdf_files.append({
                'path': path,
                'name': name,
                'pages': pages,
                'size': size
            })
            added += 1
            
        if added > 0:
            self._refresh_list()
            self.lbl_progress.configure(text=f"Added {added} file(s)")
            self.after(2000, lambda: self.lbl_progress.configure(text=""))
            
    def _refresh_list(self):
        # Clear existing widgets
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        if not self.pdf_files:
            self.empty_label = ctk.CTkLabel(self.scroll_frame, 
                                           text="No files added yet\nClick 'Add PDF Files' or drag & drop PDFs here",
                                           font=ctk.CTkFont(size=14), text_color="gray")
            self.empty_label.grid(row=0, column=0, columnspan=5, pady=50)
            self.lbl_stats.configure(text="0 files | 0 pages")
            return
            
        total_pages = sum(f['pages'] for f in self.pdf_files)
        self.lbl_stats.configure(text=f"{len(self.pdf_files)} files | {total_pages} pages")
        
        for idx, file_info in enumerate(self.pdf_files):
            self._create_file_row(idx, file_info)
            
    def _create_file_row(self, idx, file_info):
        row_frame = ctk.CTkFrame(self.scroll_frame)
        row_frame.grid(row=idx, column=0, columnspan=5, sticky="ew", pady=1)
        row_frame.grid_columnconfigure(1, weight=1)
        
        # Alternating colors
        if idx % 2 == 0:
            row_frame.configure(fg_color=("gray90", "gray20"))
        else:
            row_frame.configure(fg_color=("gray95", "gray17"))
            
        # Drag handle
        drag_lbl = ctk.CTkLabel(row_frame, text="≡", font=ctk.CTkFont(size=16), 
                                text_color="gray", width=30)
        drag_lbl.grid(row=0, column=0, padx=(10, 0))
        
        # Index
        idx_lbl = ctk.CTkLabel(row_frame, text=str(idx + 1), 
                              font=ctk.CTkFont(size=12, weight="bold"), width=30)
        idx_lbl.grid(row=0, column=1, padx=5)
        
        # Filename (truncated if too long)
        display_name = file_info['name']
        if len(display_name) > 50:
            display_name = display_name[:25] + "..." + display_name[-20:]
        name_lbl = ctk.CTkLabel(row_frame, text=display_name, 
                               font=ctk.CTkFont(size=12), anchor="w")
        name_lbl.grid(row=0, column=2, padx=5, sticky="w")
        
        # Pages
        pages_lbl = ctk.CTkLabel(row_frame, text=str(file_info['pages']), 
                                font=ctk.CTkFont(size=12), width=60)
        pages_lbl.grid(row=0, column=3, padx=10)
        
        # Size
        size_lbl = ctk.CTkLabel(row_frame, text=file_info['size'], 
                               font=ctk.CTkFont(size=11), width=80)
        size_lbl.grid(row=0, column=4, padx=10)
        
        # Move up/down buttons
        move_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        move_frame.grid(row=0, column=5, padx=5)
        
        btn_up = ctk.CTkButton(move_frame, text="▲", width=28, height=28,
                              font=ctk.CTkFont(size=10),
                              command=lambda i=idx: self._move_up(i))
        btn_up.grid(row=0, column=0, padx=1)
        if idx == 0:
            btn_up.configure(state="disabled", fg_color="gray")
            
        btn_down = ctk.CTkButton(move_frame, text="▼", width=28, height=28,
                                font=ctk.CTkFont(size=10),
                                command=lambda i=idx: self._move_down(i))
        btn_down.grid(row=0, column=1, padx=1)
        if idx == len(self.pdf_files) - 1:
            btn_down.configure(state="disabled", fg_color="gray")
            
        # Remove button
        btn_remove = ctk.CTkButton(row_frame, text="✕", width=30, height=28,
                                  font=ctk.CTkFont(size=12),
                                  fg_color="transparent", hover_color=("#ff4444", "#cc0000"),
                                  text_color=("red", "#ff6666"),
                                  command=lambda i=idx: self._remove_file(i))
        btn_remove.grid(row=0, column=6, padx=(5, 10))
        
        # Bind drag events for reordering
        row_frame.bind("<Button-1>", lambda e, i=idx: self._drag_start(i))
        row_frame.bind("<B1-Motion>", lambda e, i=idx: self._drag_motion(i, e))
        row_frame.bind("<ButtonRelease-1>", lambda e, i=idx: self._drag_drop(i))
        
        for child in row_frame.winfo_children():
            child.bind("<Button-1>", lambda e, i=idx: self._drag_start(i))
            
    def _drag_start(self, idx):
        self.drag_start_index = idx
        
    def _drag_motion(self, idx, event):
        pass  # Visual feedback could be added here
        
    def _drag_drop(self, idx):
        if self.drag_start_index is not None and self.drag_start_index != idx:
            # Swap items
            item = self.pdf_files.pop(self.drag_start_index)
            self.pdf_files.insert(idx, item)
            self._refresh_list()
        self.drag_start_index = None
        
    def _move_up(self, idx):
        if idx > 0:
            self.pdf_files[idx], self.pdf_files[idx-1] = self.pdf_files[idx-1], self.pdf_files[idx]
            self._refresh_list()
            
    def _move_down(self, idx):
        if idx < len(self.pdf_files) - 1:
            self.pdf_files[idx], self.pdf_files[idx+1] = self.pdf_files[idx+1], self.pdf_files[idx]
            self._refresh_list()
            
    def _remove_file(self, idx):
        self.pdf_files.pop(idx)
        self._refresh_list()
        
    def _clear_all(self):
        if not self.pdf_files:
            return
        if messagebox.askyesno("Confirm", "Remove all files from the list?"):
            self.pdf_files.clear()
            self._refresh_list()
            
    def _merge_pdfs(self):
        if len(self.pdf_files) < 2:
            messagebox.showwarning("Not Enough Files", "Please add at least 2 PDF files to merge.")
            return
            
        output_dir = self.output_folder.get().strip()
        if not output_dir:
            output_dir = self.default_output
            self.output_folder.set(output_dir)
            
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"Merged_PDF_{timestamp}.pdf"
        output_path = os.path.join(output_dir, output_name)
        
        # Run merge in thread to keep UI responsive
        self.btn_merge.configure(state="disabled", text="Merging...")
        self.progress.grid()
        self.progress.set(0)
        self.lbl_progress.configure(text="Starting merge...")
        self.update()
        
        thread = threading.Thread(target=self._do_merge, args=(output_path,))
        thread.daemon = True
        thread.start()
        
    def _do_merge(self, output_path):
        try:
            merger = PdfMerger()
            total = len(self.pdf_files)
            
            for i, file_info in enumerate(self.pdf_files):
                self.after(0, lambda p=(i+1)/total: self.progress.set(p))
                self.after(0, lambda msg=f"Merging {i+1}/{total}: {file_info['name'][:30]}...": 
                          self.lbl_progress.configure(text=msg))
                merger.append(file_info['path'])
                
            self.after(0, lambda: self.lbl_progress.configure(text="Saving file..."))
            merger.write(output_path)
            merger.close()
            
            self.after(0, lambda: self._merge_complete(output_path))
        except Exception as e:
            self.after(0, lambda err=str(e): self._merge_error(err))
            
    def _merge_complete(self, output_path):
        self.progress.set(1)
        self.lbl_progress.configure(text=f"✅ Saved: {os.path.basename(output_path)}")
        self.btn_merge.configure(state="normal", text="🔀 Merge PDFs")
        
        if messagebox.askyesno("Success!", 
                              f"PDF merged successfully!\n\nSaved to:\n{output_path}\n\nOpen output folder?"):
            os.startfile(os.path.dirname(output_path))
            
        self.after(3000, lambda: self.lbl_progress.configure(text=""))
        self.progress.grid_remove()
        
    def _merge_error(self, error_msg):
        self.progress.grid_remove()
        self.lbl_progress.configure(text=f"❌ Error: {error_msg}")
        self.btn_merge.configure(state="normal", text="🔀 Merge PDFs")
        messagebox.showerror("Merge Failed", f"An error occurred:\n{error_msg}")


if __name__ == "__main__":
    app = PDFMergeApp()
    app.mainloop()
