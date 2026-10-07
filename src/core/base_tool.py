"""BaseToolFrame - Universal 2-Pane Apple Studio Interaction Architecture.

Standardizes all Boltools tools:
- Top Header: Back navigation, icon in tinted squircle, title, subtitle, favorite heart, and more options.
- Left Canvas: Workflow Sub-Tabs, structured dropzone, loaded file specs card, mode cards, sliders, and primary action CTA.
- Right Inspector: Live State Canvas (Video Player / Document Preview / Comparison Matrix) paired with compact Activity Feed.
"""

import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, List, Callable, Dict, Tuple
import customtkinter as ctk

from src.core.theme import Theme
from src.core.worker import AsyncWorker
from src.core.favorites import favorites_service


class BaseToolFrame(ctk.CTkFrame):
    """Universal 2-pane studio frame ensuring consistent Apple-grade UX across tools."""

    def __init__(
        self,
        master,
        tool_id: str,
        title: str,
        description: str,
        icon: str = "⚡",
        category_id: str = "system",
        on_back: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color=Theme.SURFACE_BASE, corner_radius=0, **kwargs)

        self.tool_id = tool_id
        self.title_text = title
        self.desc_text = description
        self.icon_glyph = icon
        self.category_id = category_id
        self.on_back = on_back

        self.selected_files: List[str] = []
        self.output_directory: str = ""
        self.last_output_file: Optional[str] = None
        self.is_running = False
        self.is_favorited = favorites_service.is_favorite(self.tool_id)

        self.worker = AsyncWorker()

        # Grid layout: Row 0 Header, Row 1 Studio Canvas
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_panes()

    def _build_header(self):
        """Top tool header with icon in tinted squircle, title, subtitle, favorite, and more options."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=Theme.PAD_LG, pady=(Theme.PAD_MD, Theme.PAD_SM))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        # Left Info Row
        left_col = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="w")

        # Back Button
        self.btn_back = ctk.CTkButton(
            left_col,
            text="←",
            font=(Theme.FONT_FAMILY, 14, "bold"),
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            width=32,
            height=32,
            command=self._handle_back_click
        )
        self.btn_back.pack(side="left", padx=(0, Theme.PAD_SM))

        # Tinted Icon Box
        tint_cfg = Theme.CATEGORY_COLORS.get(self.category_id, {"accent": Theme.BRAND_PRIMARY, "bg": Theme.SURFACE_INSET})
        self.ico_box = ctk.CTkLabel(
            left_col,
            text=self.icon_glyph,
            font=(Theme.FONT_FAMILY, 16),
            fg_color=tint_cfg["bg"],
            corner_radius=8,
            width=36,
            height=36
        )
        self.ico_box.pack(side="left", padx=(0, Theme.PAD_SM))

        # Title + Description
        text_col = ctk.CTkFrame(left_col, fg_color="transparent")
        text_col.pack(side="left")

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
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        desc_lbl.pack(anchor="w", pady=(1, 0))

        # Right Action Buttons (Favorite ♡/♥, More •••)
        right_actions = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_actions.grid(row=0, column=1, sticky="e")

        fav_icon = "♥" if self.is_favorited else "♡"
        fav_color = Theme.STATUS_ERROR if self.is_favorited else Theme.TEXT_SECONDARY

        self.btn_fav = ctk.CTkButton(
            right_actions,
            text=fav_icon,
            font=(Theme.FONT_FAMILY, 14),
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=fav_color,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            width=34,
            height=32,
            command=self._toggle_favorite
        )
        self.btn_fav.pack(side="left", padx=(0, Theme.PAD_XS))

        self.btn_more = ctk.CTkButton(
            right_actions,
            text="•••",
            font=(Theme.FONT_FAMILY, 11),
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            width=34,
            height=32,
            command=self._on_more_options
        )
        self.btn_more.pack(side="left")

    def _toggle_favorite(self):
        self.is_favorited = favorites_service.toggle_favorite(self.tool_id)
        if self.is_favorited:
            self.btn_fav.configure(text="♥", text_color=Theme.STATUS_ERROR)
        else:
            self.btn_fav.configure(text="♡", text_color=Theme.TEXT_SECONDARY)

    def _on_more_options(self):
        messagebox.showinfo(self.title_text, f"{self.title_text}\nOffline Engine: Active\nStatus: 100% Private on this PC")

    def _handle_back_click(self):
        if self.on_back:
            self.on_back()
        else:
            app = self.winfo_toplevel()
            if hasattr(app, "navigate_back"):
                app.navigate_back()
            elif hasattr(app, "show_home"):
                app.show_home()

    def _build_panes(self):
        """Builds Left (Config) and Right (Inspector & Results) studio panes."""
        studio_canvas = ctk.CTkFrame(self, fg_color="transparent")
        studio_canvas.grid(row=1, column=0, sticky="nsew", padx=Theme.PAD_LG, pady=(0, Theme.PAD_LG))
        studio_canvas.grid_columnconfigure(0, weight=6, uniform="studio_col")
        studio_canvas.grid_columnconfigure(1, weight=5, uniform="studio_col")
        studio_canvas.grid_rowconfigure(0, weight=1)

        # ── Left Pane (Inputs & Controls with smooth scroll)
        self.left_pane = ctk.CTkScrollableFrame(
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
        """Constructs the standard live inspector canvas and activity drawer."""
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)  # Live Stage
        container.grid_rowconfigure(1, weight=0)  # Progress & CTA
        container.grid_rowconfigure(2, weight=0)  # Activity Feed

        # 1. Live State Canvas
        self.stage_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.stage_frame.grid(row=0, column=0, sticky="nsew", padx=Theme.PAD_MD, pady=Theme.PAD_MD)
        self._build_idle_state(self.stage_frame)

        # 2. Linear Progress Bar & Actions
        progress_box = ctk.CTkFrame(container, fg_color="transparent")
        progress_box.grid(row=1, column=0, sticky="ew", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        self.progress_bar = ctk.CTkProgressBar(
            progress_box,
            height=6,
            corner_radius=3,
            progress_color=Theme.BRAND_PRIMARY,
            fg_color=Theme.SURFACE_INSET
        )
        self.progress_bar.pack(fill="x", pady=(0, 4))
        self.progress_bar.set(0.0)

        prog_info_row = ctk.CTkFrame(progress_box, fg_color="transparent")
        prog_info_row.pack(fill="x")

        self.progress_lbl = ctk.CTkLabel(
            prog_info_row,
            text="Ready",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_MUTED
        )
        self.progress_lbl.pack(side="left")

        self.pct_lbl = ctk.CTkLabel(
            prog_info_row,
            text="0%",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_MUTED
        )
        self.pct_lbl.pack(side="right")

        # 3. Compact Activity Feed Drawer (90px)
        log_header = ctk.CTkFrame(container, fg_color="transparent")
        log_header.grid(row=2, column=0, sticky="ew", padx=Theme.PAD_MD, pady=(0, 2))

        feed_lbl = ctk.CTkLabel(
            log_header,
            text="ACTIVITY LOG",
            font=(Theme.FONT_FAMILY, 9, "bold"),
            text_color=Theme.TEXT_MUTED
        )
        feed_lbl.pack(side="left")

        self.log_box = ctk.CTkTextbox(
            container,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_SECONDARY,
            font=(Theme.FONT_MONO, 10),
            corner_radius=Theme.RADIUS_INPUT,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            height=85
        )
        self.log_box.grid(row=3, column=0, sticky="ew", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))
        self.log_box.configure(state="disabled")

    def _build_idle_state(self, parent):
        for w in parent.winfo_children():
            w.destroy()

        idle_box = ctk.CTkFrame(
            parent,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        idle_box.pack(fill="both", expand=True, padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        inner = ctk.CTkFrame(idle_box, fg_color="transparent")
        inner.pack(expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_MD)

        # Shield badge
        badge = ctk.CTkLabel(
            inner,
            text="🛡  100% Offline Local Engine",
            font=(Theme.FONT_FAMILY, 10, "bold"),
            text_color=Theme.STATUS_SUCCESS,
            fg_color=Theme.SURFACE_PILL,
            corner_radius=Theme.RADIUS_PILL,
            padx=10,
            pady=4
        )
        badge.pack(pady=(0, Theme.PAD_MD))

        lbl = ctk.CTkLabel(
            inner,
            text="Studio Inspector & Output",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.TEXT_PRIMARY
        )
        lbl.pack()

        sub = ctk.CTkLabel(
            inner,
            text="Configure your operation on the left and run to preview real-time results.",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_MUTED,
            wraplength=280
        )
        sub.pack(pady=(4, Theme.PAD_LG))

        # Checklist specs
        spec_box = ctk.CTkFrame(inner, fg_color="transparent")
        spec_box.pack(fill="x")

        specs = [
            ("✓ Zero Cloud Latency", "Runs natively on your local processor"),
            ("✓ Private & Confidential", "Files never leave your local storage"),
            ("✓ Direct Storage I/O", "High-speed zero-upload transformations")
        ]

        for s_title, s_desc in specs:
            row = ctk.CTkFrame(spec_box, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=s_title, font=(Theme.FONT_FAMILY, 10, "bold"), text_color=Theme.TEXT_PRIMARY, anchor="w").pack(fill="x")
            ctk.CTkLabel(row, text=s_desc, font=Theme.FONT_CAPTION, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")

    # ── Universal UI Helper Builders for Child Tools ─────────────────────────

    def create_subtabs(self, parent: ctk.CTkFrame, tabs: List[str], on_change: Callable[[str], None]) -> ctk.CTkFrame:
        """Constructs Apple-style horizontal sub-tabs with active underline/pill indicator."""
        tabs_bar = ctk.CTkFrame(parent, fg_color="transparent")
        tabs_bar.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_SM))

        active_tab = [tabs[0]]
        tab_buttons = {}

        def _select(t_name):
            active_tab[0] = t_name
            for name, btn in tab_buttons.items():
                is_cur = (name == t_name)
                btn.configure(
                    fg_color=Theme.SURFACE_PILL if is_cur else "transparent",
                    text_color=Theme.TEXT_PRIMARY if is_cur else Theme.TEXT_MUTED,
                    font=Theme.FONT_BODY_BOLD if is_cur else Theme.FONT_BODY
                )
            on_change(t_name)

        for t in tabs:
            is_cur = (t == tabs[0])
            b = ctk.CTkButton(
                tabs_bar,
                text=t,
                font=Theme.FONT_BODY_BOLD if is_cur else Theme.FONT_BODY,
                fg_color=Theme.SURFACE_PILL if is_cur else "transparent",
                hover_color=Theme.SURFACE_CARD_HOVER,
                text_color=Theme.TEXT_PRIMARY if is_cur else Theme.TEXT_MUTED,
                corner_radius=Theme.RADIUS_BUTTON,
                height=30,
                width=100,
                command=lambda name=t: _select(name)
            )
            b.pack(side="left", padx=(0, 4))
            tab_buttons[t] = b

        return tabs_bar

    def create_dropzone(self, parent: ctk.CTkFrame, title: str, subtitle: str, on_click: Callable) -> ctk.CTkFrame:
        """Constructs tactile dashed dropzone with file picker binding."""
        drop = ctk.CTkFrame(
            parent,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            cursor="hand2"
        )
        drop.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        inner = ctk.CTkFrame(drop, fg_color="transparent", cursor="hand2")
        inner.pack(fill="both", expand=True, padx=Theme.PAD_LG, pady=Theme.PAD_MD)

        ico = ctk.CTkLabel(inner, text="☁", font=(Theme.FONT_FAMILY, 24), text_color=Theme.BRAND_PRIMARY, cursor="hand2")
        ico.pack(pady=(0, 4))

        t_lbl = ctk.CTkLabel(inner, text=title, font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_PRIMARY, cursor="hand2")
        t_lbl.pack()

        s_lbl = ctk.CTkLabel(inner, text=subtitle, font=Theme.FONT_CAPTION, text_color=Theme.TEXT_MUTED, cursor="hand2")
        s_lbl.pack(pady=(2, 0))

        for w in [drop, inner, ico, t_lbl, s_lbl]:
            w.bind("<Button-1>", lambda e: on_click())

        return drop

    def create_comparison_matrix(
        self,
        parent: ctk.CTkFrame,
        original_stats: Dict[str, str],
        estimated_stats: Dict[str, str],
        estimated_label: str = "Estimated"
    ) -> ctk.CTkFrame:
        """Builds side-by-side 'Original vs Estimated' comparison table seen in reference screen 2."""
        matrix_card = ctk.CTkFrame(
            parent,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        matrix_card.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_SM))

        inner = ctk.CTkFrame(matrix_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_MD)
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=0)
        inner.grid_columnconfigure(2, weight=1)

        # Left: Original
        orig_col = ctk.CTkFrame(inner, fg_color="transparent")
        orig_col.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(orig_col, text="Original", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(0, 4))
        for k, v in original_stats.items():
            r = ctk.CTkFrame(orig_col, fg_color="transparent")
            r.pack(fill="x", pady=1)
            ctk.CTkLabel(r, text=k, font=Theme.FONT_CAPTION, text_color=Theme.TEXT_MUTED, anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=v, font=Theme.FONT_CAPTION, text_color=Theme.TEXT_SECONDARY, anchor="e").pack(side="right")

        # Center Arrow
        arrow_col = ctk.CTkFrame(inner, fg_color="transparent")
        arrow_col.grid(row=0, column=1, padx=Theme.PAD_MD)
        ctk.CTkLabel(arrow_col, text="→", font=(Theme.FONT_FAMILY, 20), text_color=Theme.TEXT_MUTED).pack(expand=True)

        # Right: Estimated
        est_col = ctk.CTkFrame(inner, fg_color="transparent")
        est_col.grid(row=0, column=2, sticky="nsew")

        ctk.CTkLabel(est_col, text=estimated_label, font=Theme.FONT_SUBTITLE, text_color=Theme.BRAND_PRIMARY, anchor="w").pack(fill="x", pady=(0, 4))
        for k, v in estimated_stats.items():
            r = ctk.CTkFrame(est_col, fg_color="transparent")
            r.pack(fill="x", pady=1)
            ctk.CTkLabel(r, text=k, font=Theme.FONT_CAPTION, text_color=Theme.TEXT_MUTED, anchor="w").pack(side="left")
            is_size = ("size" in k.lower() or "mb" in v.lower())
            val_color = Theme.BRAND_PRIMARY if is_size else Theme.TEXT_PRIMARY
            ctk.CTkLabel(r, text=v, font=Theme.FONT_BODY_BOLD if is_size else Theme.FONT_CAPTION, text_color=val_color, anchor="e").pack(side="right")

        return matrix_card

    # ── Logging & Feedback APIs ─────────────────────────────────────────────

    def log(self, message: str):
        """Appends timestamped entry to activity drawer."""
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"› {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def set_progress(self, progress: float, status_text: Optional[str] = None):
        """Updates progress bar and percentage display smoothly."""
        pct = max(0, min(100, int(progress * 100)))
        self.progress_bar.set(progress)
        self.pct_lbl.configure(text=f"{pct}%")
        if status_text:
            self.progress_lbl.configure(text=status_text)

    def show_success(self, output_path: str, summary: str = "Operation completed successfully."):
        """Transitions inspector stage to completion state with action buttons."""
        self.last_output_file = output_path
        self.set_progress(1.0, "Completed")
        self.log(f"✓ Success: {os.path.basename(output_path)}")

        for w in self.stage_frame.winfo_children():
            w.destroy()

        success_card = ctk.CTkFrame(self.stage_frame, fg_color=Theme.SURFACE_INSET, corner_radius=Theme.RADIUS_CARD)
        success_card.pack(fill="both", expand=True, padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        inner = ctk.CTkFrame(success_card, fg_color="transparent")
        inner.pack(expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_MD)

        chk = ctk.CTkLabel(inner, text="✓", font=(Theme.FONT_FAMILY, 32, "bold"), text_color=Theme.STATUS_SUCCESS)
        chk.pack(pady=(0, 4))

        head = ctk.CTkLabel(inner, text="Processing Complete", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_PRIMARY)
        head.pack()

        desc = ctk.CTkLabel(inner, text=summary, font=Theme.FONT_CAPTION, text_color=Theme.TEXT_MUTED)
        desc.pack(pady=(2, Theme.PAD_MD))

        # Action Buttons
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack()

        btn_open = ctk.CTkButton(
            btn_row,
            text="Open File",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=Theme.FONT_CAPTION,
            height=32,
            command=self.open_output_file
        )
        btn_open.pack(side="left", padx=(0, Theme.PAD_SM))

        btn_folder = ctk.CTkButton(
            btn_row,
            text="Reveal in Folder",
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            font=Theme.FONT_CAPTION,
            height=32,
            command=self.open_output_folder
        )
        btn_folder.pack(side="left")

    def show_error(self, error_message: str):
        """Displays error feedback state."""
        self.set_progress(0.0, "Failed")
        self.log(f"✕ Error: {error_message}")
        messagebox.showerror("Error", error_message)

    def open_output_file(self):
        if self.last_output_file and os.path.exists(self.last_output_file):
            try:
                os.startfile(self.last_output_file)
            except Exception as e:
                self.log(f"Unable to open file: {e}")

    def open_output_folder(self):
        folder = None
        if self.last_output_file and os.path.exists(self.last_output_file):
            folder = os.path.dirname(self.last_output_file)
        elif self.output_directory and os.path.exists(self.output_directory):
            folder = self.output_directory

        if folder and os.path.exists(folder):
            try:
                subprocess.Popen(f'explorer "{folder}"')
            except Exception as e:
                self.log(f"Unable to open folder: {e}")
