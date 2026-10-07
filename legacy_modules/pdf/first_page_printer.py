"""Tool 3.1: First-Page Document Extractor & Auto-Printer.

Extracts the first page from a batch of PDF documents (e.g. shipping labels,
invoices), consolidates them into a single PDF, and optionally spools them
directly to the physical printer.
"""

import os
import platform
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk
from pypdf import PdfReader, PdfWriter

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class FirstPagePrinterTool(BaseToolFrame):
    """Universal 2-pane tool for batch extracting page 1 and auto-printing."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="pdf_first_page",
            title="First-Page Document Extractor & Auto-Printer",
            description="Extract page 1 from multiple documents, merge into one compilation, and optionally print.",
            **kwargs
        )
        self.file_paths: List[str] = []

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # File selection header & buttons
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM))

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

        btn_folder = ctk.CTkButton(
            btn_row,
            text="📁 Add Folder",
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12),
            height=32,
            command=self._add_folder
        )
        btn_folder.pack(side="left", padx=(0, Theme.PAD_SM))

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

        # Files Count Label
        self.files_counter_lbl = ctk.CTkLabel(
            container,
            text="No documents selected",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        self.files_counter_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_XS))

        # Selected Files List Preview Box
        self.files_listbox = ctk.CTkTextbox(
            container,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_SECONDARY,
            font=(Theme.FONT_MONO, 11),
            corner_radius=Theme.RADIUS_INPUT,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            height=140
        )
        self.files_listbox.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        self.files_listbox.configure(state="disabled")

        # Output File Destination Row
        dest_label = ctk.CTkLabel(
            container,
            text="OUTPUT DESTINATION",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        dest_label.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        dest_row = ctk.CTkFrame(container, fg_color="transparent")
        dest_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        default_out = os.path.join(os.path.expanduser("~/Documents"), "first_pages_compilation.pdf")
        self.out_var = tk.StringVar(value=default_out)

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
            command=self._browse_output
        )
        btn_browse.pack(side="right")

        # Action Buttons
        action_row = ctk.CTkFrame(container, fg_color="transparent")
        action_row.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

        self.btn_merge = ctk.CTkButton(
            action_row,
            text="📄  Merge First Pages",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=40,
            command=lambda: self._execute(print_job=False)
        )
        self.btn_merge.pack(side="left", fill="x", expand=True, padx=(0, Theme.PAD_SM))

        self.btn_print = ctk.CTkButton(
            action_row,
            text="🖨️  Merge & Print",
            fg_color=Theme.BRAND_HOVER,
            hover_color=Theme.BRAND_ACCENT,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=40,
            command=lambda: self._execute(print_job=True)
        )
        self.btn_print.pack(side="right", fill="x", expand=True)

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF Documents",
            filetypes=[("PDF Documents", "*.pdf")]
        )
        if paths:
            for p in paths:
                if p not in self.file_paths:
                    self.file_paths.append(p)
            self._update_files_preview()

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder containing PDFs")
        if folder:
            count = 0
            for fname in sorted(os.listdir(folder)):
                if fname.lower().endswith(".pdf"):
                    full_p = os.path.join(folder, fname)
                    if full_p not in self.file_paths:
                        self.file_paths.append(full_p)
                        count += 1
            self.log(f"Added {count} document(s) from folder: {folder}")
            self._update_files_preview()

    def _clear_files(self):
        self.file_paths.clear()
        self._update_files_preview()

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Save Merged Compilation As",
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            initialfile="first_pages_compilation.pdf"
        )
        if path:
            self.out_var.set(path)

    def _update_files_preview(self):
        n = len(self.file_paths)
        txt = f"{n} document{'s' if n != 1 else ''} loaded" if n else "No documents selected"
        self.files_counter_lbl.configure(text=txt)

        self.files_listbox.configure(state="normal")
        self.files_listbox.delete("1.0", "end")
        for p in self.file_paths:
            self.files_listbox.insert("end", f"• {os.path.basename(p)}\n")
        self.files_listbox.configure(state="disabled")

    def _execute(self, print_job: bool):
        if not self.file_paths:
            messagebox.showwarning("Notice", "Please add at least one PDF file first.")
            return

        out_path = self.out_var.get().strip()
        if not out_path:
            messagebox.showwarning("Notice", "Please specify a destination file path.")
            return

        self.output_directory = os.path.dirname(out_path)
        self.btn_merge.configure(state="disabled")
        self.btn_print.configure(state="disabled")

        def _task():
            writer = PdfWriter()
            total = len(self.file_paths)
            extracted_count = 0

            self.log(f"Starting extraction of page 1 from {total} documents...")

            for i, path in enumerate(self.file_paths):
                try:
                    reader = PdfReader(path)
                    if len(reader.pages) > 0:
                        writer.add_page(reader.pages[0])
                        extracted_count += 1
                        self.log(f"[{i+1}/{total}] Extracted: {os.path.basename(path)}")
                    else:
                        self.log(f"[{i+1}/{total}] Skipped empty: {os.path.basename(path)}")
                except Exception as exc:
                    self.log(f"[{i+1}/{total}] Warning: Could not read {os.path.basename(path)} ({exc})")

                self.set_progress((i + 1) / total * 0.8)

            if extracted_count == 0:
                raise RuntimeError("No pages could be extracted from the selected files.")

            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f_out:
                writer.write(f_out)

            self.log(f"Successfully saved compilation: {out_path} ({extracted_count} pages)")
            self.set_progress(0.9)

            if print_job:
                self.log("Sending compilation to default printer...")
                sys_platform = platform.system()
                if sys_platform == "Windows":
                    os.startfile(out_path, "print")
                    self.log("Print job sent to Windows print spooler.")
                elif sys_platform in ("Darwin", "Linux"):
                    res = subprocess.run(["lpr", out_path], capture_output=True, text=True)
                    if res.returncode == 0:
                        self.log("Print job sent via lpr.")
                    else:
                        self.log(f"Print warning: {res.stderr}")

            return out_path

        def _on_done(result):
            self.btn_merge.configure(state="normal")
            self.btn_print.configure(state="normal")
            msg = f"Merged {len(self.file_paths)} document(s) successfully!\nSaved to: {result}"
            if print_job:
                msg += "\nPrint spooler job dispatched."
            messagebox.showinfo("Success", msg)

        def _on_err(err):
            self.btn_merge.configure(state="normal")
            self.btn_print.configure(state="normal")
            messagebox.showerror("Error", f"Failed to complete task: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
