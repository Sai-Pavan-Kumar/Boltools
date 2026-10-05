"""Category tool gallery screen displaying all tools within a selected category."""

from typing import Callable
import customtkinter as ctk

from src.core.theme import Theme
from src.core.registry import ToolRegistry, ToolDefinition


class CategoryGallery(ctk.CTkScrollableFrame):
    """Grid display of all tools inside a specific domain category."""

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

        self.meta = ToolRegistry.CATEGORIES.get(category_id, {"name": category_id, "icon": "🛠️", "desc": ""})
        self.tools = ToolRegistry.get_by_category(category_id)

        self._build_header()
        self._build_grid()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=Theme.PAD_LG, pady=(Theme.PAD_LG, Theme.PAD_MD))

        title_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_row.pack(fill="x")

        title_lbl = ctk.CTkLabel(
            title_row,
            text=f"{self.meta['icon']}  {self.meta['name']}",
            font=(Theme.FONT_FAMILY, 22, "bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title_lbl.pack(side="left")

        count_badge = ctk.CTkLabel(
            title_row,
            text=f"{len(self.tools)} Tools Available",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.BRAND_ACCENT,
            anchor="e"
        )
        count_badge.pack(side="right")

        desc_lbl = ctk.CTkLabel(
            header_frame,
            text=self.meta['desc'],
            font=(Theme.FONT_FAMILY, 13),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        desc_lbl.pack(fill="x", pady=(2, 0))

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
                border_color=Theme.BORDER_SUBTLE
            )
            card.grid(row=row, column=col, padx=Theme.PAD_XS, pady=Theme.PAD_XS, sticky="nsew")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_MD)

            name_lbl = ctk.CTkLabel(
                inner,
                text=tool.name,
                font=(Theme.FONT_FAMILY, 14, "bold"),
                text_color=Theme.TEXT_PRIMARY,
                anchor="w",
                justify="left"
            )
            name_lbl.pack(fill="x")

            desc_lbl = ctk.CTkLabel(
                inner,
                text=tool.description,
                font=(Theme.FONT_FAMILY, 12),
                text_color=Theme.TEXT_SECONDARY,
                anchor="w",
                justify="left",
                wraplength=380
            )
            desc_lbl.pack(fill="x", pady=(Theme.PAD_XS, Theme.PAD_SM))

            action_row = ctk.CTkFrame(inner, fg_color="transparent")
            action_row.pack(fill="x")

            status_text = "READY TO LAUNCH" if tool.is_implemented else "UPCOMING"
            status_col = Theme.STATUS_SUCCESS if tool.is_implemented else Theme.TEXT_MUTED
            
            status_lbl = ctk.CTkLabel(
                action_row,
                text=status_text,
                font=(Theme.FONT_FAMILY, 10, "bold"),
                text_color=status_col,
                anchor="w"
            )
            status_lbl.pack(side="left")

            btn_open = ctk.CTkButton(
                action_row,
                text="Open Tool",
                fg_color=Theme.BRAND_PRIMARY if tool.is_implemented else Theme.SURFACE_INSET,
                hover_color=Theme.BRAND_HOVER,
                text_color=Theme.TEXT_PRIMARY,
                corner_radius=Theme.RADIUS_BUTTON,
                height=28,
                width=100,
                font=(Theme.FONT_FAMILY, 11, "bold"),
                command=lambda t=tool: self.on_tool_select(t)
            )
            btn_open.pack(side="right")
