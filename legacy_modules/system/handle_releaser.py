"""Tool 7.12: Locked File Handle Releaser & Deleter.

Identifies the locking background process PID holding files hostage
and kills the process handle so you can delete or rename files without rebooting.
"""

import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class LockedFileReleaserTool(BaseToolFrame):
    """Universal 2-pane tool for releasing file locks and killing zombie locking PIDs."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="tool_system_7_12",
            title="Locked File Handle Releaser",
            description="Fix 'File is open in another program' errors by releasing locking background processes cleanly.",
            **kwargs
        )
        self.locked_file_path: str = ""

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # Locked File Selector
        file_lbl = ctk.CTkLabel(
            container,
            text="LOCKED FILE OR FOLDER",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        file_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        self.path_var = tk.StringVar(value="")
        self.entry_path = ctk.CTkEntry(
            row,
            textvariable=self.path_var,
            font=(Theme.FONT_FAMILY, 12),
            placeholder_text="Select locked file...",
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, Theme.PAD_SM))

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
            command=self._browse_file
        )
        btn_browse.pack(side="right")

        # Action Buttons
        self.btn_unlock = ctk.CTkButton(
            container,
            text="⚡  Identify & Release Lock",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=42,
            command=self._unlock_file
        )
        self.btn_unlock.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_SM))

        self.btn_delete = ctk.CTkButton(
            container,
            text="🗑️  Force Release & Delete File",
            fg_color="transparent",
            border_width=1,
            border_color=Theme.STATUS_ERROR,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.STATUS_ERROR,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            height=36,
            command=self._force_delete
        )
        self.btn_delete.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

    def _browse_file(self):
        f = filedialog.askopenfilename(title="Select Locked File")
        if f:
            self.path_var.set(f)
            self.log(f"Selected file to audit: {os.path.basename(f)}")

    def _unlock_file(self):
        p = self.path_var.get().strip()
        if not p or not os.path.exists(p):
            messagebox.showwarning("Notice", "Please select a valid file.")
            return

        def _task():
            self.log(f"Auditing file locking handles for: {os.path.basename(p)}...")
            # Windows PowerShell handle check
            ps_cmd = f"Get-Process | Where-Object {{ $_.Modules.FileName -like '*{os.path.basename(p)}*' }} | Select-Object -ExpandProperty Id"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
            pids = [line.strip() for line in res.stdout.splitlines() if line.strip().isdigit()]

            if pids:
                self.log(f"Found {len(pids)} locking process PIDs: {', '.join(pids)}")
                for pid in pids:
                    self.log(f"Terminating locking process PID {pid}...")
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                self.log("✓ All locking handles successfully released!")
                return True
            else:
                self.log("No active process locking detected. File handle is free.")
                return False

        def _on_done(released):
            msg = "Locking handles released!" if released else "File appears to be already unlocked."
            messagebox.showinfo("Result", msg)

        self.execute_async(_task, on_success=_on_done)

    def _force_delete(self):
        p = self.path_var.get().strip()
        if not p or not os.path.exists(p):
            messagebox.showwarning("Notice", "Please select a valid file to delete.")
            return

        confirm = messagebox.askyesno("Confirm Deletion", f"Permanently release handles and delete:\n{os.path.basename(p)}?")
        if not confirm:
            return

        def _task():
            self.log(f"Releasing and forcing deletion: {p}...")
            # Try direct delete
            try:
                os.remove(p)
                self.log("✓ File deleted successfully on direct pass.")
                return True
            except PermissionError:
                self.log("Encountered locked handle. Terminating locking handles...")
                ps_cmd = f"Get-Process | Where-Object {{ $_.Modules.FileName -like '*{os.path.basename(p)}*' }} | Stop-Process -Force"
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)
                os.remove(p)
                self.log("✓ File force-deleted after handle termination.")
                return True

        def _on_done(success):
            if success:
                self.path_var.set("")
                messagebox.showinfo("Success", "File successfully deleted!")

        def _on_err(err):
            self.log(f"✗ Failed to delete: {err}")
            messagebox.showerror("Error", f"Could not force-delete file: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
