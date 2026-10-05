"""BaseToolFrame - Universal 2-Pane Apple Studio Interaction Architecture.

Standardizes all Boltools tools:
- Left Canvas: Configuration, structured dropzone inputs, options, and tactile action CTA.
- Right Inspector: Live State Canvas (Idle Hero, Running Progress Meter, Success Completion Hub)
  paired with a clean, compact Activity Feed drawer.
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
    """Abstract 2-pane studio frame ensuring consistent Apple-grade UX across tools."""

    def __init__(self, master, tool_id: str, title: str, description: str, **kwargs):
        super().__init__(master, fg_color=Theme.SURFACE_BASE, corner_radius=0, **kwargs)

        self.tool_id = tool_id
        self.title_text = title
        self.desc_text = description

        self.selected_files: List[str] = []
        self.output_directory: str = ""
        self.last_output_file: Optional[str] = None
        self.is_running = False

        self.worker = AsyncWorker()

        # Grid layout: Row 0 Header, Row 1 Studio Canvas
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_panes()

    def _build_header(self):
        """Top tool header with title, description, and status pill."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=Theme.PAD_LG, pady=(Theme.PAD_MD, Theme.PAD_SM))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        # Title & Subtitle column
        text_col = ctk.CTkFrame(header_frame, fg_color="transparent")
        text_col.grid(row=0, column=0, sticky="w")

        title_lbl = ctk.CTkLabel(
            text_col,
            text=self.title_text,
            font=Theme.FONT_DISPLAY,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title_lbl.pack(anchor="w")

        desc_lbl = ctk.CTkLabel(
            text_col,
            text=self.desc_text,
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        desc_lbl.pack(anchor="w", pady=(2, 0))

        # Top Right Engine Badge
        self.badge_engine = ctk.CTkLabel(
            header_frame,
            text="● Ready to Use",
            font=Theme.FONT_LABEL,
            fg_color=Theme.SURFACE_CARD,
            text_color=Theme.STATUS_SUCCESS,
            corner_radius=Theme.RADIUS_PILL,
            padx=12,
            pady=4
        )
        self.badge_engine.grid(row=0, column=1, sticky="e")

    def _build_panes(self):
        """Builds Left (Config) and Right (Inspector & Results) studio panes."""
        studio_canvas = ctk.CTkFrame(self, fg_color="transparent")
        studio_canvas.grid(row=1, column=0, sticky="nsew", padx=Theme.PAD_LG, pady=(0, Theme.PAD_LG))
        studio_canvas.grid_columnconfigure(0, weight=6, uniform="studio_col")
        studio_canvas.grid_columnconfigure(1, weight=5, uniform="studio_col")
        studio_canvas.grid_rowconfigure(0, weight=1)

        # ── Left Pane (Inputs & Controls)
        self.left_pane = ctk.CTkFrame(
            studio_canvas,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        self.left_pane.grid(row=0, column=0, sticky="nsew", padx=(0, Theme.PAD_SM))

        # ── Right Pane (Live Inspector & Output Hub)
        self.right_pane = ctk.CTkFrame(
            studio_canvas,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        self.right_pane.grid(row=0, column=1, sticky="nsew", padx=(Theme.PAD_SM, 0))

        # Allow child classes to populate left pane
        self.build_left_panel(self.left_pane)
        self.build_right_panel(self.right_pane)

    def build_left_panel(self, container: ctk.CTkFrame):
        """Override in subclasses to build custom input controls."""
        pass

    def build_right_panel(self, container: ctk.CTkFrame):
        """Constructs the Apple-grade live inspector with 3-state canvas and activity drawer."""
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)
        container.grid_rowconfigure(2, weight=0)

        # ── 1. Top Inspector Header Bar
        top_bar = ctk.CTkFrame(container, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM))

        insp_lbl = ctk.CTkLabel(
            top_bar,
            text="PREVIEW & RESULT",
            font=Theme.FONT_LABEL,
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        insp_lbl.pack(side="left")

        self.status_pill = ctk.CTkLabel(
            top_bar,
            text="READY",
            font=(Theme.FONT_FAMILY, 10, "bold"),
            fg_color=Theme.SURFACE_PILL,
            text_color=Theme.TEXT_SECONDARY,
            corner_radius=Theme.RADIUS_PILL,
            padx=10,
            pady=2
        )
        self.status_pill.pack(side="right")

        # ── 2. Central Live Canvas (Stateful Stage)
        self.stage_container = ctk.CTkFrame(container, fg_color=Theme.SURFACE_INSET, corner_radius=Theme.RADIUS_INPUT)
        self.stage_container.grid(row=1, column=0, sticky="nsew", padx=Theme.PAD_MD, pady=Theme.PAD_XS)
        self.stage_container.grid_columnconfigure(0, weight=1)
        self.stage_container.grid_rowconfigure(0, weight=1)

        self._build_stage_views()

        # ── 3. Bottom Compact Activity Feed
        feed_container = ctk.CTkFrame(container, fg_color="transparent")
        feed_container.grid(row=2, column=0, sticky="ew", padx=Theme.PAD_MD, pady=Theme.PAD_MD)

        feed_header = ctk.CTkFrame(feed_container, fg_color="transparent")
        feed_header.pack(fill="x", pady=(0, 4))

        feed_title = ctk.CTkLabel(
            feed_header,
            text="PROGRESS DETAILS",
            font=Theme.FONT_LABEL,
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        feed_title.pack(side="left")

        # Monospace styled mini activity box
        self.log_box = ctk.CTkTextbox(
            feed_container,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_SECONDARY,
            font=Theme.FONT_MONO_TEXT,
            corner_radius=Theme.RADIUS_INPUT,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            height=110
        )
        self.log_box.pack(fill="x")
        self.log_box.configure(state="disabled")

        # Compatibility references
        self.status_text = ctk.CTkLabel(feed_container, text="Ready", font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY)
        self.btn_open_folder = ctk.CTkButton(
            feed_container,
            text="Show in Folder",
            fg_color="transparent",
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            height=30,
            command=self.open_output_folder
        )

    def _build_stage_views(self):
        """Constructs the visual cards for Idle, Running, and Completed states."""
        # ── Idle Stage View
        self.idle_view = ctk.CTkFrame(self.stage_container, fg_color="transparent")
        self.idle_view.grid(row=0, column=0, sticky="nsew")

        idle_center = ctk.CTkFrame(self.idle_view, fg_color="transparent")
        idle_center.place(relx=0.5, rely=0.5, anchor="center")

        icon_glyph = ctk.CTkLabel(
            idle_center,
            text="◈",
            font=(Theme.FONT_FAMILY, 40),
            text_color=Theme.TEXT_MUTED
        )
        icon_glyph.pack(pady=(0, Theme.PAD_SM))

        idle_title = ctk.CTkLabel(
            idle_center,
            text="Ready When You Are",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY
        )
        idle_title.pack()

        idle_desc = ctk.CTkLabel(
            idle_center,
            text="Choose your files on the left, pick options, and click Start.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            wraplength=320,
            justify="center"
        )
        idle_desc.pack(pady=(4, Theme.PAD_MD))

        specs_badge = ctk.CTkLabel(
            idle_center,
            text="100% Private • Works Offline • Free Forever",
            font=Theme.FONT_CAPTION,
            fg_color=Theme.SURFACE_CARD,
            text_color=Theme.TEXT_MUTED,
            corner_radius=Theme.RADIUS_PILL,
            padx=12,
            pady=4
        )
        specs_badge.pack()

        # ── Running Stage View
        self.running_view = ctk.CTkFrame(self.stage_container, fg_color="transparent")
        run_center = ctk.CTkFrame(self.running_view, fg_color="transparent")
        run_center.place(relx=0.5, rely=0.5, anchor="center")

        self.running_title = ctk.CTkLabel(
            run_center,
            text="Working on your files...",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY
        )
        self.running_title.pack(pady=(0, Theme.PAD_MD))

        self.progress_bar = ctk.CTkProgressBar(
            run_center,
            fg_color=Theme.SURFACE_CARD,
            progress_color=Theme.BRAND_PRIMARY,
            height=8,
            corner_radius=4,
            width=300
        )
        self.progress_bar.pack(pady=(0, Theme.PAD_SM))
        self.progress_bar.set(0)

        self.progress_percent = ctk.CTkLabel(
            run_center,
            text="0%",
            font=Theme.FONT_LABEL,
            text_color=Theme.BRAND_ACCENT
        )
        self.progress_percent.pack()

        # ── Completed Stage View
        self.completed_view = ctk.CTkFrame(self.stage_container, fg_color="transparent")
        done_center = ctk.CTkFrame(self.completed_view, fg_color="transparent")
        done_center.place(relx=0.5, rely=0.5, anchor="center")

        done_badge = ctk.CTkLabel(
            done_center,
            text="✓ All Done!",
            font=Theme.FONT_TITLE,
            text_color=Theme.STATUS_SUCCESS
        )
        done_badge.pack(pady=(0, Theme.PAD_XS))

        self.output_info_lbl = ctk.CTkLabel(
            done_center,
            text="Your file is ready to use.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            wraplength=340,
            justify="center"
        )
        self.output_info_lbl.pack(pady=(0, Theme.PAD_MD))

        # Tactile Action Hub
        action_cluster = ctk.CTkFrame(done_center, fg_color="transparent")
        action_cluster.pack()

        self.btn_open_file = ctk.CTkButton(
            action_cluster,
            text="↗  Open File",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            text_color=Theme.TEXT_ON_BRAND,
            font=Theme.FONT_BODY_BOLD,
            height=34,
            corner_radius=Theme.RADIUS_BUTTON,
            command=self._open_output_file
        )
        self.btn_open_file.pack(side="left", padx=Theme.PAD_XS)

        btn_show_folder = ctk.CTkButton(
            action_cluster,
            text="📁 Show in Folder",
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            font=Theme.FONT_BODY,
            height=34,
            corner_radius=Theme.RADIUS_BUTTON,
            command=self.open_output_folder
        )
        btn_show_folder.pack(side="left", padx=Theme.PAD_XS)

    def log(self, text: str):
        """Appends text to the activity feed thread-safely."""
        def _append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", f"› {text}\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _append)

    def set_status(self, message: str, color: Optional[str] = None):
        """Sets status indicators across the inspector."""
        def _update():
            self.status_text.configure(text=message)
            if self.is_running:
                self.status_pill.configure(text="WORKING...", text_color=Theme.STATUS_WARNING, fg_color=Theme.STATUS_WARNING_BG)
                self.running_title.configure(text=message)
            elif "Completed" in message or "Finished" in message or "Done" in message:
                self.status_pill.configure(text="DONE", text_color=Theme.STATUS_SUCCESS, fg_color=Theme.STATUS_SUCCESS_BG)
            elif "Error" in message or "Failed" in message:
                self.status_pill.configure(text="FAILED", text_color=Theme.STATUS_ERROR, fg_color=Theme.STATUS_ERROR_BG)
            else:
                self.status_pill.configure(text="READY", text_color=Theme.TEXT_SECONDARY, fg_color=Theme.SURFACE_PILL)
        self.after(0, _update)

    def set_progress(self, value: float):
        """Sets progress bar and percentage label."""
        clamped = max(0.0, min(1.0, value))
        pct = int(clamped * 100)
        def _update():
            self.progress_bar.set(clamped)
            self.progress_percent.configure(text=f"{pct}%")
        self.after(0, _update)

    def set_output_file(self, file_path: str):
        """Records the latest generated file and reveals action controls."""
        self.last_output_file = file_path
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            filename = os.path.basename(file_path)
            self.output_info_lbl.configure(text=f"{filename}\n({size_mb:.2f} MB)")

    def _open_output_file(self):
        """Opens the generated file with system default handler."""
        if self.last_output_file and os.path.exists(self.last_output_file):
            try:
                os.startfile(self.last_output_file)
            except Exception as e:
                messagebox.showerror("Launch Error", f"Could not open file: {e}")
        else:
            self.open_output_folder()

    def open_output_folder(self):
        """Reveals output destination in Windows Explorer."""
        folder = self.output_directory
        if self.last_output_file and os.path.exists(self.last_output_file):
            folder = os.path.dirname(self.last_output_file)
        if not folder or not os.path.exists(folder):
            folder = os.path.expanduser("~/Documents")
        if os.path.exists(folder):
            os.startfile(folder)
        else:
            messagebox.showinfo("Notice", f"Path does not exist yet: {folder}")

    def execute_async(self, worker_func, on_success=None, on_error=None, *args, **kwargs):
        """Launches a task safely on background thread with live state switching."""
        if self.is_running:
            return

        self.is_running = True
        self._switch_stage("running")
        self.set_status("Processing pipeline active...", Theme.STATUS_WARNING)
        self.set_progress(0.05)

        def _success(res):
            self.is_running = False
            self.set_progress(1.0)
            if isinstance(res, str) and os.path.exists(res):
                self.set_output_file(res)
            self.set_status("Completed Successfully", Theme.STATUS_SUCCESS)
            self._switch_stage("completed")
            if on_success:
                on_success(res)

        def _err(exc):
            self.is_running = False
            self.set_status(f"Error: {str(exc)}", Theme.STATUS_ERROR)
            self.log(f"[Error] {str(exc)}")
            self._switch_stage("idle")
            if on_error:
                on_error(exc)

        self.worker.run_task(self, worker_func, _success, _err, *args, **kwargs)

    def _switch_stage(self, stage: str):
        """Switches central inspector stage between 'idle', 'running', and 'completed'."""
        def _perform():
            self.idle_view.grid_forget()
            self.running_view.grid_forget()
            self.completed_view.grid_forget()

            if stage == "running":
                self.running_view.grid(row=0, column=0, sticky="nsew")
            elif stage == "completed":
                self.completed_view.grid(row=0, column=0, sticky="nsew")
            else:
                self.idle_view.grid(row=0, column=0, sticky="nsew")
        self.after(0, _perform)
