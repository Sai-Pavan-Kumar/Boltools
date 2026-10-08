"""Tool: Video Compressor Studio.

Gold-standard proof implementation adhering to the new Tool Contract:
- Clean 2-pane Apple Studio Layout
- Isolated background FFmpeg execution
- Live Original vs Estimated comparison table
"""

import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Optional, Dict
import customtkinter as ctk

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class VideoCompressorTool(BaseToolFrame):
    """Universal 2-pane studio tool for intelligent video compression."""

    def __init__(self, master, **kwargs):
        self.selected_file: Optional[str] = None
        self.file_duration = 0.0
        self.file_resolution = "1920 × 1080"
        self.active_mode = "Balanced"
        self.mode_buttons: Dict[str, ctk.CTkFrame] = {}

        super().__init__(
            master=master,
            tool_id="video_compressor",
            title="Video Compressor",
            description="Compress video files with Low, Balanced, and Maximum compression presets.",
            category_id="video",
            **kwargs
        )

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # ── Dropzone Container
        self.dropzone = self.create_dropzone(
            container,
            title="Drop video file here or click to browse",
            subtitle="Supports MP4, MKV, MOV, AVI, WebM",
            on_click=self._browse_single_file
        )

        # ── Loaded File Card
        self.file_card = ctk.CTkFrame(
            container,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_BUTTON,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )

        # ── Compression Mode Selector (4 Cards)
        mode_hdr = ctk.CTkLabel(
            container,
            text="Compression Mode",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        mode_hdr.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        modes_grid = ctk.CTkFrame(container, fg_color="transparent")
        modes_grid.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        modes_grid.grid_columnconfigure((0, 1), weight=1, uniform="modes")

        modes_data = [
            ("Balanced", "Balanced", "Good quality, smaller size"),
            ("High Quality", "High Quality", "Better quality, larger size"),
            ("Small Size", "Small Size", "Maximum compression"),
            ("Custom", "Custom", "Target size slider"),
        ]

        for idx, (m_id, m_title, m_desc) in enumerate(modes_data):
            row = idx // 2
            col = idx % 2
            self._render_mode_card(modes_grid, row, col, m_id, m_title, m_desc)

        # ── Target Slider (For custom)
        self.slider_wrap = ctk.CTkFrame(container, fg_color="transparent")
        self.slider_wrap.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        slider_top = ctk.CTkFrame(self.slider_wrap, fg_color="transparent")
        slider_top.pack(fill="x", pady=(0, 2))

        ctk.CTkLabel(slider_top, text="Target File Size", font=Theme.FONT_CAPTION, text_color=Theme.TEXT_MUTED).pack(side="left")
        self.target_val_lbl = ctk.CTkLabel(slider_top, text="50 MB", font=Theme.FONT_BODY_BOLD, text_color=Theme.BRAND_PRIMARY)
        self.target_val_lbl.pack(side="right")

        self.size_slider = ctk.CTkSlider(
            self.slider_wrap,
            from_=10,
            to=500,
            number_of_steps=98,
            height=14,
            progress_color=Theme.BRAND_PRIMARY,
            command=self._on_slider_change
        )
        self.size_slider.set(50)
        self.size_slider.pack(fill="x")

        # ── Destination Option
        loc_box = ctk.CTkFrame(container, fg_color="transparent")
        loc_box.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))
        ctk.CTkLabel(loc_box, text="Destination Folder", font=Theme.FONT_CAPTION, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", pady=(0, 2))
        self.combo_loc = ctk.CTkComboBox(
            loc_box,
            values=["Same as input", "Desktop", "Custom Folder..."],
            font=Theme.FONT_CAPTION,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            height=30,
            command=self._on_location_change
        )
        self.combo_loc.set("Same as input")
        self.combo_loc.pack(fill="x")

        # ── Primary Action CTA Button
        self.btn_compress = ctk.CTkButton(
            container,
            text="Compress Video →",
            font=Theme.FONT_SUBTITLE,
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            text_color=Theme.TEXT_ON_BRAND,
            corner_radius=Theme.RADIUS_BUTTON,
            height=36,
            command=self._execute_compression
        )
        self.btn_compress.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

    def _render_mode_card(self, parent, row: int, col: int, m_id: str, title: str, desc: str):
        is_active = (m_id == self.active_mode)
        card = ctk.CTkFrame(
            parent,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_BUTTON,
            border_width=2 if is_active else 1,
            border_color=Theme.BRAND_PRIMARY if is_active else Theme.BORDER_SUBTLE,
            cursor="hand2"
        )
        card.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        inner.pack(fill="both", expand=True, padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        t_lbl = ctk.CTkLabel(
            inner,
            text=title,
            font=Theme.FONT_BODY_BOLD if is_active else Theme.FONT_BODY,
            text_color=Theme.BRAND_PRIMARY if is_active else Theme.TEXT_PRIMARY,
            anchor="w",
            cursor="hand2"
        )
        t_lbl.pack(fill="x")

        d_lbl = ctk.CTkLabel(
            inner,
            text=desc,
            font=(Theme.FONT_FAMILY, 9),
            text_color=Theme.TEXT_MUTED,
            anchor="w",
            cursor="hand2"
        )
        d_lbl.pack(fill="x")

        for w in [card, inner, t_lbl, d_lbl]:
            w.bind("<Button-1>", lambda e, mode=m_id: self._select_mode(mode))

        self.mode_buttons[m_id] = card

    def _select_mode(self, mode_id: str):
        self.active_mode = mode_id
        for m_id, card in self.mode_buttons.items():
            is_cur = (m_id == mode_id)
            card.configure(
                border_width=2 if is_cur else 1,
                border_color=Theme.BRAND_PRIMARY if is_cur else Theme.BORDER_SUBTLE
            )
        self._update_comparison_inspector()

    def _on_slider_change(self, val):
        mb = int(val)
        self.target_val_lbl.configure(text=f"{mb} MB")
        self._update_comparison_inspector()

    def _on_location_change(self, choice: str):
        if choice == "Custom Folder...":
            folder = filedialog.askdirectory(title="Choose Destination Folder")
            if folder:
                self.output_directory = folder
                self.combo_loc.set(os.path.basename(folder) or folder)
            else:
                self.combo_loc.set("Same as input")

    def _browse_single_file(self):
        path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video Files", "*.mp4 *.mkv *.mov *.avi *.webm *.flv *.wmv"), ("All Files", "*.*")]
        )
        if not path:
            return

        self.selected_file = path
        size_bytes = os.path.getsize(path)
        size_mb = size_bytes / (1024 * 1024)

        self._probe_video_specs(path)
        self._display_loaded_file_card(path, size_mb)
        self._update_comparison_inspector()

    def _probe_video_specs(self, path: str):
        self.file_duration = 0.0
        self.file_resolution = "1920 × 1080"
        try:
            cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,duration",
                "-of", "default=noprint_wrappers=1", path
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            for line in res.stdout.splitlines():
                if line.startswith("width="):
                    w = line.split("=")[1]
                elif line.startswith("height="):
                    h = line.split("=")[1]
                    self.file_resolution = f"{w} × {h}"
                elif line.startswith("duration="):
                    try:
                        self.file_duration = float(line.split("=")[1])
                    except Exception:
                        pass
        except Exception:
            pass

    def _display_loaded_file_card(self, path: str, size_mb: float):
        for w in self.file_card.winfo_children():
            w.destroy()

        self.dropzone.pack_forget()
        self.file_card.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        inner = ctk.CTkFrame(self.file_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        info_col = ctk.CTkFrame(inner, fg_color="transparent")
        info_col.pack(side="left", fill="both", expand=True)

        name_lbl = ctk.CTkLabel(
            info_col,
            text=os.path.basename(path),
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        name_lbl.pack(fill="x")

        dur_str = f"{int(self.file_duration // 60):02d}:{int(self.file_duration % 60):02d}" if self.file_duration > 0 else "Video"
        specs_lbl = ctk.CTkLabel(
            info_col,
            text=f"{self.file_resolution}   •   {size_mb:.1f} MB   •   {dur_str}",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        specs_lbl.pack(fill="x")

        btn_close = ctk.CTkButton(
            inner,
            text="✕",
            font=Theme.FONT_CAPTION,
            fg_color="transparent",
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_MUTED,
            width=24,
            height=24,
            command=self._clear_selected_file
        )
        btn_close.pack(side="right")

    def _clear_selected_file(self):
        self.selected_file = None
        self.file_card.pack_forget()
        self.dropzone.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        self._build_idle_state(self.stage_frame)

    def _update_comparison_inspector(self):
        if not self.selected_file:
            return

        size_mb = os.path.getsize(self.selected_file) / (1024 * 1024)

        if self.active_mode == "Balanced":
            est_mb = max(2.0, size_mb * 0.45)
        elif self.active_mode == "High Quality":
            est_mb = max(3.0, size_mb * 0.75)
        elif self.active_mode == "Small Size":
            est_mb = max(1.5, size_mb * 0.25)
        else:
            est_mb = float(self.size_slider.get())

        for w in self.stage_frame.winfo_children():
            w.destroy()

        dur_str = f"{int(self.file_duration // 60):02d}:{int(self.file_duration % 60):02d}" if self.file_duration > 0 else "--:--"
        orig_stats = {
            "File Size": f"{size_mb:.1f} MB",
            "Resolution": self.file_resolution,
            "Duration": dur_str,
            "Format": os.path.splitext(self.selected_file)[1].upper().replace(".", "")
        }

        est_stats = {
            "File Size": f"~ {est_mb:.1f} MB",
            "Resolution": self.file_resolution,
            "Duration": dur_str,
            "Format": "MP4"
        }

        self.create_comparison_matrix(self.stage_frame, orig_stats, est_stats, f"Estimated ({self.active_mode})")

    def _execute_compression(self):
        if not self.selected_file or not os.path.exists(self.selected_file):
            messagebox.showwarning("Notice", "Please select a video file first.")
            return

        out_dir = self.output_directory or os.path.dirname(self.selected_file)
        base, ext = os.path.splitext(os.path.basename(self.selected_file))
        out_path = os.path.join(out_dir, f"{base}_compressed.mp4")

        self.btn_compress.configure(state="disabled")
        self.set_progress(0.1, "Initializing FFmpeg encoder...")
        self.log(f"Starting {self.active_mode} compression: {base}{ext}")

        crf_map = {"Balanced": "28", "High Quality": "23", "Small Size": "34", "Custom": "28"}
        crf = crf_map.get(self.active_mode, "28")

        def _work():
            cmd = [
                "ffmpeg", "-y",
                "-i", self.selected_file,
                "-vcodec", "libx264",
                "-crf", crf,
                "-preset", "faster",
                "-acodec", "aac",
                "-b:a", "128k",
                out_path
            ]
            self.set_progress(0.4, "Encoding video frames...")
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and os.path.exists(out_path):
                new_mb = os.path.getsize(out_path) / (1024 * 1024)
                return out_path, new_mb
            else:
                raise RuntimeError(res.stderr[-300:] if res.stderr else "FFmpeg failed.")

        def _on_success(result):
            out_file, new_mb = result
            self.btn_compress.configure(state="normal")
            orig_mb = os.path.getsize(self.selected_file) / (1024 * 1024)
            pct_saved = ((orig_mb - new_mb) / orig_mb) * 100 if orig_mb > 0 else 0
            self.show_success(
                out_file,
                summary=f"Compressed from {orig_mb:.1f} MB down to {new_mb:.1f} MB (saved {pct_saved:.1f}%)."
            )

        def _on_error(err):
            self.btn_compress.configure(state="normal")
            self.show_error(str(err))

        self.worker.run_async(_work, on_success=_on_success, on_error=_on_error)
