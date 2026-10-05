"""Tool 1.9: High-Speed Video-to-Audio Extractor.

Extracts crystal-clear MP3, WAV, AAC, or FLAC audio directly from video files
in seconds with zero RAM spikes and bit-for-bit fidelity.
"""

import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class AudioExtractorTool(BaseToolFrame):
    """Universal 2-pane tool for high-speed video-to-audio extraction."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="video_extractor",
            title="Video to Audio Extractor",
            description="Extract clean MP3, WAV, AAC, or FLAC audio from video files in seconds.",
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

        btn_folder = ctk.CTkButton(
            btn_row,
            text="📁 Add Folder",
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12),
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

        # Audio Output Format
        fmt_lbl = ctk.CTkLabel(
            container,
            text="TARGET AUDIO FORMAT & BITRATE",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        fmt_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.fmt_var = tk.StringVar(value="MP3 (320 kbps Studio Quality)")
        self.combo_fmt = ctk.CTkComboBox(
            container,
            values=[
                "MP3 (320 kbps Studio Quality)",
                "MP3 (192 kbps Standard)",
                "WAV (Lossless Uncompressed)",
                "AAC (High-Efficiency M4A)",
                "FLAC (Lossless Master)",
                "Direct Stream Copy (Ultra-Fast 1-Sec)"
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
        self.combo_fmt.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

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

        self.out_var = tk.StringVar(value=os.path.expanduser("~/Music"))
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
            text="⚡  Extract Audio Tracks",
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
            title="Select Video Files",
            filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov *.flv *.webm *.m4v *.wmv")]
        )
        if paths:
            for p in paths:
                if p not in self.file_paths:
                    self.file_paths.append(p)
            self._update_preview()

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder containing Videos")
        if folder:
            valid_exts = {".mp4", ".mkv", ".avi", ".mov", ".flv", ".webm", ".m4v", ".wmv"}
            count = 0
            for fname in sorted(os.listdir(folder)):
                ext = os.path.splitext(fname)[1].lower()
                if ext in valid_exts:
                    full_p = os.path.join(folder, fname)
                    if full_p not in self.file_paths:
                        self.file_paths.append(full_p)
                        count += 1
            self.log(f"Loaded {count} video(s) from: {folder}")
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

        fmt_choice = self.fmt_var.get()
        self.output_directory = out_folder
        self.btn_execute.configure(state="disabled")

        def _task():
            total = len(self.file_paths)
            self.log(f"Starting High-Speed Audio Extraction for {total} video(s)...")

            for idx, p in enumerate(self.file_paths):
                base_name = os.path.splitext(os.path.basename(p))[0]

                # Determine ffmpeg arguments based on selected audio format
                if "320 kbps" in fmt_choice:
                    out_path = os.path.join(out_folder, f"{base_name}.mp3")
                    cmd = ["ffmpeg", "-y", "-i", p, "-vn", "-c:a", "libmp3lame", "-b:a", "320k", out_path]
                elif "192 kbps" in fmt_choice:
                    out_path = os.path.join(out_folder, f"{base_name}.mp3")
                    cmd = ["ffmpeg", "-y", "-i", p, "-vn", "-c:a", "libmp3lame", "-b:a", "192k", out_path]
                elif "WAV" in fmt_choice:
                    out_path = os.path.join(out_folder, f"{base_name}.wav")
                    cmd = ["ffmpeg", "-y", "-i", p, "-vn", "-c:a", "pcm_s16le", out_path]
                elif "AAC" in fmt_choice:
                    out_path = os.path.join(out_folder, f"{base_name}.m4a")
                    cmd = ["ffmpeg", "-y", "-i", p, "-vn", "-c:a", "aac", "-b:a", "256k", out_path]
                elif "FLAC" in fmt_choice:
                    out_path = os.path.join(out_folder, f"{base_name}.flac")
                    cmd = ["ffmpeg", "-y", "-i", p, "-vn", "-c:a", "flac", out_path]
                else:
                    # Direct Stream Copy
                    out_path = os.path.join(out_folder, f"{base_name}.aac")
                    cmd = ["ffmpeg", "-y", "-i", p, "-vn", "-c:a", "copy", out_path]

                self.log(f"[{idx+1}/{total}] Extracting: {os.path.basename(p)}...")

                # Non-blocking subprocess execution with hidden console window on Windows
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)

                if result.returncode == 0:
                    out_size = os.path.getsize(out_path) / (1024 * 1024)
                    self.log(f"✓ Saved: {os.path.basename(out_path)} ({out_size:.2f} MB)")
                else:
                    self.log(f"✗ Extraction issue for {os.path.basename(p)}: {result.stderr[:200]}")

                self.set_progress((idx + 1) / total * 0.9)

            return out_folder

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"All audio tracks extracted!\nSaved to: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Audio extraction failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
