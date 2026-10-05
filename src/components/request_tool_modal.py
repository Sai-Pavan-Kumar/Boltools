"""Request a Tool Modal for Boltools."""

import tkinter as tk
from typing import Callable, Optional
import customtkinter as ctk

from src.core.theme import Theme
from src.core.community import community_service


class RequestToolModal(ctk.CTkToplevel):
    """Allows users to submit offline tool requests directly to founder's roadmap."""

    def __init__(self, master, on_close: Optional[Callable[[], None]] = None):
        super().__init__(master)

        self.on_close_cb = on_close
        self.title("Request a Tool")
        self.geometry("520x460")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # Center on parent window
        self.update_idletasks()
        pw = master.winfo_width()
        ph = master.winfo_height()
        px = master.winfo_x()
        py = master.winfo_y()
        cx = px + (pw - 520) // 2
        cy = py + (ph - 460) // 2
        self.geometry(f"520x460+{max(0, cx)}+{max(0, cy)}")

        self.configure(fg_color=Theme.SURFACE_BASE)
        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(
            self,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_MODAL,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        container.pack(fill="both", expand=True, padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        # Header Bar
        top_bar = ctk.CTkFrame(container, fg_color="transparent")
        top_bar.pack(fill="x", padx=Theme.PAD_LG, pady=(Theme.PAD_LG, Theme.PAD_XS))

        title_lbl = ctk.CTkLabel(
            top_bar,
            text="Request a New Tool 💡",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title_lbl.pack(side="left")

        btn_close = ctk.CTkButton(
            top_bar,
            text="✕",
            font=(Theme.FONT_FAMILY, 12, "bold"),
            fg_color="transparent",
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_MUTED,
            width=28,
            height=28,
            corner_radius=Theme.RADIUS_BUTTON,
            command=self.destroy
        )
        btn_close.pack(side="right")

        sub_lbl = ctk.CTkLabel(
            container,
            text="Need a specific offline task solved without paid subscriptions? Tell the founder directly.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
            wraplength=460,
            justify="left"
        )
        sub_lbl.pack(fill="x", padx=Theme.PAD_LG, pady=(0, Theme.PAD_MD))

        # Tool Name Input
        name_lbl = ctk.CTkLabel(
            container,
            text="TOOL NAME OR SHORT CONCEPT",
            font=Theme.FONT_LABEL,
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        name_lbl.pack(fill="x", padx=Theme.PAD_LG, pady=(0, 2))

        self.entry_name = ctk.CTkEntry(
            container,
            placeholder_text="e.g. Batch Audio Pitch Shifter / OCR Signature Extractor",
            font=Theme.FONT_BODY,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=36
        )
        self.entry_name.pack(fill="x", padx=Theme.PAD_LG, pady=(0, Theme.PAD_MD))

        # Problem / Description Input
        desc_lbl = ctk.CTkLabel(
            container,
            text="WHAT PROBLEM DOES THIS SOLVE FOR YOU?",
            font=Theme.FONT_LABEL,
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        desc_lbl.pack(fill="x", padx=Theme.PAD_LG, pady=(0, 2))

        self.txt_desc = ctk.CTkTextbox(
            container,
            font=Theme.FONT_BODY,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=110
        )
        self.txt_desc.pack(fill="x", padx=Theme.PAD_LG, pady=(0, Theme.PAD_LG))

        # Submit CTA
        self.btn_submit = ctk.CTkButton(
            container,
            text="Submit to Founder Roadmap 🚀",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            height=40,
            command=self._submit
        )
        self.btn_submit.pack(fill="x", padx=Theme.PAD_LG, pady=(0, Theme.PAD_MD))

        self.status_lbl = ctk.CTkLabel(
            container,
            text="",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.STATUS_SUCCESS
        )
        self.status_lbl.pack(fill="x", padx=Theme.PAD_LG)

    def _submit(self):
        name = self.entry_name.get().strip()
        desc = self.txt_desc.get("1.0", "end").strip()
        if not name or not desc:
            self.status_lbl.configure(text="Please provide both a tool name and description.", text_color=Theme.STATUS_ERROR)
            return

        community_service.submit_tool_request(name, desc)
        self.btn_submit.configure(state="disabled")
        self.status_lbl.configure(text="✓ Thank you! Your request was sent directly to the roadmap.", text_color=Theme.STATUS_SUCCESS)
        self.after(1600, self.destroy)
