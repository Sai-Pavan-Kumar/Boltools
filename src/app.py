"""Main Desktop Application Shell for Boltools.

Enforces:
- Apple Pro / Linear-grade dark theme
- 3-Layer UX Discovery
- Lazy-mounted tool frames
- Non-blocking async execution
"""

import os
import sys
import tkinter as tk
from typing import Optional, Dict
import customtkinter as ctk

# Ensure 'src' is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.core.theme import Theme
from src.core.paths import get_asset_path, get_data_path, get_base_dir
from src.core.registry import ToolRegistry, ToolDefinition
from src.core.worker import AsyncWorker
from src.core.announcements import announcement_service
from src.core.community import community_service
from src.components.header import AppHeader
from src.components.sidebar import AppSidebar
from src.components.home_dashboard import HomeDashboard
from src.components.category_gallery import CategoryGallery
from src.components.command_palette import CommandPalette
from src.components.notification_modal import NotificationModal
from src.components.tool_directory import ToolDirectoryView
from src.components.poll_modal import CommunityPollModal
from src.components.request_tool_modal import RequestToolModal


class BoltoolsApp(ctk.CTk):
    """Primary application window and view controller."""

    def __init__(self):
        super().__init__()

        # Theme Initialization
        Theme.apply_appearance()

        # Window Setup
        self.title("Boltools — Built by The SurfBoard")
        self.geometry("1240x820")
        self.minsize(1040, 680)
        self.configure(fg_color=Theme.SURFACE_BASE)

        # Asset Paths
        self.assets_dir = get_asset_path()

        # Runtime State
        self.worker = AsyncWorker()
        self.active_frame: Optional[ctk.CTkFrame] = None
        self.tool_cache: Dict[str, ctk.CTkFrame] = {}

        # Layout Grids (Row 0: Header, Row 1: Sidebar + Content)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._build_shell()
        self._bind_global_shortcuts()
        self.show_home()
        self._init_announcements()

        # Protocol for clean background thread termination
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_shell(self):
        # Top Header Bar
        self.header = AppHeader(
            self,
            assets_dir=self.assets_dir,
            on_search_click=self.open_command_palette,
            on_home_click=self.show_home,
            on_notification_click=self.open_notification_modal
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")

        # Left Sidebar Navigation
        self.sidebar = AppSidebar(
            self,
            on_select_category=self.show_category,
            on_select_home=self.show_home,
            on_select_directory=self.show_directory
        )
        self.sidebar.grid(row=1, column=0, sticky="nsew")

        # Main Content Canvas (Hosts Home, Galleries & Tools)
        self.content_area = ctk.CTkFrame(self, fg_color=Theme.SURFACE_BASE, corner_radius=0)
        self.content_area.grid(row=1, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

    def _bind_global_shortcuts(self):
        # Raycast-style Ctrl+K search palette
        self.bind("<Control-k>", lambda e: self.open_command_palette())
        self.bind("<Control-K>", lambda e: self.open_command_palette())

    def _set_active_content(self, frame: ctk.CTkFrame):
        if self.active_frame is not None:
            self.active_frame.grid_forget()
        self.active_frame = frame
        self.active_frame.grid(row=0, column=0, sticky="nsew")

    def show_home(self):
        self.header.set_breadcrumb(["Home"])
        self.sidebar.active_category = None
        self.sidebar._update_button_states("home")
        home = HomeDashboard(
            self.content_area,
            on_tool_select=self.show_tool,
            on_category_select=self.show_category,
            on_directory_click=self.show_directory,
            on_poll_click=self.open_poll_modal
        )
        self._set_active_content(home)

    def show_directory(self):
        self.header.set_breadcrumb(["Home", "Tool Directory"])
        self.sidebar.active_category = None
        self.sidebar._update_button_states("directory")
        directory_view = ToolDirectoryView(
            self.content_area,
            on_select_tool=self.show_tool_by_id
        )
        self._set_active_content(directory_view)

    def show_tool_by_id(self, tool_id: str):
        tool = ToolRegistry.get(tool_id)
        if tool:
            self.show_tool(tool)

    def show_category(self, category_id: str):
        meta = ToolRegistry.CATEGORIES.get(category_id, {})
        cat_name = meta.get("name", category_id)
        self.header.set_breadcrumb(["Home", cat_name])
        self.sidebar.active_category = category_id
        self.sidebar._update_button_states(category_id)
        gallery = CategoryGallery(
            self.content_area,
            category_id=category_id,
            on_tool_select=self.show_tool,
            on_back=self.show_home
        )
        self._set_active_content(gallery)

    def show_tool(self, tool: ToolDefinition):
        self.header.set_breadcrumb(["Home", tool.category_name, tool.name])
        self.sidebar.active_category = tool.category_id
        self.sidebar._update_button_states()

        # Lazy instantiate or pull from cache
        if tool.id in self.tool_cache:
            self._set_active_content(self.tool_cache[tool.id])
            return

        if tool.factory:
            frame_class = tool.factory()
            tool_frame = frame_class(self.content_area)
            self.tool_cache[tool.id] = tool_frame
            self._set_active_content(tool_frame)
        else:
            # Placeholder frame for tools queued in upcoming migration batches
            placeholder = self._create_placeholder_frame(tool)
            self._set_active_content(placeholder)

    def _create_placeholder_frame(self, tool: ToolDefinition) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content_area, fg_color=Theme.SURFACE_BASE)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(
            frame,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            width=540,
            height=280
        )
        card.grid(row=0, column=0)
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(expand=True, padx=Theme.PAD_LG, pady=Theme.PAD_LG)

        title = ctk.CTkLabel(
            inner,
            text=tool.name,
            font=(Theme.FONT_FAMILY, 18, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title.pack(pady=(0, Theme.PAD_XS))

        cat_lbl = ctk.CTkLabel(
            inner,
            text=f"Module: {tool.category_name}",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.BRAND_ACCENT
        )
        cat_lbl.pack(pady=(0, Theme.PAD_SM))

        desc = ctk.CTkLabel(
            inner,
            text=tool.description,
            font=(Theme.FONT_FAMILY, 13),
            text_color=Theme.TEXT_SECONDARY,
            wraplength=460
        )
        desc.pack(pady=(0, Theme.PAD_LG))

        btn_back = ctk.CTkButton(
            inner,
            text="← Return to Dashboard",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            command=self.show_home
        )
        btn_back.pack()

        return frame

    def open_command_palette(self):
        CommandPalette(self, on_tool_select=self.show_tool)

    def open_notification_modal(self):
        """Displays the announcement hub popover and resets the unread count badge."""
        NotificationModal(self, on_close=lambda: self.header.set_unread_notifications(0))
        self.header.set_unread_notifications(0)

    def open_poll_modal(self):
        """Opens community roadmap voting modal."""
        CommunityPollModal(self)

    def open_request_modal(self):
        """Opens tool request modal."""
        RequestToolModal(self)

    def _init_announcements(self):
        """Checks for remote announcements and community polls silently on background threads."""
        def _on_complete(unread_count: int):
            try:
                self.after(0, lambda: self.header.set_unread_notifications(unread_count))
            except Exception:
                pass

        announcement_service.fetch_async(_on_complete)
        community_service.fetch_poll()

    def _on_close(self):
        self.worker.shutdown()
        self.destroy()


def main():
    app = BoltoolsApp()
    app.mainloop()


if __name__ == "__main__":
    main()
