"""Theme tokens and styling specifications for Boltools.

Enforces Apple macOS and The SurfBoard Design System standards:
- Dynamic Dual-Token System: Seamless (Light, Dark) mode support across all widgets
- Layered Surface Architecture: Subtle contrast, depth, and elevation
- Hairline Dividers: 1px high-precision borders
- Harmonic Typography: Segoe UI hierarchy with crisp weights and tracking
"""

from typing import Tuple


class Theme:
    """Central design token registry for Boltools desktop suite."""

    # ── Layered Surface Palette (Light, Dark)
    SURFACE_BASE: Tuple[str, str] = ("#F5F6F9", "#0B0E14")        # Window background canvas
    SURFACE_SIDEBAR: Tuple[str, str] = ("#EBF0F6", "#0F131D")     # Navigation panel
    SURFACE_CARD: Tuple[str, str] = ("#FFFFFF", "#131824")        # Primary content card
    SURFACE_CARD_HOVER: Tuple[str, str] = ("#F1F5F9", "#1A2234")  # Hover interaction state
    SURFACE_ELEVATED: Tuple[str, str] = ("#FFFFFF", "#1B2232")    # Modals, toolbars, popovers
    SURFACE_INSET: Tuple[str, str] = ("#EDF1F7", "#07090E")       # Deep dropzones, activity feed
    SURFACE_PILL: Tuple[str, str] = ("#E2E8F0", "#1C2436")        # Micro-badges and tags

    # ── Brand & Signature Accents (Light, Dark)
    BRAND_PRIMARY: Tuple[str, str] = ("#005AE0", "#005AE0")       # SurfBoard Signature Electric Blue
    BRAND_HOVER: Tuple[str, str] = ("#0047B3", "#1268C0")         # Button active/hover state
    BRAND_LIGHT: Tuple[str, str] = ("#EBF2FF", "#0A254D")         # Tinted brand badge background
    BRAND_ACCENT: Tuple[str, str] = ("#005AE0", "#38BDF8")        # Cyan glow highlight in dark mode

    # ── Hairline Borders & Dividers (Light, Dark)
    BORDER_SUBTLE: Tuple[str, str] = ("#E2E8F0", "#1E2638")       # Hairline 1px border
    BORDER_HOVER: Tuple[str, str] = ("#CBD5E1", "#2D3B55")        # Card hover border highlight
    BORDER_ACTIVE: Tuple[str, str] = ("#005AE0", "#005AE0")       # Focused input border
    BORDER_LIGHT: Tuple[str, str] = ("#F1F5F9", "#151B29")        # Minimal inner divider

    # ── High-Contrast Typography Palette (Light, Dark)
    TEXT_PRIMARY: Tuple[str, str] = ("#0F172A", "#F1F5F9")        # Primary titles and body copy
    TEXT_SECONDARY: Tuple[str, str] = ("#64748B", "#94A3B8")      # Subtitles and descriptions
    TEXT_MUTED: Tuple[str, str] = ("#94A3B8", "#475569")          # Micro-labels, shortcuts, hints
    TEXT_ON_BRAND: Tuple[str, str] = ("#FFFFFF", "#FFFFFF")       # Crisp white on brand buttons

    # ── Semantic Feedback Tokens (Light, Dark)
    STATUS_SUCCESS: Tuple[str, str] = ("#10B981", "#10B981")      # Complete / Healthy state
    STATUS_SUCCESS_BG: Tuple[str, str] = ("#ECFDF5", "#064E3B")   # Soft green container
    STATUS_ERROR: Tuple[str, str] = ("#EF4444", "#EF4444")        # Error state
    STATUS_ERROR_BG: Tuple[str, str] = ("#FEF2F2", "#450A0A")      # Soft red container
    STATUS_WARNING: Tuple[str, str] = ("#F59E0B", "#F59E0B")      # Attention / Warning
    STATUS_WARNING_BG: Tuple[str, str] = ("#FFFBEB", "#451A03")    # Soft amber container
    STATUS_INFO: Tuple[str, str] = ("#3B82F6", "#38BDF8")         # Information / In-progress

    # ── Option 3 Precision Typography Scale (Instrument Sans + Satoshi + DM Mono)
    FONT_DISPLAY_FAMILY = "Instrument Sans"
    FONT_BODY_FAMILY = "Satoshi"
    FONT_MONO_FAMILY = "DM Mono"

    # Backward-compatible family aliases for modules
    FONT_FAMILY = FONT_BODY_FAMILY
    FONT_MONO = FONT_MONO_FAMILY

    # Quiet, elegant weights (no aggressive shouting bold)
    FONT_DISPLAY = (FONT_DISPLAY_FAMILY, 18, "normal")
    FONT_TITLE = (FONT_DISPLAY_FAMILY, 14, "bold")
    FONT_SUBTITLE = (FONT_BODY_FAMILY, 12, "bold")
    FONT_BODY = (FONT_BODY_FAMILY, 12, "normal")
    FONT_BODY_BOLD = (FONT_BODY_FAMILY, 12, "bold")
    FONT_LABEL = (FONT_BODY_FAMILY, 11, "normal")
    FONT_CAPTION = (FONT_BODY_FAMILY, 10, "normal")
    FONT_MONO_TEXT = (FONT_MONO_FAMILY, 10, "normal")

    # ── Corner Radii (Apple-grade squircles)
    RADIUS_INPUT = 8
    RADIUS_BUTTON = 8
    RADIUS_CARD = 12
    RADIUS_PILL = 20
    RADIUS_MODAL = 14

    # ── Spacing Rhythm (Strict 4px/8px grid)
    PAD_XS = 4
    PAD_SM = 8
    PAD_MD = 16
    PAD_LG = 24
    PAD_XL = 32

    _fonts_registered = False

    @classmethod
    def register_custom_fonts(cls):
        """Registers bundled Instrument Sans, Satoshi, and DM Mono fonts with Windows GDI."""
        if cls._fonts_registered:
            return
        cls._fonts_registered = True
        try:
            import os
            import sys
            import ctypes
            from src.core.paths import get_asset_path
            
            fonts_dir = get_asset_path("fonts")
            if os.path.exists(fonts_dir) and sys.platform.startswith("win"):
                FR_PRIVATE = 0x10
                for f in os.listdir(fonts_dir):
                    if f.lower().endswith((".ttf", ".otf")):
                        font_path = os.path.join(fonts_dir, f)
                        ctypes.windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0)
        except Exception:
            pass

    @classmethod
    def apply_appearance(cls, mode: str = "Dark"):
        """Sets CustomTkinter global appearance defaults and registers custom fonts."""
        cls.register_custom_fonts()
        import customtkinter as ctk
        ctk.set_appearance_mode(mode)
        ctk.set_default_color_theme("blue")
