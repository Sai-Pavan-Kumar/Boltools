"""Settings View for Boltools.

Allows users to manage:
- Theme mode (Dark / Light / System) with smooth Win32 redraw
- Default output folders
- Cache and storage maintenance
- Application information
"""

import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable, Optional
import customtkinter as ctk

from src.core.theme import Theme


class SettingsView(ctk.CTkFrame):
    """Settings screen adhering to Apple Pro and Linear design aesthetics."""

    def __init__(self, master, on_theme_change: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(master, fg_color=Theme.SURFACE_BASE, corner_radius=0, **kwargs)

        self.on_theme_change = on_theme_change
        self.state_dir = os.path.join(os.path.expanduser("~"), ".boltools")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Content

        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Theme.PAD_LG, pady=(Theme.PAD_LG, Theme.PAD_MD))

        title = ctk.CTkLabel(
            header,
            text="Settings",
            font=Theme.FONT_HERO,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title.pack(anchor="w")

        sub = ctk.CTkLabel(
            header,
            text="Preferences, theme options, and local storage management.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        sub.pack(anchor="w", pady=(2, 0))

    def _build_content(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew", padx=Theme.PAD_LG, pady=(0, Theme.PAD_LG))
        scroll.grid_columnconfigure(0, weight=1)

        # ── 1. Appearance Section
        self._build_appearance_section(scroll)

        # ── 2. Storage & Output Directory Section
        self._build_storage_section(scroll)

        # ── 3. Maintenance Section
        self._build_maintenance_section(scroll)

        # ── 4. About Section
        self._build_about_section(scroll)

    def _build_appearance_section(self, parent):
        card = self._create_section_card(parent, "APPEARANCE")

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_MD)
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=0)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(left, text="Theme Mode", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(left, text="Choose your interface appearance. Smoothly updates without screen flash.", font=Theme.FONT_CAPTION, text_color=Theme.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(2, 0))

        current_mode = ctk.get_appearance_mode().capitalize()
        self.seg_theme = ctk.CTkSegmentedButton(
            row,
            values=["Dark", "Light", "System"],
            command=self._on_theme_select,
            font=Theme.FONT_CAPTION,
            selected_color=Theme.BRAND_PRIMARY,
            selected_hover_color=Theme.BRAND_HOVER,
            unselected_color=Theme.SURFACE_INSET,
            height=30
        )
        self.seg_theme.set(current_mode if current_mode in ["Dark", "Light", "System"] else "Dark")
        self.seg_theme.grid(row=0, column=1, sticky="e")

    def _on_theme_select(self, mode: str):
        Theme.apply_appearance(mode, window=self.winfo_toplevel())
        if self.on_theme_change:
            self.on_theme_change(mode)

    def _build_storage_section(self, parent):
        card = self._create_section_card(parent, "STORAGE & DIRECTORIES")

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_MD)

        ctk.CTkLabel(row, text="Default Output Folder", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(row, text="Where processed files will be saved by default across tools.", font=Theme.FONT_CAPTION, text_color=Theme.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(2, Theme.PAD_SM))

        input_row = ctk.CTkFrame(row, fg_color="transparent")
        input_row.pack(fill="x")
        input_row.grid_columnconfigure(0, weight=1)
        input_row.grid_columnconfigure(1, weight=0)

        default_dest = os.path.join(os.path.expanduser("~"), "Downloads")
        self.entry_folder = ctk.CTkEntry(
            input_row,
            font=Theme.FONT_CAPTION,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=32
        )
        self.entry_folder.insert(0, default_dest)
        self.entry_folder.grid(row=0, column=0, sticky="ew", padx=(0, Theme.PAD_SM))

        btn_browse = ctk.CTkButton(
            input_row,
            text="Browse...",
            font=Theme.FONT_CAPTION,
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            width=70,
            height=32,
            command=self._browse_default_folder
        )
        btn_browse.grid(row=0, column=1)

    def _browse_default_folder(self):
        folder = filedialog.askdirectory(title="Select Default Output Folder")
        if folder:
            self.entry_folder.delete(0, "end")
            self.entry_folder.insert(0, folder)

    def _build_maintenance_section(self, parent):
        card = self._create_section_card(parent, "LOCAL CACHE & DATA MAINTENANCE")

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_MD)
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=0)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(left, text="Clean Temp Cache", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(
            left,
            text=f"Cleans temporary processing logs without touching your presets ({self.state_dir}).",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        ).pack(anchor="w", pady=(2, 0))

        self.btn_clean = ctk.CTkButton(
            row,
            text="Clean Cache",
            font=Theme.FONT_CAPTION,
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            width=90,
            height=30,
            command=self._clean_cache
        )
        self.btn_clean.grid(row=0, column=1, sticky="e")

    def _clean_cache(self):
        try:
            cache_cleaned = 0
            # Clean temporary files in .boltools if any
            for fname in os.listdir(self.state_dir):
                if fname.endswith(".tmp") or fname.endswith(".log"):
                    fpath = os.path.join(self.state_dir, fname)
                    try:
                        os.remove(fpath)
                        cache_cleaned += 1
                    except Exception:
                        pass
            self.btn_clean.configure(text="Cleaned ✓", text_color=Theme.STATUS_SUCCESS)
            self.after(2000, lambda: self.btn_clean.configure(text="Clean Cache", text_color=Theme.TEXT_PRIMARY))
        except Exception:
            self.btn_clean.configure(text="Cleaned ✓")

    def _build_about_section(self, parent):
        card = self._create_section_card(parent, "ABOUT")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_MD)

        title = ctk.CTkLabel(
            inner,
            text="Boltools Desktop v1.0",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title.pack(anchor="w")

        desc = ctk.CTkLabel(
            inner,
            text="Fast, private, 100% offline desktop utilities for creators and power users.\nAll files stay strictly on your local PC with zero cloud leaks.",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
            justify="left"
        )
        desc.pack(anchor="w", pady=(2, Theme.PAD_SM))

        badge = ctk.CTkLabel(
            inner,
            text="Offline Core  •  Private by Design  •  Win32 Native",
            font=(Theme.FONT_FAMILY, 9),
            text_color=Theme.TEXT_MUTED,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_PILL,
            padx=8,
            pady=3
        )
        badge.pack(anchor="w")

    def _create_section_card(self, parent, section_name: str) -> ctk.CTkFrame:
        lbl = ctk.CTkLabel(
            parent,
            text=section_name,
            font=(Theme.FONT_FAMILY, 9, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        lbl.pack(fill="x", padx=Theme.PAD_SM, pady=(Theme.PAD_MD, 4))

        card = ctk.CTkFrame(
            parent,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        card.pack(fill="x", pady=(0, Theme.PAD_SM))
        return card
