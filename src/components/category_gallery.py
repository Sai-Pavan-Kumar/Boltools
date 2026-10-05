"""Category tool gallery screen displaying all tools within a selected category."""

from typing import Callable
import customtkinter as ctk

from src.core.theme import Theme
from src.core.registry import ToolRegistry, ToolDefinition


class CategoryGallery(ctk.CTkScrollableFrame):
    """Grid display of all tools inside a specific domain category with Apple card aesthetics."""

    def __init__(
        self,
        master,
        category_id: str,
        on_tool_select: Callable[[ToolDefinition], None],
        on_back: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, fg_color=Theme.SURFACE_BASE, corner_radius=0, **kwargs)

        self.category_id = category_id
        self.on_tool_select = on_tool_select
        self.on_back = on_back

        self.meta = ToolRegistry.CATEGORIES.get(category_id, {"name": category_id, "glyph": "◈", "desc": ""})
        self.tools = ToolRegistry.get_by_category(category_id)

        self._build_header()
        self._build_grid()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=Theme.PAD_LG, pady=(Theme.PAD_LG, Theme.PAD_MD))

        # Back link
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Back to Home",
            fg_color="transparent",
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            font=Theme.FONT_CAPTION,
            height=24,
            width=120,
            anchor="w",
            command=self.on_back
        )
        back_btn.pack(anchor="w", pady=(0, Theme.PAD_XS))

        # Title row
        title_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_row.pack(fill="x")

        glyph = self.meta.get("glyph", "◈")
        title_lbl = ctk.CTkLabel(
            title_row,
            text=f"{glyph}   {self.meta['name']}",
            font=Theme.FONT_DISPLAY,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title_lbl.pack(side="left")

        count_badge = ctk.CTkLabel(
            title_row,
            text=f"{len(self.tools)} Tools Available",
            font=Theme.FONT_LABEL,
            fg_color=Theme.SURFACE_PILL,
            text_color=Theme.BRAND_ACCENT,
            corner_radius=Theme.RADIUS_PILL,
            padx=12,
            pady=4
        )
        count_badge.pack(side="right")

        desc_lbl = ctk.CTkLabel(
            header_frame,
            text=self.meta['desc'],
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        desc_lbl.pack(fill="x", pady=(4, 0))

    def _build_grid(self):
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="x", padx=Theme.PAD_LG, pady=(0, Theme.PAD_LG))
        grid_frame.grid_columnconfigure((0, 1), weight=1, uniform="tool_col")

        for idx, tool in enumerate(self.tools):
            row = idx // 2
            col = idx % 2

            card = ctk.CTkFrame(
                grid_frame,
                fg_color=Theme.SURFACE_CARD,
                corner_radius=Theme.RADIUS_CARD,
                border_width=1,
                border_color=Theme.BORDER_SUBTLE,
                cursor="hand2"
            )
            card.grid(row=row, column=col, padx=Theme.PAD_XS, pady=Theme.PAD_XS, sticky="nsew")

            inner = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
            inner.pack(fill="both", expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_MD)

            # Top: Status Pill
            top_bar = ctk.CTkFrame(inner, fg_color="transparent", cursor="hand2")
            top_bar.pack(fill="x")

            status_text = "● READY" if tool.is_implemented else "○ COMING SOON"
            status_col = Theme.STATUS_SUCCESS if tool.is_implemented else Theme.TEXT_MUTED

            status_lbl = ctk.CTkLabel(
                top_bar,
                text=status_text,
                font=Theme.FONT_CAPTION,
                text_color=status_col,
                anchor="w",
                cursor="hand2"
            )
            status_lbl.pack(side="left")

            name_lbl = ctk.CTkLabel(
                inner,
                text=tool.name,
                font=Theme.FONT_SUBTITLE,
                text_color=Theme.TEXT_PRIMARY,
                anchor="w",
                justify="left",
                cursor="hand2"
            )
            name_lbl.pack(fill="x", pady=(Theme.PAD_XS, 2))

            desc_lbl = ctk.CTkLabel(
                inner,
                text=tool.description,
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_SECONDARY,
                anchor="w",
                justify="left",
                wraplength=380,
                cursor="hand2"
            )
            desc_lbl.pack(fill="x", pady=(0, Theme.PAD_MD))

            action_row = ctk.CTkFrame(inner, fg_color="transparent", cursor="hand2")
            action_row.pack(fill="x")

            launch_btn = ctk.CTkButton(
                action_row,
                text="Open Tool  ↗",
                fg_color=Theme.BRAND_PRIMARY if tool.is_implemented else Theme.SURFACE_INSET,
                hover_color=Theme.BRAND_HOVER,
                text_color=Theme.TEXT_ON_BRAND if tool.is_implemented else Theme.TEXT_MUTED,
                corner_radius=Theme.RADIUS_BUTTON,
                height=32,
                font=Theme.FONT_BODY_BOLD,
                command=lambda t=tool: self.on_tool_select(t)
            )
            launch_btn.pack(side="right")

            # Bind entire card click to open tool
            for w in [card, inner, top_bar, status_lbl, name_lbl, desc_lbl]:
                w.bind("<Button-1>", lambda e, t=tool: self.on_tool_select(t))
