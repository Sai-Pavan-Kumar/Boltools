"""Tool 5.2: Bolt Web Video & Stream Harvester.

High-speed stream downloader supporting individual videos, entire playlists,
and audio extraction up to 4K 60fps. Zero web ads, zero popups.
"""

import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk
import yt_dlp

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class StreamHarvesterTool(BaseToolFrame):
    """Universal 2-pane tool for harvesting web videos and audio streams."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="creator_bolt_down",
            title="Web Video Downloader",
            description="Download videos, shorts, and playlists up to 4K 60fps or save audio directly.",
            **kwargs
        )

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # URL Input Label
        url_lbl = ctk.CTkLabel(
            container,
            text="VIDEO OR PLAYLIST URL(S) (Paste one or multiple links)",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        url_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

        # Multi-line URL text area
        self.url_textbox = ctk.CTkTextbox(
            container,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            font=(Theme.FONT_MONO, 12),
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=100
        )
        self.url_textbox.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Quality Preset Dropdown
        qual_lbl = ctk.CTkLabel(
            container,
            text="DOWNLOAD QUALITY & FORMAT",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        qual_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.quality_var = tk.StringVar(value="Best Available (Up to 4K 60fps)")
        self.combo_quality = ctk.CTkComboBox(
            container,
            values=[
                "Best Available (Up to 4K 60fps)",
                "1080p Full HD (MP4)",
                "720p HD (MP4)",
                "Audio Only - High Bitrate (MP3)",
                "Audio Only - Lossless (WAV)"
            ],
            variable=self.quality_var,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.combo_quality.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Playlist Mode Checkbox
        self.playlist_var = tk.BooleanVar(value=False)
        self.chk_playlist = ctk.CTkCheckBox(
            container,
            text="Allow Whole Playlist Download (if playlist URL detected)",
            variable=self.playlist_var,
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_PRIMARY
        )
        self.chk_playlist.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

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

        self.out_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
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
            text="⚡  Start Download",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=42,
            command=self._execute
        )
        self.btn_execute.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Destination Folder")
        if folder:
            self.out_var.set(folder)

    def _get_urls(self) -> List[str]:
        raw = self.url_textbox.get("1.0", "end").strip()
        lines = re.split(r"[\s,\n]+", raw)
        return [l.strip() for l in lines if l.startswith("http")]

    def _execute(self):
        urls = self._get_urls()
        if not urls:
            messagebox.showwarning("Notice", "Please paste at least one valid web URL (starts with http).")
            return

        out_folder = self.out_var.get().strip()
        if not out_folder or not os.path.exists(out_folder):
            messagebox.showwarning("Notice", "Please choose a valid destination folder.")
            return

        q_preset = self.quality_var.get()
        allow_playlist = self.playlist_var.get()
        self.output_directory = out_folder
        self.btn_execute.configure(state="disabled")

        def _task():
            self.log(f"Initializing Bolt Stream Engine for {len(urls)} link(s)...")

            # Configure download parameters based on quality preset
            is_audio = "Audio Only" in q_preset
            ydl_opts = {
                'outtmpl': os.path.join(out_folder, '%(title)s.%(ext)s'),
                'noplaylist': not allow_playlist,
                'quiet': True,
                'no_warnings': True
            }

            if "Audio Only - High Bitrate (MP3)" in q_preset:
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '320',
                    }]
                })
            elif "Audio Only - Lossless (WAV)" in q_preset:
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'wav',
                    }]
                })
            elif "1080p" in q_preset:
                ydl_opts.update({
                    'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
                    'merge_output_format': 'mp4'
                })
            elif "720p" in q_preset:
                ydl_opts.update({
                    'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
                    'merge_output_format': 'mp4'
                })
            else:
                # Best available (4K 60fps)
                ydl_opts.update({
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4'
                })

            def _progress_hook(d):
                if d.get('status') == 'downloading':
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    downloaded = d.get('downloaded_bytes', 0)
                    speed = d.get('speed', 0) or 0
                    speed_mb = speed / (1024 * 1024) if speed else 0

                    if total_bytes > 0:
                        pct = downloaded / total_bytes
                        self.set_progress(pct)
                        self.set_status(f"Downloading: {pct*100:.1f}% ({speed_mb:.1f} MB/s)", Theme.STATUS_INFO)
                elif d.get('status') == 'finished':
                    fname = os.path.basename(d.get('filename', 'video'))
                    self.log(f"✓ Download complete: {fname}")

            ydl_opts['progress_hooks'] = [_progress_hook]

            for idx, url in enumerate(urls):
                self.log(f"\n[{idx+1}/{len(urls)}] Connecting: {url}")
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        title = info.get('title', 'Media file')
                        self.log(f"✓ Harvested: {title}")
                except Exception as exc:
                    self.log(f"✗ Failed link {url}: {exc}")

                self.set_progress((idx + 1) / len(urls))

            return out_folder

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"All downloads completed!\nSaved to: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Stream download failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
