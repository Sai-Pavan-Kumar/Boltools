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

    # ── Typography Scale
    FONT_FAMILY = "Segoe UI"
    FONT_MONO = "Consolas"

    FONT_DISPLAY = (FONT_FAMILY, 22, "bold")
    FONT_TITLE = (FONT_FAMILY, 17, "bold")
    FONT_SUBTITLE = (FONT_FAMILY, 13, "bold")
    FONT_BODY = (FONT_FAMILY, 13, "normal")
    FONT_BODY_BOLD = (FONT_FAMILY, 13, "bold")
    FONT_LABEL = (FONT_FAMILY, 11, "bold")
    FONT_CAPTION = (FONT_FAMILY, 10, "normal")
    FONT_MONO_TEXT = (FONT_MONO, 11, "normal")

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

    @classmethod
    def apply_appearance(cls, mode: str = "Dark"):
        """Sets CustomTkinter global appearance defaults."""
        import customtkinter as ctk
        ctk.set_appearance_mode(mode)
        ctk.set_default_color_theme("blue")
