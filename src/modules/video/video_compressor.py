"""Tool 1.3: Target Video Size Compressor.

Calculates mathematically exact target bitrates to fit files under:
- WhatsApp Limit (16 MB)
- Discord Limit (25 MB)
- Custom target MB limits
"""

import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class VideoCompressorTool(BaseToolFrame):
    """Universal 2-pane tool for mathematical target-size video compression."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="tool_video_1_3",
            title="Target Video Size Compressor",
            description="Crush video recordings to fit strict upload limits (WhatsApp 16MB, Discord 25MB) with zero guesswork.",
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
            text="+ Add Videos",
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
            text="No videos loaded",
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
            height=110
        )
        self.preview_box.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        self.preview_box.configure(state="disabled")

        # Target Size Preset Options
        preset_lbl = ctk.CTkLabel(
            container,
            text="TARGET SIZE PRESET",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        preset_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.preset_var = tk.StringVar(value="Discord (25 MB)")
        combo_preset = ctk.CTkComboBox(
            container,
            values=[
                "WhatsApp Attachment (16 MB)",
                "Discord Free Limit (25 MB)",
                "Email Attachment (20 MB)",
                "Telegram / Web (50 MB)",
                "Custom Size Limit"
            ],
            variable=self.preset_var,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34,
            command=self._on_preset_change
        )
        combo_preset.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Custom MB input entry
        self.custom_mb_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.custom_mb_frame.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        mb_lbl = ctk.CTkLabel(
            self.custom_mb_frame,
            text="Target Size (MB):",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_SECONDARY
        )
        mb_lbl.pack(side="left", padx=(0, Theme.PAD_SM))

        self.target_mb_var = tk.StringVar(value="25")
        self.entry_mb = ctk.CTkEntry(
            self.custom_mb_frame,
            textvariable=self.target_mb_var,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            width=80,
            height=30
        )
        self.entry_mb.pack(side="left")

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

        self.out_var = tk.StringVar(value=os.path.expanduser("~/Videos"))
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
            text="⚡  Compress to Target Size",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=42,
            command=self._execute
        )
        self.btn_execute.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

    def _on_preset_change(self, val):
        if "16 MB" in val:
            self.target_mb_var.set("15.5")
        elif "25 MB" in val:
            self.target_mb_var.set("24.5")
        elif "20 MB" in val:
            self.target_mb_var.set("19.5")
        elif "50 MB" in val:
            self.target_mb_var.set("49.0")

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov *.flv *.webm *.m4v *.wmv")]
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
        txt = f"{n} video{'s' if n != 1 else ''} loaded" if n else "No videos loaded"
        self.counter_lbl.configure(text=txt)

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        for idx, p in enumerate(self.file_paths):
            sz_mb = os.path.getsize(p) / (1024 * 1024)
            self.preview_box.insert("end", f"{idx+1}. {os.path.basename(p)} ({sz_mb:.1f} MB)\n")
        self.preview_box.configure(state="disabled")

    def _execute(self):
        if not self.file_paths:
            messagebox.showwarning("Notice", "Please add at least one video file.")
            return

        out_folder = self.out_var.get().strip()
        if not out_folder or not os.path.exists(out_folder):
            messagebox.showwarning("Notice", "Please specify a valid destination folder.")
            return

        try:
            target_mb = float(self.target_mb_var.get().strip())
            if target_mb <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Notice", "Please specify a valid target size in MB.")
            return

        self.output_directory = out_folder
        self.btn_execute.configure(state="disabled")

        def _task():
            total = len(self.file_paths)
            self.log(f"Starting target size compression (Target: {target_mb:.1f} MB)...")

            for idx, p in enumerate(self.file_paths):
                base_name = os.path.splitext(os.path.basename(p))[0]
                out_file = os.path.join(out_folder, f"{base_name}_{int(target_mb)}MB.mp4")
                self.log(f"Analyzing duration & bitrates for: {base_name}...")

                # Use ffprobe to get duration
                dur_cmd = [
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", p
                ]
                try:
                    res = subprocess.run(dur_cmd, capture_output=True, text=True, check=True)
                    duration = float(res.stdout.strip())
                except Exception:
                    duration = 60.0  # Fallback duration estimate

                target_total_bits = target_mb * 8 * 1024 * 1024
                audio_bitrate_kb = 128
                video_bitrate_kb = max(50, int((target_total_bits / duration / 1000) - audio_bitrate_kb))

                self.log(f"Computed Target Bitrate: {video_bitrate_kb}k (Audio: {audio_bitrate_kb}k)")
                
                cmd = [
                    "ffmpeg", "-y", "-i", p,
                    "-c:v", "libx264", "-b:v", f"{video_bitrate_kb}k",
                    "-maxrate", f"{int(video_bitrate_kb * 1.5)}k",
                    "-bufsize", f"{video_bitrate_kb * 2}k",
                    "-c:a", "aac", "-b:a", f"{audio_bitrate_kb}k",
                    "-preset", "faster", out_file
                ]

                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode == 0 and os.path.exists(out_file):
                    actual_sz = os.path.getsize(out_file) / (1024 * 1024)
                    self.log(f"✓ Output: {os.path.basename(out_file)} ({actual_sz:.2f} MB)")
                else:
                    self.log(f"✗ Failed to compress: {base_name}")

                self.set_progress((idx + 1) / total)

            return out_folder

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"Target video compression completed!\nSaved to: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Compression failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
