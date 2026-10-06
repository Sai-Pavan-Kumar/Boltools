"""Tool 8.4: Saved Wi-Fi Password Revealer & Phone QR.

Extracts plaintext security keys for all saved Wi-Fi profiles on Windows
and generates a scan-to-connect Wi-Fi QR code for phones.
"""

import os
import subprocess
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List
import customtkinter as ctk

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class WifiPasswordRevealerTool(BaseToolFrame):
    """Universal 2-pane tool for revealing saved Wi-Fi keys and sharing as QR codes."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="tool_windows_8_4",
            title="Saved Wi-Fi Password Revealer & QR",
            description="Reveal forgotten Wi-Fi network passwords on your PC and generate instant scan-to-connect QR codes.",
            **kwargs
        )
        self.wifi_profiles: Dict[str, str] = {}

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # Refresh Profiles Button
        btn_refresh = ctk.CTkButton(
            container,
            text="🔄 Scan Saved Wi-Fi Profiles",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            height=34,
            command=self._scan_profiles
        )
        btn_refresh.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM))

        # Profile Selector
        sel_lbl = ctk.CTkLabel(
            container,
            text="SELECT SAVED NETWORK",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        sel_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.network_var = tk.StringVar(value="Click Scan first...")
        self.combo_networks = ctk.CTkComboBox(
            container,
            values=["Click Scan first..."],
            variable=self.network_var,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34,
            command=self._on_select_network
        )
        self.combo_networks.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Password Display Card
        pwd_card = ctk.CTkFrame(container, fg_color=Theme.SURFACE_INSET, corner_radius=Theme.RADIUS_CARD, border_width=1, border_color=Theme.BORDER_SUBTLE)
        pwd_card.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

        ctk.CTkLabel(pwd_card, text="PLAINTEXT PASSWORD", font=(Theme.FONT_FAMILY, 10, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, 0))

        self.lbl_password = ctk.CTkLabel(
            pwd_card,
            text="••••••••••••",
            font=(Theme.FONT_MONO, 16, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.lbl_password.pack(anchor="w", padx=Theme.PAD_MD, pady=(2, Theme.PAD_SM))

        # Copy & QR Actions
        act_row = ctk.CTkFrame(container, fg_color="transparent")
        act_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        btn_copy = ctk.CTkButton(
            act_row,
            text="📋 Copy Password",
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12),
            height=34,
            command=self._copy_password
        )
        btn_copy.pack(side="left", padx=(0, Theme.PAD_SM))

        btn_show_all = ctk.CTkButton(
            act_row,
            text="List All Passwords",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            height=34,
            command=self._list_all
        )
        btn_show_all.pack(side="left")

    def _scan_profiles(self):
        self.log("Interrogating Windows WLAN subsystem for saved profiles...")
        cmd = ["netsh", "wlan", "show", "profiles"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        profiles = []
        for line in res.stdout.splitlines():
            if "All User Profile" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    profiles.append(parts[1].strip())

        if profiles:
            self.combo_networks.configure(values=profiles)
            self.network_var.set(profiles[0])
            self.log(f"✓ Found {len(profiles)} saved Wi-Fi profiles.")
            self._reveal_key(profiles[0])
        else:
            self.log("No saved Wi-Fi profiles found.")

    def _on_select_network(self, network_name):
        self._reveal_key(network_name)

    def _reveal_key(self, name):
        cmd = ["netsh", "wlan", "show", "profile", f"name={name}", "key=clear"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        key = "[Open Network / No Password]"
        for line in res.stdout.splitlines():
            if "Key Content" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    key = parts[1].strip()
                    break

        self.wifi_profiles[name] = key
        self.lbl_password.configure(text=key)
        self.log(f"✓ {name}: Key retrieved successfully.")

    def _copy_password(self):
        cur = self.lbl_password.cget("text")
        if cur and cur != "••••••••••••":
            self.clipboard_clear()
            self.clipboard_append(cur)
            messagebox.showinfo("Copied", "Wi-Fi password copied to clipboard!")

    def _list_all(self):
        self.log("Exporting all saved network profiles & keys:")
        for name, key in self.wifi_profiles.items():
            self.log(f" • {name} ➔ {key}")
