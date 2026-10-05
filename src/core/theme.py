"""Theme tokens and styling specifications for Boltools.

Enforces The SurfBoard Design System tokens strictly:
- Deep space surface palette
- Hairline borders (1px)
- High contrast typography
- Tactile feedback colors
"""

class Theme:
    # ── Color Tokens
    SURFACE_BASE = "#09090F"        # Deep space window canvas
    SURFACE_CARD = "#11111B"        # Main panels & containers
    SURFACE_CARD_HOVER = "#181827"  # Hover state for card elements
    SURFACE_INSET = "#06060A"       # Dropzones, text inputs, console logs
    SURFACE_SIDEBAR = "#0D0D15"     # Sidebar navigation panel
    
    BRAND_PRIMARY = "#005AE0"       # Primary action & active state
    BRAND_HOVER = "#1268C0"         # Hover state for primary buttons
    BRAND_ACCENT = "#2563EB"        # Accent highlights
    
    BORDER_SUBTLE = "#162035"       # Hairline dividers and outlines
    BORDER_HOVER = "#223555"        # Interactive focus/hover border
    BORDER_ACTIVE = "#005AE0"       # Active field border
    
    TEXT_PRIMARY = "#F0F4FC"        # Headlines, primary labels
    TEXT_SECONDARY = "#8898B8"      # Secondary descriptions, meta
    TEXT_MUTED = "#4A5873"          # Shortcuts, placeholders
    
    STATUS_SUCCESS = "#10B981"      # Complete / healthy state
    STATUS_ERROR = "#EF4444"        # Error / invalid state
    STATUS_WARNING = "#F59E0B"      # Attention / pending state
    STATUS_INFO = "#3B82F6"         # In-progress information

    # ── Typography Settings
    FONT_FAMILY = "Segoe UI"
    FONT_MONO = "Consolas"
    
    # ── Corner Radii
    RADIUS_INPUT = 8
    RADIUS_BUTTON = 8
    RADIUS_CARD = 12
    RADIUS_MODAL = 16
    
    # ── Spacing Rhythm
    PAD_XS = 4
    PAD_SM = 8
    PAD_MD = 16
    PAD_LG = 24
    PAD_XL = 32

    @classmethod
    def apply_appearance(cls):
        """Sets CustomTkinter global appearance defaults."""
        import customtkinter as ctk
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
