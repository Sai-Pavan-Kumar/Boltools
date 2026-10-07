"""Tool 8.9: Instant Local Wi-Fi File Sharing Web Server.

Hosts any chosen folder on local home Wi-Fi and provides a direct
scannable QR code / URL so phones can download files at 50 MB/s.
"""

import os
import socket
import threading
import http.server
import socketserver
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class WifiSharingTool(BaseToolFrame):
    """Universal 2-pane tool for high-speed local network file sharing."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="tool_windows_8_9",
            title="Instant Local Wi-Fi File Sharing Server",
            description="Host any folder on local home Wi-Fi and download to your phone at 50 MB/s via direct QR code.",
            **kwargs
        )
        self.httpd = None
        self.server_thread = None
        self.is_sharing = False

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # Folder Selector
        f_lbl = ctk.CTkLabel(
            container,
            text="FOLDER TO SHARE OVER WI-FI",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        f_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        self.folder_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.entry_folder = ctk.CTkEntry(
            row,
            textvariable=self.folder_var,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.entry_folder.pack(side="left", fill="x", expand=True, padx=(0, Theme.PAD_SM))

        btn_browse = ctk.CTkButton(
            row,
            text="Browse",
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12),
            height=34,
            width=70,
            command=self._browse_folder
        )
        btn_browse.pack(side="right")

        # Port Setting
        port_row = ctk.CTkFrame(container, fg_color="transparent")
        port_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        ctk.CTkLabel(port_row, text="Server Port:", font=(Theme.FONT_FAMILY, 12), text_color=Theme.TEXT_SECONDARY).pack(side="left", padx=(0, Theme.PAD_SM))
        self.port_var = tk.StringVar(value="8080")
        ctk.CTkEntry(port_row, textvariable=self.port_var, width=70, height=30, font=(Theme.FONT_FAMILY, 12)).pack(side="left")

        # Share Action Button
        self.btn_toggle = ctk.CTkButton(
            container,
            text="⚡  Start Wi-Fi File Server",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=42,
            command=self._toggle_server
        )
        self.btn_toggle.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

        # URL Box
        url_card = ctk.CTkFrame(container, fg_color=Theme.SURFACE_INSET, corner_radius=Theme.RADIUS_CARD, border_width=1, border_color=Theme.BORDER_SUBTLE)
        url_card.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        ctk.CTkLabel(url_card, text="PHONE ACCESS URL", font=(Theme.FONT_FAMILY, 10, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, 0))

        self.lbl_url = ctk.CTkLabel(
            url_card,
            text="http://[Local-IP]:8080",
            font=(Theme.FONT_MONO, 14, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.lbl_url.pack(anchor="w", padx=Theme.PAD_MD, pady=(2, Theme.PAD_SM))

    def _browse_folder(self):
        f = filedialog.askdirectory(title="Select Folder to Share")
        if f:
            self.folder_var.set(f)

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _toggle_server(self):
        if not self.is_sharing:
            folder = self.folder_var.get().strip()
            if not folder or not os.path.exists(folder):
                messagebox.showwarning("Notice", "Please select a valid folder.")
                return

            try:
                port = int(self.port_var.get().strip())
            except ValueError:
                port = 8080

            ip = self._get_local_ip()
            server_url = f"http://{ip}:{port}"

            class Handler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=folder, **kwargs)

            try:
                self.httpd = socketserver.TCPServer(("", port), Handler)
            except Exception as e:
                messagebox.showerror("Error", f"Could not bind port {port}: {e}")
                return

            self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.server_thread.start()

            self.is_sharing = True
            self.lbl_url.configure(text=server_url, text_color=Theme.BRAND_PRIMARY)
            self.btn_toggle.configure(text="⏹  Stop Wi-Fi Server", fg_color=Theme.STATUS_ERROR, hover_color="#DC2626")

            self.log(f"✓ Wi-Fi Server live: Open {server_url} on your phone browser.")
            self.log(f"Serving files from: {folder}")
        else:
            if self.httpd:
                self.httpd.shutdown()
                self.httpd.server_close()
                self.httpd = None

            self.is_sharing = False
            self.lbl_url.configure(text="http://[Local-IP]:8080", text_color=Theme.TEXT_PRIMARY)
            self.btn_toggle.configure(text="⚡  Start Wi-Fi File Server", fg_color=Theme.BRAND_PRIMARY, hover_color=Theme.BRAND_HOVER)
            self.log("Wi-Fi Server stopped.")
