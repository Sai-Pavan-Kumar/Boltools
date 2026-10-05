"""Tool 3.2: Master Document Split & Merge Hub.

Combines unlimited PDF files or splits documents into individual sheets or custom ranges.
100% offline, zero quality loss.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk
from pypdf import PdfReader, PdfWriter

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class PdfSplitMergeTool(BaseToolFrame):
    """Universal 2-pane tool for splitting and merging PDF documents."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="pdf_split_merge",
            title="Master Document Split & Merge Hub",
            description="Merge unlimited PDF documents together or slice documents into separate pages or ranges.",
            **kwargs
        )
        self.file_paths: List[str] = []

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # Mode Selection Segmented Button
        mode_lbl = ctk.CTkLabel(
            container,
            text="CHOOSE OPERATION",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        mode_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

        self.mode_var = tk.StringVar(value="merge")
        self.seg_mode = ctk.CTkSegmentedButton(
            container,
            values=["Merge Documents", "Split Document"],
            command=self._on_mode_change,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            selected_color=Theme.BRAND_PRIMARY,
            selected_hover_color=Theme.BRAND_HOVER,
            unselected_color=Theme.SURFACE_INSET,
            height=34
        )
        self.seg_mode.set("Merge Documents")
        self.seg_mode.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # File Selection Header & Buttons
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.btn_add = ctk.CTkButton(
            btn_row,
            text="+ Add Files",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            height=32,
            command=self._add_files
        )
        self.btn_add.pack(side="left", padx=(0, Theme.PAD_SM))

        self.btn_clear = ctk.CTkButton(
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
        self.btn_clear.pack(side="right")

        # Files Counter
        self.counter_lbl = ctk.CTkLabel(
            container,
            text="No documents selected",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        self.counter_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_XS))

        # Files Preview Box
        self.preview_box = ctk.CTkTextbox(
            container,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_SECONDARY,
            font=(Theme.FONT_MONO, 11),
            corner_radius=Theme.RADIUS_INPUT,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            height=120
        )
        self.preview_box.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        self.preview_box.configure(state="disabled")

        # Options Container for Split (e.g. Page Range)
        self.split_options_frame = ctk.CTkFrame(container, fg_color="transparent")

        split_lbl = ctk.CTkLabel(
            self.split_options_frame,
            text="SPLIT RULE (Optional Range e.g. 1-3, 5, 8-10 or leave blank for all pages):",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        split_lbl.pack(fill="x", pady=(0, 4))

        self.split_range_var = tk.StringVar(value="")
        self.entry_split_range = ctk.CTkEntry(
            self.split_options_frame,
            textvariable=self.split_range_var,
            placeholder_text="Leave blank to export every page as a separate PDF",
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.entry_split_range.pack(fill="x", pady=(0, Theme.PAD_SM))

        # Output Destination
        out_lbl = ctk.CTkLabel(
            container,
            text="DESTINATION",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        out_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        out_row = ctk.CTkFrame(container, fg_color="transparent")
        out_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        self.out_var = tk.StringVar(value=os.path.join(os.path.expanduser("~/Documents"), "merged_output.pdf"))
        self.entry_out = ctk.CTkEntry(
            out_row,
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
            out_row,
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
            command=self._browse_destination
        )
        btn_browse.pack(side="right")

        # Action Execute CTA
        self.btn_execute = ctk.CTkButton(
            container,
            text="⚡  Start Process",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=42,
            command=self._execute
        )
        self.btn_execute.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

    def _on_mode_change(self, value):
        if "Split" in value:
            self.split_options_frame.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
            self.btn_execute.configure(text="✂️  Split Documents")
            # If current destination ends in .pdf, change to folder
            curr = self.out_var.get()
            if curr.endswith(".pdf"):
                self.out_var.set(os.path.dirname(curr))
        else:
            self.split_options_frame.pack_forget()
            self.btn_execute.configure(text="📄  Merge Documents")
            curr = self.out_var.get()
            if not curr.endswith(".pdf"):
                self.out_var.set(os.path.join(curr, "merged_output.pdf"))

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

    def _browse_destination(self):
        is_split = "Split" in self.seg_mode.get()
        if is_split:
            folder = filedialog.askdirectory(title="Select Destination Folder")
            if folder:
                self.out_var.set(folder)
        else:
            path = filedialog.asksaveasfilename(
                title="Save Merged PDF As",
                defaultextension=".pdf",
                filetypes=[("PDF Document", "*.pdf")],
                initialfile="merged_output.pdf"
            )
            if path:
                self.out_var.set(path)

    def _update_preview(self):
        n = len(self.file_paths)
        txt = f"{n} document{'s' if n != 1 else ''} loaded" if n else "No documents selected"
        self.counter_lbl.configure(text=txt)

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        for idx, p in enumerate(self.file_paths):
            self.preview_box.insert("end", f"{idx+1}. {os.path.basename(p)}\n")
        self.preview_box.configure(state="disabled")

    def _parse_ranges(self, range_str: str, max_pages: int) -> List[int]:
        """Parses strings like '1-3, 5, 8' into 0-indexed page integers."""
        if not range_str.strip():
            return list(range(max_pages))
        
        pages = set()
        parts = range_str.split(",")
        for part in parts:
            part = part.strip()
            if "-" in part:
                try:
                    start_s, end_s = part.split("-", 1)
                    start = max(1, int(start_s))
                    end = min(max_pages, int(end_s))
                    for p in range(start, end + 1):
                        pages.add(p - 1)
                except ValueError:
                    continue
            elif part.isdigit():
                p = int(part)
                if 1 <= p <= max_pages:
                    pages.add(p - 1)
        return sorted(list(pages))

    def _execute(self):
        if not self.file_paths:
            messagebox.showwarning("Notice", "Please select at least one PDF file first.")
            return

        dest = self.out_var.get().strip()
        if not dest:
            messagebox.showwarning("Notice", "Please specify a destination path.")
            return

        is_split = "Split" in self.seg_mode.get()
        self.btn_execute.configure(state="disabled")

        if is_split:
            self.output_directory = dest if os.path.isdir(dest) else os.path.dirname(dest)
        else:
            self.output_directory = os.path.dirname(dest)

        def _task():
            if not is_split:
                # ── MERGE MODE
                merger = PdfWriter()
                total = len(self.file_paths)
                self.log(f"Merging {total} document(s)...")

                for i, p in enumerate(self.file_paths):
                    self.log(f"Appending: {os.path.basename(p)}")
                    merger.append(p)
                    self.set_progress((i + 1) / total * 0.85)

                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as f_out:
                    merger.write(f_out)
                merger.close()

                self.log(f"✓ Merge complete: {dest}")
                return dest
            else:
                # ── SPLIT MODE
                folder = dest if os.path.isdir(dest) else os.path.dirname(dest)
                os.makedirs(folder, exist_ok=True)
                range_spec = self.split_range_var.get().strip()
                total_files = len(self.file_paths)
                total_slices = 0

                for fi, p in enumerate(self.file_paths):
                    reader = PdfReader(p)
                    base = os.path.splitext(os.path.basename(p))[0]
                    target_pages = self._parse_ranges(range_spec, len(reader.pages))

                    self.log(f"Splitting {base} ({len(target_pages)} target pages)...")

                    for pi in target_pages:
                        writer = PdfWriter()
                        writer.add_page(reader.pages[pi])
                        out_file = os.path.join(folder, f"{base}_page_{pi+1}.pdf")
                        with open(out_file, "wb") as f_slice:
                            writer.write(f_slice)
                        total_slices += 1

                    self.set_progress((fi + 1) / total_files * 0.9)

                self.log(f"✓ Split complete! Saved {total_slices} page files to: {folder}")
                return folder

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"Operation completed successfully!\nResult saved to: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Operation failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
