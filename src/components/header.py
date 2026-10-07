"""Clean, minimalist application header with breadcrumbs and Spotlight trigger."""

import os
from typing import Callable, Optional, List
import customtkinter as ctk

from src.core.theme import Theme


class AppHeader(ctk.CTkFrame):
    """Header toolbar featuring breadcrumbs, compact search trigger, and theme toggle."""

    def __init__(
        self,
        master,
        assets_dir: str,
        on_search_click: Callable[[], None],
        on_home_click: Callable[[], None],
        on_notification_click: Optional[Callable[[], None]] = None,
        on_back_click: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=Theme.SURFACE_SIDEBAR,
            height=46,
            corner_radius=0,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            **kwargs
        )
        self.grid_propagate(False)
        self.assets_dir = assets_dir
        self.on_search_click = on_search_click
        self.on_home_click = on_home_click
        self.on_notification_click = on_notification_click
        self.on_back_click = on_back_click
        self.unread_count = 0
        self.current_theme_mode = "Dark"

        self.grid_columnconfigure(0, weight=1)  # Left Breadcrumbs
        self.grid_columnconfigure(1, weight=0)  # Right Actions
        self.grid_rowconfigure(0, weight=1)

        self._build_breadcrumbs()
        self._build_actions()

    def _build_breadcrumbs(self):
        self.crumb_container = ctk.CTkFrame(self, fg_color="transparent")
        self.crumb_container.grid(row=0, column=0, sticky="w", padx=Theme.PAD_MD)
        self.set_breadcrumb(["Home"])

    def set_breadcrumb(
        self,
        segments: List[str],
        on_home: Optional[Callable[[], None]] = None,
        on_category: Optional[Callable[[], None]] = None,
        on_back: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """Updates the active path navigation indicator with back button and clickable crumbs."""
        for w in self.crumb_container.winfo_children():
            w.destroy()

        is_subpage = len(segments) > 1

        if is_subpage:
            back_cmd = on_back or self.on_back_click or on_home
            if back_cmd:
                back_btn = ctk.CTkButton(
                    self.crumb_container,
                    text="← Back",
                    font=Theme.FONT_CAPTION,
                    fg_color=Theme.SURFACE_CARD,
                    hover_color=Theme.SURFACE_CARD_HOVER,
                    text_color=Theme.TEXT_PRIMARY,
                    border_width=1,
                    border_color=Theme.BORDER_SUBTLE,
                    corner_radius=Theme.RADIUS_BUTTON,
                    width=60,
                    height=26,
                    command=back_cmd
                )
                back_btn.pack(side="left", padx=(0, Theme.PAD_SM))

        total = len(segments)
        for idx, text in enumerate(segments):
            is_last = (idx == total - 1)
            cmd = None
            if idx == 0 and not is_last and on_home:
                cmd = on_home
            elif idx == 1 and not is_last and on_category:
                cmd = on_category

            if cmd:
                lbl = ctk.CTkLabel(
                    self.crumb_container,
                    text=text,
                    font=Theme.FONT_BODY,
                    text_color=Theme.BRAND_PRIMARY,
                    cursor="hand2"
                )
                lbl.pack(side="left")
                lbl.bind("<Button-1>", lambda e, c=cmd: c())
            else:
                lbl = ctk.CTkLabel(
                    self.crumb_container,
                    text=text,
                    font=Theme.FONT_BODY_BOLD if is_last else Theme.FONT_BODY,
                    text_color=Theme.TEXT_PRIMARY if is_last else Theme.TEXT_MUTED
                )
                lbl.pack(side="left")

            if not is_last:
                sep = ctk.CTkLabel(
                    self.crumb_container,
                    text="  /  ",
                    font=Theme.FONT_CAPTION,
                    text_color=Theme.TEXT_MUTED
                )
                sep.pack(side="left")

    def _build_actions(self):
        """Right action buttons: Search trigger, Announcement Bell, and Theme Toggle."""
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.grid(row=0, column=1, sticky="e", padx=Theme.PAD_MD)

        # Search Trigger Pill
        self.search_btn = ctk.CTkButton(
            actions_frame,
            text="Search tools...   Ctrl + K",
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_MUTED,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            font=Theme.FONT_CAPTION,
            height=28,
            width=180,
            command=self.on_search_click
        )
        self.search_btn.pack(side="left", padx=(0, Theme.PAD_SM))

        # Notification & Community Hub Bell
        self.bell_btn = ctk.CTkButton(
            actions_frame,
            text="🔔",
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 11),
            width=28,
            height=28,
            command=self._handle_notification_click
        )
        self.bell_btn.pack(side="left", padx=(0, Theme.PAD_SM))

        # Dynamic Theme Switcher (Dark / Light)
        self.theme_btn = ctk.CTkButton(
            actions_frame,
            text="☀",
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12),
            width=28,
            height=28,
            command=self._toggle_theme
        )
        self.theme_btn.pack(side="left")

    def _handle_notification_click(self):
        if self.on_notification_click:
            self.on_notification_click()

    def set_unread_notifications(self, count: int):
        """Updates unread badge display on the bell button. 0 unread removes any badge text."""
        self.unread_count = max(0, count)
        if self.unread_count > 0:
            badge_text = f"🔔 {self.unread_count}" if self.unread_count < 10 else "🔔 9+"
            self.bell_btn.configure(
                text=badge_text,
                width=46,
                text_color=Theme.BRAND_ACCENT,
                border_color=Theme.BRAND_PRIMARY
            )
        else:
            self.bell_btn.configure(
                text="🔔",
                width=28,
                text_color=Theme.TEXT_PRIMARY,
                border_color=Theme.BORDER_SUBTLE
            )

    def _toggle_theme(self):
        new_mode = "Light" if self.current_theme_mode == "Dark" else "Dark"
        self.current_theme_mode = new_mode
        self.theme_btn.configure(text="☾" if new_mode == "Light" else "☀")
        Theme.apply_appearance(new_mode, window=self.winfo_toplevel())
