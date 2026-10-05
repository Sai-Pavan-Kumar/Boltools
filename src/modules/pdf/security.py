"""Tool 3.4: Document Security & Encryption Hub.

Encrypts confidential PDFs with AES-256 passwords or unlocks password-protected
documents with legitimate keys. 100% offline security.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk
from pypdf import PdfReader, PdfWriter

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class PdfSecurityTool(BaseToolFrame):
    """Universal 2-pane tool for encrypting and decrypting PDF documents."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="pdf_security",
            title="Document Security & Encryption Hub",
            description="Protect confidential files with military-grade AES encryption or unlock protected PDFs.",
            **kwargs
        )
        self.file_paths: List[str] = []

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # Mode Selection
        mode_lbl = ctk.CTkLabel(
            container,
            text="SECURITY ACTION",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        mode_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

        self.mode_var = tk.StringVar(value="encrypt")
        self.seg_mode = ctk.CTkSegmentedButton(
            container,
            values=["Lock (Encrypt)", "Unlock (Decrypt)"],
            font=(Theme.FONT_FAMILY, 12, "bold"),
            selected_color=Theme.BRAND_PRIMARY,
            selected_hover_color=Theme.BRAND_HOVER,
            unselected_color=Theme.SURFACE_INSET,
            height=34
        )
        self.seg_mode.set("Lock (Encrypt)")
        self.seg_mode.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # File Selection Header & Buttons
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        btn_add = ctk.CTkButton(
            btn_row,
            text="+ Add Files",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            height=32,
            command=self._add_files
        )
        btn_add.pack(side="left", padx=(0, Theme.PAD_SM))

        btn_clear = ctk.CTkButton(
            btn_row,
            text="Clear",
            fg_color="transparent",
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.STATUS_ERROR,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12),
            height=32,
            width=60,
            command=self._clear_files
        )
        btn_clear.pack(side="right")

        # Files Counter & Preview Box
        self.counter_lbl = ctk.CTkLabel(
            container,
            text="No documents selected",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        self.counter_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_XS))

        self.preview_box = ctk.CTkTextbox(
            container,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_SECONDARY,
            font=(Theme.FONT_MONO, 11),
            corner_radius=Theme.RADIUS_INPUT,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            height=110
        )
        self.preview_box.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        self.preview_box.configure(state="disabled")

        # Password Entry Row
        pw_lbl = ctk.CTkLabel(
            container,
            text="PASSPHRASE / PASSWORD",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        pw_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        pw_row = ctk.CTkFrame(container, fg_color="transparent")
        pw_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        self.pw_var = tk.StringVar()
        self.entry_pw = ctk.CTkEntry(
            pw_row,
            textvariable=self.pw_var,
            show="•",
            font=(Theme.FONT_FAMILY, 13),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=36
        )
        self.entry_pw.pack(side="left", fill="x", expand=True, padx=(0, Theme.PAD_SM))

        self.show_pw_var = tk.BooleanVar(value=False)
        btn_toggle_pw = ctk.CTkCheckBox(
            pw_row,
            text="Show",
            variable=self.show_pw_var,
            font=(Theme.FONT_FAMILY, 11),
            command=self._toggle_pw
        )
        btn_toggle_pw.pack(side="right")

        # Output Folder Destination
        out_lbl = ctk.CTkLabel(
            container,
            text="OUTPUT DESTINATION FOLDER",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        out_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        dest_row = ctk.CTkFrame(container, fg_color="transparent")
        dest_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        self.out_var = tk.StringVar(value=os.path.expanduser("~/Documents"))
        self.entry_out = ctk.CTkEntry(
            dest_row,
            textvariable=self.out_var,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.entry_out.pack(side="left", fill="x", expand=True, padx=(0, Theme.PAD_SM))

        btn_browse = ctk.CTkButton(
            dest_row,
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

        # Execute CTA
        self.btn_execute = ctk.CTkButton(
            container,
            text="🔒  Apply Security",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=42,
            command=self._execute
        )
        self.btn_execute.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

    def _toggle_pw(self):
        show_char = "" if self.show_pw_var.get() else "•"
        self.entry_pw.configure(show=show_char)

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF Documents",
            filetypes=[("PDF Documents", "*.pdf")]
        )
        if paths:
            for p in paths:
                if p not in self.file_paths:
                    self.file_paths.append(p)
            self._update_preview()

    def _clear_files(self):
        self.file_paths.clear()
        self._update_preview()

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Destination Folder")
        if folder:
            self.out_var.set(folder)

    def _update_preview(self):
        n = len(self.file_paths)
        txt = f"{n} document{'s' if n != 1 else ''} loaded" if n else "No documents selected"
        self.counter_lbl.configure(text=txt)

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        for idx, p in enumerate(self.file_paths):
            self.preview_box.insert("end", f"{idx+1}. {os.path.basename(p)}\n")
        self.preview_box.configure(state="disabled")

    def _execute(self):
        if not self.file_paths:
            messagebox.showwarning("Notice", "Please add at least one PDF file first.")
            return

        password = self.pw_var.get().strip()
        if not password:
            messagebox.showwarning("Notice", "Please enter a password.")
            return

        out_folder = self.out_var.get().strip()
        if not out_folder or not os.path.exists(out_folder):
            messagebox.showwarning("Notice", "Please provide a valid destination folder.")
            return

        is_encrypt = "Lock" in self.seg_mode.get()
        self.output_directory = out_folder
        self.btn_execute.configure(state="disabled")

        def _task():
            total = len(self.file_paths)
            action_name = "Encrypting" if is_encrypt else "Unlocking"
            self.log(f"Starting {action_name} for {total} document(s)...")

            for i, p in enumerate(self.file_paths):
                base_name = os.path.splitext(os.path.basename(p))[0]

                if is_encrypt:
                    # Encrypt with AES
                    reader = PdfReader(p)
                    writer = PdfWriter()
                    for page in reader.pages:
                        writer.add_page(page)
                    writer.encrypt(password)
                    out_path = os.path.join(out_folder, f"{base_name}_locked.pdf")
                    with open(out_path, "wb") as f_out:
                        writer.write(f_out)
                    self.log(f"✓ Locked: {os.path.basename(out_path)}")
                else:
                    # Decrypt
                    reader = PdfReader(p)
                    if reader.is_encrypted:
                        res = reader.decrypt(password)
                        if res == 0:
                            self.log(f"✗ Failed (Wrong Password): {os.path.basename(p)}")
                            continue
                    writer = PdfWriter()
                    for page in reader.pages:
                        writer.add_page(page)
                    out_path = os.path.join(out_folder, f"{base_name}_unlocked.pdf")
                    with open(out_path, "wb") as f_out:
                        writer.write(f_out)
                    self.log(f"✓ Unlocked: {os.path.basename(out_path)}")

                self.set_progress((i + 1) / total * 0.9)

            return out_folder

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"Operation completed!\nFiles saved in: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Security operation failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
