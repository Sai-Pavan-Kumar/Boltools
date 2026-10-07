"""Clean, professional application sidebar for Boltools.

Enforces:
- Apple Pro / Linear minimalist desktop standards
- High information density (compact 32px items)
- Zero cartoon emojis, zero fake notification/update badges
- Native real-time Win32 System Resource meters at the bottom
"""

import os
from typing import Callable, Optional, Dict
import customtkinter as ctk
from PIL import Image

from src.core.theme import Theme
from src.core.paths import get_asset_path
from src.core.system_monitor import system_monitor


class AppSidebar(ctk.CTkFrame):
    """Left navigation panel featuring brand heading, primary navigation, and live system metrics."""

    def __init__(
        self,
        master,
        on_select_home: Callable[[], None],
        on_select_tools: Optional[Callable[[], None]] = None,
        on_select_directory: Optional[Callable[[], None]] = None,
        on_select_category: Optional[Callable[[str], None]] = None,
        on_select_favorites: Optional[Callable[[], None]] = None,
        on_select_settings: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=Theme.SURFACE_SIDEBAR,
            width=210,
            corner_radius=0,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            **kwargs
        )
        self.grid_propagate(False)
        self.on_select_home = on_select_home
        self.on_select_tools = on_select_tools or on_select_directory or on_select_home
        self.on_select_directory = on_select_directory or self.on_select_tools
        self.on_select_category = on_select_category
        self.on_select_favorites = on_select_favorites or self.on_select_tools
        self.on_select_settings = on_select_settings or on_select_home

        self.active_item: str = "home"
        self.buttons: Dict[str, ctk.CTkFrame] = {}
        self.assets_dir = get_asset_path()

        # Layout grids (Row 0: Navigation, Row 1: System Monitor)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self._build_nav()
        self._build_system_monitor()

        # Connect live system monitor
        system_monitor.subscribe(self._on_system_stats_update)

    def _build_nav(self):
        nav_container = ctk.CTkFrame(self, fg_color="transparent")
        nav_container.grid(row=0, column=0, sticky="nsew", padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        # ── Brand Header
        self._build_brand_header(nav_container)

        # ── Primary Section Label
        lbl_sec = ctk.CTkLabel(
            nav_container,
            text="NAVIGATION",
            font=(Theme.FONT_FAMILY, 9, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        lbl_sec.pack(fill="x", padx=Theme.PAD_SM, pady=(Theme.PAD_SM, 4))

        # ── Navigation Items (Zero fake badges)
        self._add_nav_item(nav_container, "home", "Home", self._handle_home_click)
        self._add_nav_item(nav_container, "tools", "Tools", self._handle_tools_click)
        self._add_nav_item(nav_container, "favorites", "Favorites", self._handle_favorites_click)
        self._add_nav_item(nav_container, "settings", "Settings", self._handle_settings_click)

    def _build_brand_header(self, parent: ctk.CTkFrame):
        brand_row = ctk.CTkFrame(parent, fg_color="transparent", cursor="hand2")
        brand_row.pack(fill="x", padx=Theme.PAD_SM, pady=(Theme.PAD_XS, Theme.PAD_MD))
        brand_row.bind("<Button-1>", lambda e: self._handle_home_click())

        # Monogram Bolt Logo
        logo_path = os.path.join(self.assets_dir, "Boltools_logo.webp")
        logo_img = None
        if os.path.exists(logo_path):
            try:
                pil = Image.open(logo_path)
                logo_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(22, 22))
            except Exception:
                pass

        if logo_img:
            lbl_ico = ctk.CTkLabel(brand_row, image=logo_img, text="", cursor="hand2")
            lbl_ico.pack(side="left", padx=(0, 8))
            lbl_ico.bind("<Button-1>", lambda e: self._handle_home_click())

        lbl_txt = ctk.CTkLabel(
            brand_row,
            text="Boltools",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY,
            cursor="hand2"
        )
        lbl_txt.pack(side="left")
        lbl_txt.bind("<Button-1>", lambda e: self._handle_home_click())

        badge = ctk.CTkLabel(
            brand_row,
            text="v1.0",
            font=(Theme.FONT_FAMILY, 9),
            text_color=Theme.TEXT_MUTED,
            fg_color=Theme.SURFACE_PILL,
            corner_radius=Theme.RADIUS_PILL,
            padx=6,
            pady=1
        )
        badge.pack(side="right")

    def _add_nav_item(self, parent: ctk.CTkFrame, key: str, label: str, command: Callable):
        is_active = (key == self.active_item)

        btn = ctk.CTkFrame(
            parent,
            fg_color=Theme.SURFACE_CARD if is_active else "transparent",
            corner_radius=Theme.RADIUS_BUTTON,
            border_width=1 if is_active else 0,
            border_color=Theme.BORDER_SUBTLE,
            cursor="hand2",
            height=32
        )
        btn.pack(fill="x", pady=1)
        btn.pack_propagate(False)

        lbl = ctk.CTkLabel(
            btn,
            text=f"  {label}",
            font=Theme.FONT_BODY_BOLD if is_active else Theme.FONT_BODY,
            text_color=Theme.TEXT_PRIMARY if is_active else Theme.TEXT_SECONDARY,
            anchor="w",
            cursor="hand2"
        )
        lbl.pack(fill="both", expand=True, padx=Theme.PAD_SM)

        for w in [btn, lbl]:
            w.bind("<Button-1>", lambda e: command())

        self.buttons[key] = btn

    def _build_system_monitor(self):
        """Compact Win32 hardware monitor widget docked at the bottom."""
        mon_card = ctk.CTkFrame(
            self,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        mon_card.grid(row=1, column=0, sticky="ew", padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        inner = ctk.CTkFrame(mon_card, fg_color="transparent")
        inner.pack(fill="both", padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        # Title
        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.pack(fill="x", pady=(0, 4))

        dot = ctk.CTkLabel(title_row, text="●", font=(Theme.FONT_FAMILY, 8), text_color=Theme.STATUS_SUCCESS)
        dot.pack(side="left", padx=(0, 4))

        title = ctk.CTkLabel(
            title_row,
            text="RESOURCES",
            font=(Theme.FONT_FAMILY, 9, "bold"),
            text_color=Theme.TEXT_MUTED
        )
        title.pack(side="left")

        # Gauges
        self.cpu_lbl, self.cpu_bar = self._create_gauge_row(inner, "CPU", 12)
        self.ram_lbl, self.ram_bar = self._create_gauge_row(inner, "RAM", 45)
        self.disk_lbl, self.disk_bar = self._create_gauge_row(inner, "Disk", 38)

    def _create_gauge_row(self, parent: ctk.CTkFrame, label: str, init_val: int):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        row.grid_columnconfigure(0, weight=0)
        row.grid_columnconfigure(1, weight=1)
        row.grid_columnconfigure(2, weight=0)

        name = ctk.CTkLabel(row, text=label, font=Theme.FONT_CAPTION, text_color=Theme.TEXT_MUTED, width=28, anchor="w")
        name.grid(row=0, column=0, sticky="w")

        bar = ctk.CTkProgressBar(
            row,
            height=5,
            corner_radius=2,
            progress_color=Theme.STATUS_SUCCESS,
            fg_color=Theme.SURFACE_INSET
        )
        bar.set(init_val / 100.0)
        bar.grid(row=0, column=1, sticky="ew", padx=6)

        val = ctk.CTkLabel(row, text=f"{init_val}%", font=(Theme.FONT_FAMILY, 9), text_color=Theme.TEXT_SECONDARY, width=28, anchor="e")
        val.grid(row=0, column=2, sticky="e")

        return val, bar

    def _on_system_stats_update(self, cpu: int, ram: int, disk: int):
        try:
            self.after(0, self._apply_stats, cpu, ram, disk)
        except Exception:
            pass

    def _apply_stats(self, cpu: int, ram: int, disk: int):
        if not self.winfo_exists():
            return
        self.cpu_lbl.configure(text=f"{cpu}%")
        self.cpu_bar.set(cpu / 100.0)
        self.ram_lbl.configure(text=f"{ram}%")
        self.ram_bar.set(ram / 100.0)
        self.disk_lbl.configure(text=f"{disk}%")
        self.disk_bar.set(disk / 100.0)

    def _handle_home_click(self):
        self._set_active("home")
        self.on_select_home()

    def _handle_tools_click(self):
        self._set_active("tools")
        self.on_select_tools()

    def _handle_favorites_click(self):
        self._set_active("favorites")
        self.on_select_favorites()

    def _handle_settings_click(self):
        self._set_active("settings")
        self.on_select_settings()

    def _set_active(self, key: str):
        self.active_item = key
        for k, btn in self.buttons.items():
            is_cur = (k == key)
            btn.configure(
                fg_color=Theme.SURFACE_CARD if is_cur else "transparent",
                border_width=1 if is_cur else 0
            )
            for w in btn.winfo_children():
                if isinstance(w, ctk.CTkLabel):
                    w.configure(
                        text_color=Theme.TEXT_PRIMARY if is_cur else Theme.TEXT_SECONDARY,
                        font=Theme.FONT_BODY_BOLD if is_cur else Theme.FONT_BODY
                    )

    def set_active_key(self, key: str):
        self._set_active(key)

    def _update_selection(self):
        self._set_active(self.active_item)
