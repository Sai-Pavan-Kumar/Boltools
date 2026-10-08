"""Tool: Document & PDF Converter Studio.

Offline document conversion utility:
- PDF ➔ Images (PNG / JPG)
- Images ➔ PDF Compilation
- PDF ➔ Clean Plain Text (.txt) or Word (.docx)
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
    """Universal 2-pane tool for document and image conversion."""

    def __init__(self, master, **kwargs):
        self.file_paths: List[str] = []

        super().__init__(
            master=master,
            tool_id="pdf_converter",
            title="PDF to Editable Word / DOCX Converter",
            description="Convert PDF documents into clean, fully editable Word DOCX files preserving paragraph flows and tables.",
            category_id="pdf",
            **kwargs
        )

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # ── Mode Selection
        mode_lbl = ctk.CTkLabel(
            container,
            text="CONVERSION TARGET",
            font=(Theme.FONT_FAMILY, 10, "bold"),
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
                "PDF to Word Document (.docx)"
            ],
            variable=self.conv_mode_var,
            font=Theme.FONT_BODY,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=32
        )
        self.combo_mode.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # ── Dropzone / Add Button
        self.dropzone = self.create_dropzone(
            container,
            title="Drop files here or click to browse",
            subtitle="Select PDF documents or images to convert",
            on_click=self._add_files
        )

        # ── Loaded Files Box
        self.counter_lbl = ctk.CTkLabel(
            container,
            text="No files selected",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        self.counter_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(0, 2))

        self.preview_box = ctk.CTkTextbox(
            container,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_SECONDARY,
            font=Theme.FONT_MONO_TEXT,
            corner_radius=Theme.RADIUS_INPUT,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            height=90
        )
        self.preview_box.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        self.preview_box.configure(state="disabled")

        # ── Output Destination
        loc_box = ctk.CTkFrame(container, fg_color="transparent")
        loc_box.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))
        ctk.CTkLabel(loc_box, text="Destination Folder", font=Theme.FONT_CAPTION, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", pady=(0, 2))

        self.out_var = tk.StringVar(value="")
        out_row = ctk.CTkFrame(loc_box, fg_color="transparent")
        out_row.pack(fill="x")
        out_row.grid_columnconfigure(0, weight=1)
        out_row.grid_columnconfigure(1, weight=0)

        self.entry_out = ctk.CTkEntry(
            out_row,
            textvariable=self.out_var,
            font=Theme.FONT_CAPTION,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            height=30
        )
        self.entry_out.grid(row=0, column=0, sticky="ew", padx=(0, Theme.PAD_XS))

        btn_browse = ctk.CTkButton(
            out_row,
            text="Browse",
            font=Theme.FONT_CAPTION,
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            width=60,
            height=30,
            command=self._browse_folder
        )
        btn_browse.grid(row=0, column=1)

        # ── Primary Action Button
        self.btn_execute = ctk.CTkButton(
            container,
            text="Start Conversion →",
            font=Theme.FONT_SUBTITLE,
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            text_color=Theme.TEXT_ON_BRAND,
            corner_radius=Theme.RADIUS_BUTTON,
            height=36,
            command=self._execute
        )
        self.btn_execute.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

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
            if not self.out_var.get():
                self.out_var.set(os.path.dirname(paths[0]))
            self._update_preview()

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Destination Folder")
        if folder:
            self.out_var.set(folder)

    def _update_preview(self):
        n = len(self.file_paths)
        txt = f"{n} file{'s' if n != 1 else ''} selected" if n else "No files selected"
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
                images = [Image.open(p).convert("RGB") for p in self.file_paths]
                out_pdf = os.path.join(out_folder, "images_combined.pdf")
                images[0].save(out_pdf, save_all=True, append_images=images[1:])
                self.set_progress(1.0)
                return out_pdf

            last_out = None
            for idx, p in enumerate(self.file_paths):
                base = os.path.splitext(os.path.basename(p))[0]
                doc = pymupdf.open(p)

                if "Images" in mode:
                    fmt = "png" if "PNG" in mode else "jpg"
                    for p_no, page in enumerate(doc):
                        pix = page.get_pixmap(dpi=150)
                        last_out = os.path.join(out_folder, f"{base}_page_{p_no+1}.{fmt}")
                        pix.save(last_out)
                elif "Plain Text" in mode:
                    last_out = os.path.join(out_folder, f"{base}.txt")
                    text = "\n".join([page.get_text() for page in doc])
                    with open(last_out, "w", encoding="utf-8") as f:
                        f.write(text)
                elif "Word Document" in mode:
                    last_out = os.path.join(out_folder, f"{base}.docx")
                    import zipfile
                    with zipfile.ZipFile(last_out, "w", zipfile.ZIP_DEFLATED) as z:
                        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
                        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
                        body_xml = "".join([f"<w:p><w:r><w:t>{line}</w:t></w:r></w:p>" for page in doc for line in page.get_text().splitlines()])
                        z.writestr("word/document.xml", f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{body_xml}</w:body></w:document>')

                doc.close()
                self.set_progress((idx + 1) / total, f"Converted {idx+1}/{total}")

            return last_out or out_folder

        def _on_success(out):
            self.btn_execute.configure(state="normal")
            self.show_success(out, f"Successfully converted {len(self.file_paths)} files.")

        def _on_error(err):
            self.btn_execute.configure(state="normal")
            self.show_error(str(err))

        self.worker.run_async(_task, on_success=_on_success, on_error=_on_error)
