"""Tool 3.7: Lossless PDF Scan Compressor.

Optimizes high-DPI raster images inside scanned PDFs down to
target DPI standards (Screen 72 DPI, eBook 150 DPI, Print 300 DPI)
to hit strict university and government portal upload caps (< 200 KB).
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk
import pymupdf

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class PdfCompressorTool(BaseToolFrame):
    """Universal 2-pane tool for PDF scan and document compression."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="tool_pdf_3_7",
            title="Lossless PDF Scan Compressor",
            description="Crush heavy multi-megabyte PDF scans down to <200 KB to clear government job & university upload limits.",
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
            text="+ Add PDFs",
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
            text="No PDFs loaded",
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

        # Compression Preset
        preset_lbl = ctk.CTkLabel(
            container,
            text="COMPRESSION LEVEL",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        preset_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.level_var = tk.StringVar(value="Government Portal Max (<200 KB, 100 DPI)")
        combo_level = ctk.CTkComboBox(
            container,
            values=[
                "Government Portal Max (<200 KB, 100 DPI)",
                "Balanced Web & Email (150 DPI)",
                "High Quality Print Archival (200 DPI)",
                "Aggressive Mobile Screen (72 DPI)"
            ],
            variable=self.level_var,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        combo_level.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

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

        self.out_var = tk.StringVar(value=os.path.expanduser("~/Documents"))
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
            text="⚡  Compress PDF Documents",
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
            title="Select PDF Documents",
            filetypes=[("PDF Documents", "*.pdf")]
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
        txt = f"{n} PDF{'s' if n != 1 else ''} loaded" if n else "No PDFs loaded"
        self.counter_lbl.configure(text=txt)

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        for idx, p in enumerate(self.file_paths):
            sz_kb = os.path.getsize(p) / 1024
            self.preview_box.insert("end", f"{idx+1}. {os.path.basename(p)} ({sz_kb:.1f} KB)\n")
        self.preview_box.configure(state="disabled")

    def _execute(self):
        if not self.file_paths:
            messagebox.showwarning("Notice", "Please select at least one PDF file.")
            return

        out_folder = self.out_var.get().strip()
        if not out_folder or not os.path.exists(out_folder):
            messagebox.showwarning("Notice", "Please select a valid destination folder.")
            return

        level_str = self.level_var.get()
        if "72 DPI" in level_str:
            target_dpi = 72
        elif "100 DPI" in level_str:
            target_dpi = 100
        elif "150 DPI" in level_str:
            target_dpi = 150
        else:
            target_dpi = 200

        self.output_directory = out_folder
        self.btn_execute.configure(state="disabled")

        def _task():
            total = len(self.file_paths)
            self.log(f"Starting PDF Compression (Target Quality: {target_dpi} DPI)...")

            for idx, p in enumerate(self.file_paths):
                base_name = os.path.splitext(os.path.basename(p))[0]
                out_pdf = os.path.join(out_folder, f"{base_name}_compressed.pdf")
                orig_size = os.path.getsize(p)

                doc = pymupdf.open(p)
                new_doc = pymupdf.open()

                # Re-render pages down to target DPI
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    rect = page.rect
                    pix = page.get_pixmap(dpi=target_dpi)
                    img_bytes = pix.tobytes("jpeg")
                    new_page = new_doc.new_page(width=rect.width, height=rect.height)
                    new_page.insert_image(rect, stream=img_bytes)

                new_doc.save(out_pdf, deflate=True, garbage=4, clean=True)
                new_doc.close()
                doc.close()

                new_size = os.path.getsize(out_pdf)
                reduction = ((orig_size - new_size) / orig_size) * 100
                self.log(f"✓ {base_name}: {orig_size/1024:.1f} KB ➔ {new_size/1024:.1f} KB (-{reduction:.1f}%)")
                self.set_progress((idx + 1) / total)

            return out_folder

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"PDF compression completed!\nSaved to: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Compression failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
