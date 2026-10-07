"""Tool 4.8: Dominant Color Palette Harvester.

Extracts top 5 dominant aesthetic colors from thumbnails, artwork, or photos
with exact Hex and RGB swatches and one-click CSS variable generation.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class PaletteHarvesterTool(BaseToolFrame):
    """Universal 2-pane tool for extracting color palettes from images."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="image_palette_harvest",
            title="Dominant Color Palette Harvester",
            description="Extract top 5 dominant colors from thumbnails or graphics with instant Hex & CSS codes.",
            **kwargs
        )
        self.image_path = ""
        self.extracted_colors = []

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # File Select Button
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM))

        btn_pick = ctk.CTkButton(
            btn_row,
            text="🖼️ Select Source Image",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            height=36,
            command=self._select_image
        )
        btn_pick.pack(fill="x")

        # Image Info Label
        self.info_lbl = ctk.CTkLabel(
            container,
            text="No image selected",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        self.info_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Swatches Display Container
        swatch_lbl = ctk.CTkLabel(
            container,
            text="DOMINANT COLOR SWATCHES",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        swatch_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.swatches_frame = ctk.CTkFrame(container, fg_color=Theme.SURFACE_INSET, corner_radius=Theme.RADIUS_CARD)
        self.swatches_frame.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        self.swatch_widgets = []
        for i in range(5):
            row = ctk.CTkFrame(self.swatches_frame, fg_color="transparent")
            row.pack(fill="x", padx=Theme.PAD_SM, pady=Theme.PAD_XS)

            chip = ctk.CTkLabel(row, text="", width=28, height=28, corner_radius=6, fg_color=Theme.SURFACE_CARD)
            chip.pack(side="left", padx=(0, Theme.PAD_SM))

            code_lbl = ctk.CTkLabel(row, text="--", font=(Theme.FONT_MONO, 12), text_color=Theme.TEXT_PRIMARY)
            code_lbl.pack(side="left")

            btn_copy = ctk.CTkButton(
                row,
                text="Copy Hex",
                width=70,
                height=26,
                font=(Theme.FONT_FAMILY, 10),
                fg_color=Theme.SURFACE_CARD,
                hover_color=Theme.SURFACE_CARD_HOVER,
                text_color=Theme.TEXT_SECONDARY,
                command=lambda idx=i: self._copy_color(idx)
            )
            btn_copy.pack(side="right")

            self.swatch_widgets.append((chip, code_lbl, btn_copy))

        # Copy All CSS Variables CTA
        btn_copy_css = ctk.CTkButton(
            container,
            text="📋  Copy All as CSS Variables",
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            height=36,
            command=self._copy_all_css
        )
        btn_copy_css.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

    def _select_image(self):
        path = filedialog.askopenfilename(
            title="Select Image to Extract Colors",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp *.bmp")]
        )
        if path:
            self.image_path = path
            fname = os.path.basename(path)
            self.info_lbl.configure(text=f"Selected: {fname}")
            self._extract_colors()

    def _extract_colors(self):
        if not self.image_path:
            return

        def _task():
            self.log(f"Analyzing color distribution for: {os.path.basename(self.image_path)}...")
            with Image.open(self.image_path) as img:
                # Resize for fast sampling
                small = img.resize((150, 150)).convert("P", palette=Image.Palette.ADAPTIVE, colors=5)
                palette = small.getpalette()
                color_counts = sorted(small.getcolors(), reverse=True)

                colors = []
                for count, col_idx in color_counts[:5]:
                    r = palette[col_idx * 3]
                    g = palette[col_idx * 3 + 1]
                    b = palette[col_idx * 3 + 2]
                    hex_code = f"#{r:02x}{g:02x}{b:02x}".upper()
                    colors.append((hex_code, (r, g, b)))
                return colors

        def _on_done(colors):
            self.extracted_colors = colors
            for idx, (hex_code, (r, g, b)) in enumerate(colors):
                if idx < len(self.swatch_widgets):
                    chip, code_lbl, _ = self.swatch_widgets[idx]
                    chip.configure(fg_color=hex_code)
                    code_lbl.configure(text=f"{hex_code}  rgb({r}, {g}, {b})")
            
            self.log("✓ Successfully extracted top 5 dominant colors:")
            for hx, rgb in colors:
                self.log(f"  • {hx}  -> rgb{rgb}")

        self.execute_async(_task, on_success=_on_done)

    def _copy_color(self, idx: int):
        if idx < len(self.extracted_colors):
            hex_code = self.extracted_colors[idx][0]
            self.clipboard_clear()
            self.clipboard_append(hex_code)
            messagebox.showinfo("Copied", f"Copied {hex_code} to clipboard!")

    def _copy_all_css(self):
        if not self.extracted_colors:
            return
        lines = [":root {"]
        for idx, (hx, _) in enumerate(self.extracted_colors):
            lines.append(f"  --palette-color-{idx+1}: {hx};")
        lines.append("}")
        css_str = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(css_str)
        messagebox.showinfo("Copied", "Copied CSS variables palette to clipboard!")
