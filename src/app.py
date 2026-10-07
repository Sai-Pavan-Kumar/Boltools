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
from src.components.favorites_view import FavoritesView
from src.components.settings_view import SettingsView
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

        # Native Window Icon
        ico_file = os.path.join(self.assets_dir, "boltools.ico")
        if os.path.exists(ico_file):
            try:
                self.iconbitmap(ico_file)
            except Exception:
                pass

        # Runtime State
        # Runtime State & View Caching
        self.worker = AsyncWorker()
        self.active_frame: Optional[ctk.CTkFrame] = None
        self.tool_cache: Dict[str, ctk.CTkFrame] = {}
        self.home_view: Optional[HomeDashboard] = None
        self.directory_view: Optional[ToolDirectoryView] = None
        self.favorites_view: Optional[FavoritesView] = None
        self.settings_view: Optional[SettingsView] = None
        self.gallery_cache: Dict[str, CategoryGallery] = {}
        self.nav_history: list = [("home", None)]

        # Layout Grids (Row 0: Header, Row 1: Sidebar + Content)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._build_shell()
        self._bind_global_shortcuts()
        self.show_home(push_history=False)
        self._init_announcements()
        self._prewarm_dependencies()

        # Protocol for clean background thread termination
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _prewarm_dependencies(self):
        """Silently imports core utility engines in background to avoid any first-click delay."""
        import threading
        def _bg_warm():
            try:
                import pymupdf
            except Exception:
                pass
            try:
                import pypdf
            except Exception:
                pass
            try:
                from PIL import Image
            except Exception:
                pass
        threading.Thread(target=_bg_warm, daemon=True).start()

    def _build_shell(self):
        # Top Header Bar
        self.header = AppHeader(
            self,
            assets_dir=self.assets_dir,
            on_search_click=self.open_command_palette,
            on_home_click=self.show_home,
            on_notification_click=self.open_notification_modal,
            on_back_click=self.navigate_back
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")

        # Left Sidebar Navigation
        self.sidebar = AppSidebar(
            self,
            on_select_category=self.show_category,
            on_select_home=self.show_home,
            on_select_directory=self.show_directory,
            on_select_tools=self.show_directory,
            on_select_favorites=self.show_favorites,
            on_select_settings=self.show_settings
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

    def show_home(self, push_history: bool = True):
        self.header.set_breadcrumb(["Home"])
        self.sidebar.active_item = "home"
        self.sidebar._update_selection()
        if not self.home_view:
            self.home_view = HomeDashboard(
                self.content_area,
                on_tool_select=self.show_tool,
                on_category_select=self.show_category,
                on_directory_click=self.show_directory,
                on_poll_click=self.open_poll_modal
            )
        self._set_active_content(self.home_view)
        if push_history:
            if not self.nav_history or self.nav_history[-1] != ("home", None):
                self.nav_history.append(("home", None))

    def show_directory(self, push_history: bool = True):
        self.header.set_breadcrumb(["Home", "Tool Hub"], on_home=self.show_home, on_back=self.navigate_back)
        self.sidebar.active_item = "tools"
        self.sidebar._update_selection()
        if not self.directory_view:
            self.directory_view = ToolDirectoryView(
                self.content_area,
                on_select_tool=self.show_tool_by_id
            )
        self._set_active_content(self.directory_view)
        if push_history:
            if not self.nav_history or self.nav_history[-1] != ("directory", None):
                self.nav_history.append(("directory", None))

    def show_favorites(self, push_history: bool = True):
        self.header.set_breadcrumb(["Home", "Favorites"], on_home=self.show_home, on_back=self.navigate_back)
        self.sidebar.active_item = "favorites"
        self.sidebar._update_selection()
        if not self.favorites_view:
            self.favorites_view = FavoritesView(
                self.content_area,
                on_select_tool=self.show_tool,
                on_browse_tools=self.show_directory
            )
        else:
            self.favorites_view.refresh()
        self._set_active_content(self.favorites_view)
        if push_history:
            if not self.nav_history or self.nav_history[-1] != ("favorites", None):
                self.nav_history.append(("favorites", None))

    def show_settings(self, push_history: bool = True):
        self.header.set_breadcrumb(["Home", "Settings"], on_home=self.show_home, on_back=self.navigate_back)
        self.sidebar.active_item = "settings"
        self.sidebar._update_selection()
        if not self.settings_view:
            self.settings_view = SettingsView(
                self.content_area
            )
        self._set_active_content(self.settings_view)
        if push_history:
            if not self.nav_history or self.nav_history[-1] != ("settings", None):
                self.nav_history.append(("settings", None))

    def show_tool_by_id(self, tool_id: str):
        tool = ToolRegistry.get(tool_id)
        if tool:
            self.show_tool(tool)

    def show_category(self, category_id: str, push_history: bool = True):
        meta = ToolRegistry.CATEGORIES.get(category_id, {})
        cat_name = meta.get("name", category_id)
        self.header.set_breadcrumb(["Home", cat_name], on_home=self.show_home, on_back=self.navigate_back)
        self.sidebar.active_item = "categories"
        self.sidebar._update_selection()
        if category_id not in self.gallery_cache:
            self.gallery_cache[category_id] = CategoryGallery(
                self.content_area,
                category_id=category_id,
                on_tool_select=self.show_tool,
                on_back=self.show_home
            )
        self._set_active_content(self.gallery_cache[category_id])
        if push_history:
            if not self.nav_history or self.nav_history[-1] != ("category", category_id):
                self.nav_history.append(("category", category_id))

    def show_tool(self, tool: ToolDefinition, push_history: bool = True):
        self.header.set_breadcrumb(
            ["Home", tool.category_name, tool.name],
            on_home=self.show_home,
            on_category=lambda cid=tool.category_id: self.show_category(cid),
            on_back=self.navigate_back
        )
        self.sidebar.active_item = "categories"
        self.sidebar._update_selection()

        if push_history:
            if not self.nav_history or self.nav_history[-1] != ("tool", tool.id):
                self.nav_history.append(("tool", tool.id))

        # Lazy instantiate or pull from cache
        if tool.id in self.tool_cache:
            frame = self.tool_cache[tool.id]
            if hasattr(frame, "on_back"):
                frame.on_back = self.navigate_back
            self._set_active_content(frame)
            return

        if tool.factory:
            frame_class = tool.factory()
            try:
                tool_frame = frame_class(self.content_area, on_back=self.navigate_back)
            except TypeError:
                tool_frame = frame_class(self.content_area)
                if hasattr(tool_frame, "on_back"):
                    tool_frame.on_back = self.navigate_back
            self.tool_cache[tool.id] = tool_frame
            self._set_active_content(tool_frame)
        else:
            # Placeholder frame for tools queued in upcoming migration batches
            placeholder = self._create_placeholder_frame(tool)
            self._set_active_content(placeholder)

    def navigate_back(self):
        """Pops navigation history and returns smoothly to the previous view."""
        if len(self.nav_history) > 1:
            self.nav_history.pop()  # Pop current view
            prev_type, prev_data = self.nav_history[-1]
            if prev_type == "home":
                self.show_home(push_history=False)
            elif prev_type == "directory":
                self.show_directory(push_history=False)
            elif prev_type == "favorites":
                self.show_favorites(push_history=False)
            elif prev_type == "settings":
                self.show_settings(push_history=False)
            elif prev_type == "category":
                self.show_category(prev_data, push_history=False)
            elif prev_type == "tool":
                prev_tool = ToolRegistry.get(prev_data)
                if prev_tool:
                    self.show_tool(prev_tool, push_history=False)
                else:
                    self.show_home(push_history=False)
        else:
            self.show_home(push_history=False)

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
