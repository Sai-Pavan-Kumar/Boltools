"""Category tool gallery screen displaying active tools within a selected suite."""

from typing import Callable
import customtkinter as ctk

from src.core.theme import Theme
from src.core.registry import ToolRegistry, ToolDefinition


class CategoryGallery(ctk.CTkScrollableFrame):
    """Clean, unclipped grid of active tools inside a category suite."""

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

        self.meta = ToolRegistry.CATEGORIES.get(category_id, {"name": category_id, "desc": ""})
        self.tools = [t for t in ToolRegistry.get_by_category(category_id) if t.is_implemented]

        self._build_header()
        self._build_grid()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=Theme.PAD_LG, pady=(Theme.PAD_LG, Theme.PAD_MD))

        # Title row
        title_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_row.pack(fill="x")

        title_lbl = ctk.CTkLabel(
            title_row,
            text=self.meta["name"],
            font=Theme.FONT_HERO,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title_lbl.pack(side="left")

        desc_lbl = ctk.CTkLabel(
            header_frame,
            text=self.meta.get("desc", ""),
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        desc_lbl.pack(fill="x", pady=(2, 0))

    def _build_grid(self):
        if not self.tools:
            empty_frame = ctk.CTkFrame(self, fg_color=Theme.SURFACE_CARD, corner_radius=Theme.RADIUS_CARD, border_width=1, border_color=Theme.BORDER_SUBTLE)
            empty_frame.pack(fill="x", padx=Theme.PAD_LG, pady=Theme.PAD_LG)
            empty_lbl = ctk.CTkLabel(
                empty_frame,
                text="Tools for this suite are currently queued in upcoming modular drops.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MUTED
            )
            empty_lbl.pack(pady=Theme.PAD_XL)
            return

        grid_container = ctk.CTkFrame(self, fg_color="transparent")
        grid_container.pack(fill="x", padx=Theme.PAD_LG, pady=(0, Theme.PAD_LG))
        grid_container.grid_columnconfigure((0, 1), weight=1, uniform="tool_col")

        for idx, tool in enumerate(self.tools):
            row = idx // 2
            col = idx % 2
            card = self._create_card(grid_container, tool)
            card.grid(row=row, column=col, padx=Theme.PAD_XS, pady=Theme.PAD_XS, sticky="nsew")

    def _create_card(self, parent, tool: ToolDefinition) -> ctk.CTkFrame:
        tint_cfg = Theme.CATEGORY_COLORS.get(tool.category_id, {"accent": Theme.BRAND_PRIMARY, "bg": Theme.SURFACE_INSET})

        card = ctk.CTkFrame(
            parent,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            cursor="hand2"
        )

        inner = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        inner.pack(fill="both", expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_MD)

        # Header Row: Icon Squircle + Status
        hdr_row = ctk.CTkFrame(inner, fg_color="transparent", cursor="hand2")
        hdr_row.pack(fill="x", pady=(0, 4))

        ico_box = ctk.CTkLabel(
            hdr_row,
            text=getattr(tool, "icon", "⚡"),
            font=(Theme.FONT_FAMILY, 14),
            fg_color=tint_cfg["bg"],
            corner_radius=6,
            width=28,
            height=28,
            cursor="hand2"
        )
        ico_box.pack(side="left", padx=(0, 6))

        title = ctk.CTkLabel(
            hdr_row,
            text=tool.name,
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
            cursor="hand2"
        )
        title.pack(side="left")

        status_lbl = ctk.CTkLabel(
            hdr_row,
            text="● Ready",
            font=(Theme.FONT_FAMILY, 9, "bold"),
            text_color=Theme.STATUS_SUCCESS,
            anchor="e"
        )
        status_lbl.pack(side="right")

        # Description
        desc = ctk.CTkLabel(
            inner,
            text=tool.description,
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
            cursor="hand2",
            wraplength=340,
            justify="left"
        )
        desc.pack(fill="x", pady=(2, Theme.PAD_SM))

        # Bottom Action CTA Button (Clearly visible, never clipped)
        cta_row = ctk.CTkFrame(inner, fg_color="transparent", cursor="hand2")
        cta_row.pack(fill="x", pady=(4, 0))

        btn_launch = ctk.CTkButton(
            cta_row,
            text="Launch Utility  →",
            font=Theme.FONT_CAPTION,
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            text_color=Theme.TEXT_ON_BRAND,
            corner_radius=Theme.RADIUS_BUTTON,
            height=28,
            command=lambda t=tool: self.on_tool_select(t)
        )
        btn_launch.pack(side="left")

        for w in [card, inner, hdr_row, ico_box, title, desc, cta_row]:
            w.bind("<Button-1>", lambda e, t=tool: self.on_tool_select(t))

        return card
