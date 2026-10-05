"""BaseToolFrame - Universal 2-Pane Interaction Pattern for all 57 Boltools.

Every tool inherits from this standard frame:
- Left Pane: Inputs, File Picker, Options, Primary CTA.
- Right Pane: Real-time Preview, Output Details, Progress Meter, Action Log.
"""

import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, List
import customtkinter as ctk

from src.core.theme import Theme
from src.core.worker import AsyncWorker


class BaseToolFrame(ctk.CTkFrame):
    """Abstract 2-pane template ensuring uniform muscle memory across all tools."""

    def __init__(self, master, tool_id: str, title: str, description: str, **kwargs):
        super().__init__(master, fg_color=Theme.SURFACE_BASE, corner_radius=0, **kwargs)
        
        self.tool_id = tool_id
        self.title_text = title
        self.desc_text = description
        
        self.selected_files: List[str] = []
        self.output_directory: str = ""
        self.is_running = False
        
        self.worker = AsyncWorker()
        
        # Grid layout (Header on row 0, 2-Pane layout on row 1)
        self.grid_columnconfigure(0, weight=1, uniform="pane")
        self.grid_columnconfigure(1, weight=1, uniform="pane")
        self.grid_rowconfigure(1, weight=1)
        
        self._build_header()
        self._build_panes()

    def _build_header(self):
        """Constructs the standard title & description header."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=Theme.PAD_LG, pady=(Theme.PAD_LG, Theme.PAD_MD))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=self.title_text,
            font=(Theme.FONT_FAMILY, 20, "bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title_label.pack(fill="x")
        
        desc_label = ctk.CTkLabel(
            header_frame,
            text=self.desc_text,
            font=(Theme.FONT_FAMILY, 13),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        desc_label.pack(fill="x", pady=(2, 0))

    def _build_panes(self):
        """Builds Left (Config) and Right (Preview/Progress) panels."""
        # ── Left Pane (Inputs & Controls)
        self.left_pane = ctk.CTkFrame(
            self,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        self.left_pane.grid(row=1, column=0, sticky="nsew", padx=(Theme.PAD_LG, Theme.PAD_SM), pady=(0, Theme.PAD_LG))
        
        # ── Right Pane (Preview, Progress, Results)
        self.right_pane = ctk.CTkFrame(
            self,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        self.right_pane.grid(row=1, column=1, sticky="nsew", padx=(Theme.PAD_SM, Theme.PAD_LG), pady=(0, Theme.PAD_LG))
        
        # Allow child classes to populate panels
        self.build_left_panel(self.left_pane)
        self.build_right_panel(self.right_pane)

    def build_left_panel(self, container: ctk.CTkFrame):
        """Override in subclasses to add custom inputs, options, and actions."""
        pass

    def build_right_panel(self, container: ctk.CTkFrame):
        """Standard right panel providing progress, logs, and output shortcuts."""
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)
        
        # Top Label
        lbl = ctk.CTkLabel(
            container,
            text="STATUS & PREVIEW",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        lbl.grid(row=0, column=0, sticky="ew", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))
        
        # Log / Output Box
        self.log_box = ctk.CTkTextbox(
            container,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            font=(Theme.FONT_MONO, 12),
            corner_radius=Theme.RADIUS_INPUT,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=Theme.PAD_MD, pady=Theme.PAD_XS)
        self.log_box.configure(state="disabled")
        
        # Progress Bar & Status Text
        progress_frame = ctk.CTkFrame(container, fg_color="transparent")
        progress_frame.grid(row=2, column=0, sticky="ew", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))
        
        self.status_text = ctk.CTkLabel(
            progress_frame,
            text="Ready",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        self.status_text.pack(fill="x", pady=(0, Theme.PAD_XS))
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            fg_color=Theme.SURFACE_INSET,
            progress_color=Theme.BRAND_PRIMARY,
            height=6,
            corner_radius=3
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)
        
        # Output directory action button
        self.btn_open_folder = ctk.CTkButton(
            progress_frame,
            text="Open Destination Folder",
            fg_color="transparent",
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            height=32,
            font=(Theme.FONT_FAMILY, 12),
            command=self.open_output_folder
        )
        self.btn_open_folder.pack(fill="x", pady=(Theme.PAD_SM, 0))

    def log(self, text: str):
        """Appends text to the right-side console box thread-safely."""
        def _append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", text + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _append)

    def set_status(self, message: str, color: Optional[str] = None):
        """Sets the status indicator text."""
        col = color or Theme.TEXT_SECONDARY
        self.after(0, lambda: self.status_text.configure(text=message, text_color=col))

    def set_progress(self, value: float):
        """Sets progress bar between 0.0 and 1.0."""
        self.after(0, lambda: self.progress_bar.set(max(0.0, min(1.0, value))))

    def open_output_folder(self):
        """Opens output folder in Windows Explorer."""
        folder = self.output_directory or os.path.expanduser("~/Documents")
        if os.path.exists(folder):
            os.startfile(folder)
        else:
            messagebox.showinfo("Folder Notice", f"Path does not exist yet: {folder}")

    def execute_async(self, worker_func, on_success=None, on_error=None, *args, **kwargs):
        """Launches a task safely on background thread."""
        if self.is_running:
            return
            
        self.is_running = True
        self.set_status("Processing...", Theme.STATUS_WARNING)
        self.set_progress(0.05)
        
        def _success(res):
            self.is_running = False
            self.set_status("Completed Successfully", Theme.STATUS_SUCCESS)
            self.set_progress(1.0)
            if on_success:
                on_success(res)
                
        def _err(exc):
            self.is_running = False
            self.set_status(f"Error: {str(exc)}", Theme.STATUS_ERROR)
            self.log(f"[Error] {str(exc)}")
            if on_error:
                on_error(exc)
                
        self.worker.run_task(self, worker_func, _success, _err, *args, **kwargs)
