"""Smart 2-Tier Tool Uninstall Decision Modal for Boltools."""

import tkinter as tk
from typing import Callable, Optional
import customtkinter as ctk

from src.core.theme import Theme
from src.core.community import community_service


class UninstallModal(ctk.CTkToplevel):
    """Presents user with 2-tier uninstall choice: Preserve Data vs Complete Purge."""

    def __init__(self, master, tool_id: str, tool_name: str, on_success: Optional[Callable[[], None]] = None):
        super().__init__(master)

        self.tool_id = tool_id
        self.tool_name = tool_name
        self.on_success = on_success

        self.title("Remove Tool")
        self.geometry("480x380")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # Center on parent window
        self.update_idletasks()
        pw = master.winfo_width()
        ph = master.winfo_height()
        px = master.winfo_x()
        py = master.winfo_y()
        cx = px + (pw - 480) // 2
        cy = py + (ph - 380) // 2
        self.geometry(f"480x380+{max(0, cx)}+{max(0, cy)}")

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

        # Header Title
        title_lbl = ctk.CTkLabel(
            container,
            text=f"Remove {self.tool_name}?",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title_lbl.pack(fill="x", padx=Theme.PAD_LG, pady=(Theme.PAD_LG, Theme.PAD_XS))

        sub_lbl = ctk.CTkLabel(
            container,
            text="Choose how you want to remove this tool from your PC:",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        sub_lbl.pack(fill="x", padx=Theme.PAD_LG, pady=(0, Theme.PAD_MD))

        # Radio Selection Var: "preserve" vs "purge"
        self.choice_var = tk.StringVar(value="preserve")

        # Option 1: Preserve Work (Recommended)
        opt1_frame = ctk.CTkFrame(
            container,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        opt1_frame.pack(fill="x", padx=Theme.PAD_LG, pady=(0, Theme.PAD_SM))

        rb1 = ctk.CTkRadioButton(
            opt1_frame,
            text="Keep My Work & Settings (Recommended)",
            variable=self.choice_var,
            value="preserve",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_PRIMARY,
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER
        )
        rb1.pack(anchor="w", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, 2))

        desc1 = ctk.CTkLabel(
            opt1_frame,
            text="Frees up tool files. Your custom presets, templates, and history remain safely saved for instant restoration upon reinstall.",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_SECONDARY,
            wraplength=400,
            justify="left",
            anchor="w"
        )
        desc1.pack(fill="x", padx=(Theme.PAD_MD + 24, Theme.PAD_MD), pady=(0, Theme.PAD_SM))

        # Option 2: Complete Purge
        opt2_frame = ctk.CTkFrame(
            container,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        opt2_frame.pack(fill="x", padx=Theme.PAD_LG, pady=(0, Theme.PAD_LG))

        rb2 = ctk.CTkRadioButton(
            opt2_frame,
            text="Completely Delete All Data",
            variable=self.choice_var,
            value="purge",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.STATUS_ERROR,
            fg_color=Theme.STATUS_ERROR,
            hover_color="#DC2626"
        )
        rb2.pack(anchor="w", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, 2))

        desc2 = ctk.CTkLabel(
            opt2_frame,
            text="Permanently scrubs the tool engine, caches, and all saved user settings. Reclaims maximum disk space.",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_SECONDARY,
            wraplength=400,
            justify="left",
            anchor="w"
        )
        desc2.pack(fill="x", padx=(Theme.PAD_MD + 24, Theme.PAD_MD), pady=(0, Theme.PAD_SM))

        # Action Buttons
        btn_bar = ctk.CTkFrame(container, fg_color="transparent")
        btn_bar.pack(fill="x", padx=Theme.PAD_LG, pady=(0, Theme.PAD_MD))

        btn_cancel = ctk.CTkButton(
            btn_bar,
            text="Cancel",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            height=36,
            command=self.destroy
        )
        btn_cancel.pack(side="left", expand=True, fill="x", padx=(0, Theme.PAD_SM))

        btn_confirm = ctk.CTkButton(
            btn_bar,
            text="Confirm Removal",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.STATUS_ERROR,
            hover_color="#DC2626",
            text_color="#FFFFFF",
            corner_radius=Theme.RADIUS_BUTTON,
            height=36,
            command=self._confirm
        )
        btn_confirm.pack(side="right", expand=True, fill="x")

    def _confirm(self):
        purge = (self.choice_var.get() == "purge")
        community_service.uninstall_tool(self.tool_id, purge_data=purge)
        self.destroy()
        if self.on_success:
            self.on_success()
