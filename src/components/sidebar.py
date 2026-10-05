"""Sidebar navigation panel for Boltools with Apple macOS-grade hierarchy."""

from typing import Callable, Optional, Dict
import customtkinter as ctk

from src.core.theme import Theme
from src.core.registry import ToolRegistry


class AppSidebar(ctk.CTkFrame):
    """Left sidebar offering category navigation, clean section groups, and live engine status."""

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
            width=230,
            corner_radius=0,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            **kwargs
        )
        self.grid_propagate(False)
        self.on_select_category = on_select_category
        self.on_select_home = on_select_home

        self.active_category: Optional[str] = None
        self.buttons: Dict[str, ctk.CTkButton] = {}

        self._build_ui()

    def _build_ui(self):
        # Top Container for Navigation Items
        self.nav_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.nav_scroll.pack(fill="both", expand=True, padx=Theme.PAD_SM, pady=(Theme.PAD_SM, Theme.PAD_XS))

        # Section: WORKSPACE
        self._build_section_header("WORKSPACE")

        # Home Hub Button
        self.home_btn = ctk.CTkButton(
            self.nav_scroll,
            text="  ⊞   Home Hub",
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            anchor="w",
            font=Theme.FONT_BODY_BOLD,
            height=34,
            corner_radius=Theme.RADIUS_BUTTON,
            command=self._handle_home_click
        )
        self.home_btn.pack(fill="x", pady=(2, Theme.PAD_SM))

        # Section: CREATIVE SUITES
        self._build_section_header("CREATIVE SUITES")
        for cat_id in ["video", "audio", "image"]:
            self._build_category_row(cat_id)

        # Section: PRODUCTIVITY & OPS
        self._build_section_header("PRODUCTIVITY & OPS", pady=(Theme.PAD_SM, 4))
        for cat_id in ["pdf", "creator", "design", "system"]:
            self._build_category_row(cat_id)

        # Bottom System Status Badge
        self._build_footer_status()

    def _build_section_header(self, title: str, pady=(Theme.PAD_XS, 4)):
        lbl = ctk.CTkLabel(
            self.nav_scroll,
            text=title,
            font=Theme.FONT_LABEL,
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        lbl.pack(fill="x", padx=Theme.PAD_SM, pady=pady)

    def _build_category_row(self, cat_id: str):
        meta = ToolRegistry.CATEGORIES.get(cat_id)
        if not meta:
            return

        count = len(ToolRegistry.get_by_category(cat_id))
        glyph = meta.get("glyph", "●")
        name = meta["name"]

        # Container row
        row_btn = ctk.CTkButton(
            self.nav_scroll,
            text=f"  {glyph}   {name}   ·  {count}",
            fg_color="transparent",
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
            font=Theme.FONT_BODY,
            height=32,
            corner_radius=Theme.RADIUS_BUTTON,
            command=lambda cid=cat_id: self._handle_cat_click(cid)
        )
        row_btn.pack(fill="x", pady=1)
        self.buttons[cat_id] = row_btn

    def _build_footer_status(self):
        footer_frame = ctk.CTkFrame(
            self,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_BUTTON,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        footer_frame.pack(fill="x", padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        inner = ctk.CTkFrame(footer_frame, fg_color="transparent")
        inner.pack(fill="both", padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        status_lbl = ctk.CTkLabel(
            inner,
            text="● Local Engines Active",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.STATUS_SUCCESS,
            anchor="w"
        )
        status_lbl.pack(anchor="w")

        info_lbl = ctk.CTkLabel(
            inner,
            text="100% Offline • Zero Data Leaks",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        info_lbl.pack(anchor="w", pady=(1, 0))

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
            self.home_btn.configure(
                fg_color=Theme.SURFACE_CARD,
                text_color=Theme.TEXT_PRIMARY,
                border_width=1,
                border_color=Theme.BORDER_SUBTLE
            )
        else:
            self.home_btn.configure(
                fg_color="transparent",
                text_color=Theme.TEXT_SECONDARY,
                border_width=0
            )

        for cid, btn in self.buttons.items():
            if cid == self.active_category:
                btn.configure(
                    fg_color=Theme.SURFACE_CARD,
                    text_color=Theme.TEXT_PRIMARY,
                    border_width=1,
                    border_color=Theme.BORDER_SUBTLE
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=Theme.TEXT_SECONDARY,
                    border_width=0
                )
