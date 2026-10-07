"""Tool 5.3: Ultra-HD Thumbnail & Meta Grabber.

Preview and download full 1080p/4K official max-res video thumbnails
and extract metadata with zero API keys.
"""

import os
import io
import re
import urllib.request
from urllib.parse import urlparse, parse_qs
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class ThumbnailGrabberTool(BaseToolFrame):
    """Universal 2-pane tool for previewing and grabbing 4K video thumbnails."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="creator_thumb_grab",
            title="YouTube Thumbnail Downloader",
            description="Preview and download official full-HD video thumbnails with 1-click save.",
            **kwargs
        )
        self.current_img_bytes = None
        self.current_vid_id = ""

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # URL Input
        url_lbl = ctk.CTkLabel(
            container,
            text="VIDEO URL (YouTube)",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        url_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

        self.url_var = tk.StringVar()
        self.entry_url = ctk.CTkEntry(
            container,
            textvariable=self.url_var,
            placeholder_text="https://www.youtube.com/watch?v=...",
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=36
        )
        self.entry_url.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Fetch Preview CTA
        self.btn_fetch = ctk.CTkButton(
            container,
            text="🔍  Fetch Thumbnail & Meta",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            height=36,
            command=self._fetch_thumbnail
        )
        self.btn_fetch.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        # Thumbnail Visual Preview Frame
        preview_header = ctk.CTkLabel(
            container,
            text="THUMBNAIL PREVIEW",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        preview_header.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_XS))

        self.preview_canvas = ctk.CTkLabel(
            container,
            text="Paste a link and click Fetch",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_MUTED,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_CARD,
            height=180
        )
        self.preview_canvas.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        # Save Button
        self.btn_save = ctk.CTkButton(
            container,
            text="💾  Download Max-Res Image",
            fg_color=Theme.BRAND_HOVER,
            hover_color=Theme.BRAND_ACCENT,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=40,
            command=self._save_thumbnail
        )
        self.btn_save.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        self.btn_save.configure(state="disabled")

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

    def _fetch_thumbnail(self):
        url = self.url_var.get().strip()
        vid_id = self._get_video_id(url)
        if not vid_id:
            messagebox.showwarning("Notice", "Invalid YouTube URL.")
            return

        self.current_vid_id = vid_id
        self.btn_fetch.configure(state="disabled")

        def _task():
            self.log(f"Fetching official thumbnail for video ID: {vid_id}...")
            # Try maxresdefault first, fallback to hqdefault
            urls = [
                f"https://img.youtube.com/vi/{vid_id}/maxresdefault.jpg",
                f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"
            ]

            img_data = None
            for thumb_url in urls:
                try:
                    req = urllib.request.Request(thumb_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as resp:
                        img_data = resp.read()
                        if len(img_data) > 2000: # Ensure valid image payload
                            self.log(f"✓ Found image at: {thumb_url}")
                            break
                except Exception:
                    continue

            if not img_data:
                raise RuntimeError("Could not retrieve thumbnail.")

            return img_data

        def _on_done(data):
            self.btn_fetch.configure(state="normal")
            self.current_img_bytes = data
            self.btn_save.configure(state="normal")

            # Render in preview canvas
            pil_img = Image.open(io.BytesIO(data))
            ratio = pil_img.width / pil_img.height
            preview_h = 160
            preview_w = int(preview_h * ratio)
            ctk_thumb = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(preview_w, preview_h))
            self.preview_canvas.configure(image=ctk_thumb, text="")

            self.log(f"Ready to download! Resolution: {pil_img.width}x{pil_img.height}px ({len(data)/1024:.1f} KB)")

        def _on_err(err):
            self.btn_fetch.configure(state="normal")
            messagebox.showerror("Error", f"Failed to fetch thumbnail: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)

    def _save_thumbnail(self):
        if not self.current_img_bytes:
            return
        save_path = filedialog.asksaveasfilename(
            title="Save Thumbnail Image",
            defaultextension=".jpg",
            initialfile=f"thumbnail_{self.current_vid_id}.jpg",
            filetypes=[("JPEG Image", "*.jpg")]
        )
        if save_path:
            with open(save_path, "wb") as f_out:
                f_out.write(self.current_img_bytes)
            self.output_directory = os.path.dirname(save_path)
            messagebox.showinfo("Success", f"Thumbnail saved successfully!\nSaved to: {save_path}")
            self.log(f"✓ Saved thumbnail to: {save_path}")
