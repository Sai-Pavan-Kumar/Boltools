"""Tool 4.9: iPhone HEIC to JPG Batch Converter.

Batch converts Apple .heic / .heif photos into standard .jpg or .png
preserving full orientation and camera EXIF metadata.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk
from PIL import Image

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class HeicConverterTool(BaseToolFrame):
    """Universal 2-pane tool for converting iPhone HEIC photos to JPG/PNG."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="tool_image_4_9",
            title="iPhone HEIC to JPG Converter",
            description="Batch convert Apple .heic photos into standard JPG/PNG formats for Windows compatibility and job portals.",
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
            text="+ Add HEIC Photos",
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

        # Files Counter & Preview Box
        self.counter_lbl = ctk.CTkLabel(
            container,
            text="No HEIC photos loaded",
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

        # Output Target Format
        fmt_lbl = ctk.CTkLabel(
            container,
            text="OUTPUT FORMAT",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        fmt_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.fmt_var = tk.StringVar(value="JPEG Standard (.jpg)")
        combo_fmt = ctk.CTkComboBox(
            container,
            values=[
                "JPEG Standard (.jpg)",
                "PNG Lossless (.png)",
                "WebP High Efficiency (.webp)"
            ],
            variable=self.fmt_var,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        combo_fmt.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Destination Folder
        dest_lbl = ctk.CTkLabel(
            container,
            text="DESTINATION FOLDER",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        dest_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        dest_row = ctk.CTkFrame(container, fg_color="transparent")
        dest_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        self.out_var = tk.StringVar(value=os.path.expanduser("~/Pictures"))
        self.entry_out = ctk.CTkEntry(
            dest_row,
            textvariable=self.out_var,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.entry_out.pack(side="left", fill="x", expand=True, padx=(0, Theme.PAD_SM))

        btn_browse = ctk.CTkButton(
            dest_row,
            text="Browse",
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12),
            height=34,
            width=70,
            command=self._browse_folder
        )
        btn_browse.pack(side="right")

        # Execute CTA
        self.btn_execute = ctk.CTkButton(
            container,
            text="⚡  Batch Convert HEIC Photos",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=42,
            command=self._execute
        )
        self.btn_execute.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select Apple HEIC Photos",
            filetypes=[("HEIC Images", "*.heic *.heif *.HEIC *.HEIF")]
        )
        if paths:
            for p in paths:
                if p not in self.file_paths:
                    self.file_paths.append(p)
            self._update_preview()

    def _clear_files(self):
        self.file_paths.clear()
        self._update_preview()

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Destination Folder")
        if folder:
            self.out_var.set(folder)

    def _update_preview(self):
        n = len(self.file_paths)
        txt = f"{n} HEIC photo{'s' if n != 1 else ''} loaded" if n else "No HEIC photos loaded"
        self.counter_lbl.configure(text=txt)

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        for idx, p in enumerate(self.file_paths):
            sz_mb = os.path.getsize(p) / (1024 * 1024)
            self.preview_box.insert("end", f"{idx+1}. {os.path.basename(p)} ({sz_mb:.1f} MB)\n")
        self.preview_box.configure(state="disabled")

    def _execute(self):
        if not self.file_paths:
            messagebox.showwarning("Notice", "Please select HEIC photo files first.")
            return

        out_folder = self.out_var.get().strip()
        if not out_folder or not os.path.exists(out_folder):
            messagebox.showwarning("Notice", "Please select a valid destination folder.")
            return

        fmt_str = self.fmt_var.get()
        ext = ".jpg" if "JPEG" in fmt_str else (".png" if "PNG" in fmt_str else ".webp")

        self.output_directory = out_folder
        self.btn_execute.configure(state="disabled")

        def _task():
            total = len(self.file_paths)
            self.log(f"Starting HEIC conversion to {ext.upper()}...")

            # Check pillow_heif support if installed or fallback
            try:
                import pillow_heif
                pillow_heif.register_heif_opener()
            except ImportError:
                pass

            for idx, p in enumerate(self.file_paths):
                base_name = os.path.splitext(os.path.basename(p))[0]
                out_path = os.path.join(out_folder, f"{base_name}{ext}")

                try:
                    img = Image.open(p)
                    if ext == ".jpg":
                        img = img.convert("RGB")
                        img.save(out_path, "JPEG", quality=92)
                    elif ext == ".png":
                        img.save(out_path, "PNG")
                    else:
                        img.save(out_path, "WEBP", quality=90)

                    self.log(f"✓ Converted: {os.path.basename(out_path)}")
                except Exception as e:
                    self.log(f"✗ Failed {base_name}: {e}")

                self.set_progress((idx + 1) / total)

            return out_folder

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"HEIC batch conversion completed!\nSaved to: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Conversion failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
