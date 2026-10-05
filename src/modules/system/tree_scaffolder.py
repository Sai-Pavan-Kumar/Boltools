"""Project Tree Structure Scaffolder.

Parses ASCII folder tree diagrams and instantly scaffolds the entire directory
and placeholder file hierarchy on your hard drive with 1 click.
"""

import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class TreeScaffolderTool(BaseToolFrame):
    """Universal 2-pane tool for generating project directory scaffolds from ASCII trees."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="system_tree_scaffold",
            title="Project Tree Structure Scaffolder",
            description="Paste any ASCII project tree diagram and automatically generate all folders & files on disk.",
            **kwargs
        )

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # ASCII Input Label
        tree_lbl = ctk.CTkLabel(
            container,
            text="PASTE YOUR PROJECT TREE DIAGRAM BELOW:",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        tree_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

        sample_tree = """my_project/
├── public/
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── Header.tsx
│   │   └── Footer.tsx
│   ├── utils/
│   │   └── helpers.ts
│   └── index.ts
├── package.json
└── README.md"""

        self.tree_textbox = ctk.CTkTextbox(
            container,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            font=(Theme.FONT_MONO, 11),
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_INPUT,
            height=160
        )
        self.tree_textbox.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))
        self.tree_textbox.insert("1.0", sample_tree)

        # Destination Folder
        dest_lbl = ctk.CTkLabel(
            container,
            text="ROOT GENERATION DIRECTORY",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        dest_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        dest_row = ctk.CTkFrame(container, fg_color="transparent")
        dest_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        self.out_var = tk.StringVar(value=os.path.expanduser("~/Projects") if os.path.exists(os.path.expanduser("~/Projects")) else os.path.expanduser("~/Documents"))
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
            text="🚀  Scaffold Project Structure",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=42,
            command=self._execute
        )
        self.btn_execute.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Root Directory")
        if folder:
            self.out_var.set(folder)

    def _execute(self):
        tree_text = self.tree_textbox.get("1.0", "end").strip()
        if not tree_text:
            messagebox.showwarning("Notice", "Please paste an ASCII tree structure.")
            return

        base_path = self.out_var.get().strip()
        if not base_path or not os.path.exists(base_path):
            messagebox.showwarning("Notice", "Please select a valid generation directory.")
            return

        self.output_directory = base_path
        self.btn_execute.configure(state="disabled")

        def _task():
            lines = tree_text.split('\n')
            path_stack = [] # (indent_level, folder_path)
            created_dirs = 0
            created_files = 0

            self.log(f"Starting scaffold in: {base_path}\n")

            for line in lines:
                clean_line = line.split('#')[0].rstrip()
                if not clean_line.strip():
                    continue

                match = re.match(r'^([\s│├└─]+)(.*)', clean_line)
                if match:
                    prefix = match.group(1)
                    name = match.group(2).strip()
                else:
                    prefix = ""
                    name = clean_line.strip()

                clean_name = name.rstrip('/')
                if not clean_name:
                    continue

                current_indent = len(prefix)

                # Pop stack to parent level
                while path_stack and path_stack[-1][0] >= current_indent:
                    path_stack.pop()

                parent = path_stack[-1][1] if path_stack else base_path
                full_path = os.path.join(parent, clean_name)

                # Decision: File or Folder?
                is_file = '.' in clean_name and not name.endswith('/')

                if is_file:
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    if not os.path.exists(full_path):
                        with open(full_path, 'w', encoding='utf-8') as f:
                            pass
                        self.log(f"📄 File:   {clean_name}")
                        created_files += 1
                    else:
                        self.log(f"⚠️ Exists: {clean_name}")
                else:
                    os.makedirs(full_path, exist_ok=True)
                    self.log(f"📁 Folder: {clean_name}")
                    created_dirs += 1
                    path_stack.append((current_indent, full_path))

            self.log(f"\n✓ Scaffolding complete! Created {created_dirs} folder(s) and {created_files} file(s).")
            return base_path

        def _on_done(result):
            self.btn_execute.configure(state="normal")
            messagebox.showinfo("Success", f"Project structure scaffolded successfully!\nLocation: {result}")

        def _on_err(err):
            self.btn_execute.configure(state="normal")
            messagebox.showerror("Error", f"Scaffolding failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)
