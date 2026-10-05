"""Top application header with official Boltools and The SurfBoard branding."""

import os
from typing import Callable, Optional
import customtkinter as ctk
from PIL import Image

from src.core.theme import Theme


class AppHeader(ctk.CTkFrame):
    """Header bar featuring brand assets, subtitle, and search palette trigger."""

    def __init__(
        self,
        master,
        assets_dir: str,
        on_search_click: Callable[[], None],
        on_home_click: Callable[[], None],
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=Theme.SURFACE_SIDEBAR,
            height=60,
            corner_radius=0,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            **kwargs
        )
        self.grid_propagate(False)
        self.assets_dir = assets_dir
        self.on_search_click = on_search_click
        self.on_home_click = on_home_click
        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self._build_branding()
        self._build_search_trigger()

    def _load_image(self, filename: str, size: tuple[int, int]) -> Optional[ctk.CTkImage]:
        path = os.path.join(self.assets_dir, filename)
        if os.path.exists(path):
            try:
                pil_img = Image.open(path)
                return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            except Exception as e:
                print(f"[Boltools Asset Error] Failed to load {filename}: {e}")
        return None

    def _build_branding(self):
        # Clickable brand container returning to Home
        brand_container = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        brand_container.grid(row=0, column=0, sticky="w", padx=Theme.PAD_MD, pady=Theme.PAD_SM)
        brand_container.bind("<Button-1>", lambda e: self.on_home_click())

        # Monogram Bolt Logo
        bolt_img = self._load_image("bolt_logo.webp", (32, 32))
        if bolt_img:
            bolt_label = ctk.CTkLabel(brand_container, image=bolt_img, text="")
            bolt_label.pack(side="left", padx=(0, Theme.PAD_SM))

        # Title & Subtitle column
        text_col = ctk.CTkFrame(brand_container, fg_color="transparent")
        text_col.pack(side="left", fill="y")
        
        title_lbl = ctk.CTkLabel(
            text_col,
            text="BOLTOOLS",
            font=(Theme.FONT_FAMILY, 15, "bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title_lbl.pack(anchor="w")
        
        # Subtitle with SurfBoard brand
        sub_row = ctk.CTkFrame(text_col, fg_color="transparent")
        sub_row.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            sub_row,
            text="Built by The SurfBoard",
            font=(Theme.FONT_FAMILY, 11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        sub_lbl.pack(side="left")

        surfboard_img = self._load_image("surfboard_logo.png", (14, 14))
        if surfboard_img:
            surf_icon = ctk.CTkLabel(sub_row, image=surfboard_img, text="")
            surf_icon.pack(side="left", padx=(4, 0))

    def _build_search_trigger(self):
        # Raycast-style search bar trigger button
        search_btn = ctk.CTkButton(
            self,
            text="Search all 57 tools...            Ctrl + K",
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_MUTED,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12),
            height=34,
            command=self.on_search_click
        )
        search_btn.grid(row=0, column=2, sticky="e", padx=Theme.PAD_LG, pady=Theme.PAD_SM)
