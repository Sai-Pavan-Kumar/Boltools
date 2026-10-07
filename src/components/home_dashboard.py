"""Clean, high-density Home Dashboard for Boltools.

Enforces:
- Linear / Apple Pro information density with rich visual category squircles
- 100% truthful data (all 4 active offline utility categories)
- Interactive category routing and instant utility launch cards
"""

from typing import Callable, Optional
import customtkinter as ctk

from src.core.theme import Theme
from src.core.registry import ToolRegistry, ToolDefinition


class HomeDashboard(ctk.CTkScrollableFrame):
    """Minimalist landing workspace featuring visual suite categories and instant launch utilities."""

    def __init__(
        self,
        master,
        on_tool_select: Callable[[ToolDefinition], None],
        on_category_select: Callable[[str], None],
        on_directory_click: Optional[Callable[[], None]] = None,
        on_poll_click: Optional[Callable[[], None]] = None,
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
        self.on_directory_click = on_directory_click
        self.on_poll_click = on_poll_click

        self._build_header_shelf()
        self._build_compact_categories()
        self._build_utilities_shelf()

    def _build_header_shelf(self):
        """Top workspace banner with clean typography and zero hype fluff."""
        header_box = ctk.CTkFrame(
            self,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        header_box.pack(fill="x", padx=Theme.PAD_LG, pady=(Theme.PAD_LG, Theme.PAD_MD))

        inner = ctk.CTkFrame(header_box, fg_color="transparent")
        inner.pack(fill="both", padx=Theme.PAD_LG, pady=Theme.PAD_MD)

        title = ctk.CTkLabel(
            inner,
            text="Desktop Workspace",
            font=Theme.FONT_HERO,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title.pack(anchor="w")

        desc = ctk.CTkLabel(
            inner,
            text="High-performance, private desktop utilities. All processing runs 100% locally on your PC.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=(2, 0))

    def _build_compact_categories(self):
        """Categories grid with dedicated colored squircles and tool counters."""
        cat_section = ctk.CTkFrame(self, fg_color="transparent")
        cat_section.pack(fill="x", padx=Theme.PAD_LG, pady=(0, Theme.PAD_MD))

        header_row = ctk.CTkFrame(cat_section, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, Theme.PAD_XS))

        lbl = ctk.CTkLabel(
            header_row,
            text="CATEGORIES",
            font=(Theme.FONT_FAMILY, 10, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        lbl.pack(side="left")

        if self.on_directory_click:
            btn_hub = ctk.CTkButton(
                header_row,
                text="Open Tool Hub ›",
                font=Theme.FONT_CAPTION,
                fg_color="transparent",
                hover_color=Theme.SURFACE_CARD_HOVER,
                text_color=Theme.BRAND_PRIMARY,
                height=22,
                command=self.on_directory_click
            )
            btn_hub.pack(side="right")

        grid = ctk.CTkFrame(cat_section, fg_color="transparent")
        grid.pack(fill="x")
        grid.grid_columnconfigure((0, 1), weight=1, uniform="cats")

        active_categories = [
            ("video", "Video & Media", "▶", Theme.CAT_VIDEO, "Compression, extraction & conversion"),
            ("pdf", "Documents & PDF", "📄", Theme.CAT_DOCS, "Conversion, merge, split & security"),
            ("image", "Images & Visuals", "🖼", Theme.CAT_IMAGE, "WebP compression & batch resizing"),
            ("system", "System & Files", "⚡", Theme.CAT_SYSTEM, "Batch renaming & extension organization"),
        ]

        for idx, (cid, name, glyph, accent, desc) in enumerate(active_categories):
            row = idx // 2
            col = idx % 2
            self._render_compact_category(grid, row, col, cid, name, glyph, accent, desc)

    def _render_compact_category(self, parent, row: int, col: int, cid: str, name: str, glyph: str, accent, desc: str):
        card = ctk.CTkFrame(
            parent,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            cursor="hand2",
            height=72
        )
        card.grid(row=row, column=col, padx=Theme.PAD_XS, pady=Theme.PAD_XS, sticky="nsew")
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        inner.pack(fill="both", expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_SM)

        # Icon box in rounded squircle
        ico_box = ctk.CTkLabel(
            inner,
            text=glyph,
            font=(Theme.FONT_FAMILY, 15, "bold"),
            fg_color=Theme.SURFACE_INSET,
            text_color=accent,
            corner_radius=8,
            width=38,
            height=38,
            cursor="hand2"
        )
        ico_box.pack(side="left", padx=(0, Theme.PAD_SM))

        # Center text
        left_col = ctk.CTkFrame(inner, fg_color="transparent", cursor="hand2")
        left_col.pack(side="left", fill="both", expand=True)

        t_lbl = ctk.CTkLabel(
            left_col,
            text=name,
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
            cursor="hand2"
        )
        t_lbl.pack(fill="x")

        d_lbl = ctk.CTkLabel(
            left_col,
            text=desc,
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_MUTED,
            anchor="w",
            cursor="hand2"
        )
        d_lbl.pack(fill="x", pady=(1, 0))

        # Right chevron
        chev = ctk.CTkLabel(
            inner,
            text="›",
            font=(Theme.FONT_FAMILY, 16, "bold"),
            text_color=Theme.TEXT_MUTED,
            cursor="hand2"
        )
        chev.pack(side="right")

        for w in [card, inner, ico_box, left_col, t_lbl, d_lbl, chev]:
            w.bind("<Button-1>", lambda e, c=cid: self.on_category_select(c))

    def _build_utilities_shelf(self):
        """Displays primary available offline utilities in high-density Linear-style cards."""
        shelf = ctk.CTkFrame(self, fg_color="transparent")
        shelf.pack(fill="x", padx=Theme.PAD_LG, pady=(0, Theme.PAD_LG))

        lbl = ctk.CTkLabel(
            shelf,
            text="AVAILABLE UTILITIES",
            font=(Theme.FONT_FAMILY, 10, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        lbl.pack(fill="x", pady=(0, Theme.PAD_XS))

        # List container
        list_card = ctk.CTkFrame(
            shelf,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        list_card.pack(fill="x")

        # Get implemented tools only
        implemented = [t for t in ToolRegistry.get_all() if t.is_implemented]

        if not implemented:
            empty_lbl = ctk.CTkLabel(
                list_card,
                text="No utilities currently loaded. Shell is ready for module integration.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MUTED
            )
            empty_lbl.pack(pady=Theme.PAD_LG)
            return

        cat_glyphs = {
            "video": "▶",
            "pdf": "📄",
            "image": "🖼",
            "system": "⚡",
        }

        for idx, tool in enumerate(implemented):
            row = ctk.CTkFrame(list_card, fg_color="transparent", height=54, cursor="hand2")
            row.pack(fill="x", padx=Theme.PAD_MD, pady=2)
            row.pack_propagate(False)

            # Left squircle icon
            g = cat_glyphs.get(tool.category_id, "⚡")
            ico = ctk.CTkLabel(
                row,
                text=g,
                font=(Theme.FONT_FAMILY, 13, "bold"),
                fg_color=Theme.SURFACE_INSET,
                text_color=Theme.BRAND_PRIMARY,
                corner_radius=6,
                width=32,
                height=32,
                cursor="hand2"
            )
            ico.pack(side="left", padx=(0, Theme.PAD_SM))

            left = ctk.CTkFrame(row, fg_color="transparent", cursor="hand2")
            left.pack(side="left", fill="both", expand=True)

            top_row = ctk.CTkFrame(left, fg_color="transparent", cursor="hand2")
            top_row.pack(fill="x")

            name = ctk.CTkLabel(
                top_row,
                text=tool.name,
                font=Theme.FONT_BODY_BOLD,
                text_color=Theme.TEXT_PRIMARY,
                anchor="w",
                cursor="hand2"
            )
            name.pack(side="left", padx=(0, Theme.PAD_SM))

            cat_pill = ctk.CTkLabel(
                top_row,
                text=tool.category_name,
                font=(Theme.FONT_FAMILY, 9),
                fg_color=Theme.SURFACE_PILL,
                text_color=Theme.TEXT_MUTED,
                corner_radius=Theme.RADIUS_PILL,
                padx=6,
                pady=1,
                cursor="hand2"
            )
            cat_pill.pack(side="left")

            desc = ctk.CTkLabel(
                left,
                text=tool.description,
                font=Theme.FONT_CAPTION,
                text_color=Theme.TEXT_MUTED,
                anchor="w",
                cursor="hand2"
            )
            desc.pack(fill="x", pady=(1, 0))

            btn_open = ctk.CTkButton(
                row,
                text="Launch Utility →",
                font=Theme.FONT_CAPTION,
                fg_color=Theme.BRAND_PRIMARY,
                hover_color=Theme.BRAND_HOVER,
                text_color=Theme.TEXT_ON_BRAND,
                corner_radius=Theme.RADIUS_BUTTON,
                height=28,
                width=110,
                command=lambda t=tool: self.on_tool_select(t)
            )
            btn_open.pack(side="right")

            for w in [row, ico, left, top_row, name, cat_pill, desc]:
                w.bind("<Button-1>", lambda e, t=tool: self.on_tool_select(t))

            # Separator between rows
            if idx < len(implemented) - 1:
                sep = ctk.CTkFrame(list_card, fg_color=Theme.BORDER_SUBTLE, height=1)
                sep.pack(fill="x", padx=Theme.PAD_MD)
