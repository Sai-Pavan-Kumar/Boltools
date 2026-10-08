"""Tool: Power Batch File Renamer.

Rule-based batch renaming: prefix, suffix, sequential numbering, find-and-replace,
and case transformation with live preview before applying. 100% offline.
"""

import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
import customtkinter as ctk

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class BatchRenamerTool(BaseToolFrame):
    """Universal 2-pane tool for batch rule-based file renaming."""

    def __init__(self, master, **kwargs):
        self.file_paths: List[str] = []

        super().__init__(
            master=master,
            tool_id="system_batch_rename",
            title="Bulk File & Folder Renamer",
            description="Batch rename files with rule-based prefix, suffix, sequence numbering, and find-and-replace locally.",
            category_id="system",
            **kwargs
        )

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
            font=Theme.FONT_BODY_BOLD,
            height=32,
            command=self._add_files
        )
        btn_add.pack(side="left", padx=(0, Theme.PAD_SM))

        btn_folder = ctk.CTkButton(
            btn_row,
            text="Add Folder",
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.RADIUS_BUTTON,
            font=Theme.FONT_BODY,
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
            font=Theme.FONT_BODY,
            height=32,
            width=60,
            command=self._clear_files
        )
        btn_clear.pack(side="right")

        # Files Counter & List Box
        self.counter_lbl = ctk.CTkLabel(
            container,
            text="No files loaded",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        self.counter_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_XS))

        # Rename Rule Selection
        rule_lbl = ctk.CTkLabel(
            container,
            text="RENAMING RULE",
            font=(Theme.FONT_FAMILY, 10, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        rule_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.rule_var = tk.StringVar(value="Add Suffix")
        self.combo_rule = ctk.CTkComboBox(
            container,
            values=[
                "Add Prefix (e.g. 2026_)",
                "Add Suffix (e.g. _final)",
                "Sequential Numbering (_01, _02...)",
                "Find & Replace String",
                "Lowercase all characters",
                "UPPERCASE all characters"
            ],
            variable=self.rule_var,
            command=self._on_rule_change,
            font=Theme.FONT_BODY,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.combo_rule.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Text Input 1 (Prefix / Suffix / Find)
        self.text1_lbl = ctk.CTkLabel(
            container,
            text="SUFFIX TO ADD:",
            font=(Theme.FONT_FAMILY, 10, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        self.text1_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_XS, 2))

        self.text1_var = tk.StringVar(value="_v1")
        self.text1_var.trace_add("write", lambda *args: self._update_preview())
        self.entry_text1 = ctk.CTkEntry(
            container,
            textvariable=self.text1_var,
            font=Theme.FONT_BODY,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.entry_text1.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Text Input 2 (Replace with - initially hidden)
        self.replace_frame = ctk.CTkFrame(container, fg_color="transparent")
        
        rep_lbl = ctk.CTkLabel(
            self.replace_frame,
            text="REPLACE WITH:",
            font=(Theme.FONT_FAMILY, 10, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        rep_lbl.pack(fill="x", pady=(0, 2))

        self.text2_var = tk.StringVar(value="")
        self.text2_var.trace_add("write", lambda *args: self._update_preview())
        self.entry_text2 = ctk.CTkEntry(
            self.replace_frame,
            textvariable=self.text2_var,
            font=Theme.FONT_BODY,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.entry_text2.pack(fill="x")

        # Destination Mode
        mode_lbl = ctk.CTkLabel(
            container,
            text="OUTPUT OPERATION",
            font=(Theme.FONT_FAMILY, 10, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        mode_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.op_mode_var = tk.StringVar(value="Rename In-Place")
        self.seg_op = ctk.CTkSegmentedButton(
            container,
            values=["Rename In-Place", "Copy to New Folder"],
            variable=self.op_mode_var,
            command=self._on_op_change,
            font=Theme.FONT_BODY_BOLD,
            selected_color=Theme.BRAND_PRIMARY,
            selected_hover_color=Theme.BRAND_HOVER,
            unselected_color=Theme.SURFACE_INSET,
            height=34
        )
        self.seg_op.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Destination Folder Picker (Hidden unless Copy to New Folder)
        self.dest_picker_frame = ctk.CTkFrame(container, fg_color="transparent")

        self.out_var = tk.StringVar(value=os.path.expanduser("~/Documents"))
        self.entry_out = ctk.CTkEntry(
            self.dest_picker_frame,
            textvariable=self.out_var,
            font=Theme.FONT_BODY,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=34
        )
        self.entry_out.pack(side="left", fill="x", expand=True, padx=(0, Theme.PAD_SM))

        btn_browse = ctk.CTkButton(
            self.dest_picker_frame,
            text="Browse",
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.RADIUS_BUTTON,
            font=Theme.FONT_BODY,
            height=34,
            width=70,
            command=self._browse_folder
        )
        btn_browse.pack(side="right")

        # Execute CTA
        self.btn_execute = ctk.CTkButton(
            container,
            text="Apply Renaming Rules →",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=Theme.FONT_BODY_BOLD,
            height=42,
            command=self._execute
        )
        self.btn_execute.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

    def _on_rule_change(self, choice):
        if "Find & Replace" in choice:
            self.text1_lbl.configure(text="FIND STRING:")
            self.replace_frame.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        else:
            self.replace_frame.pack_forget()
            if "Prefix" in choice: self.text1_lbl.configure(text="PREFIX TO ADD:")
            elif "Suffix" in choice: self.text1_lbl.configure(text="SUFFIX TO ADD:")
            elif "Numbering" in choice: self.text1_lbl.configure(text="START NUMBER (e.g. 1):")
            else: self.text1_lbl.configure(text="OPTIONAL PARAM:")
        self._update_preview()

    def _on_op_change(self, choice):
        if "Copy" in choice:
            self.dest_picker_frame.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        else:
            self.dest_picker_frame.pack_forget()

    def _add_files(self):
        paths = filedialog.askopenfilenames(title="Select Files to Rename")
        if paths:
            for p in paths:
                if p not in self.file_paths:
                    self.file_paths.append(p)
            self._update_preview()

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            count = 0
            for fname in sorted(os.listdir(folder)):
                full_p = os.path.join(folder, fname)
                if os.path.isfile(full_p) and full_p not in self.file_paths:
                    self.file_paths.append(full_p)
                    count += 1
            self.log(f"Loaded {count} files from folder: {folder}")
            self._update_preview()

    def _clear_files(self):
        self.file_paths.clear()
        self._update_preview()

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.out_var.set(folder)

    def _compute_new_name(self, idx: int, orig_name: str) -> str:
        base, ext = os.path.splitext(orig_name)
        rule = self.rule_var.get()
        param1 = self.text1_var.get()
        param2 = self.text2_var.get()

        if "Prefix" in rule:
            return f"{param1}{base}{ext}"
        elif "Suffix" in rule:
            return f"{base}{param1}{ext}"
        elif "Numbering" in rule:
            start_num = int(param1) if param1.isdigit() else 1
            num_str = f"{start_num + idx:02d}"
            return f"{base}_{num_str}{ext}"
        elif "Find & Replace" in rule:
            new_base = base.replace(param1, param2) if param1 else base
            return f"{new_base}{ext}"
        elif "Lowercase" in rule:
            return f"{base.lower()}{ext.lower()}"
        elif "UPPERCASE" in rule:
            return f"{base.upper()}{ext.upper()}"
        return orig_name

    def _update_preview(self):
        n = len(self.file_paths)
        txt = f"{n} file{'s' if n != 1 else ''} loaded" if n else "No files loaded"
        self.counter_lbl.configure(text=txt)

        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.insert("end", "=== LIVE RENAMING PREVIEW ===\n\n")

        for idx, p in enumerate(self.file_paths[:15]):
            orig_name = os.path.basename(p)
            new_name = self._compute_new_name(idx, orig_name)
            self.log_box.insert("end", f"{orig_name}  ➔  {new_name}\n")

        if len(self.file_paths) > 15:
            self.log_box.insert("end", f"\n... and {len(self.file_paths) - 15} more files.\n")
        self.log_box.configure(state="disabled")

    def _execute(self):
        if not self.file_paths:
            messagebox.showwarning("Notice", "Please select at least one file to rename.")
            return

        is_copy = "Copy" in self.op_mode_var.get()
        dest_folder = self.out_var.get().strip()
        if is_copy and (not dest_folder or not os.path.exists(dest_folder)):
            messagebox.showwarning("Notice", "Please provide a valid output folder.")
            return

        self.btn_execute.configure(state="disabled")

        def _task():
            total = len(self.file_paths)
            self.log(f"Starting batch renaming for {total} files...")

            for idx, p in enumerate(self.file_paths):
                parent_dir = os.path.dirname(p)
                orig_name = os.path.basename(p)
                new_name = self._compute_new_name(idx, orig_name)

                if is_copy:
                    target_path = os.path.join(dest_folder, new_name)
                    shutil.copy2(p, target_path)
                    self.log(f"[{idx+1}/{total}] Copied: {orig_name} ➔ {new_name}")
                else:
                    target_path = os.path.join(parent_dir, new_name)
                    if p != target_path:
                        os.rename(p, target_path)
                        self.log(f"[{idx+1}/{total}] Renamed: {orig_name} ➔ {new_name}")
                    else:
                        self.log(f"[{idx+1}/{total}] Skipped unchanged: {orig_name}")

                self.set_progress((idx + 1) / total * 0.9)

            return dest_folder if is_copy else os.path.dirname(self.file_paths[0])

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            self.file_paths.clear()
            self._update_preview()
            self.render_completion_stage("Batch Renaming Complete", f"All files renamed successfully in {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Renaming failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
