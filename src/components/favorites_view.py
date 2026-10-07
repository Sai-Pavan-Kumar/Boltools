"""Favorites View for Boltools.

Displays pinned utilities with quick-launch cards and an elegant empty state.
"""

from typing import Callable, List
import customtkinter as ctk

from src.core.theme import Theme
from src.core.registry import ToolRegistry, ToolDefinition
from src.core.favorites import favorites_service


class FavoritesView(ctk.CTkFrame):
    """Clean, high-performance view for managing pinned favorite utilities."""

    def __init__(
        self,
        master,
        on_select_tool: Callable[[ToolDefinition], None],
        on_browse_tools: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, fg_color=Theme.SURFACE_BASE, corner_radius=0, **kwargs)

        self.on_select_tool = on_select_tool
        self.on_browse_tools = on_browse_tools

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Content

        self._build_header()
        self._build_content_area()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Theme.PAD_LG, pady=(Theme.PAD_LG, Theme.PAD_MD))

        title = ctk.CTkLabel(
            header,
            text="Favorites",
            font=Theme.FONT_HERO,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title.pack(anchor="w")

        sub = ctk.CTkLabel(
            header,
            text="Quick access to your pinned utilities for fast daily workflows.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        sub.pack(anchor="w", pady=(2, 0))

    def _build_content_area(self):
        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll_canvas.grid(row=1, column=0, sticky="nsew", padx=Theme.PAD_LG, pady=(0, Theme.PAD_LG))
        self.scroll_canvas.grid_columnconfigure((0, 1), weight=1, uniform="fav_col")
        self.refresh()

    def refresh(self):
        for w in self.scroll_canvas.winfo_children():
            w.destroy()

        fav_ids = favorites_service.get_all()
        fav_tools: List[ToolDefinition] = []
        for tid in fav_ids:
            tool = ToolRegistry.get(tid)
            if tool:
                fav_tools.append(tool)

        if not fav_tools:
            self._render_empty_state()
            return

        for idx, tool in enumerate(fav_tools):
            row = idx // 2
            col = idx % 2
            card = self._create_card(self.scroll_canvas, tool)
            card.grid(row=row, column=col, sticky="nsew", padx=Theme.PAD_XS, pady=Theme.PAD_XS)

    def _render_empty_state(self):
        empty_card = ctk.CTkFrame(
            self.scroll_canvas,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        empty_card.grid(row=0, column=0, columnspan=2, sticky="ew", pady=Theme.PAD_LG, padx=Theme.PAD_SM)

        inner = ctk.CTkFrame(empty_card, fg_color="transparent")
        inner.pack(padx=Theme.PAD_XL, pady=Theme.PAD_XL)

        # Heart Icon Box
        ico = ctk.CTkLabel(
            inner,
            text="♡",
            font=(Theme.FONT_FAMILY, 28),
            text_color=Theme.TEXT_MUTED,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=12,
            width=56,
            height=56
        )
        ico.pack(pady=(0, Theme.PAD_MD))

        title = ctk.CTkLabel(
            inner,
            text="No Pinned Favorites Yet",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.TEXT_PRIMARY
        )
        title.pack()

        sub = ctk.CTkLabel(
            inner,
            text="Pin frequently used utilities using the heart icon inside any tool studio.",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_MUTED,
            wraplength=340
        )
        sub.pack(pady=(4, Theme.PAD_MD))

        btn_browse = ctk.CTkButton(
            inner,
            text="Browse Tool Hub →",
            font=Theme.FONT_CAPTION,
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            text_color=Theme.TEXT_ON_BRAND,
            corner_radius=Theme.RADIUS_BUTTON,
            height=32,
            command=self.on_browse_tools
        )
        btn_browse.pack()

    def _create_card(self, parent, tool: ToolDefinition) -> ctk.CTkFrame:
        tint_cfg = Theme.CATEGORY_COLORS.get(tool.category_id, {"accent": Theme.BRAND_PRIMARY, "bg": Theme.SURFACE_INSET})

        card = ctk.CTkFrame(
            parent,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_MD)

        # Header Row: Icon Squircle + Suite Badge + Heart Unpin
        hdr_row = ctk.CTkFrame(inner, fg_color="transparent")
        hdr_row.pack(fill="x", pady=(0, 4))

        ico_box = ctk.CTkLabel(
            hdr_row,
            text=getattr(tool, "icon", "⚡"),
            font=(Theme.FONT_FAMILY, 14),
            fg_color=tint_cfg["bg"],
            corner_radius=6,
            width=28,
            height=28
        )
        ico_box.pack(side="left", padx=(0, 6))

        title = ctk.CTkLabel(
            hdr_row,
            text=tool.name,
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title.pack(side="left")

        btn_unpin = ctk.CTkButton(
            hdr_row,
            text="♥",
            font=(Theme.FONT_FAMILY, 14),
            fg_color="transparent",
            hover_color=Theme.SURFACE_INSET,
            text_color=Theme.STATUS_ERROR,
            width=28,
            height=28,
            command=lambda tid=tool.id: self._remove_fav(tid)
        )
        btn_unpin.pack(side="right")

        # Description
        desc = ctk.CTkLabel(
            inner,
            text=tool.description,
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
            wraplength=320,
            justify="left"
        )
        desc.pack(fill="x", pady=(2, Theme.PAD_SM))

        # Bottom Action Row
        act_row = ctk.CTkFrame(inner, fg_color="transparent")
        act_row.pack(fill="x", pady=(4, 0))

        btn_launch = ctk.CTkButton(
            act_row,
            text="Launch Utility  →",
            font=Theme.FONT_CAPTION,
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            text_color=Theme.TEXT_ON_BRAND,
            corner_radius=Theme.RADIUS_BUTTON,
            height=28,
            command=lambda t=tool: self.on_select_tool(t)
        )
        btn_launch.pack(side="left")

        return card

    def _remove_fav(self, tool_id: str):
        favorites_service.remove_favorite(tool_id)
        self.refresh()
