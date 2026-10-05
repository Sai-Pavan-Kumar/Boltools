"""Top application header with official Boltools branding, dynamic breadcrumbs, notification bell, and theme toggle."""

import os
from typing import Callable, Optional, List
import customtkinter as ctk
from PIL import Image

from src.core.theme import Theme


class AppHeader(ctk.CTkFrame):
    """Header toolbar featuring branding, breadcrumbs, search trigger, notification bell, and theme toggle."""

    def __init__(
        self,
        master,
        assets_dir: str,
        on_search_click: Callable[[], None],
        on_home_click: Callable[[], None],
        on_notification_click: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=Theme.SURFACE_SIDEBAR,
            height=56,
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
        self.current_theme_mode = "Dark"
        self.unread_count = 0

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self._build_branding()
        self._build_breadcrumbs()
        self._build_actions()

    def _load_image(self, filename: str, size: tuple[int, int]) -> Optional[ctk.CTkImage]:
        path = os.path.join(self.assets_dir, filename)
        if os.path.exists(path):
            try:
                pil_img = Image.open(path)
                return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            except Exception as e:
                print(f"[Boltools Asset Error] Failed to load {filename}: {e}")
        return None

    def _build_branding(self):
        # Clickable brand container returning to Home
        brand_frame = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        brand_frame.grid(row=0, column=0, sticky="w", padx=(Theme.PAD_MD, Theme.PAD_SM), pady=Theme.PAD_XS)
        brand_frame.bind("<Button-1>", lambda e: self.on_home_click())

        # Monogram Bolt Logo
        bolt_img = self._load_image("bolt_logo.webp", (28, 28))
        if bolt_img:
            bolt_label = ctk.CTkLabel(brand_frame, image=bolt_img, text="", cursor="hand2")
            bolt_label.pack(side="left", padx=(0, Theme.PAD_SM))
            bolt_label.bind("<Button-1>", lambda e: self.on_home_click())

        # Title + Pro Badge
        title_box = ctk.CTkFrame(brand_frame, fg_color="transparent", cursor="hand2")
        title_box.pack(side="left")
        title_box.bind("<Button-1>", lambda e: self.on_home_click())

        title_lbl = ctk.CTkLabel(
            title_box,
            text="BOLTOOLS",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
            cursor="hand2"
        )
        title_lbl.pack(side="left", padx=(0, 6))
        title_lbl.bind("<Button-1>", lambda e: self.on_home_click())

        studio_badge = ctk.CTkLabel(
            title_box,
            text="PRO",
            font=(Theme.FONT_FAMILY, 9, "bold"),
            fg_color=Theme.SURFACE_PILL,
            text_color=Theme.BRAND_ACCENT,
            corner_radius=Theme.RADIUS_PILL,
            width=36,
            height=18
        )
        studio_badge.pack(side="left")

    def _build_breadcrumbs(self):
        self.crumb_container = ctk.CTkFrame(self, fg_color="transparent")
        self.crumb_container.grid(row=0, column=1, sticky="w", padx=Theme.PAD_MD)
        self.crumb_label = ctk.CTkLabel(
            self.crumb_container,
            text="Home",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        self.crumb_label.pack(side="left")

    def set_breadcrumb(self, segments: List[str]):
        """Updates the active path navigation indicator."""
        trail = "  ›  ".join(segments)
        self.crumb_label.configure(text=trail)

    def _build_actions(self):
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.grid(row=0, column=2, sticky="e", padx=Theme.PAD_MD)

        # Raycast / Spotlight Style Search Trigger
        self.search_btn = ctk.CTkButton(
            actions_frame,
            text="Search tools...   Ctrl + K",
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_MUTED,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_PILL,
            font=Theme.FONT_BODY,
            height=32,
            width=210,
            command=self.on_search_click
        )
        self.search_btn.pack(side="left", padx=(0, Theme.PAD_SM))

        # Notification & Product Launch Bell
        self.bell_btn = ctk.CTkButton(
            actions_frame,
            text="🔔",
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_PILL,
            font=(Theme.FONT_FAMILY, 13),
            width=38,
            height=32,
            command=self._handle_bell_click
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
            corner_radius=Theme.RADIUS_PILL,
            font=(Theme.FONT_FAMILY, 14),
            width=36,
            height=32,
            command=self._toggle_theme
        )
        self.theme_btn.pack(side="left")

    def set_unread_notifications(self, count: int):
        """Updates the notification bell with an unread badge dot."""
        self.unread_count = count
        if count > 0:
            self.bell_btn.configure(
                text=f"🔔 ●",
                text_color=Theme.BRAND_ACCENT,
                border_color=Theme.BRAND_ACCENT
            )
        else:
            self.bell_btn.configure(
                text="🔔",
                text_color=Theme.TEXT_SECONDARY,
                border_color=Theme.BORDER_SUBTLE
            )

    def _handle_bell_click(self):
        if self.on_notification_click:
            self.on_notification_click()

    def _toggle_theme(self):
        """Switches dynamically between Apple Dark Mode and Light Mode."""
        if self.current_theme_mode == "Dark":
            self.current_theme_mode = "Light"
            ctk.set_appearance_mode("Light")
            self.theme_btn.configure(text="☾")
        else:
            self.current_theme_mode = "Dark"
            ctk.set_appearance_mode("Dark")
            self.theme_btn.configure(text="☀")
