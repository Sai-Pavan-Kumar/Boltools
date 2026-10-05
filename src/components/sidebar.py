"""Sidebar navigation panel for Boltools with category filtering and favorites."""

from typing import Callable, Optional
import customtkinter as ctk

from src.core.theme import Theme
from src.core.registry import ToolRegistry


class AppSidebar(ctk.CTkFrame):
    """Left sidebar offering category filtering, pinned tools, and quick navigation."""

    def __init__(
        self,
        master,
        on_select_category: Callable[[str], None],
        on_select_home: Callable[[], None],
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=Theme.SURFACE_SIDEBAR,
            width=240,
            corner_radius=0,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            **kwargs
        )
        self.grid_propagate(False)
        self.on_select_category = on_select_category
        self.on_select_home = on_select_home
        
        self.active_category: Optional[str] = None
        self.buttons = {}

        self._build_ui()

    def _build_ui(self):
        # Home Hub Button
        self.home_btn = ctk.CTkButton(
            self,
            text="🏠  Home Hub",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=36,
            corner_radius=Theme.RADIUS_BUTTON,
            command=self._handle_home_click
        )
        self.home_btn.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM))

        # Categories Section Header
        cat_header = ctk.CTkLabel(
            self,
            text="CATEGORIES",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        cat_header.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        # Scrollable Category List
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=Theme.PAD_XS, pady=Theme.PAD_XS)

        for cat_id, meta in ToolRegistry.CATEGORIES.items():
            count = len(ToolRegistry.get_by_category(cat_id))
            btn_text = f"{meta['icon']}  {meta['name']}  ({count})"
            
            btn = ctk.CTkButton(
                self.scroll_frame,
                text=btn_text,
                fg_color="transparent",
                hover_color=Theme.SURFACE_CARD_HOVER,
                text_color=Theme.TEXT_SECONDARY,
                anchor="w",
                font=(Theme.FONT_FAMILY, 12),
                height=34,
                corner_radius=Theme.RADIUS_BUTTON,
                command=lambda cid=cat_id: self._handle_cat_click(cid)
            )
            btn.pack(fill="x", pady=2)
            self.buttons[cat_id] = btn

        # Bottom System Badge
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_MD)
        
        system_badge = ctk.CTkLabel(
            footer_frame,
            text="⚡ 100% Offline & Private\n₹0 / $0 Forever",
            font=(Theme.FONT_FAMILY, 10),
            text_color=Theme.TEXT_MUTED,
            justify="left"
        )
        system_badge.pack(anchor="w")

    def _handle_home_click(self):
        self.active_category = None
        self._update_button_states()
        self.on_select_home()

    def _handle_cat_click(self, cat_id: str):
        self.active_category = cat_id
        self._update_button_states()
        self.on_select_category(cat_id)

    def _update_button_states(self):
        if self.active_category is None:
            self.home_btn.configure(fg_color=Theme.BRAND_PRIMARY, text_color=Theme.TEXT_PRIMARY)
        else:
            self.home_btn.configure(fg_color="transparent", text_color=Theme.TEXT_SECONDARY)

        for cid, btn in self.buttons.items():
            if cid == self.active_category:
                btn.configure(fg_color=Theme.SURFACE_CARD, text_color=Theme.TEXT_PRIMARY, border_width=1, border_color=Theme.BORDER_HOVER)
            else:
                btn.configure(fg_color="transparent", text_color=Theme.TEXT_SECONDARY, border_width=0)
