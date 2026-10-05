"""Home Dashboard view (Layer 2 discovery hub) for Boltools."""

from typing import Callable
import customtkinter as ctk

from src.core.theme import Theme
from src.core.registry import ToolRegistry, ToolDefinition


class HomeDashboard(ctk.CTkScrollableFrame):
    """Default landing screen displaying the 7 functional domains and quick access tools."""

    def __init__(
        self,
        master,
        on_tool_select: Callable[[ToolDefinition], None],
        on_category_select: Callable[[str], None],
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=Theme.SURFACE_BASE,
            corner_radius=0,
            **kwargs
        )
        self.on_tool_select = on_tool_select
        self.on_category_select = on_category_select

        self._build_hero()
        self._build_featured_shelf()
        self._build_domains_grid()

    def _build_hero(self):
        hero_card = ctk.CTkFrame(
            self,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        hero_card.pack(fill="x", padx=Theme.PAD_LG, pady=(Theme.PAD_LG, Theme.PAD_MD))

        inner = ctk.CTkFrame(hero_card, fg_color="transparent")
        inner.pack(fill="both", padx=Theme.PAD_LG, pady=Theme.PAD_LG)

        title = ctk.CTkLabel(
            inner,
            text="Welcome to Boltools",
            font=(Theme.FONT_FAMILY, 24, "bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title.pack(anchor="w")

        desc = ctk.CTkLabel(
            inner,
            text="The 100% Offline-First Swiss Army Knife for Creators & Power Users. Zero subscriptions. Zero data leaks.",
            font=(Theme.FONT_FAMILY, 13),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=(4, Theme.PAD_SM))

        stats_row = ctk.CTkLabel(
            inner,
            text="57 Specialized Power Tools   •   48 Offline Engines   •   9 Smart Web Tools   •   Built by The SurfBoard",
            font=(Theme.FONT_FAMILY, 11),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        stats_row.pack(anchor="w")

    def _build_featured_shelf(self):
        """Displays quick-access highlighted tools."""
        shelf_frame = ctk.CTkFrame(self, fg_color="transparent")
        shelf_frame.pack(fill="x", padx=Theme.PAD_LG, pady=(Theme.PAD_SM, Theme.PAD_MD))

        lbl = ctk.CTkLabel(
            shelf_frame,
            text="QUICK ACCESS",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        lbl.pack(anchor="w", pady=(0, Theme.PAD_XS))

        cards_row = ctk.CTkFrame(shelf_frame, fg_color="transparent")
        cards_row.pack(fill="x")
        cards_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="shelf")

        quick_tool_ids = ["pdf_first_page", "image_webp_compress", "creator_bolt_down", "video_extractor"]
        for idx, tid in enumerate(quick_tool_ids):
            tool = ToolRegistry.get(tid)
            if not tool:
                continue

            btn = ctk.CTkButton(
                cards_row,
                text=f"{tool.name}\n{tool.category_name}",
                fg_color=Theme.SURFACE_CARD,
                hover_color=Theme.SURFACE_CARD_HOVER,
                text_color=Theme.TEXT_PRIMARY,
                border_width=1,
                border_color=Theme.BORDER_SUBTLE,
                corner_radius=Theme.RADIUS_BUTTON,
                height=56,
                font=(Theme.FONT_FAMILY, 12),
                command=lambda t=tool: self.on_tool_select(t)
            )
            btn.grid(row=0, column=idx, padx=Theme.PAD_XS, pady=Theme.PAD_XS, sticky="ew")

    def _build_domains_grid(self):
        """Displays the 7 core domains with tool counters."""
        domains_frame = ctk.CTkFrame(self, fg_color="transparent")
        domains_frame.pack(fill="x", padx=Theme.PAD_LG, pady=(Theme.PAD_SM, Theme.PAD_LG))

        lbl = ctk.CTkLabel(
            domains_frame,
            text="FUNCTIONAL DOMAINS",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        lbl.pack(anchor="w", pady=(0, Theme.PAD_SM))

        grid_container = ctk.CTkFrame(domains_frame, fg_color="transparent")
        grid_container.pack(fill="x")
        grid_container.grid_columnconfigure((0, 1), weight=1, uniform="domain_col")

        categories = list(ToolRegistry.CATEGORIES.items())
        for idx, (cat_id, meta) in enumerate(categories):
            row = idx // 2
            col = idx % 2
            count = len(ToolRegistry.get_by_category(cat_id))

            card = ctk.CTkButton(
                grid_container,
                text=f"{meta['icon']}  {meta['name']}  ({count} Tools)\n{meta['desc']}",
                fg_color=Theme.SURFACE_CARD,
                hover_color=Theme.SURFACE_CARD_HOVER,
                text_color=Theme.TEXT_PRIMARY,
                border_width=1,
                border_color=Theme.BORDER_SUBTLE,
                corner_radius=Theme.RADIUS_CARD,
                anchor="w",
                font=(Theme.FONT_FAMILY, 13),
                height=72,
                command=lambda cid=cat_id: self.on_category_select(cid)
            )
            card.grid(row=row, column=col, padx=Theme.PAD_XS, pady=Theme.PAD_XS, sticky="ew")
