"""Tool Hub & Utility Catalog for Boltools.

Features:
- Apple Pro / Linear minimalist desktop standards
- High information density with zero clipped labels
- 3 Segmented Filter Tabs: All Utilities, Installed (Ready), Hub Catalog
- Status Badges: Ready Offline vs Available in Hub
- macOS-style 2-Tier Uninstall decision triggering UninstallModal
- Instant Free Install action for catalog utilities
- Search & category filtering
"""

from typing import Callable, List, Optional
import customtkinter as ctk

from src.core.theme import Theme
from src.core.registry import ToolRegistry, ToolDefinition
from src.core.community import community_service
from src.components.uninstall_modal import UninstallModal


class ToolDirectoryView(ctk.CTkFrame):
    """Elevated Tool Hub managing offline tools, catalog discovery, and tool lifecycles."""

    def __init__(self, master, on_select_tool: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=Theme.SURFACE_BASE, corner_radius=0, **kwargs)

        self.on_select_tool = on_select_tool
        self.search_query = ""
        self.filter_tab = "All"  # "All", "Installed", "Catalog"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Hero
        self.grid_rowconfigure(1, weight=0)  # Filter & Search bar
        self.grid_rowconfigure(2, weight=1)  # Grid canvas

        self._build_hero()
        self._build_filter_bar()
        self._build_grid()

    def _build_hero(self):
        hero = ctk.CTkFrame(self, fg_color="transparent")
        hero.grid(row=0, column=0, sticky="ew", padx=Theme.PAD_LG, pady=(Theme.PAD_LG, Theme.PAD_SM))

        title = ctk.CTkLabel(
            hero,
            text="Tool Hub",
            font=Theme.FONT_HERO,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title.pack(anchor="w")

        sub = ctk.CTkLabel(
            hero,
            text="Browse, launch, and manage offline utility modules on your PC.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        sub.pack(anchor="w", pady=(2, 0))

    def _build_filter_bar(self):
        bar = ctk.CTkFrame(
            self,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        bar.grid(row=1, column=0, sticky="ew", padx=Theme.PAD_LG, pady=(0, Theme.PAD_MD))
        bar.grid_columnconfigure(0, weight=0)
        bar.grid_columnconfigure(1, weight=1)

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        # Segmented Filter Tabs
        self.seg_filter = ctk.CTkSegmentedButton(
            inner,
            values=["All", "Installed", "Hub Catalog"],
            command=self._on_tab_change,
            font=Theme.FONT_BODY_BOLD,
            selected_color=Theme.BRAND_PRIMARY,
            selected_hover_color=Theme.BRAND_HOVER,
            unselected_color=Theme.SURFACE_INSET,
            unselected_hover_color=Theme.SURFACE_CARD_HOVER,
            height=32
        )
        self.seg_filter.set("All")
        self.seg_filter.pack(side="left", padx=(0, Theme.PAD_MD))

        # Search Input Field
        self.entry_search = ctk.CTkEntry(
            inner,
            placeholder_text="Filter utilities by name, suite, or keyword...",
            font=Theme.FONT_BODY,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            placeholder_text_color=Theme.TEXT_MUTED,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=32
        )
        self.entry_search.pack(side="left", fill="x", expand=True)
        self.entry_search.bind("<KeyRelease>", self._on_search_type)

    def _build_grid(self):
        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll_canvas.grid(row=2, column=0, sticky="nsew", padx=Theme.PAD_LG, pady=(0, Theme.PAD_LG))
        self.scroll_canvas.grid_columnconfigure((0, 1), weight=1, uniform="tool_col")
        self._render_tools()

    def _on_tab_change(self, selected_tab: str):
        self.filter_tab = selected_tab
        self._render_tools()

    def _on_search_type(self, event):
        self.search_query = self.entry_search.get().strip().lower()
        self._render_tools()

    def _render_tools(self):
        for w in self.scroll_canvas.winfo_children():
            w.destroy()

        # Query from registry
        all_tools = ToolRegistry.search(self.search_query) if self.search_query else ToolRegistry.get_all()

        # Filter by Tab
        filtered_tools: List[ToolDefinition] = []
        for t in all_tools:
            # Check override status in community service
            status = community_service.get_tool_status(t.id, "installed" if t.is_implemented else "available")
            is_installed = (status == "installed")

            if self.filter_tab == "Installed" and not is_installed:
                continue
            if self.filter_tab == "Hub Catalog" and is_installed:
                continue
            filtered_tools.append(t)

        if not filtered_tools:
            empty_box = ctk.CTkFrame(self.scroll_canvas, fg_color=Theme.SURFACE_CARD, corner_radius=Theme.RADIUS_CARD, border_width=1, border_color=Theme.BORDER_SUBTLE)
            empty_box.grid(row=0, column=0, columnspan=2, sticky="ew", pady=Theme.PAD_XL, padx=Theme.PAD_SM)
            
            lbl = ctk.CTkLabel(
                empty_box,
                text="No utilities match your filter query.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MUTED
            )
            lbl.pack(pady=Theme.PAD_LG)
            return

        for idx, tool in enumerate(filtered_tools):
            row = idx // 2
            col = idx % 2
            card = self._create_card(self.scroll_canvas, tool)
            card.grid(row=row, column=col, sticky="nsew", padx=Theme.PAD_XS, pady=Theme.PAD_XS)

    def _create_card(self, parent, tool: ToolDefinition) -> ctk.CTkFrame:
        status = community_service.get_tool_status(tool.id, "installed" if tool.is_implemented else "available")
        is_installed = (status == "installed")
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

        # ── Top Row: Category Icon Squircle + Suite Badge + Status Pill
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 6))

        ico_lbl = ctk.CTkLabel(
            top_row,
            text=getattr(tool, "icon", "⚡"),
            font=(Theme.FONT_FAMILY, 14),
            fg_color=tint_cfg["bg"],
            corner_radius=6,
            width=30,
            height=30
        )
        ico_lbl.pack(side="left", padx=(0, 8))

        suite_badge = ctk.CTkLabel(
            top_row,
            text=tool.category_name.upper(),
            font=(Theme.FONT_FAMILY, 9, "bold"),
            text_color=tint_cfg["accent"],
            fg_color=tint_cfg["bg"],
            corner_radius=Theme.RADIUS_PILL,
            padx=7,
            pady=2
        )
        suite_badge.pack(side="left")

        # Status badge (Right)
        if is_installed:
            st_badge = ctk.CTkLabel(
                top_row,
                text="● Ready Offline",
                font=(Theme.FONT_FAMILY, 9, "bold"),
                text_color=Theme.STATUS_SUCCESS,
                fg_color=Theme.SURFACE_PILL,
                corner_radius=Theme.RADIUS_PILL,
                padx=8,
                pady=2
            )
        else:
            st_badge = ctk.CTkLabel(
                top_row,
                text="In Catalog",
                font=(Theme.FONT_FAMILY, 9),
                text_color=Theme.TEXT_MUTED,
                fg_color=Theme.SURFACE_PILL,
                corner_radius=Theme.RADIUS_PILL,
                padx=8,
                pady=2
            )
        st_badge.pack(side="right")

        # ── Title & Description
        title = ctk.CTkLabel(
            inner,
            text=tool.name,
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title.pack(fill="x", pady=(2, 0))

        desc = ctk.CTkLabel(
            inner,
            text=tool.description,
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
            wraplength=320,
            justify="left"
        )
        desc.pack(fill="x", pady=(3, Theme.PAD_SM))

        # ── Bottom Action Row
        action_row = ctk.CTkFrame(inner, fg_color="transparent")
        action_row.pack(fill="x", pady=(4, 0))

        if is_installed:
            # Open Tool Button
            btn_launch = ctk.CTkButton(
                action_row,
                text="Open Tool  →",
                font=Theme.FONT_CAPTION,
                fg_color=Theme.BRAND_PRIMARY,
                hover_color=Theme.BRAND_HOVER,
                text_color=Theme.TEXT_ON_BRAND,
                corner_radius=Theme.RADIUS_BUTTON,
                height=28,
                command=lambda tid=tool.id: self.on_select_tool(tid)
            )
            btn_launch.pack(side="left")

            # 2-Tier Uninstall Button (Triggers UninstallModal)
            btn_uninstall = ctk.CTkButton(
                action_row,
                text="Uninstall",
                font=Theme.FONT_CAPTION,
                fg_color="transparent",
                hover_color=Theme.SURFACE_INSET,
                text_color=Theme.TEXT_MUTED,
                border_width=1,
                border_color=Theme.BORDER_SUBTLE,
                corner_radius=Theme.RADIUS_BUTTON,
                height=28,
                width=70,
                command=lambda t=tool: self._open_uninstall_modal(t)
            )
            btn_uninstall.pack(side="right")
        else:
            # Install Button (Unlocks module)
            btn_install = ctk.CTkButton(
                action_row,
                text="+ Install (Free)",
                font=Theme.FONT_CAPTION,
                fg_color=Theme.SURFACE_INSET,
                hover_color=Theme.SURFACE_CARD_HOVER,
                text_color=Theme.TEXT_PRIMARY,
                border_width=1,
                border_color=Theme.BORDER_SUBTLE,
                corner_radius=Theme.RADIUS_BUTTON,
                height=28,
                command=lambda tid=tool.id: self._install_tool(tid)
            )
            btn_install.pack(side="left")

        return card

    def _open_uninstall_modal(self, tool: ToolDefinition):
        """Presents user with 2-tier uninstall modal: Keep Work vs Complete Purge."""
        UninstallModal(
            master=self.winfo_toplevel(),
            tool_id=tool.id,
            tool_name=tool.name,
            on_success=self._render_tools
        )

    def _install_tool(self, tool_id: str):
        """Installs tool into local environment and updates display."""
        community_service.install_tool(tool_id)
        self._render_tools()
