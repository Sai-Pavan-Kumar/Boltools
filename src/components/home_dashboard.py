"""Home Dashboard view with Apple Bento-Grid hierarchy and discovery architecture."""

from typing import Callable
import customtkinter as ctk

from src.core.theme import Theme
from src.core.registry import ToolRegistry, ToolDefinition


class HomeDashboard(ctk.CTkScrollableFrame):
    """Default landing screen featuring Spotlight Hero, Quick-Launch Shelf, and Bento Domains."""

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
        self._build_domains_bento()

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
        inner.pack(fill="both", padx=Theme.PAD_XL, pady=Theme.PAD_XL)

        # Micro Pill Badge
        badge = ctk.CTkLabel(
            inner,
            text="BOLTOOLS DESKTOP SUITE  ·  100% LOCAL",
            font=Theme.FONT_LABEL,
            fg_color=Theme.SURFACE_PILL,
            text_color=Theme.BRAND_ACCENT,
            corner_radius=Theme.RADIUS_PILL,
            padx=12,
            pady=4
        )
        badge.pack(anchor="w", pady=(0, Theme.PAD_SM))

        # Title
        title = ctk.CTkLabel(
            inner,
            text="Swiss Army Knife for Creators & Power Users",
            font=Theme.FONT_DISPLAY,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title.pack(anchor="w")

        # Subtitle
        desc = ctk.CTkLabel(
            inner,
            text="57 specialized offline utilities. Zero monthly fees. Zero data leaks. Native performance on your machine.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=(4, Theme.PAD_MD))

        # Metrics Row
        stats_frame = ctk.CTkFrame(inner, fg_color="transparent")
        stats_frame.pack(anchor="w")

        metrics = [
            ("57", "Power Tools"),
            ("48", "Offline Engines"),
            ("9", "Web Harvesters"),
            ("₹0", "Forever Free")
        ]
        for val, lbl in metrics:
            item = ctk.CTkFrame(stats_frame, fg_color=Theme.SURFACE_INSET, corner_radius=Theme.RADIUS_BUTTON)
            item.pack(side="left", padx=(0, Theme.PAD_SM))
            
            val_lbl = ctk.CTkLabel(item, text=f" {val} ", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_PRIMARY)
            val_lbl.pack(side="left", padx=(8, 2), pady=4)
            
            sub_lbl = ctk.CTkLabel(item, text=f"{lbl} ", font=Theme.FONT_CAPTION, text_color=Theme.TEXT_MUTED)
            sub_lbl.pack(side="left", padx=(0, 8), pady=4)

    def _build_featured_shelf(self):
        """Displays quick-launch shortcut cards for highest-utility tools."""
        shelf_frame = ctk.CTkFrame(self, fg_color="transparent")
        shelf_frame.pack(fill="x", padx=Theme.PAD_LG, pady=(Theme.PAD_XS, Theme.PAD_MD))

        lbl = ctk.CTkLabel(
            shelf_frame,
            text="QUICK LAUNCH SHORTCUTS",
            font=Theme.FONT_LABEL,
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        lbl.pack(anchor="w", pady=(0, Theme.PAD_SM))

        cards_row = ctk.CTkFrame(shelf_frame, fg_color="transparent")
        cards_row.pack(fill="x")
        cards_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="shelf")

        quick_tool_ids = [
            ("pdf_first_page", "FIRST-PAGE PRINT", "PDF Studio"),
            ("image_webp_compress", "WEBP COMPRESS", "Image Lab"),
            ("creator_bolt_down", "STREAM HARVEST", "Creator Intel"),
            ("video_extractor", "AUDIO EXTRACTOR", "Video Studio")
        ]

        for idx, (tid, shortcut_name, suite_name) in enumerate(quick_tool_ids):
            tool = ToolRegistry.get(tid)
            if not tool:
                continue

            card = ctk.CTkFrame(
                cards_row,
                fg_color=Theme.SURFACE_CARD,
                corner_radius=Theme.RADIUS_CARD,
                border_width=1,
                border_color=Theme.BORDER_SUBTLE,
                cursor="hand2"
            )
            card.grid(row=0, column=idx, padx=Theme.PAD_XS, pady=Theme.PAD_XS, sticky="nsew")

            card_inner = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
            card_inner.pack(fill="both", expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_MD)

            tag_lbl = ctk.CTkLabel(
                card_inner,
                text=suite_name.upper(),
                font=Theme.FONT_CAPTION,
                text_color=Theme.TEXT_MUTED,
                anchor="w",
                cursor="hand2"
            )
            tag_lbl.pack(anchor="w")

            title_lbl = ctk.CTkLabel(
                card_inner,
                text=tool.name,
                font=Theme.FONT_BODY_BOLD,
                text_color=Theme.TEXT_PRIMARY,
                anchor="w",
                cursor="hand2"
            )
            title_lbl.pack(anchor="w", pady=(4, Theme.PAD_SM))

            action_row = ctk.CTkLabel(
                card_inner,
                text="Launch Engine  ↗",
                font=Theme.FONT_CAPTION,
                text_color=Theme.BRAND_ACCENT,
                anchor="w",
                cursor="hand2"
            )
            action_row.pack(anchor="w")

            # Click binding across entire card
            for w in [card, card_inner, tag_lbl, title_lbl, action_row]:
                w.bind("<Button-1>", lambda e, t=tool: self.on_tool_select(t))

    def _build_domains_bento(self):
        """Displays the 7 core domains in an Apple Bento-Grid layout."""
        domains_frame = ctk.CTkFrame(self, fg_color="transparent")
        domains_frame.pack(fill="x", padx=Theme.PAD_LG, pady=(Theme.PAD_SM, Theme.PAD_LG))

        lbl = ctk.CTkLabel(
            domains_frame,
            text="FUNCTIONAL SUITES & DOMAINS",
            font=Theme.FONT_LABEL,
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
            glyph = meta.get("glyph", "●")

            card = ctk.CTkFrame(
                grid_container,
                fg_color=Theme.SURFACE_CARD,
                corner_radius=Theme.RADIUS_CARD,
                border_width=1,
                border_color=Theme.BORDER_SUBTLE,
                cursor="hand2"
            )
            card.grid(row=row, column=col, padx=Theme.PAD_XS, pady=Theme.PAD_XS, sticky="nsew")

            card_inner = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
            card_inner.pack(fill="both", expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_MD)

            # Top Row: Glyph + Title + Count Pill
            top_row = ctk.CTkFrame(card_inner, fg_color="transparent", cursor="hand2")
            top_row.pack(fill="x")

            title_txt = f"{glyph}   {meta['name']}"
            t_lbl = ctk.CTkLabel(
                top_row,
                text=title_txt,
                font=Theme.FONT_SUBTITLE,
                text_color=Theme.TEXT_PRIMARY,
                anchor="w",
                cursor="hand2"
            )
            t_lbl.pack(side="left")

            count_pill = ctk.CTkLabel(
                top_row,
                text=f"{count} Tools",
                font=Theme.FONT_CAPTION,
                fg_color=Theme.SURFACE_PILL,
                text_color=Theme.TEXT_SECONDARY,
                corner_radius=Theme.RADIUS_PILL,
                padx=8,
                pady=2,
                cursor="hand2"
            )
            count_pill.pack(side="right")

            # Description
            desc_lbl = ctk.CTkLabel(
                card_inner,
                text=meta['desc'],
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_SECONDARY,
                anchor="w",
                cursor="hand2"
            )
            desc_lbl.pack(anchor="w", pady=(6, 0))

            # Bind click across entire card
            for w in [card, card_inner, top_row, t_lbl, count_pill, desc_lbl]:
                w.bind("<Button-1>", lambda e, cid=cat_id: self.on_category_select(cid))
