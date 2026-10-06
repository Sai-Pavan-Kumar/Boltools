"""Tool Directory & Modular In-App Hub for Boltools.

Displays all 100 power tools across 9 specialized suites.
Supports filtering by Installed vs Available, in-place installation,
smart 2-tier uninstalling, and access to Community Polls & Tool Requests.
"""

import tkinter as tk
from typing import Callable, List, Optional
import customtkinter as ctk

from src.core.theme import Theme
from src.core.registry import ToolRegistry, ToolDefinition
from src.core.community import community_service
from src.components.uninstall_modal import UninstallModal
from src.components.poll_modal import CommunityPollModal
from src.components.request_tool_modal import RequestToolModal


class ToolDirectoryView(ctk.CTkFrame):
    """Modern Apple-grade Tool Directory and App Store hub."""

    def __init__(self, master, on_select_tool: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=Theme.SURFACE_BASE, corner_radius=0, **kwargs)

        self.on_select_tool = on_select_tool
        self.active_status_filter = "all"  # "all" | "installed" | "available"
        self.active_cat_filter = "all"
        self.search_query = ""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Hero & Stats
        self.grid_rowconfigure(1, weight=0)  # Filter bar
        self.grid_rowconfigure(2, weight=1)  # Scrollable Tool Grid

        self._build_hero()
        self._build_filters()
        self._build_grid_container()
        self._render_tools()

    def _build_hero(self):
        """Top hero shelf with directory title, metrics, and community action buttons."""
        hero = ctk.CTkFrame(self, fg_color="transparent")
        hero.grid(row=0, column=0, sticky="ew", padx=Theme.PAD_LG, pady=(Theme.PAD_LG, Theme.PAD_SM))
        hero.grid_columnconfigure(0, weight=1)
        hero.grid_columnconfigure(1, weight=0)

        # Title block
        left_col = ctk.CTkFrame(hero, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="w")

        title_lbl = ctk.CTkLabel(
            left_col,
            text="Tool Hub & Directory",
            font=Theme.FONT_DISPLAY,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            left_col,
            text="Explore, install, and manage all 100 offline power tools across 9 specialized suites.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        sub_lbl.pack(anchor="w", pady=(2, Theme.PAD_SM))

        # Metrics Pills
        all_tools = ToolRegistry.get_all()
        installed_count = sum(1 for t in all_tools if community_service.get_tool_status(t.id, t.status) == "installed")
        available_count = len(all_tools) - installed_count

        pills_row = ctk.CTkFrame(left_col, fg_color="transparent")
        pills_row.pack(anchor="w")

        self.pill_installed = self._create_stat_pill(pills_row, f"● {installed_count} Installed", Theme.STATUS_SUCCESS)
        self.pill_installed.pack(side="left", padx=(0, Theme.PAD_SM))

        self.pill_available = self._create_stat_pill(pills_row, f"○ {available_count} In Hub / Next Drops", Theme.BRAND_PRIMARY)
        self.pill_available.pack(side="left", padx=(0, Theme.PAD_SM))

        pill_free = self._create_stat_pill(pills_row, "✓ ₹0 Free Forever", Theme.TEXT_MUTED)
        pill_free.pack(side="left")

        # Right Action Buttons
        actions_row = ctk.CTkFrame(hero, fg_color="transparent")
        actions_row.grid(row=0, column=1, sticky="e")

        btn_poll = ctk.CTkButton(
            actions_row,
            text="🗳️ Vote Next Drop",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.BRAND_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            height=34,
            command=self._open_poll_modal
        )
        btn_poll.pack(side="left", padx=(0, Theme.PAD_SM))

        btn_req = ctk.CTkButton(
            actions_row,
            text="💡 Request a Tool",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            height=34,
            command=self._open_request_modal
        )
        btn_req.pack(side="left")

    def _create_stat_pill(self, parent, text: str, color: tuple) -> ctk.CTkLabel:
        return ctk.CTkLabel(
            parent,
            text=text,
            font=Theme.FONT_CAPTION,
            fg_color=Theme.SURFACE_CARD,
            text_color=color,
            corner_radius=Theme.RADIUS_PILL,
            padx=10,
            pady=3
        )

    def _build_filters(self):
        """Search box and segmented filter controls."""
        bar = ctk.CTkFrame(self, fg_color=Theme.SURFACE_CARD, corner_radius=Theme.RADIUS_CARD, border_width=1, border_color=Theme.BORDER_SUBTLE)
        bar.grid(row=1, column=0, sticky="ew", padx=Theme.PAD_LG, pady=(0, Theme.PAD_MD))
        bar.grid_columnconfigure(0, weight=1)
        bar.grid_columnconfigure(1, weight=0)

        # Search Bar
        search_row = ctk.CTkFrame(bar, fg_color="transparent")
        search_row.grid(row=0, column=0, sticky="ew", padx=Theme.PAD_SM, pady=Theme.PAD_SM)
        search_row.grid_columnconfigure(1, weight=1)

        search_icon = ctk.CTkLabel(search_row, text="🔍", font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED)
        search_icon.grid(row=0, column=0, padx=(Theme.PAD_SM, Theme.PAD_XS))

        self.entry_search = ctk.CTkEntry(
            search_row,
            placeholder_text="Search 100 tools by name, number (e.g. 1.8), keyword...",
            font=Theme.FONT_BODY,
            fg_color="transparent",
            text_color=Theme.TEXT_PRIMARY,
            border_width=0,
            height=32
        )
        self.entry_search.grid(row=0, column=1, sticky="ew")
        self.entry_search.bind("<KeyRelease>", self._on_search_change)

        # Right segmented filters
        ctrl_row = ctk.CTkFrame(bar, fg_color="transparent")
        ctrl_row.grid(row=0, column=1, sticky="e", padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        self.seg_status = ctk.CTkSegmentedButton(
            ctrl_row,
            values=["All", "Installed", "In Hub"],
            font=Theme.FONT_LABEL,
            selected_color=Theme.BRAND_PRIMARY,
            selected_hover_color=Theme.BRAND_HOVER,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            command=self._on_status_filter_change
        )
        self.seg_status.set("All")
        self.seg_status.pack(side="left", padx=(0, Theme.PAD_SM))

        # Category Dropdown Filter
        cat_names = ["All Categories"] + [v["name"] for v in ToolRegistry.CATEGORIES.values()]
        self.cat_var = tk.StringVar(value="All Categories")
        self.combo_cat = ctk.CTkComboBox(
            ctrl_row,
            values=cat_names,
            variable=self.cat_var,
            font=Theme.FONT_BODY,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            width=180,
            height=32,
            command=self._on_cat_filter_change
        )
        self.combo_cat.pack(side="left")

    def _build_grid_container(self):
        """Scrollable frame hosting all tool cards."""
        self.scroll_canvas = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_canvas.grid(row=2, column=0, sticky="nsew", padx=Theme.PAD_LG, pady=(0, Theme.PAD_LG))
        self.scroll_canvas.grid_columnconfigure((0, 1), weight=1, uniform="tool_col")

    def _render_tools(self):
        """Filters and renders tool cards into 2-column responsive layout."""
        # Clear existing cards
        for widget in self.scroll_canvas.winfo_children():
            widget.destroy()

        all_tools = ToolRegistry.get_all()

        # Apply search
        filtered: List[ToolDefinition] = []
        if self.search_query:
            filtered = ToolRegistry.search(self.search_query)
        else:
            filtered = all_tools

        # Apply status filter
        if self.active_status_filter == "installed":
            filtered = [t for t in filtered if community_service.get_tool_status(t.id, t.status) == "installed"]
        elif self.active_status_filter == "available":
            filtered = [t for t in filtered if community_service.get_tool_status(t.id, t.status) != "installed"]

        # Apply category filter
        if self.active_cat_filter != "all":
            filtered = [t for t in filtered if t.category_name == self.active_cat_filter]

        if not filtered:
            empty_lbl = ctk.CTkLabel(
                self.scroll_canvas,
                text="No tools match your current filter. Try searching for another name or number.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MUTED
            )
            empty_lbl.grid(row=0, column=0, columnspan=2, pady=Theme.PAD_XL)
            return

        for idx, tool in enumerate(filtered):
            row = idx // 2
            col = idx % 2
            card = self._create_tool_card(self.scroll_canvas, tool)
            card.grid(row=row, column=col, sticky="nsew", padx=Theme.PAD_XS, pady=Theme.PAD_XS)

    def _create_tool_card(self, parent, tool: ToolDefinition) -> ctk.CTkFrame:
        """Constructs an individual Apple-grade tool card."""
        current_status = community_service.get_tool_status(tool.id, tool.status)
        is_installed = (current_status == "installed")

        card = ctk.CTkFrame(
            parent,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        card.grid_columnconfigure(0, weight=1)

        # Top Category & Status Bar
        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

        cat_badge = ctk.CTkLabel(
            top_row,
            text=f"{tool.glyph} {tool.category_name.upper()}",
            font=Theme.FONT_LABEL,
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        cat_badge.pack(side="left")

        # Status badge
        if is_installed:
            status_pill = ctk.CTkLabel(
                top_row,
                text="● READY",
                font=Theme.FONT_CAPTION,
                fg_color=Theme.SURFACE_INSET,
                text_color=Theme.STATUS_SUCCESS,
                corner_radius=Theme.RADIUS_PILL,
                padx=8,
                pady=2
            )
        else:
            status_pill = ctk.CTkLabel(
                top_row,
                text=f"○ DROP {tool.batch_drop}",
                font=Theme.FONT_CAPTION,
                fg_color=Theme.SURFACE_INSET,
                text_color=Theme.BRAND_PRIMARY,
                corner_radius=Theme.RADIUS_PILL,
                padx=8,
                pady=2
            )
        status_pill.pack(side="right")

        # Tool Title (Number + Name)
        title_text = f"{tool.num} {tool.name}"
        title_lbl = ctk.CTkLabel(
            card,
            text=title_text,
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_XS))

        # Description
        desc_lbl = ctk.CTkLabel(
            card,
            text=tool.description,
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            wraplength=380,
            justify="left",
            anchor="w"
        )
        desc_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        # Action Footer
        action_row = ctk.CTkFrame(card, fg_color="transparent")
        action_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        if is_installed:
            btn_launch = ctk.CTkButton(
                action_row,
                text="Open Tool ↗",
                font=Theme.FONT_BODY_BOLD,
                fg_color=Theme.BRAND_PRIMARY,
                hover_color=Theme.BRAND_HOVER,
                corner_radius=Theme.RADIUS_BUTTON,
                height=32,
                command=lambda tid=tool.id: self.on_select_tool(tid)
            )
            btn_launch.pack(side="left", fill="x", expand=True, padx=(0, Theme.PAD_SM))

            btn_uninstall = ctk.CTkButton(
                action_row,
                text="Remove",
                font=Theme.FONT_LABEL,
                fg_color=Theme.SURFACE_INSET,
                hover_color=Theme.SURFACE_CARD_HOVER,
                text_color=Theme.TEXT_MUTED,
                border_width=1,
                border_color=Theme.BORDER_SUBTLE,
                corner_radius=Theme.RADIUS_BUTTON,
                height=32,
                width=65,
                command=lambda tid=tool.id, tname=tool.name: self._open_uninstall_modal(tid, tname)
            )
            btn_uninstall.pack(side="right")
        else:
            btn_install = ctk.CTkButton(
                action_row,
                text="+ Install (Free)",
                font=Theme.FONT_BODY_BOLD,
                fg_color=Theme.SURFACE_INSET,
                hover_color=Theme.BRAND_HOVER,
                text_color=Theme.TEXT_PRIMARY,
                border_width=1,
                border_color=Theme.BORDER_SUBTLE,
                corner_radius=Theme.RADIUS_BUTTON,
                height=32,
                command=lambda tid=tool.id: self._install_tool(tid)
            )
            btn_install.pack(fill="x")

        return card

    def _install_tool(self, tool_id: str):
        community_service.install_tool(tool_id)
        self._refresh_metrics()
        self._render_tools()

    def _open_uninstall_modal(self, tool_id: str, tool_name: str):
        UninstallModal(self.winfo_toplevel(), tool_id=tool_id, tool_name=tool_name, on_success=self._on_uninstalled)

    def _on_uninstalled(self):
        self._refresh_metrics()
        self._render_tools()

    def _refresh_metrics(self):
        all_tools = ToolRegistry.get_all()
        installed_count = sum(1 for t in all_tools if community_service.get_tool_status(t.id, t.status) == "installed")
        available_count = len(all_tools) - installed_count
        self.pill_installed.configure(text=f"● {installed_count} Installed")
        self.pill_available.configure(text=f"○ {available_count} In Hub / Next Drops")

    def _open_poll_modal(self):
        CommunityPollModal(self.winfo_toplevel())

    def _open_request_modal(self):
        RequestToolModal(self.winfo_toplevel())

    def _on_search_change(self, event=None):
        self.search_query = self.entry_search.get().strip()
        self._render_tools()

    def _on_status_filter_change(self, value: str):
        mapping = {"All": "all", "Installed": "installed", "In Hub": "available"}
        self.active_status_filter = mapping.get(value, "all")
        self._render_tools()

    def _on_cat_filter_change(self, value: str):
        self.active_cat_filter = "all" if value == "All Categories" else value
        self._render_tools()
