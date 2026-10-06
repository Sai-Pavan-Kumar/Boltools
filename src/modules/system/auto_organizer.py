"""Tool 7.9: Smart Auto-Organizer.

1-Click organizes chaotic Downloads or Desktop directories:
- Sorts files into categorised subfolders (Documents, Images, Videos, Software, Archives, Code)
- Tracks move history for 1-Click Instant Undo
"""

import os
import shutil
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Dict, List
import customtkinter as ctk

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class AutoOrganizerTool(BaseToolFrame):
    """Universal 2-pane tool for 1-click directory cleanup and organization."""

    CATEGORIES = {
        "Documents": {".pdf", ".docx", ".doc", ".xlsx", ".pptx", ".txt", ".csv"},
        "Images": {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".ico", ".heic"},
        "Videos": {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"},
        "Audio": {".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"},
        "Software & Installers": {".exe", ".msi", ".iso", ".bat"},
        "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
        "Code & Data": {".py", ".js", ".html", ".css", ".json", ".xml", ".sql"}
    }

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="tool_system_7_9",
            title="Smart Auto-Organizer",
            description="1-Click clean chaotic 1,000-file Downloads folders into structured category subfolders with instant Undo.",
            **kwargs
        )
        self.move_history: List[Dict[str, str]] = []

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # Target Directory Selector
        dir_lbl = ctk.CTkLabel(
            container,
            text="TARGET DIRECTORY TO ORGANIZE",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        dir_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

        dir_row = ctk.CTkFrame(container, fg_color="transparent")
        dir_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        self.target_dir_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.entry_dir = ctk.CTkEntry(
            dir_row,
            textvariable=self.target_dir_var,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.entry_dir.pack(side="left", fill="x", expand=True, padx=(0, Theme.PAD_SM))

        btn_browse = ctk.CTkButton(
            dir_row,
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
            command=self._browse_dir
        )
        btn_browse.pack(side="right")

        # Quick Preset Buttons
        preset_row = ctk.CTkFrame(container, fg_color="transparent")
        preset_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        btn_dl = ctk.CTkButton(
            preset_row,
            text="📁 Downloads Folder",
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 11),
            height=28,
            command=lambda: self.target_dir_var.set(os.path.expanduser("~/Downloads"))
        )
        btn_dl.pack(side="left", padx=(0, Theme.PAD_SM))

        btn_dt = ctk.CTkButton(
            preset_row,
            text="🖥️ Desktop Folder",
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 11),
            height=28,
            command=lambda: self.target_dir_var.set(os.path.expanduser("~/Desktop"))
        )
        btn_dt.pack(side="left")

        # Action Execution Buttons
        self.btn_execute = ctk.CTkButton(
            container,
            text="⚡  Clean & Organize Now",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=42,
            command=self._execute
        )
        self.btn_execute.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_SM))

        self.btn_undo = ctk.CTkButton(
            container,
            text="↺  Undo Last Organization",
            fg_color="transparent",
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12),
            height=36,
            command=self._undo
        )
        self.btn_undo.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))
        self.btn_undo.configure(state="disabled")

    def _browse_dir(self):
        folder = filedialog.askdirectory(title="Select Folder to Organize")
        if folder:
            self.target_dir_var.set(folder)

    def _execute(self):
        target = self.target_dir_var.get().strip()
        if not target or not os.path.exists(target):
            messagebox.showwarning("Notice", "Please select a valid directory to organize.")
            return

        self.btn_execute.configure(state="disabled")
        self.output_directory = target

        def _task():
            self.log(f"Scanning target directory: {target}...")
            files = [f for f in os.listdir(target) if os.path.isfile(os.path.join(target, f))]
            total = len(files)
            if total == 0:
                self.log("No loose files found to organize.")
                return 0

            self.move_history.clear()
            moved_count = 0

            for idx, fname in enumerate(files):
                ext = os.path.splitext(fname)[1].lower()
                dest_subfolder = "Other"

                for cat_name, ext_set in self.CATEGORIES.items():
                    if ext in ext_set:
                        dest_subfolder = cat_name
                        break

                dest_dir = os.path.join(target, dest_subfolder)
                os.makedirs(dest_dir, exist_ok=True)

                src_p = os.path.join(target, fname)
                dest_p = os.path.join(dest_dir, fname)

                # Avoid collision
                if not os.path.exists(dest_p):
                    shutil.move(src_p, dest_p)
                    self.move_history.append({"src": dest_p, "orig": src_p})
                    moved_count += 1

                self.set_progress((idx + 1) / total)

            self.log(f"✓ Successfully organized {moved_count} files into categories!")
            return moved_count

        def _on_done(cnt):
            self.btn_execute.configure(state="normal")
            if cnt > 0:
                self.btn_undo.configure(state="normal")
                messagebox.showinfo("Success", f"Cleaned {cnt} files into structured folders!")
            else:
                messagebox.showinfo("Notice", "No files needed reorganization.")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Failed to organize: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)

    def _undo(self):
        if not self.move_history:
            return

        def _task():
            self.log("Reverting files back to original positions...")
            count = 0
            for item in self.move_history:
                if os.path.exists(item["src"]) and not os.path.exists(item["orig"]):
                    shutil.move(item["src"], item["orig"])
                    count += 1
            self.move_history.clear()
            self.log(f"✓ Reverted {count} files back to source folder.")
            return count

        def _on_done(cnt):
            self.btn_undo.configure(state="disabled")
            messagebox.showinfo("Undo Successful", f"Restored {cnt} files back to root directory!")

        self.execute_async(_task, on_success=_on_done)
