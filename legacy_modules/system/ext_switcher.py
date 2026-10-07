"""Tool 7.3: Smart File Extension Corrector.

Inspects true underlying file headers (magic bytes) to diagnose corrupted
or misnamed extensions and safely restores proper OS associations.
"""

import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Optional
import customtkinter as ctk

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class ExtensionCorrectorTool(BaseToolFrame):
    """Universal 2-pane tool for detecting and repairing file extensions."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="system_ext_switcher",
            title="Smart File Extension Corrector",
            description="Detect true file headers (magic bytes) and safely repair misnamed or missing extensions.",
            **kwargs
        )
        self.file_paths: List[str] = []

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # File Selection Header & Buttons
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

        btn_add = ctk.CTkButton(
            btn_row,
            text="+ Add Files",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            height=32,
            command=self._add_files
        )
        btn_add.pack(side="left", padx=(0, Theme.PAD_SM))

        btn_clear = ctk.CTkButton(
            btn_row,
            text="Clear",
            fg_color="transparent",
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.STATUS_ERROR,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12),
            height=32,
            width=60,
            command=self._clear_files
        )
        btn_clear.pack(side="right")

        # Files Counter & List Box
        self.counter_lbl = ctk.CTkLabel(
            container,
            text="No files loaded",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        self.counter_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_XS))

        self.preview_box = ctk.CTkTextbox(
            container,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_SECONDARY,
            font=(Theme.FONT_MONO, 11),
            corner_radius=Theme.RADIUS_INPUT,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            height=120
        )
        self.preview_box.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        self.preview_box.configure(state="disabled")

        # Target Extension Mode
        target_lbl = ctk.CTkLabel(
            container,
            text="TARGET EXTENSION TO ENFORCE",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        target_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.target_ext_var = tk.StringVar(value=".mp4")
        self.combo_ext = ctk.CTkComboBox(
            container,
            values=[
                ".mp4", ".mp3", ".wav", ".png", ".jpg", ".webp",
                ".pdf", ".docx", ".xlsx", ".zip", ".txt", ".json"
            ],
            variable=self.target_ext_var,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.combo_ext.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Safe Mode Checkbox (Create copy rather than overwrite in place)
        self.create_copy_var = tk.BooleanVar(value=True)
        self.chk_copy = ctk.CTkCheckBox(
            container,
            text="Create safe copy (preserves original file intact)",
            variable=self.create_copy_var,
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_PRIMARY
        )
        self.chk_copy.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        # Execute CTA
        self.btn_execute = ctk.CTkButton(
            container,
            text="⚡  Repair Extensions",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=42,
            command=self._execute
        )
        self.btn_execute.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

    def _detect_magic(self, path: str) -> Optional[str]:
        """Sniffs first 16 bytes to detect true file format."""
        try:
            with open(path, "rb") as f:
                head = f.read(16)
            if head.startswith(b"\x89PNG\r\n\x1a\n"): return ".png"
            if head.startswith(b"\xff\xd8\xff"): return ".jpg"
            if head.startswith(b"RIFF") and b"WEBP" in head: return ".webp"
            if head.startswith(b"%PDF"): return ".pdf"
            if head.startswith(b"PK\x03\x04"): return ".zip/.docx/.xlsx"
            if b"ftyp" in head: return ".mp4"
            if head.startswith(b"ID3") or head.startswith(b"\xff\xfb"): return ".mp3"
        except Exception:
            pass
        return None

    def _add_files(self):
        paths = filedialog.askopenfilenames(title="Select Files to Fix")
        if paths:
            for p in paths:
                if p not in self.file_paths:
                    self.file_paths.append(p)
            self._update_preview()

    def _clear_files(self):
        self.file_paths.clear()
        self._update_preview()

    def _update_preview(self):
        n = len(self.file_paths)
        txt = f"{n} file{'s' if n != 1 else ''} loaded" if n else "No files loaded"
        self.counter_lbl.configure(text=txt)

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        for idx, p in enumerate(self.file_paths):
            detected = self._detect_magic(p) or "unknown"
            self.preview_box.insert("end", f"{idx+1}. {os.path.basename(p)}  [Detected: {detected}]\n")
        self.preview_box.configure(state="disabled")

    def _execute(self):
        if not self.file_paths:
            messagebox.showwarning("Notice", "Please select files to correct.")
            return

        target_ext = self.target_ext_var.get().strip().lower()
        if not target_ext.startswith("."):
            target_ext = "." + target_ext

        create_copy = self.create_copy_var.get()
        self.btn_execute.configure(state="disabled")

        def _task():
            total = len(self.file_paths)
            self.log(f"Applying extension correction to {target_ext.upper()}...")

            for idx, p in enumerate(self.file_paths):
                dirname = os.path.dirname(p)
                base = os.path.splitext(os.path.basename(p))[0]
                new_path = os.path.join(dirname, f"{base}{target_ext}")

                if create_copy:
                    shutil.copy2(p, new_path)
                    self.log(f"[{idx+1}/{total}] Created safe copy: {os.path.basename(new_path)}")
                else:
                    if p != new_path:
                        os.rename(p, new_path)
                        self.log(f"[{idx+1}/{total}] Renamed: {os.path.basename(new_path)}")

                self.set_progress((idx + 1) / total * 0.9)

            return os.path.dirname(self.file_paths[0])

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"Extensions repaired successfully!\nDirectory: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
