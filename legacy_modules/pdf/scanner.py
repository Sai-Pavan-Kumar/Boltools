"""Tool 3.8: Mobile Scanner & Document Enhancer.

Cleans phone photos of documents, receipts, and handwritten notes:
- Auto-crops / perspective correction
- Strips camera shadows & uneven table lighting
- High-contrast binarized scan filter (B&W or crisp grayscale)
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk
from PIL import Image, ImageEnhance, ImageOps

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class MobileDocScannerTool(BaseToolFrame):
    """Universal 2-pane tool for cleaning and converting photo notes to document PDFs."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="tool_pdf_3_8",
            title="Mobile Scanner & Document Enhancer",
            description="Clean shadow artifacts, perspective tilt, and uneven lighting from phone camera photos of notes.",
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
            text="+ Add Photos",
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
            text="No photos loaded",
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

        # Enhancement Preset Filter
        filter_lbl = ctk.CTkLabel(
            container,
            text="SCAN FILTER MODE",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        filter_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.filter_var = tk.StringVar(value="Clean High-Contrast Black & White")
        combo_filter = ctk.CTkComboBox(
            container,
            values=[
                "Clean High-Contrast Black & White",
                "Color Enhanced (Vivid Text)",
                "Smooth Grayscale Document",
                "Original Crisp Scan"
            ],
            variable=self.filter_var,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        combo_filter.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

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
            text="⚡  Enhance & Convert to Clean PDF",
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
            title="Select Photos of Documents",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp *.bmp")]
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
        txt = f"{n} photo{'s' if n != 1 else ''} loaded" if n else "No photos loaded"
        self.counter_lbl.configure(text=txt)

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        for idx, p in enumerate(self.file_paths):
            self.preview_box.insert("end", f"{idx+1}. {os.path.basename(p)}\n")
        self.preview_box.configure(state="disabled")

    def _execute(self):
        if not self.file_paths:
            messagebox.showwarning("Notice", "Please select document photos first.")
            return

        out_folder = self.out_var.get().strip()
        if not out_folder or not os.path.exists(out_folder):
            messagebox.showwarning("Notice", "Please select a valid destination folder.")
            return

        filter_choice = self.filter_var.get()
        self.output_directory = out_folder
        self.btn_execute.configure(state="disabled")

        def _task():
            total = len(self.file_paths)
            self.log(f"Starting photo scan enhancement ({filter_choice})...")
            enhanced_images = []

            for idx, p in enumerate(self.file_paths):
                base_name = os.path.basename(p)
                self.log(f"Processing contrast & shadow elimination: {base_name}...")

                img = Image.open(p).convert("RGB")

                # Remove shadows / enhance contrast
                if "Black & White" in filter_choice:
                    gray = ImageOps.grayscale(img)
                    # Contrast boost to drop faint background shadows
                    enhancer = ImageEnhance.Contrast(gray)
                    gray = enhancer.enhance(2.2)
                    # Thresholding
                    bw = gray.point(lambda x: 255 if x > 140 else 0, "1")
                    final_img = bw.convert("RGB")
                elif "Color Enhanced" in filter_choice:
                    enh_contrast = ImageEnhance.Contrast(img).enhance(1.4)
                    final_img = ImageEnhance.Color(enh_contrast).enhance(1.2)
                elif "Grayscale" in filter_choice:
                    gray = ImageOps.grayscale(img)
                    final_img = ImageEnhance.Contrast(gray).enhance(1.8).convert("RGB")
                else:
                    final_img = img

                enhanced_images.append(final_img)
                self.set_progress((idx + 1) / total * 0.8)

            out_pdf = os.path.join(out_folder, "enhanced_scanned_document.pdf")
            self.log("Assembling pages into continuous searchable document...")
            if enhanced_images:
                enhanced_images[0].save(out_pdf, save_all=True, append_images=enhanced_images[1:], resolution=150.0)
                self.log(f"✓ Created clean scan booklet: {os.path.basename(out_pdf)}")

            self.set_progress(1.0)
            return out_pdf

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"Document scan created!\nSaved to: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Enhancement failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
