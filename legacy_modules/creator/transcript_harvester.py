"""Tool 5.4: Multi-Language Subtitle & Transcript Harvester.

Harvests official and auto-generated transcripts across 20+ languages
into clean readable text scripts or time-synced .SRT caption files.
"""

import os
import re
import urllib.request
from urllib.parse import urlparse, parse_qs
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk
from youtube_transcript_api import YouTubeTranscriptApi

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class TranscriptHarvesterTool(BaseToolFrame):
    """Universal 2-pane tool for extracting video scripts and subtitle captions."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="creator_trans_harvest",
            title="YouTube Subtitle & Transcript Downloader",
            description="Download video subtitles and spoken transcripts in 20+ languages as .txt or .srt files.",
            **kwargs
        )

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # URL Textbox
        url_lbl = ctk.CTkLabel(
            container,
            text="VIDEO URL(S) (Paste YouTube links, one per line)",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        url_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

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

        # Output Format Option (.txt vs .srt)
        fmt_lbl = ctk.CTkLabel(
            container,
            text="EXPORT FORMAT",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        fmt_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.fmt_seg = ctk.CTkSegmentedButton(
            container,
            values=["Plain Script (.txt)", "Timestamped Captions (.srt)"],
            font=(Theme.FONT_FAMILY, 12, "bold"),
            selected_color=Theme.BRAND_PRIMARY,
            selected_hover_color=Theme.BRAND_HOVER,
            unselected_color=Theme.SURFACE_INSET,
            height=34
        )
        self.fmt_seg.set("Plain Script (.txt)")
        self.fmt_seg.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Preferred Language Priority
        lang_lbl = ctk.CTkLabel(
            container,
            text="PRIMARY LANGUAGE PREFERENCE",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        lang_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.lang_var = tk.StringVar(value="English (en)")
        self.combo_lang = ctk.CTkComboBox(
            container,
            values=[
                "English (en)",
                "Telugu (te)",
                "Hindi (hi)",
                "Tamil (ta)",
                "Kannada (kn)",
                "Spanish (es)",
                "German (de)",
                "French (fr)",
                "Japanese (ja)"
            ],
            variable=self.lang_var,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.combo_lang.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

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
            text="⚡  Harvest Transcripts",
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

    def _get_video_id(self, url: str):
        parsed = urlparse(url)
        if parsed.hostname in ('youtu.be', 'www.youtu.be'):
            return parsed.path.lstrip('/')
        if 'youtube.com' in (parsed.hostname or ''):
            if '/shorts/' in parsed.path:
                return parsed.path.split('/shorts/')[1].split('/')[0].split('?')[0]
            if '/watch' in parsed.path:
                qs = parse_qs(parsed.query)
                return qs.get('v', [None])[0]
        return None

    def _format_srt_time(self, seconds: float) -> str:
        millis = int((seconds % 1) * 1000)
        total_seconds = int(seconds)
        secs = total_seconds % 60
        mins = (total_seconds // 60) % 60
        hrs = total_seconds // 3600
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    def _execute(self):
        raw = self.url_textbox.get("1.0", "end").strip()
        urls = [u.strip() for u in re.split(r"[\s,\n]+", raw) if u.startswith("http")]

        if not urls:
            messagebox.showwarning("Notice", "Please paste at least one video link.")
            return

        out_folder = self.out_var.get().strip()
        if not out_folder or not os.path.exists(out_folder):
            messagebox.showwarning("Notice", "Please specify a valid destination folder.")
            return

        is_srt = ".srt" in self.fmt_seg.get()
        chosen_lang = re.search(r"\(([a-z]{2})\)", self.lang_var.get())
        primary_lang = chosen_lang.group(1) if chosen_lang else "en"

        # Language fallback priority list
        lang_list = [primary_lang, 'en', 'hi', 'te', 'ta', 'es', 'fr', 'de']
        if primary_lang not in lang_list:
            lang_list.insert(0, primary_lang)

        self.output_directory = out_folder
        self.btn_execute.configure(state="disabled")

        def _task():
            total = len(urls)
            self.log(f"Starting transcript extraction for {total} video(s)...")

            for idx, url in enumerate(urls):
                vid_id = self._get_video_id(url)
                if not vid_id:
                    self.log(f"[{idx+1}/{total}] Skipped invalid link: {url}")
                    continue

                self.log(f"[{idx+1}/{total}] Fetching captions for ID: {vid_id}...")
                try:
                    # Fetch transcript
                    transcript_items = YouTubeTranscriptApi.get_transcript(vid_id, languages=lang_list)
                    title = f"Transcript_{vid_id}"

                    # Clean filename
                    filename = f"{title}.srt" if is_srt else f"{title}.txt"
                    save_path = os.path.join(out_folder, filename)

                    if is_srt:
                        lines = []
                        for i, item in enumerate(transcript_items):
                            start = item['start']
                            end = start + item['duration']
                            lines.append(f"{i+1}")
                            lines.append(f"{self._format_srt_time(start)} --> {self._format_srt_time(end)}")
                            lines.append(item['text'])
                            lines.append("")
                        content = "\n".join(lines)
                    else:
                        content = "\n".join([item['text'] for item in transcript_items])

                    with open(save_path, "w", encoding="utf-8") as f_out:
                        f_out.write(content)

                    self.log(f"✓ Harvested {len(transcript_items)} lines ➔ {filename}")
                except Exception as exc:
                    self.log(f"✗ Could not fetch captions for {vid_id}: {exc}")

                self.set_progress((idx + 1) / total * 0.9)

            return out_folder

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"Transcripts harvested!\nSaved in: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Transcript harvesting failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
