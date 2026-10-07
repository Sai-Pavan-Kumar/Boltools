"""Theme tokens and styling specifications for Boltools.

Enforces Apple Pro and Linear-grade design standards from DESIGN_AND_TECH_STACK.md:
- Exact SurfBoard color tokens (Dark / Light)
- High-contrast typography scale (Segoe UI / Inter font stack)
- Strict 4px/8px grid rhythms
- Zero cartoon emojis, zero cheap hype gradients
"""

import os
import sys
import ctypes
from typing import Tuple

from src.core.paths import get_asset_path

_FONTS_REGISTERED = False


def _register_custom_fonts():
    """Dynamically registers Instrument Sans and DM Mono into Windows GDI font table."""
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED or sys.platform != "win32":
        return
    try:
        fonts_dir = os.path.join(get_asset_path(), "fonts")
        if os.path.exists(fonts_dir):
            for fname in ["InstrumentSans-Variable.ttf", "DMMono-Regular.ttf", "DMMono-Medium.ttf"]:
                fpath = os.path.join(fonts_dir, fname)
                if os.path.exists(fpath):
                    ctypes.windll.gdi32.AddFontResourceExW(os.path.abspath(fpath), 0x10, 0)
        _FONTS_REGISTERED = True
    except Exception:
        pass


# Register immediately on module load
_register_custom_fonts()


class Theme:
    """Central design token registry for Boltools desktop suite."""

    # ── Layered Surface Palette (Light, Dark)
    SURFACE_BASE: Tuple[str, str] = ("#F8FAFC", "#09090F")        # Main background
    SURFACE_SIDEBAR: Tuple[str, str] = ("#F1F5F9", "#0D0D15")     # Sidebar background
    SURFACE_CARD: Tuple[str, str] = ("#FFFFFF", "#12121E")        # Card & container background
    SURFACE_CARD_HOVER: Tuple[str, str] = ("#F8FAFC", "#181828")  # Interactive hover state
    SURFACE_INSET: Tuple[str, str] = ("#EEF2F6", "#06060A")       # Dropzones, text inputs, progress
    SURFACE_PILL: Tuple[str, str] = ("#E2E8F0", "#1C1C2E")        # Subtle badges & tags

    # ── Brand & Signature Accents (Light, Dark)
    BRAND_PRIMARY: Tuple[str, str] = ("#005AE0", "#005AE0")       # SurfBoard Signature Blue
    BRAND_HOVER: Tuple[str, str] = ("#0047B3", "#1268C0")         # Button hover
    BRAND_LIGHT: Tuple[str, str] = ("#EBF2FF", "#0A254D")         # Tinted active state
    BRAND_ACCENT: Tuple[str, str] = ("#005AE0", "#38BDF8")        # Focus highlight

    # ── Hairline Borders & Dividers (Light, Dark)
    BORDER_SUBTLE: Tuple[str, str] = ("#E2E8F0", "#182032")       # 1px hairline border
    BORDER_HOVER: Tuple[str, str] = ("#CBD5E1", "#283550")        # Card hover border
    BORDER_ACTIVE: Tuple[str, str] = ("#005AE0", "#005AE0")       # Focused border

    # ── High-Contrast Typography Palette (Light, Dark)
    TEXT_PRIMARY: Tuple[str, str] = ("#0F172A", "#F0F4FC")        # Primary headings and labels
    TEXT_SECONDARY: Tuple[str, str] = ("#475569", "#8898B8")      # Subheadings & descriptions
    TEXT_MUTED: Tuple[str, str] = ("#94A3B8", "#4A5873")          # Shortcuts, placeholders
    TEXT_ON_BRAND: Tuple[str, str] = ("#FFFFFF", "#FFFFFF")       # White on brand buttons

    # ── Semantic Feedback Tokens (Light, Dark)
    STATUS_SUCCESS: Tuple[str, str] = ("#10B981", "#10B981")      # Green
    STATUS_ERROR: Tuple[str, str] = ("#EF4444", "#EF4444")        # Red
    STATUS_WARNING: Tuple[str, str] = ("#F59E0B", "#F59E0B")      # Amber
    STATUS_INFO: Tuple[str, str] = ("#005AE0", "#38BDF8")         # Blue

    # ── Category Palette (Subtle accents)
    CAT_VIDEO = ("#2563EB", "#3B82F6")
    CAT_AUDIO = ("#7C3AED", "#A855F7")
    CAT_DOCS = ("#DC2626", "#F87171")
    CAT_IMAGE = ("#059669", "#34D399")
    CAT_CREATOR = ("#D97706", "#FBBF24")
    CAT_SYSTEM = ("#475569", "#94A3B8")

    CATEGORY_COLORS = {
        "video": {"accent": CAT_VIDEO, "bg": SURFACE_INSET},
        "audio": {"accent": CAT_AUDIO, "bg": SURFACE_INSET},
        "pdf": {"accent": CAT_DOCS, "bg": SURFACE_INSET},
        "image": {"accent": CAT_IMAGE, "bg": SURFACE_INSET},
        "creator": {"accent": CAT_CREATOR, "bg": SURFACE_INSET},
        "system": {"accent": CAT_SYSTEM, "bg": SURFACE_INSET},
    }

    # ── Typography Scale (1:1 with Website: Instrument Sans + DM Mono)
    FONT_FAMILY = "Instrument Sans"
    FONT_MONO = "DM Mono"

    FONT_HERO = (FONT_FAMILY, 18, "bold")
    FONT_DISPLAY = (FONT_FAMILY, 15, "bold")
    FONT_TITLE = (FONT_FAMILY, 13, "bold")
    FONT_SUBTITLE = (FONT_FAMILY, 12, "bold")
    FONT_BODY = (FONT_FAMILY, 12, "normal")
    FONT_BODY_BOLD = (FONT_FAMILY, 12, "bold")
    FONT_LABEL = (FONT_FAMILY, 11, "normal")
    FONT_CAPTION = (FONT_FAMILY, 10, "normal")
    FONT_MONO_TEXT = (FONT_MONO, 10, "normal")

    # ── Corner Radii (Compact modern squircles)
    RADIUS_INPUT = 6
    RADIUS_BUTTON = 6
    RADIUS_CARD = 10
    RADIUS_PILL = 14

    # ── Spacing Rhythm (Strict 4px/8px grid)
    PAD_XS = 4
    PAD_SM = 8
    PAD_MD = 16
    PAD_LG = 24
    PAD_XL = 32

    @classmethod
    def apply_appearance(cls, mode: str = "Dark", window=None):
        _register_custom_fonts()
        import customtkinter as ctk

        if window is not None and sys.platform == "win32":
            try:
                hwnd = window.winfo_id()
                # WM_SETREDRAW = 0x000B: Freeze redraw during bulk widget palette updates
                ctypes.windll.user32.SendMessageW(hwnd, 0x000B, 0, 0)
                ctk.set_appearance_mode(mode)
                window.update_idletasks()
                ctypes.windll.user32.SendMessageW(hwnd, 0x000B, 1, 0)
                # Atomic 60fps repaint: RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN (0x0085)
                ctypes.windll.user32.RedrawWindow(hwnd, None, None, 0x0085)
                return
            except Exception:
                pass

        ctk.set_appearance_mode(mode)
        ctk.set_default_color_theme("blue")
