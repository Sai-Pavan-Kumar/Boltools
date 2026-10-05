"""Command Palette modal (Ctrl+K) for instant fuzzy search across all 57 tools."""

import tkinter as tk
from typing import Callable, List
import customtkinter as ctk

from src.core.theme import Theme
from src.core.registry import ToolRegistry, ToolDefinition


class CommandPalette(ctk.CTkToplevel):
    """Raycast-style search overlay providing sub-50ms tool discovery."""

    def __init__(self, master, on_tool_select: Callable[[ToolDefinition], None]):
        super().__init__(master)
        
        self.on_tool_select = on_tool_select
        self.results: List[ToolDefinition] = []
        self.selected_index = 0
        self.result_widgets: List[ctk.CTkButton] = []

        self.title("Command Palette")
        self.geometry("640x480")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # Center on parent window
        self.update_idletasks()
        pw = master.winfo_width()
        ph = master.winfo_height()
        px = master.winfo_x()
        py = master.winfo_y()
        cx = px + (pw - 640) // 2
        cy = py + (ph - 480) // 2
        self.geometry(f"640x480+{max(0, cx)}+{max(0, cy)}")

        self.configure(fg_color=Theme.SURFACE_BASE)
        self._build_ui()
        self._bind_keys()
        self._refresh_results("")

    def _build_ui(self):
        container = ctk.CTkFrame(
            self,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_MODAL,
            border_width=1,
            border_color=Theme.BORDER_HOVER
        )
        container.pack(fill="both", expand=True, padx=Theme.PAD_SM, pady=Theme.PAD_SM)
        container.pack_propagate(False)

        # ── Search Input Row
        search_frame = ctk.CTkFrame(container, fg_color="transparent")
        search_frame.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM))

        self.entry_var = tk.StringVar()
        self.entry_var.trace_add("write", lambda *args: self._on_search_change())

        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.entry_var,
            placeholder_text="Type tool name, format, or task... (e.g. compress, pdf, video)",
            font=(Theme.FONT_FAMILY, 14),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=44
        )
        self.search_entry.pack(fill="x")
        self.search_entry.focus_set()

        # ── Results Scrollable List
        self.results_frame = ctk.CTkScrollableFrame(
            container,
            fg_color="transparent",
            corner_radius=0
        )
        self.results_frame.pack(fill="both", expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_XS)

        # ── Bottom Helper Bar
        footer = ctk.CTkFrame(container, fg_color=Theme.SURFACE_INSET, height=32, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        
        shortcut_lbl = ctk.CTkLabel(
            footer,
            text="↑↓ Navigate   •   Enter Open   •   Esc Dismiss",
            font=(Theme.FONT_FAMILY, 11),
            text_color=Theme.TEXT_MUTED
        )
        shortcut_lbl.pack(pady=4)

    def _bind_keys(self):
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Up>", lambda e: self._navigate_selection(-1))
        self.bind("<Down>", lambda e: self._navigate_selection(1))
        self.bind("<Return>", lambda e: self._activate_current())

    def _on_search_change(self):
        query = self.entry_var.get()
        self._refresh_results(query)

    def _refresh_results(self, query: str):
        for widget in self.result_widgets:
            widget.destroy()
        self.result_widgets.clear()

        self.results = ToolRegistry.search(query)[:20]
        self.selected_index = 0

        if not self.results:
            empty_lbl = ctk.CTkLabel(
                self.results_frame,
                text="No matching tools found.",
                font=(Theme.FONT_FAMILY, 13),
                text_color=Theme.TEXT_MUTED
            )
            empty_lbl.pack(pady=Theme.PAD_LG)
            return

        for idx, tool in enumerate(self.results):
            btn_text = f"{tool.name}  [{tool.category_name}]\n{tool.description}"
            btn = ctk.CTkButton(
                self.results_frame,
                text=btn_text,
                fg_color="transparent",
                hover_color=Theme.SURFACE_CARD_HOVER,
                text_color=Theme.TEXT_PRIMARY,
                anchor="w",
                font=(Theme.FONT_FAMILY, 12),
                height=48,
                corner_radius=Theme.RADIUS_BUTTON,
                command=lambda t=tool: self._select_tool(t)
            )
            btn.pack(fill="x", pady=2)
            self.result_widgets.append(btn)

        self._highlight_selection()

    def _navigate_selection(self, delta: int):
        if not self.results:
            return
        self.selected_index = (self.selected_index + delta) % len(self.results)
        self._highlight_selection()

    def _highlight_selection(self):
        for idx, btn in enumerate(self.result_widgets):
            if idx == self.selected_index:
                btn.configure(fg_color=Theme.BRAND_PRIMARY, text_color=Theme.TEXT_PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=Theme.TEXT_PRIMARY)

    def _activate_current(self):
        if self.results and 0 <= self.selected_index < len(self.results):
            self._select_tool(self.results[self.selected_index])

    def _select_tool(self, tool: ToolDefinition):
        self.destroy()
        self.on_tool_select(tool)
