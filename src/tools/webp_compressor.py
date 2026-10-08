"""Tool: Smart WebP Batch Compressor.

Bulk compresses images into modern WebP format with automated photo vs illustration
detection, smart color quantization, and proportional downscaling. 100% offline.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk
from PIL import Image

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class WebpCompressorTool(BaseToolFrame):
    """Universal 2-pane tool for batch WebP compression."""

    def __init__(self, master, **kwargs):
        self.file_paths: List[str] = []

        super().__init__(
            master=master,
            tool_id="image_webp_compress",
            title="WebP Image Compressor",
            description="Bulk compress photos into web-optimized WebP images with custom quality controls.",
            category_id="image",
            **kwargs
        )

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # File Selection Header & Buttons
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

        btn_add = ctk.CTkButton(
            btn_row,
            text="+ Add Images",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=Theme.FONT_BODY_BOLD,
            height=32,
            command=self._add_files
        )
        btn_add.pack(side="left", padx=(0, Theme.PAD_SM))

        btn_folder = ctk.CTkButton(
            btn_row,
            text="Add Folder",
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.RADIUS_BUTTON,
            font=Theme.FONT_BODY,
            height=32,
            command=self._add_folder
        )
        btn_folder.pack(side="left", padx=(0, Theme.PAD_SM))

        btn_clear = ctk.CTkButton(
            btn_row,
            text="Clear",
            fg_color="transparent",
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.STATUS_ERROR,
            corner_radius=Theme.RADIUS_BUTTON,
            font=Theme.FONT_BODY,
            height=32,
            width=60,
            command=self._clear_files
        )
        btn_clear.pack(side="right")

        # Files Counter & List Box
        self.counter_lbl = ctk.CTkLabel(
            container,
            text="No images loaded",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        self.counter_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_XS))

        self.preview_box = ctk.CTkTextbox(
            container,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_SECONDARY,
            font=Theme.FONT_MONO_TEXT,
            corner_radius=Theme.RADIUS_INPUT,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            height=100
        )
        self.preview_box.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        self.preview_box.configure(state="disabled")

        # Compression Quality Slider
        qual_header = ctk.CTkFrame(container, fg_color="transparent")
        qual_header.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, 2))

        qual_lbl = ctk.CTkLabel(
            qual_header,
            text="COMPRESSION QUALITY",
            font=(Theme.FONT_FAMILY, 10, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        qual_lbl.pack(side="left")

        self.qual_val_lbl = ctk.CTkLabel(
            qual_header,
            text="80%",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.BRAND_ACCENT,
            anchor="e"
        )
        self.qual_val_lbl.pack(side="right")

        self.qual_slider = ctk.CTkSlider(
            container,
            from_=40,
            to=100,
            number_of_steps=60,
            command=self._on_qual_change,
            fg_color=Theme.SURFACE_INSET,
            progress_color=Theme.BRAND_PRIMARY,
            button_color=Theme.TEXT_PRIMARY
        )
        self.qual_slider.set(80)
        self.qual_slider.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Max Dimension Limit
        max_dim_lbl = ctk.CTkLabel(
            container,
            text="MAXIMUM WIDTH LIMIT (Auto Downscale)",
            font=(Theme.FONT_FAMILY, 10, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        max_dim_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.dim_var = tk.StringVar(value="1920px (Full HD)")
        self.combo_dim = ctk.CTkComboBox(
            container,
            values=["Original (No Downscale)", "1920px (Full HD)", "2560px (2K)", "3840px (4K)", "1280px (Web Compact)"],
            variable=self.dim_var,
            font=Theme.FONT_BODY,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.combo_dim.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Smart Detect Toggle
        self.smart_detect_var = tk.BooleanVar(value=True)
        self.chk_smart = ctk.CTkCheckBox(
            container,
            text="Enable Smart Mode (256-color palette for logos/graphics)",
            variable=self.smart_detect_var,
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_PRIMARY
        )
        self.chk_smart.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Destination Folder
        dest_lbl = ctk.CTkLabel(
            container,
            text="SAVE DESTINATION FOLDER",
            font=(Theme.FONT_FAMILY, 10, "bold"),
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
            font=Theme.FONT_BODY,
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
            font=Theme.FONT_BODY,
            height=34,
            width=70,
            command=self._browse_folder
        )
        btn_browse.pack(side="right")

        # Execute CTA
        self.btn_execute = ctk.CTkButton(
            container,
            text="Start Batch Compression →",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=Theme.FONT_BODY_BOLD,
            height=42,
            command=self._execute
        )
        self.btn_execute.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

    def _on_qual_change(self, val):
        self.qual_val_lbl.configure(text=f"{int(val)}%")

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select Images to Compress",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff")]
        )
        if paths:
            for p in paths:
                if p not in self.file_paths:
                    self.file_paths.append(p)
            self._update_preview()

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder Containing Images")
        if folder:
            valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
            count = 0
            for fname in sorted(os.listdir(folder)):
                ext = os.path.splitext(fname)[1].lower()
                if ext in valid_exts:
                    full_p = os.path.join(folder, fname)
                    if full_p not in self.file_paths:
                        self.file_paths.append(full_p)
                        count += 1
            self.log(f"Loaded {count} images from: {folder}")
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
        txt = f"{n} image{'s' if n != 1 else ''} loaded" if n else "No images loaded"
        self.counter_lbl.configure(text=txt)

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        for idx, p in enumerate(self.file_paths):
            self.preview_box.insert("end", f"{idx+1}. {os.path.basename(p)}\n")
        self.preview_box.configure(state="disabled")

    def _get_max_width(self) -> int:
        choice = self.dim_var.get()
        if "1920" in choice: return 1920
        if "2560" in choice: return 2560
        if "3840" in choice: return 3840
        if "1280" in choice: return 1280
        return 999999

    def _execute(self):
        if not self.file_paths:
            messagebox.showwarning("Notice", "Please select at least one image first.")
            return

        out_folder = self.out_var.get().strip()
        if not out_folder or not os.path.exists(out_folder):
            messagebox.showwarning("Notice", "Please specify a valid destination folder.")
            return

        quality = int(self.qual_slider.get())
        max_w = self._get_max_width()
        smart_detect = self.smart_detect_var.get()
        self.output_directory = out_folder
        self.btn_execute.configure(state="disabled")

        def _task():
            total = len(self.file_paths)
            total_orig_bytes = 0
            total_comp_bytes = 0

            self.log(f"Starting batch compression for {total} image(s)...")

            for i, p in enumerate(self.file_paths):
                orig_bytes = os.path.getsize(p)
                total_orig_bytes += orig_bytes
                fname = os.path.basename(p)
                base = os.path.splitext(fname)[0]
                save_path = os.path.join(out_folder, f"{base}.webp")

                with Image.open(p) as img:
                    # 1. Proportional Downscaling
                    if img.width > max_w:
                        ratio = max_w / float(img.width)
                        new_h = int(float(img.height) * ratio)
                        img = img.resize((max_w, new_h), Image.Resampling.LANCZOS)

                    # 2. Smart Graphic / Photo Detection
                    if smart_detect:
                        colors = img.getcolors(maxcolors=10000)
                        if colors is not None and img.mode in ("RGBA", "RGB"):
                            img = img.quantize(colors=256, method=Image.Quantize.MAXCOVERAGE)
                            img.save(save_path, "WEBP", quality=quality, method=6)
                        else:
                            img.save(save_path, "WEBP", quality=quality, method=6, optimize=True)
                    else:
                        img.save(save_path, "WEBP", quality=quality, method=6, optimize=True)

                comp_bytes = os.path.getsize(save_path)
                total_comp_bytes += comp_bytes

                saved_pct = ((orig_bytes - comp_bytes) / orig_bytes * 100) if orig_bytes > 0 else 0
                self.log(f"[{i+1}/{total}] {fname} ➔ {comp_bytes/1024:.1f} KB ({saved_pct:.1f}% space saved)")
                self.set_progress((i + 1) / total * 0.9)

            overall_saved = ((total_orig_bytes - total_comp_bytes) / total_orig_bytes * 100) if total_orig_bytes > 0 else 0
            self.log("=" * 45)
            self.log(f"All done! Total Saved: {overall_saved:.1f}%")
            self.log(f"Initial: {total_orig_bytes/1024/1024:.2f} MB ➔ Final: {total_comp_bytes/1024/1024:.2f} MB")
            return out_folder

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            self.render_completion_stage("Batch WebP Compression Complete", f"Saved images to {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Compression failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
