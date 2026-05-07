# =========================================================
# Professional PDF Merger App
# Built with CustomTkinter
#
# Features:
# ✔ Add Multiple PDFs
# ✔ Drag & Drop Reordering
# ✔ Remove Selected PDF
# ✔ Clear All PDFs
# ✔ Select Output Folder
# ✔ Auto Create "Effcorp_Output"
# ✔ Timestamped Output File
# ✔ Modern Professional UI
#
# INSTALL REQUIRED LIBRARIES:
#
# pip install customtkinter PyPDF2 tkinterdnd2
#
# =========================================================

import os
import sys
import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PyPDF2 import PdfMerger

# Drag & Drop Support
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except:
    DND_AVAILABLE = False


# =========================================================
# MAIN APPLICATION
# =========================================================

class PDFMergerApp(CTkApp := (TkinterDnD.Tk if DND_AVAILABLE else ctk.CTk)):

    def __init__(self):
        super().__init__()

        # ---------------- WINDOW CONFIG ----------------
        self.title("Effcorp PDF Merger Pro")
        self.geometry("900x600")
        self.minsize(800, 500)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.pdf_files = []
        self.dragging_index = None

        # ---------------- HEADER ----------------
        header = ctk.CTkFrame(self, height=70, corner_radius=0)
        header.pack(fill="x")

        title = ctk.CTkLabel(
            header,
            text="📄 Effcorp PDF Merger Pro",
            font=("Segoe UI", 28, "bold")
        )
        title.pack(pady=15)

        # ---------------- MAIN FRAME ----------------
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ---------------- LEFT PANEL ----------------
        left_frame = ctk.CTkFrame(main_frame, width=250)
        left_frame.pack(side="left", fill="y", padx=(0, 15))

        ctk.CTkLabel(
            left_frame,
            text="Controls",
            font=("Segoe UI", 20, "bold")
        ).pack(pady=(20, 15))

        # ADD PDF BUTTON
        add_btn = ctk.CTkButton(
            left_frame,
            text="➕ Add PDF Files",
            height=45,
            font=("Segoe UI", 15, "bold"),
            command=self.add_pdfs
        )
        add_btn.pack(fill="x", padx=20, pady=10)

        # REMOVE BUTTON
        remove_btn = ctk.CTkButton(
            left_frame,
            text="❌ Remove Selected",
            height=45,
            fg_color="#b22222",
            hover_color="#8b0000",
            font=("Segoe UI", 15, "bold"),
            command=self.remove_selected
        )
        remove_btn.pack(fill="x", padx=20, pady=10)

        # CLEAR BUTTON
        clear_btn = ctk.CTkButton(
            left_frame,
            text="🗑 Clear All",
            height=45,
            fg_color="#444444",
            hover_color="#222222",
            font=("Segoe UI", 15, "bold"),
            command=self.clear_all
        )
        clear_btn.pack(fill="x", padx=20, pady=10)

        # OUTPUT FOLDER
        ctk.CTkLabel(
            left_frame,
            text="Output Folder",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(25, 5))

        self.output_entry = ctk.CTkEntry(
            left_frame,
            placeholder_text="Default: Effcorp_Output"
        )
        self.output_entry.pack(fill="x", padx=20, pady=5)

        browse_output_btn = ctk.CTkButton(
            left_frame,
            text="📁 Browse Output Folder",
            height=40,
            command=self.select_output_folder
        )
        browse_output_btn.pack(fill="x", padx=20, pady=10)

        # MERGE BUTTON
        merge_btn = ctk.CTkButton(
            left_frame,
            text="🚀 Merge PDF",
            height=55,
            font=("Segoe UI", 18, "bold"),
            fg_color="#0b7d3b",
            hover_color="#095f2d",
            command=self.merge_pdfs
        )
        merge_btn.pack(fill="x", padx=20, pady=(40, 20))

        # STATUS LABEL
        self.status_label = ctk.CTkLabel(
            left_frame,
            text="Ready",
            text_color="lightgreen",
            font=("Segoe UI", 13)
        )
        self.status_label.pack(pady=5)

        # ---------------- RIGHT PANEL ----------------
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True)

        top_label = ctk.CTkLabel(
            right_frame,
            text="PDF Queue (Drag to Rearrange)",
            font=("Segoe UI", 20, "bold")
        )
        top_label.pack(pady=15)

        # LISTBOX FRAME
        list_frame = ctk.CTkFrame(right_frame)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # LISTBOX
        import tkinter as tk

        self.listbox = tk.Listbox(
            list_frame,
            bg="#1f1f1f",
            fg="white",
            selectbackground="#1f6aa5",
            font=("Segoe UI", 12),
            activestyle="none",
            relief="flat",
            bd=0
        )

        self.listbox.pack(fill="both", expand=True, padx=10, pady=10)

        # DRAG & DROP REORDER
        self.listbox.bind("<Button-1>", self.on_click)
        self.listbox.bind("<B1-Motion>", self.on_drag)

        # FILE DROP SUPPORT
        if DND_AVAILABLE:
            self.listbox.drop_target_register(DND_FILES)
            self.listbox.dnd_bind('<<Drop>>', self.drop_files)

    # =====================================================
    # ADD PDFs
    # =====================================================
    def add_pdfs(self):

        files = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF Files", "*.pdf")]
        )

        for file in files:
            if file not in self.pdf_files:
                self.pdf_files.append(file)
                self.listbox.insert("end", os.path.basename(file))

        self.update_status()

    # =====================================================
    # DRAG & DROP FILES FROM EXPLORER
    # =====================================================
    def drop_files(self, event):

        files = self.tk.splitlist(event.data)

        for file in files:

            file = file.strip("{}")

            if file.lower().endswith(".pdf"):

                if file not in self.pdf_files:
                    self.pdf_files.append(file)
                    self.listbox.insert("end", os.path.basename(file))

        self.update_status()

    # =====================================================
    # REMOVE SELECTED
    # =====================================================
    def remove_selected(self):

        selected = self.listbox.curselection()

        if not selected:
            return

        index = selected[0]

        self.listbox.delete(index)
        self.pdf_files.pop(index)

        self.update_status()

    # =====================================================
    # CLEAR ALL
    # =====================================================
    def clear_all(self):

        self.listbox.delete(0, "end")
        self.pdf_files.clear()

        self.update_status()

    # =====================================================
    # SELECT OUTPUT FOLDER
    # =====================================================
    def select_output_folder(self):

        folder = filedialog.askdirectory()

        if folder:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, folder)

    # =====================================================
    # MERGE PDFs
    # =====================================================
    def merge_pdfs(self):

        if not self.pdf_files:
            messagebox.showwarning(
                "No Files",
                "Please add PDF files first."
            )
            return

        try:

            merger = PdfMerger()

            for pdf in self.pdf_files:
                merger.append(pdf)

            # OUTPUT DIRECTORY
            output_dir = self.output_entry.get().strip()

            if not output_dir:

                output_dir = os.path.join(
                    os.getcwd(),
                    "Effcorp_Output"
                )

            os.makedirs(output_dir, exist_ok=True)

            # TIMESTAMP
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            output_file = os.path.join(
                output_dir,
                f"Merged_PDF_{timestamp}.pdf"
            )

            merger.write(output_file)
            merger.close()

            self.status_label.configure(
                text="PDF Merged Successfully ✔",
                text_color="lightgreen"
            )

            messagebox.showinfo(
                "Success",
                f"PDF merged successfully!\n\nSaved at:\n{output_file}"
            )

            # OPEN OUTPUT FOLDER
            try:
                os.startfile(output_dir)
            except:
                pass

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Failed to merge PDFs.\n\n{str(e)}"
            )

    # =====================================================
    # UPDATE STATUS
    # =====================================================
    def update_status(self):

        self.status_label.configure(
            text=f"{len(self.pdf_files)} PDF(s) Added"
        )

    # =====================================================
    # DRAG REORDER
    # =====================================================
    def on_click(self, event):

        self.dragging_index = self.listbox.nearest(event.y)

    def on_drag(self, event):

        new_index = self.listbox.nearest(event.y)

        if new_index == self.dragging_index:
            return

        # MOVE IN LISTBOX
        item = self.listbox.get(self.dragging_index)

        self.listbox.delete(self.dragging_index)
        self.listbox.insert(new_index, item)

        # MOVE IN INTERNAL LIST
        self.pdf_files.insert(
            new_index,
            self.pdf_files.pop(self.dragging_index)
        )

        self.dragging_index = new_index


# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":

    app = PDFMergerApp()
    app.mainloop()