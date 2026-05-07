"""
╔══════════════════════════════════════════════════════════╗
║         EFFCORP PDF MERGER  —  Professional Edition      ║
║         Requires: customtkinter, pypdf                   ║
║         Install : pip install customtkinter pypdf        ║
╚══════════════════════════════════════════════════════════╝
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from pathlib import Path

try:
    import customtkinter as ctk
except ImportError:
    print("customtkinter not found. Install it with: pip install customtkinter")
    sys.exit(1)

try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    print("pypdf not found. Install it with: pip install pypdf")
    sys.exit(1)


# ── Theme & Palette ──────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

PALETTE = {
    "bg":           "#0D0F14",
    "panel":        "#14171F",
    "card":         "#1C2030",
    "card_hover":   "#232840",
    "accent":       "#4F6EF7",
    "accent2":      "#7B5EF8",
    "accent_dim":   "#2A3870",
    "success":      "#23C97D",
    "danger":       "#F75E5E",
    "warning":      "#F5A623",
    "text":         "#E8ECF8",
    "text_dim":     "#6B7599",
    "border":       "#252A3D",
    "drag_active":  "#2D3A6B",
}


# ── Drag-and-drop list item ──────────────────────────────────────────────────
class FileRow(ctk.CTkFrame):
    """A single row representing one PDF in the list, draggable."""

    def __init__(self, master, file_path: str, index: int,
                 on_remove, on_drag_start, on_drag_motion, on_drag_end, **kwargs):
        super().__init__(
            master,
            fg_color=PALETTE["card"],
            corner_radius=10,
            border_width=1,
            border_color=PALETTE["border"],
            **kwargs
        )
        self.file_path = file_path
        self.index = index
        self._on_remove = on_remove
        self._on_drag_start = on_drag_start
        self._on_drag_motion = on_drag_motion
        self._on_drag_end = on_drag_end
        self._dragging = False

        self._build()
        self._bind_drag()

    def _build(self):
        self.grid_columnconfigure(1, weight=1)

        # Drag handle
        self.handle = ctk.CTkLabel(
            self, text="⠿", font=ctk.CTkFont(size=18),
            text_color=PALETTE["text_dim"], width=30
        )
        self.handle.grid(row=0, column=0, padx=(10, 4), pady=8)

        # Index badge
        self.badge = ctk.CTkLabel(
            self, text=f"{self.index + 1:02d}",
            font=ctk.CTkFont(family="Courier New", size=11, weight="bold"),
            text_color=PALETTE["accent"], width=28,
            fg_color=PALETTE["accent_dim"], corner_radius=6
        )
        self.badge.grid(row=0, column=1, padx=(0, 8), pady=8, sticky="w")

        # File icon + name
        name = Path(self.file_path).name
        short = name if len(name) <= 55 else name[:52] + "…"
        self.icon_lbl = ctk.CTkLabel(
            self, text="📄 ", font=ctk.CTkFont(size=14),
            text_color=PALETTE["text_dim"]
        )
        self.icon_lbl.grid(row=0, column=2, padx=(0, 2), pady=8)

        self.name_lbl = ctk.CTkLabel(
            self, text=short,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=PALETTE["text"], anchor="w"
        )
        self.name_lbl.grid(row=0, column=3, pady=8, sticky="ew")

        # Page count (async)
        self.pages_lbl = ctk.CTkLabel(
            self, text="— pp",
            font=ctk.CTkFont(size=11),
            text_color=PALETTE["text_dim"], width=50
        )
        self.pages_lbl.grid(row=0, column=4, padx=8, pady=8)

        # Remove button
        self.btn_remove = ctk.CTkButton(
            self, text="✕", width=30, height=28,
            fg_color="transparent", hover_color=PALETTE["danger"],
            text_color=PALETTE["text_dim"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._on_remove(self.index)
        )
        self.btn_remove.grid(row=0, column=5, padx=(4, 10), pady=8)

        self.grid_columnconfigure(3, weight=1)
        threading.Thread(target=self._load_pages, daemon=True).start()

    def _load_pages(self):
        try:
            r = PdfReader(self.file_path)
            n = len(r.pages)
            self.after(0, lambda: self.pages_lbl.configure(
                text=f"{n} pp", text_color=PALETTE["accent"]
            ))
        except Exception:
            self.after(0, lambda: self.pages_lbl.configure(text="err"))

    def set_index(self, idx: int):
        self.index = idx
        self.badge.configure(text=f"{idx + 1:02d}")

    def highlight(self, active: bool):
        color = PALETTE["drag_active"] if active else PALETTE["card"]
        self.configure(fg_color=color)

    def _bind_drag(self):
        for w in (self, self.handle, self.name_lbl, self.icon_lbl, self.badge):
            w.bind("<ButtonPress-1>",   self._drag_start)
            w.bind("<B1-Motion>",       self._drag_motion)
            w.bind("<ButtonRelease-1>", self._drag_end)

    def _drag_start(self, e):
        self._dragging = True
        self._on_drag_start(self.index, e)

    def _drag_motion(self, e):
        if self._dragging:
            self._on_drag_motion(self.index, e)

    def _drag_end(self, e):
        if self._dragging:
            self._dragging = False
            self._on_drag_end(self.index, e)


# ── Main Application ─────────────────────────────────────────────────────────
class PDFMergerApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("EffCorp PDF Merger")
        self.geometry("860x680")
        self.minsize(720, 560)
        self.configure(fg_color=PALETTE["bg"])

        self.files: list[str] = []
        self.rows: list[FileRow] = []
        self._drag_from: int | None = None
        self._ghost: ctk.CTkLabel | None = None

        self._build_ui()

    # ── UI Construction ──────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header bar ────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=PALETTE["panel"],
                              corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="⬡",
            font=ctk.CTkFont(size=26), text_color=PALETTE["accent"]
        ).pack(side="left", padx=(22, 6), pady=14)

        ctk.CTkLabel(
            header, text="EffCorp  PDF Merger",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=PALETTE["text"]
        ).pack(side="left", pady=14)

        ctk.CTkLabel(
            header, text="Professional Edition",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=PALETTE["text_dim"]
        ).pack(side="left", padx=(8, 0), pady=20)

        # Theme toggle
        self._theme_var = ctk.StringVar(value="Dark")
        ctk.CTkSegmentedButton(
            header, values=["Dark", "Light"],
            variable=self._theme_var,
            command=self._toggle_theme,
            width=130, height=30,
            font=ctk.CTkFont(size=11)
        ).pack(side="right", padx=20)

        # ── Body layout ────────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=(14, 0))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        # ── Toolbar ────────────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(body, fg_color=PALETTE["panel"], corner_radius=12)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkButton(
            toolbar, text="＋  Browse PDF",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=PALETTE["accent"], hover_color=PALETTE["accent2"],
            height=38, corner_radius=9,
            command=self._browse
        ).pack(side="left", padx=(12, 6), pady=10)

        ctk.CTkButton(
            toolbar, text="🗑  Clear All",
            font=ctk.CTkFont(size=12),
            fg_color=PALETTE["card"], hover_color=PALETTE["danger"],
            text_color=PALETTE["text"],
            height=38, corner_radius=9,
            command=self._clear_all
        ).pack(side="left", padx=6, pady=10)

        ctk.CTkButton(
            toolbar, text="↑  Move Up",
            font=ctk.CTkFont(size=12),
            fg_color=PALETTE["card"], hover_color=PALETTE["accent_dim"],
            text_color=PALETTE["text"],
            height=38, corner_radius=9,
            command=lambda: self._move_selected(-1)
        ).pack(side="left", padx=6, pady=10)

        ctk.CTkButton(
            toolbar, text="↓  Move Down",
            font=ctk.CTkFont(size=12),
            fg_color=PALETTE["card"], hover_color=PALETTE["accent_dim"],
            text_color=PALETTE["text"],
            height=38, corner_radius=9,
            command=lambda: self._move_selected(1)
        ).pack(side="left", padx=6, pady=10)

        # File count badge
        self.count_lbl = ctk.CTkLabel(
            toolbar, text="0 files",
            font=ctk.CTkFont(size=11),
            text_color=PALETTE["text_dim"]
        )
        self.count_lbl.pack(side="right", padx=16)

        # ── Drop zone / file list ──────────────────────────────────────────
        list_outer = ctk.CTkFrame(body, fg_color=PALETTE["panel"], corner_radius=12)
        list_outer.grid(row=1, column=0, sticky="nsew")
        list_outer.grid_rowconfigure(0, weight=1)
        list_outer.grid_columnconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(
            list_outer, fg_color="transparent", corner_radius=0
        )
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.scroll.grid_columnconfigure(0, weight=1)

        # Empty-state placeholder
        self.empty_frame = ctk.CTkFrame(
            self.scroll, fg_color="transparent"
        )
        self.empty_frame.grid(row=0, column=0, sticky="nsew", pady=60)
        self.empty_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.empty_frame, text="📂",
            font=ctk.CTkFont(size=52), text_color=PALETTE["text_dim"]
        ).grid(row=0, column=0, pady=(0, 8))

        ctk.CTkLabel(
            self.empty_frame,
            text="Drop PDFs here or click  ＋ Browse PDF",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=PALETTE["text_dim"]
        ).grid(row=1, column=0)

        ctk.CTkLabel(
            self.empty_frame,
            text="Drag rows to reorder  •  Supports unlimited files",
            font=ctk.CTkFont(size=11), text_color=PALETTE["border"]
        ).grid(row=2, column=0, pady=(4, 0))

        # ── Output settings ────────────────────────────────────────────────
        out_frame = ctk.CTkFrame(body, fg_color=PALETTE["panel"], corner_radius=12)
        out_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        out_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            out_frame, text="Output Folder:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=PALETTE["text"]
        ).grid(row=0, column=0, padx=(14, 8), pady=12, sticky="w")

        self.out_entry = ctk.CTkEntry(
            out_frame, placeholder_text="Leave blank → auto-create  EffCorp_Output/",
            font=ctk.CTkFont(size=12),
            fg_color=PALETTE["card"], border_color=PALETTE["border"],
            text_color=PALETTE["text"], height=36
        )
        self.out_entry.grid(row=0, column=1, padx=(0, 8), pady=12, sticky="ew")

        ctk.CTkButton(
            out_frame, text="Browse",
            width=80, height=36,
            fg_color=PALETTE["accent_dim"],
            hover_color=PALETTE["accent"],
            font=ctk.CTkFont(size=12),
            command=self._browse_output
        ).grid(row=0, column=2, padx=(0, 14), pady=12)

        # ── Status bar + Merge button ──────────────────────────────────────
        bottom = ctk.CTkFrame(body, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="ew", pady=(10, 14))
        bottom.grid_columnconfigure(0, weight=1)

        self.status_lbl = ctk.CTkLabel(
            bottom, text="Ready — add PDF files to get started.",
            font=ctk.CTkFont(size=11), text_color=PALETTE["text_dim"],
            anchor="w"
        )
        self.status_lbl.grid(row=0, column=0, sticky="ew")

        self.progress = ctk.CTkProgressBar(
            bottom, height=4,
            fg_color=PALETTE["card"],
            progress_color=PALETTE["accent"]
        )
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self.progress.set(0)

        self.merge_btn = ctk.CTkButton(
            bottom, text="⚡  Merge PDF",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=PALETTE["accent"], hover_color=PALETTE["accent2"],
            height=44, corner_radius=10, width=180,
            command=self._start_merge
        )
        self.merge_btn.grid(row=0, column=1, rowspan=2, padx=(12, 0))

        # Native drop support (Windows/Linux best-effort via tkinterdnd2)
        self._setup_native_drop()

    # ── Native drag-drop from OS ──────────────────────────────────────────
    def _setup_native_drop(self):
        """Try to enable OS-level file drop; silently skip if unavailable."""
        try:
            from tkinterdnd2 import TkinterDnD, DND_FILES  # type: ignore
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_os_drop)
        except Exception:
            pass  # Optional; app works fine without it

    def _on_os_drop(self, event):
        raw = event.data
        # tkinterdnd2 wraps paths with spaces in {}
        import re
        paths = re.findall(r'\{([^}]+)\}|(\S+)', raw)
        for g1, g2 in paths:
            p = (g1 or g2).strip()
            if p.lower().endswith(".pdf") and os.path.isfile(p):
                self._add_file(p)

    # ── File management ───────────────────────────────────────────────────
    def _browse(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        for p in paths:
            self._add_file(p)

    def _add_file(self, path: str):
        if path in self.files:
            self._status(f"Already added: {Path(path).name}", PALETTE["warning"])
            return
        self.files.append(path)
        self._render_rows()
        self._status(f"Added: {Path(path).name}", PALETTE["success"])

    def _clear_all(self):
        if not self.files:
            return
        if messagebox.askyesno("Clear All", "Remove all files from the list?"):
            self.files.clear()
            self._render_rows()
            self._status("All files removed.", PALETTE["text_dim"])

    def _remove_file(self, idx: int):
        if 0 <= idx < len(self.files):
            name = Path(self.files[idx]).name
            self.files.pop(idx)
            self._render_rows()
            self._status(f"Removed: {name}", PALETTE["warning"])

    def _move_selected(self, direction: int):
        # Move the last interacted row; fallback: move last row
        if len(self.files) < 2:
            return
        idx = self._last_selected if hasattr(self, "_last_selected") else len(self.files) - 1
        new = idx + direction
        if 0 <= new < len(self.files):
            self.files[idx], self.files[new] = self.files[new], self.files[idx]
            self._last_selected = new
            self._render_rows()

    def _browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.out_entry.delete(0, "end")
            self.out_entry.insert(0, folder)

    # ── Render file rows ──────────────────────────────────────────────────
    def _render_rows(self):
        # Destroy old rows
        for r in self.rows:
            r.destroy()
        self.rows.clear()

        show_empty = len(self.files) == 0
        if show_empty:
            self.empty_frame.grid()
        else:
            self.empty_frame.grid_remove()

        for i, fp in enumerate(self.files):
            row = FileRow(
                self.scroll, fp, i,
                on_remove=self._remove_file,
                on_drag_start=self._drag_start,
                on_drag_motion=self._drag_motion,
                on_drag_end=self._drag_end
            )
            row.grid(row=i, column=0, sticky="ew", padx=6, pady=3)
            row.bind("<Button-1>", lambda e, idx=i: setattr(self, "_last_selected", idx))
            self.rows.append(row)

        self.count_lbl.configure(
            text=f"{len(self.files)} file{'s' if len(self.files) != 1 else ''}"
        )

    # ── Drag-to-reorder logic ─────────────────────────────────────────────
    def _drag_start(self, idx: int, event):
        self._drag_from = idx
        self._last_selected = idx
        if self.rows:
            self.rows[idx].highlight(True)

    def _drag_motion(self, idx: int, event):
        if self._drag_from is None:
            return
        # Calculate which row the cursor is over
        target = self._row_under_cursor(event)
        for i, r in enumerate(self.rows):
            r.highlight(i == target and target != self._drag_from)

    def _drag_end(self, idx: int, event):
        if self._drag_from is None:
            return
        target = self._row_under_cursor(event)
        if target is not None and target != self._drag_from:
            f = self.files.pop(self._drag_from)
            self.files.insert(target, f)
            self._last_selected = target
            self._render_rows()
        else:
            for r in self.rows:
                r.highlight(False)
        self._drag_from = None

    def _row_under_cursor(self, event) -> int | None:
        """Return index of the row the cursor is over, or None."""
        try:
            x = self.winfo_pointerx()
            y = self.winfo_pointery()
            for i, r in enumerate(self.rows):
                rx, ry = r.winfo_rootx(), r.winfo_rooty()
                rw, rh = r.winfo_width(), r.winfo_height()
                if rx <= x <= rx + rw and ry <= y <= ry + rh:
                    return i
        except Exception:
            pass
        return None

    # ── Merge logic ───────────────────────────────────────────────────────
    def _start_merge(self):
        if not self.files:
            messagebox.showwarning("No Files", "Please add at least one PDF to merge.")
            return
        if len(self.files) == 1:
            if not messagebox.askyesno(
                "Single File",
                "Only one PDF is loaded. Do you want to 'merge' (copy) it?"
            ):
                return
        self.merge_btn.configure(state="disabled", text="Merging…")
        self.progress.set(0)
        threading.Thread(target=self._merge_worker, daemon=True).start()

    def _merge_worker(self):
        try:
            # Determine output folder
            out_dir = self.out_entry.get().strip()
            if not out_dir:
                out_dir = os.path.join(Path.home(), "EffCorp_Output")
            os.makedirs(out_dir, exist_ok=True)

            # Timestamped file name
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = os.path.join(out_dir, f"Merged_{ts}.pdf")

            writer = PdfWriter()
            total = len(self.files)

            for i, fp in enumerate(self.files):
                self.after(0, lambda i=i: (
                    self._status(
                        f"Processing {i+1}/{total}: {Path(fp).name}",
                        PALETTE["accent"]
                    ),
                    self.progress.set((i) / total)
                ))
                reader = PdfReader(fp)
                for page in reader.pages:
                    writer.add_page(page)
                self.after(0, lambda v=(i+1)/total: self.progress.set(v))

            self.after(0, lambda: self._status("Writing output file…", PALETTE["accent"]))
            with open(out_path, "wb") as f:
                writer.write(f)

            self.after(0, lambda: self._merge_done(out_path, total))
        except Exception as exc:
            self.after(0, lambda: self._merge_error(str(exc)))

    def _merge_done(self, out_path: str, count: int):
        self.progress.set(1)
        self.merge_btn.configure(state="normal", text="⚡  Merge PDF")
        total_pages = sum(
            len(PdfReader(f).pages) for f in self.files if os.path.isfile(f)
        )
        self._status(
            f"✓  Merged {count} files ({total_pages} pages) → {Path(out_path).name}",
            PALETTE["success"]
        )
        if messagebox.askyesno(
            "Merge Complete",
            f"✅  PDF merged successfully!\n\n"
            f"Files   : {count}\n"
            f"Pages   : {total_pages}\n"
            f"Saved to: {out_path}\n\n"
            f"Open the output folder now?"
        ):
            self._open_folder(str(Path(out_path).parent))

    def _merge_error(self, msg: str):
        self.progress.set(0)
        self.merge_btn.configure(state="normal", text="⚡  Merge PDF")
        self._status(f"✗  Error: {msg}", PALETTE["danger"])
        messagebox.showerror("Merge Failed", f"An error occurred:\n{msg}")

    # ── Helpers ───────────────────────────────────────────────────────────
    def _status(self, msg: str, color: str = PALETTE["text_dim"]):
        self.status_lbl.configure(text=msg, text_color=color)

    def _toggle_theme(self, value: str):
        ctk.set_appearance_mode("dark" if value == "Dark" else "light")

    @staticmethod
    def _open_folder(path: str):
        import subprocess
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])


# ── Entry-point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = PDFMergerApp()
    app.mainloop()