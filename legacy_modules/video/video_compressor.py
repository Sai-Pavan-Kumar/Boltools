"""Tool 1.3: Video Compressor Studio.

Gold-standard implementation matching Apple / Linear reference architecture:
- Sub-tabs: Compress | Batch Compress | Advanced
- Left: Dropzone, Loaded file specs card, 4 Preset Mode cards, Target size slider, Format/Location controls, Compress CTA
- Right: Video Preview Canvas, Original vs Estimated comparison matrix, Progress bar, Activity feed
- Native FFmpeg process isolation for zero GUI lag
"""

import os
import shutil
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
        super().__init__(
            master=master,
            tool_id="tool_video_1_3",
            title="Video Compressor",
            description="Reduce video file size while maintaining great quality. Support for MP4, MKV, MOV, AVI, WebM and more.",
            icon="🎥",
            category_id="video",
            **kwargs
        )
        self.current_tab = "Compress"
        self.selected_file: Optional[str] = None
        self.file_paths: List[str] = []
        self.file_duration = 0.0
        self.file_resolution = "1920 × 1080"
        self.file_bitrate = "N/A"
        self.active_mode = "Balanced"
        self.mode_buttons: Dict[str, ctk.CTkFrame] = {}

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # ── 1. Workflow Sub-Tabs
        self.create_subtabs(container, ["Compress", "Batch Compress", "Advanced"], self._on_tab_change)

        # ── 2. Dropzone Container (Single vs Batch)
        self.dropzone = self.create_dropzone(
            container,
            title="Drop your video file here",
            subtitle="or click to select • Supports MP4, MKV, MOV, AVI, WebM",
            on_click=self._browse_single_file
        )

        # ── 3. Loaded File Card (Hidden until file selected)
        self.file_card = ctk.CTkFrame(
            container,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_BUTTON,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        # Not packed initially

        # ── 4. Compression Mode Header & 4 Cards Grid
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
            ("Balanced", "⚖ Balanced", "Good quality, smaller size"),
            ("High Quality", "💎 High Quality", "Better quality, larger size"),
            ("Small Size", "📄 Small Size", "Maximum compression"),
            ("Custom", "⚙ Custom", "Set your own target size"),
        ]

        for idx, (m_id, m_title, m_desc) in enumerate(modes_data):
            row = idx // 2
            col = idx % 2
            self._render_mode_card(modes_grid, row, col, m_id, m_title, m_desc)

        # ── 5. Target File Size (Optional Slider)
        self.slider_wrap = ctk.CTkFrame(container, fg_color="transparent")
        self.slider_wrap.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        slider_top = ctk.CTkFrame(self.slider_wrap, fg_color="transparent")
        slider_top.pack(fill="x", pady=(0, 2))

        ctk.CTkLabel(slider_top, text="Target File Size (Optional)", font=Theme.FONT_CAPTION, text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.target_val_lbl = ctk.CTkLabel(slider_top, text="50 MB", font=Theme.FONT_BODY_BOLD, text_color=Theme.BRAND_PRIMARY)
        self.target_val_lbl.pack(side="right")

        self.size_slider = ctk.CTkSlider(
            self.slider_wrap,
            from_=10,
            to_=500,
            number_of_steps=98,
            height=16,
            progress_color=Theme.BRAND_PRIMARY,
            command=self._on_slider_change
        )
        self.size_slider.set(50)
        self.size_slider.pack(fill="x")

        # ── 6. Output Format & Output Location Row
        opts_row = ctk.CTkFrame(container, fg_color="transparent")
        opts_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))
        opts_row.grid_columnconfigure((0, 1), weight=1, uniform="opts")

        # Format
        fmt_box = ctk.CTkFrame(opts_row, fg_color="transparent")
        fmt_box.grid(row=0, column=0, sticky="ew", padx=(0, Theme.PAD_XS))
        ctk.CTkLabel(fmt_box, text="Output Format", font=Theme.FONT_CAPTION, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", pady=(0, 2))
        self.combo_fmt = ctk.CTkComboBox(
            fmt_box,
            values=["MP4 (Recommended)", "MKV", "WebM", "MOV"],
            font=Theme.FONT_CAPTION,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            height=32
        )
        self.combo_fmt.set("MP4 (Recommended)")
        self.combo_fmt.pack(fill="x")

        # Location
        loc_box = ctk.CTkFrame(opts_row, fg_color="transparent")
        loc_box.grid(row=0, column=1, sticky="ew", padx=(Theme.PAD_XS, 0))
        ctk.CTkLabel(loc_box, text="Output Location", font=Theme.FONT_CAPTION, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", pady=(0, 2))
        self.combo_loc = ctk.CTkComboBox(
            loc_box,
            values=["Same as input", "Desktop", "Custom Folder..."],
            font=Theme.FONT_CAPTION,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            height=32,
            command=self._on_location_change
        )
        self.combo_loc.set("Same as input")
        self.combo_loc.pack(fill="x")

        # ── 7. Primary Action CTA Button
        self.btn_compress = ctk.CTkButton(
            container,
            text="Compress Video →",
            font=Theme.FONT_SUBTITLE,
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            text_color=Theme.TEXT_ON_BRAND,
            corner_radius=Theme.RADIUS_BUTTON,
            height=40,
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
        card.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")

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
        d_lbl.pack(fill="x", pady=(1, 0))

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

    def _on_tab_change(self, tab_name: str):
        self.current_tab = tab_name
        self.log(f"Switched workflow mode to [{tab_name}]")

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
        self.file_paths = [path]
        size_bytes = os.path.getsize(path)
        size_mb = size_bytes / (1024 * 1024)

        # Read video specs via ffprobe if available
        self._probe_video_specs(path, size_mb)

        # Show loaded file card
        self._display_loaded_file_card(path, size_mb)
        self._update_comparison_inspector()

    def _probe_video_specs(self, path: str, size_mb: float):
        self.file_duration = 0.0
        self.file_resolution = "1920 × 1080"
        self.file_bitrate = f"{(size_mb * 8 / 60):.1f} Mbps" if size_mb > 0 else "N/A"

        try:
            cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,duration,bit_rate",
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

        # Icon
        ico = ctk.CTkLabel(inner, text="🎬", font=(Theme.FONT_FAMILY, 16))
        ico.pack(side="left", padx=(0, Theme.PAD_SM))

        # Details
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

        # Close button
        btn_close = ctk.CTkButton(
            inner,
            text="✕",
            font=(Theme.FONT_FAMILY, 11),
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
        self.file_paths.clear()
        self.file_card.pack_forget()
        self.dropzone.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        self._build_idle_state(self.stage_frame)

    def _update_comparison_inspector(self):
        """Builds and renders the side-by-side comparison table in the right inspector."""
        if not self.selected_file:
            return

        size_mb = os.path.getsize(self.selected_file) / (1024 * 1024)

        # Estimate based on mode
        if self.active_mode == "Balanced":
            est_mb = max(2.0, size_mb * 0.45)
            est_crf = 28
        elif self.active_mode == "High Quality":
            est_mb = max(3.0, size_mb * 0.75)
            est_crf = 22
        elif self.active_mode == "Small Size":
            est_mb = max(1.5, size_mb * 0.25)
            est_crf = 34
        else:  # Custom
            est_mb = float(self.size_slider.get())
            est_crf = 28

        for w in self.stage_frame.winfo_children():
            w.destroy()

        # Preview Container
        preview_box = ctk.CTkFrame(
            self.stage_frame,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            height=180
        )
        preview_box.pack(fill="x", pady=(0, Theme.PAD_SM))
        preview_box.pack_propagate(False)

        play_ico = ctk.CTkLabel(preview_box, text="▶", font=(Theme.FONT_FAMILY, 36), text_color=Theme.BRAND_PRIMARY)
        play_ico.pack(expand=True)

        preview_caption = ctk.CTkLabel(
            preview_box,
            text=f"{os.path.basename(self.selected_file)} ({self.file_resolution})",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_MUTED
        )
        preview_caption.pack(pady=(0, Theme.PAD_SM))

        # Comparison Matrix
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
            messagebox.showwarning("Notice", "Please drop or select a video file first.")
            return

        out_dir = self.output_directory or os.path.dirname(self.selected_file)
        base, ext = os.path.splitext(os.path.basename(self.selected_file))
        out_path = os.path.join(out_dir, f"{base}_compressed.mp4")

        self.btn_compress.configure(state="disabled")
        self.set_progress(0.1, "Initializing FFmpeg encoder...")
        self.log(f"Starting {self.active_mode} compression: {base}{ext}")

        crf_map = {
            "Balanced": "28",
            "High Quality": "23",
            "Small Size": "34",
            "Custom": "28"
        }
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
