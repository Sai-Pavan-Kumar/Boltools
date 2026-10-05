"""Tool 3.3: Document Page Manager & Deskewer.

Rotates upside-down pages, deletes unwanted blank pages, and reorders sheets effortlessly.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk
from pypdf import PdfReader, PdfWriter

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class PdfPageManagerTool(BaseToolFrame):
    """Universal 2-pane tool for rotating and pruning pages in PDF documents."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="pdf_page_manager",
            title="Document Page Manager & Deskewer",
            description="Rotate skewed/upside-down pages or delete blank and unwanted sheets without quality loss.",
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

        # Rotation Controls
        rot_lbl = ctk.CTkLabel(
            container,
            text="PAGE ROTATION (Clockwise)",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        rot_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.rot_seg = ctk.CTkSegmentedButton(
            container,
            values=["No Rotation", "90°", "180°", "270°"],
            font=(Theme.FONT_FAMILY, 12),
            selected_color=Theme.BRAND_PRIMARY,
            selected_hover_color=Theme.BRAND_HOVER,
            unselected_color=Theme.SURFACE_INSET,
            height=34
        )
        self.rot_seg.set("90°")
        self.rot_seg.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Delete Pages Rule Input
        del_lbl = ctk.CTkLabel(
            container,
            text="DELETE PAGES (e.g. 2, 4 or 5-7. Leave blank to keep all):",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        del_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.del_pages_var = tk.StringVar(value="")
        self.entry_del = ctk.CTkEntry(
            container,
            textvariable=self.del_pages_var,
            placeholder_text="e.g. 2, 4, 7-9",
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.entry_del.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

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
            text="🔄  Apply Adjustments",
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
        txt = f"{n} document{'s' if n != 1 else ''} loaded" if n else "No documents selected"
        self.counter_lbl.configure(text=txt)

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        for idx, p in enumerate(self.file_paths):
            self.preview_box.insert("end", f"{idx+1}. {os.path.basename(p)}\n")
        self.preview_box.configure(state="disabled")

    def _parse_delete_pages(self, del_str: str) -> set:
        """Parses page numbers (1-indexed) to delete into a set of 0-indexed integers."""
        to_del = set()
        if not del_str.strip():
            return to_del
        parts = del_str.split(",")
        for part in parts:
            part = part.strip()
            if "-" in part:
                try:
                    s, e = part.split("-", 1)
                    for n in range(int(s), int(e) + 1):
                        to_del.add(n - 1)
                except ValueError:
                    continue
            elif part.isdigit():
                to_del.add(int(part) - 1)
        return to_del

    def _execute(self):
        if not self.file_paths:
            messagebox.showwarning("Notice", "Please select at least one PDF file first.")
            return

        out_folder = self.out_var.get().strip()
        if not out_folder or not os.path.exists(out_folder):
            messagebox.showwarning("Notice", "Please specify a valid destination folder.")
            return

        rot_val = self.rot_seg.get()
        angle = 0
        if "90" in rot_val: angle = 90
        elif "180" in rot_val: angle = 180
        elif "270" in rot_val: angle = 270

        del_set = self._parse_delete_pages(self.del_pages_var.get())
        self.output_directory = out_folder
        self.btn_execute.configure(state="disabled")

        def _task():
            total = len(self.file_paths)
            self.log(f"Processing page management for {total} document(s)...")

            for i, p in enumerate(self.file_paths):
                reader = PdfReader(p)
                writer = PdfWriter()
                base_name = os.path.splitext(os.path.basename(p))[0]

                for p_idx, page in enumerate(reader.pages):
                    if p_idx in del_set:
                        self.log(f"Pruned page {p_idx+1} from {base_name}")
                        continue
                    if angle != 0:
                        page.rotate(angle)
                    writer.add_page(page)

                out_path = os.path.join(out_folder, f"{base_name}_adjusted.pdf")
                with open(out_path, "wb") as f_out:
                    writer.write(f_out)

                self.log(f"✓ Saved adjusted file: {os.path.basename(out_path)}")
                self.set_progress((i + 1) / total * 0.9)

            return out_folder

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"All adjustments applied successfully!\nSaved to: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Failed to apply adjustments: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
