"""Tool 3.5: Universal Document Converter.

Performs offline high-fidelity conversions:
- PDF ➔ Images (PNG / JPG / WebP per page)
- Images ➔ PDF (Combine photos/scans into document)
- PDF ➔ Clean Plain Text (.txt) or HTML (.html)
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk
import pymupdf
from PIL import Image

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class PdfConverterTool(BaseToolFrame):
    """Universal 2-pane tool for converting documents and image collections."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="pdf_converter",
            title="Universal Document Converter",
            description="Convert PDF documents to high-resolution images, plain text, or merge photos into documents.",
            **kwargs
        )
        self.file_paths: List[str] = []

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # Mode Selection
        mode_lbl = ctk.CTkLabel(
            container,
            text="CONVERSION TARGET",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        mode_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

        self.conv_mode_var = tk.StringVar(value="PDF to Images (PNG)")
        self.combo_mode = ctk.CTkComboBox(
            container,
            values=[
                "PDF to Images (PNG)",
                "PDF to Images (JPG)",
                "Images to PDF Document",
                "PDF to Plain Text (.txt)",
                "PDF to HTML Document (.html)"
            ],
            variable=self.conv_mode_var,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.combo_mode.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # File Selection Header & Buttons
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.btn_add = ctk.CTkButton(
            btn_row,
            text="+ Add Files",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            height=32,
            command=self._add_files
        )
        self.btn_add.pack(side="left", padx=(0, Theme.PAD_SM))

        self.btn_clear = ctk.CTkButton(
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
        self.btn_clear.pack(side="right")

        # Files Counter & Preview Box
        self.counter_lbl = ctk.CTkLabel(
            container,
            text="No files selected",
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
            text="⚡  Start Conversion",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=42,
            command=self._execute
        )
        self.btn_execute.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

    def _add_files(self):
        mode = self.conv_mode_var.get()
        if "Images to PDF" in mode:
            ftypes = [("Images", "*.png *.jpg *.jpeg *.webp *.bmp")]
            title = "Select Images to Combine"
        else:
            ftypes = [("PDF Documents", "*.pdf")]
            title = "Select PDF Documents"

        paths = filedialog.askopenfilenames(title=title, filetypes=ftypes)
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
        txt = f"{n} file{'s' if n != 1 else ''} loaded" if n else "No files selected"
        self.counter_lbl.configure(text=txt)

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        for idx, p in enumerate(self.file_paths):
            self.preview_box.insert("end", f"{idx+1}. {os.path.basename(p)}\n")
        self.preview_box.configure(state="disabled")

    def _execute(self):
        if not self.file_paths:
            messagebox.showwarning("Notice", "Please select input files first.")
            return

        out_folder = self.out_var.get().strip()
        if not out_folder or not os.path.exists(out_folder):
            messagebox.showwarning("Notice", "Please choose a valid destination folder.")
            return

        mode = self.conv_mode_var.get()
        self.output_directory = out_folder
        self.btn_execute.configure(state="disabled")

        def _task():
            total = len(self.file_paths)
            self.log(f"Starting [{mode}] conversion...")

            if "Images to PDF" in mode:
                # ── Combine images into single PDF
                images = []
                for p in self.file_paths:
                    img = Image.open(p).convert("RGB")
                    images.append(img)
                
                out_pdf = os.path.join(out_folder, "images_combined.pdf")
                images[0].save(out_pdf, save_all=True, append_images=images[1:])
                self.log(f"✓ Created compilation: {os.path.basename(out_pdf)}")
                self.set_progress(1.0)
                return out_pdf

            for idx, p in enumerate(self.file_paths):
                base_name = os.path.splitext(os.path.basename(p))[0]
                doc = pymupdf.open(p)

                if "PDF to Images" in mode:
                    ext = "png" if "PNG" in mode else "jpg"
                    self.log(f"Rendering {base_name} ({len(doc)} pages) to {ext.upper()}...")
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        pix = page.get_pixmap(dpi=200) # High-res 200 DPI
                        out_img = os.path.join(out_folder, f"{base_name}_page_{page_num+1}.{ext}")
                        pix.save(out_img)
                    self.log(f"✓ Saved {len(doc)} pages as images for: {base_name}")

                elif "Plain Text" in mode:
                    out_txt = os.path.join(out_folder, f"{base_name}_extracted.txt")
                    with open(out_txt, "w", encoding="utf-8") as f_txt:
                        for page in doc:
                            f_txt.write(page.get_text())
                    self.log(f"✓ Extracted text: {os.path.basename(out_txt)}")

                elif "HTML Document" in mode:
                    out_html = os.path.join(out_folder, f"{base_name}.html")
                    with open(out_html, "w", encoding="utf-8") as f_html:
                        for page in doc:
                            f_html.write(page.get_text("html"))
                    self.log(f"✓ Exported HTML: {os.path.basename(out_html)}")

                doc.close()
                self.set_progress((idx + 1) / total * 0.9)

            return out_folder

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"Conversion completed successfully!\nSaved to: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Conversion failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
