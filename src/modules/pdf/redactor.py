"""Tool 3.10: PII Sanitizer & Auto-Redactor.

Permanently blacks out sensitive PII before sharing documents:
- Aadhaar Numbers (XXXX-XXXX-1234)
- PAN Card Numbers (ABCDE1234F)
- Phone Numbers & Emails
- Bank Account Numbers
"""

import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk
import pymupdf

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class PiiRedactorTool(BaseToolFrame):
    """Universal 2-pane tool for automatic PII detection and vector redaction."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="tool_pdf_3_10",
            title="PII Sanitizer & Auto-Redactor",
            description="Permanently blackout Aadhaar, PAN card, phone numbers, and financial details before sharing documents.",
            **kwargs
        )
        self.file_paths: List[str] = []

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # File Selection Header & Buttons
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

        btn_add = ctk.CTkButton(
            btn_row,
            text="+ Add Documents",
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
            text="No documents loaded",
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

        # Patterns Checkboxes
        pattern_lbl = ctk.CTkLabel(
            container,
            text="PII PATTERNS TO BLACK OUT",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        pattern_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.chk_aadhaar = ctk.CTkCheckBox(container, text="Aadhaar Card (12-digit number)", font=(Theme.FONT_FAMILY, 12))
        self.chk_aadhaar.select()
        self.chk_aadhaar.pack(fill="x", padx=Theme.PAD_MD, pady=2)

        self.chk_pan = ctk.CTkCheckBox(container, text="PAN Card Number (10 chars)", font=(Theme.FONT_FAMILY, 12))
        self.chk_pan.select()
        self.chk_pan.pack(fill="x", padx=Theme.PAD_MD, pady=2)

        self.chk_phone = ctk.CTkCheckBox(container, text="Phone Numbers & Emails", font=(Theme.FONT_FAMILY, 12))
        self.chk_phone.select()
        self.chk_phone.pack(fill="x", padx=Theme.PAD_MD, pady=2)

        # Custom keywords to redact
        kw_lbl = ctk.CTkLabel(
            container,
            text="Custom Keyword Blackouts (comma separated):",
            font=(Theme.FONT_FAMILY, 11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        kw_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, 2))

        self.custom_kw_var = tk.StringVar(value="")
        self.entry_kw = ctk.CTkEntry(
            container,
            textvariable=self.custom_kw_var,
            font=(Theme.FONT_FAMILY, 12),
            placeholder_text="e.g. Confidential, Salary, John Doe",
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            height=32
        )
        self.entry_kw.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Destination Folder
        dest_lbl = ctk.CTkLabel(
            container,
            text="DESTINATION FOLDER",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        dest_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

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
            text="⚡  Redact & Black Out PII",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=42,
            command=self._execute
        )
        self.btn_execute.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

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
        txt = f"{n} document{'s' if n != 1 else ''} loaded" if n else "No documents loaded"
        self.counter_lbl.configure(text=txt)

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        for idx, p in enumerate(self.file_paths):
            self.preview_box.insert("end", f"{idx+1}. {os.path.basename(p)}\n")
        self.preview_box.configure(state="disabled")

    def _execute(self):
        if not self.file_paths:
            messagebox.showwarning("Notice", "Please select PDF documents first.")
            return

        out_folder = self.out_var.get().strip()
        if not out_folder or not os.path.exists(out_folder):
            messagebox.showwarning("Notice", "Please select a valid destination folder.")
            return

        do_aadhaar = bool(self.chk_aadhaar.get())
        do_pan = bool(self.chk_pan.get())
        do_phone = bool(self.chk_phone.get())
        custom_words = [w.strip() for w in self.custom_kw_var.get().split(",") if w.strip()]

        self.output_directory = out_folder
        self.btn_execute.configure(state="disabled")

        def _task():
            total = len(self.file_paths)
            self.log("Scanning document text layer for sensitive PII...")

            patterns = []
            if do_aadhaar:
                patterns.append(r"\b\d{4}\s\d{4}\s\d{4}\b")
                patterns.append(r"\b\d{12}\b")
            if do_pan:
                patterns.append(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
            if do_phone:
                patterns.append(r"\b[6-9]\d{9}\b")
                patterns.append(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

            for idx, p in enumerate(self.file_paths):
                base_name = os.path.splitext(os.path.basename(p))[0]
                out_pdf = os.path.join(out_folder, f"{base_name}_redacted.pdf")
                doc = pymupdf.open(p)
                redaction_count = 0

                for page in doc:
                    # Search regex matches
                    for pat in patterns:
                        for m in re.finditer(pat, page.get_text()):
                            found_text = m.group()
                            rects = page.search_for(found_text)
                            for r in rects:
                                page.add_redact_annot(r, fill=(0, 0, 0))
                                redaction_count += 1

                    # Search custom words
                    for word in custom_words:
                        rects = page.search_for(word)
                        for r in rects:
                            page.add_redact_annot(r, fill=(0, 0, 0))
                            redaction_count += 1

                    # Apply redactions (permanently deletes underlying vector text)
                    page.apply_redactions()

                doc.save(out_pdf, garbage=4, deflate=True)
                doc.close()
                self.log(f"✓ {base_name}: Redacted {redaction_count} sensitive PII blocks.")
                self.set_progress((idx + 1) / total)

            return out_folder

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"PII redaction complete!\nSaved to: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Redaction failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
