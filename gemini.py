import os
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from pypdf import PdfWriter

# Set appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PDFMergerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Effcorp PDF Merger")
        self.geometry("800x600")
        
        # Internal state
        self.pdf_list = []

        # --- UI Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header_label = ctk.CTkLabel(self, text="PDF Merger Tool", font=ctk.CTkFont(size=24, weight="bold"))
        self.header_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        # Main Frame for List and Control Buttons
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Scrollable List Area
        self.scrollable_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Files to Merge")
        self.scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Sidebar for Controls
        self.sidebar_frame = ctk.CTkFrame(self.main_frame, width=150, fg_color="transparent")
        self.sidebar_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ns")

        self.add_btn = ctk.CTkButton(self.sidebar_frame, text="Add PDF", command=self.add_files)
        self.add_btn.pack(pady=5, fill="x")

        self.remove_btn = ctk.CTkButton(self.sidebar_frame, text="Remove Selected", fg_color="#E74C3C", hover_color="#C0392B", command=self.remove_selected)
        self.remove_btn.pack(pady=5, fill="x")

        self.move_up_btn = ctk.CTkButton(self.sidebar_frame, text="Move Up", fg_color="#34495E", command=lambda: self.move_file(-1))
        self.move_up_btn.pack(pady=(20, 5), fill="x")

        self.move_down_btn = ctk.CTkButton(self.sidebar_frame, text="Move Down", fg_color="#34495E", command=lambda: self.move_file(1))
        self.move_down_btn.pack(pady=5, fill="x")

        # Bottom Action Bar
        self.bottom_frame = ctk.CTkFrame(self, height=80)
        self.bottom_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")

        self.merge_btn = ctk.CTkButton(self.bottom_frame, text="MERGE PDFS", height=45, font=ctk.CTkFont(size=16, weight="bold"), command=self.merge_pdfs)
        self.merge_btn.pack(side="right", padx=20, pady=15)

        self.status_label = ctk.CTkLabel(self.bottom_frame, text="Ready", text_color="gray")
        self.status_label.pack(side="left", padx=20)

        # Variable to hold selection
        self.selected_index = None
        self.label_widgets = []

    def refresh_list(self):
        """Redraws the list of files in the scrollable frame."""
        for widget in self.label_widgets:
            widget.destroy()
        self.label_widgets = []

        for i, file_path in enumerate(self.pdf_list):
            filename = os.path.basename(file_path)
            
            # Create a clickable frame for each item
            bg_color = "#3B3B3B" if self.selected_index == i else "transparent"
            item_frame = ctk.CTkFrame(self.scrollable_frame, fg_color=bg_color, corner_radius=5)
            item_frame.pack(fill="x", pady=2, padx=5)
            
            lbl = ctk.CTkLabel(item_frame, text=f"{i+1}. {filename}", anchor="w", padx=10)
            lbl.pack(fill="x", pady=5)
            
            # Bind click to select
            lbl.bind("<Button-1>", lambda e, index=i: self.select_item(index))
            item_frame.bind("<Button-1>", lambda e, index=i: self.select_item(index))
            
            self.label_widgets.append(item_frame)

    def select_item(self, index):
        self.selected_index = index
        self.refresh_list()

    def add_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if files:
            self.pdf_list.extend(files)
            self.refresh_list()
            self.status_label.configure(text=f"Added {len(files)} files.")

    def remove_selected(self):
        if self.selected_index is not None:
            self.pdf_list.pop(self.selected_index)
            self.selected_index = None
            self.refresh_list()
            self.status_label.configure(text="File removed.")
        else:
            messagebox.showwarning("Selection", "Please select a file to remove.")

    def move_file(self, direction):
        """Moves file up (-1) or down (1) in the list."""
        if self.selected_index is None:
            return
        
        new_index = self.selected_index + direction
        if 0 <= new_index < len(self.pdf_list):
            # Swap
            self.pdf_list[self.selected_index], self.pdf_list[new_index] = \
                self.pdf_list[new_index], self.pdf_list[self.selected_index]
            self.selected_index = new_index
            self.refresh_list()

    def merge_pdfs(self):
        if not self.pdf_list:
            messagebox.showwarning("No Files", "Please add some PDF files first.")
            return

        # Handle Output Folder
        output_dir = "Effcorp_Output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Generate Timestamped Name
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Merged_PDF_{timestamp}.pdf"
        output_path = os.path.join(output_dir, filename)

        try:
            merger = PdfWriter()
            for pdf in self.pdf_list:
                merger.append(pdf)
            
            with open(output_path, "wb") as f:
                merger.write(f)
            merger.close()

            messagebox.showinfo("Success", f"PDFs merged successfully!\nSaved to: {output_path}")
            self.status_label.configure(text="Merge Complete.", text_color="#2ECC71")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to merge PDFs: {str(e)}")

if __name__ == "__main__":
    app = PDFMergerApp()
    app.mainloop()

