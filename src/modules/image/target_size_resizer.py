"""Tool 4.4: Target Size (KB/MB) & Dimension Resizer.

Fits photos strictly under portal limits (job portals, passport portals, exam registries)
using binary-search compression and precise Lanczos dimension resampling.
"""

import os
import io
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Optional
import customtkinter as ctk
from PIL import Image

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class TargetSizeResizerTool(BaseToolFrame):
    """Universal 2-pane tool for exact target byte and pixel dimension constraint."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="image_target_size",
            title="Target Size (KB/MB) & Dimension Resizer",
            description="Fit images strictly under portal byte limits (e.g. <200 KB) and exact pixel dimensions.",
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
            text="+ Add Images",
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
            text="No images loaded",
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
            height=90
        )
        self.preview_box.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        self.preview_box.configure(state="disabled")

        # Target File Size Row
        size_lbl = ctk.CTkLabel(
            container,
            text="TARGET MAX FILE SIZE (Strict Upper Limit)",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        size_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        size_row = ctk.CTkFrame(container, fg_color="transparent")
        size_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        self.size_val_var = tk.StringVar(value="200")
        self.entry_size = ctk.CTkEntry(
            size_row,
            textvariable=self.size_val_var,
            placeholder_text="e.g. 200",
            font=(Theme.FONT_FAMILY, 13),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.entry_size.pack(side="left", fill="x", expand=True, padx=(0, Theme.PAD_SM))

        self.unit_var = tk.StringVar(value="KB")
        self.seg_unit = ctk.CTkSegmentedButton(
            size_row,
            values=["KB", "MB"],
            variable=self.unit_var,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            selected_color=Theme.BRAND_PRIMARY,
            selected_hover_color=Theme.BRAND_HOVER,
            unselected_color=Theme.SURFACE_INSET,
            height=34,
            width=100
        )
        self.seg_unit.pack(side="right")

        # Target Dimensions (Width x Height)
        dim_lbl = ctk.CTkLabel(
            container,
            text="DIMENSION LIMITS (Width x Height in px, leave blank to keep original)",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        dim_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        dim_row = ctk.CTkFrame(container, fg_color="transparent")
        dim_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        self.w_var = tk.StringVar(value="")
        self.entry_w = ctk.CTkEntry(
            dim_row,
            textvariable=self.w_var,
            placeholder_text="Width px (e.g. 600)",
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.entry_w.pack(side="left", fill="x", expand=True, padx=(0, Theme.PAD_XS))

        ctk.CTkLabel(dim_row, text="×", font=(Theme.FONT_FAMILY, 14, "bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=Theme.PAD_XS)

        self.h_var = tk.StringVar(value="")
        self.entry_h = ctk.CTkEntry(
            dim_row,
            textvariable=self.h_var,
            placeholder_text="Height px (e.g. 600)",
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.entry_h.pack(side="left", fill="x", expand=True, padx=(Theme.PAD_XS, 0))

        # Destination Folder
        dest_lbl = ctk.CTkLabel(
            container,
            text="SAVE DESTINATION FOLDER",
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
            text="⚡  Resize & Compress to Target Limit",
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
            title="Select Images to Resize",
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
        txt = f"{n} image{'s' if n != 1 else ''} loaded" if n else "No images loaded"
        self.counter_lbl.configure(text=txt)

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        for idx, p in enumerate(self.file_paths):
            size_kb = os.path.getsize(p) / 1024
            self.preview_box.insert("end", f"{idx+1}. {os.path.basename(p)} ({size_kb:.1f} KB)\n")
        self.preview_box.configure(state="disabled")

    def _execute(self):
        if not self.file_paths:
            messagebox.showwarning("Notice", "Please select at least one image.")
            return

        out_folder = self.out_var.get().strip()
        if not out_folder or not os.path.exists(out_folder):
            messagebox.showwarning("Notice", "Please specify a valid destination folder.")
            return

        size_raw = self.size_val_var.get().strip()
        if not size_raw:
            messagebox.showwarning("Notice", "Please enter a target size value.")
            return

        try:
            val = float(size_raw)
            mult = 1024 if self.unit_var.get() == "KB" else (1024 * 1024)
            target_bytes = val * mult
        except ValueError:
            messagebox.showwarning("Notice", "Invalid target size number.")
            return

        target_w = int(self.w_var.get()) if self.w_var.get().strip().isdigit() else None
        target_h = int(self.h_var.get()) if self.h_var.get().strip().isdigit() else None

        self.output_directory = out_folder
        self.btn_execute.configure(state="disabled")

        def _task():
            total = len(self.file_paths)
            self.log(f"Target limit: {val} {self.unit_var.get()} ({target_bytes:.0f} bytes)")

            for idx, p in enumerate(self.file_paths):
                fname = os.path.basename(p)
                base = os.path.splitext(fname)[0]

                with Image.open(p) as img:
                    has_transparency = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)

                    # Compute dimensions
                    cur_w, cur_h = img.width, img.height
                    new_w, new_h = cur_w, cur_h

                    if target_w and not target_h:
                        new_w = target_w
                        new_h = int((target_w / cur_w) * cur_h)
                    elif target_h and not target_w:
                        new_h = target_h
                        new_w = int((target_h / cur_h) * cur_w)
                    elif target_w and target_h:
                        new_w, new_h = target_w, target_h

                    if (new_w, new_h) != (cur_w, cur_h):
                        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    else:
                        resized = img.copy()

                    # Save format choice
                    save_ext = ".png" if has_transparency else ".jpg"
                    save_path = os.path.join(out_folder, f"{base}_resized{save_ext}")

                    # Binary search on JPEG / WEBP quality to fit target_bytes
                    if has_transparency:
                        # For transparency, try WebP lossy or PNG optimize
                        save_path = os.path.join(out_folder, f"{base}_resized.webp")
                        best_data = b""
                        low_q, high_q = 10, 95
                        for _ in range(8):
                            mid_q = (low_q + high_q) // 2
                            buf = io.BytesIO()
                            resized.save(buf, format="WEBP", quality=mid_q, optimize=True)
                            cur_size = buf.tell()
                            best_data = buf.getvalue()
                            if cur_size > target_bytes:
                                high_q = mid_q - 1
                            else:
                                low_q = mid_q + 1
                        with open(save_path, "wb") as f_out:
                            f_out.write(best_data)
                    else:
                        # JPEG binary search
                        if resized.mode in ("RGBA", "LA"):
                            resized = resized.convert("RGB")
                        best_data = b""
                        low_q, high_q = 10, 95
                        for _ in range(8):
                            mid_q = (low_q + high_q) // 2
                            buf = io.BytesIO()
                            resized.save(buf, format="JPEG", quality=mid_q, optimize=True)
                            cur_size = buf.tell()
                            best_data = buf.getvalue()
                            if cur_size > target_bytes:
                                high_q = mid_q - 1
                            else:
                                low_q = mid_q + 1
                        with open(save_path, "wb") as f_out:
                            f_out.write(best_data)

                final_kb = os.path.getsize(save_path) / 1024
                self.log(f"[{idx+1}/{total}] {fname} ➔ {final_kb:.1f} KB (Resized: {new_w}x{new_h}px)")
                self.set_progress((idx + 1) / total * 0.9)

            return out_folder

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"All images resized under target limit!\nSaved to: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Failed to resize image: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
