"""Notification & Announcements Popover Modal for Boltools."""

import webbrowser
import tkinter as tk
from typing import Callable, Optional
import customtkinter as ctk

from src.core.theme import Theme
from src.core.announcements import announcement_service
from src.core.community import community_service
from src.components.poll_modal import CommunityPollModal


class NotificationModal(ctk.CTkToplevel):
    """Raycast-style popover presenting product updates, community announcements, and launches."""

    def __init__(self, master, on_close: Optional[Callable[[], None]] = None):
        super().__init__(master)

        self.on_close_cb = on_close
        self.title("Product Updates & Announcements")
        self.geometry("540x520")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # Center near top-right
        self.update_idletasks()
        pw = master.winfo_width()
        ph = master.winfo_height()
        px = master.winfo_x()
        py = master.winfo_y()
        cx = px + pw - 560
        cy = py + 65
        self.geometry(f"540x520+{max(0, cx)}+{max(0, cy)}")

        self.configure(fg_color=Theme.SURFACE_BASE)

        # Mark all announcements as read upon opening
        announcement_service.mark_all_read()

        self._build_ui()
        self._bind_keys()

    def _build_ui(self):
        container = ctk.CTkFrame(
            self,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_MODAL,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        container.pack(fill="both", expand=True, padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        # ── Header Bar
        top_bar = ctk.CTkFrame(container, fg_color="transparent")
        top_bar.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM))

        title_lbl = ctk.CTkLabel(
            top_bar,
            text="Product Updates & Radar",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        title_lbl.pack(side="left")

        btn_close = ctk.CTkButton(
            top_bar,
            text="✕",
            font=(Theme.FONT_FAMILY, 12, "bold"),
            fg_color="transparent",
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.TEXT_MUTED,
            width=28,
            height=28,
            corner_radius=Theme.RADIUS_BUTTON,
            command=self._dismiss
        )
        btn_close.pack(side="right")

        # ── Announcements Scroll List
        scroll_frame = ctk.CTkScrollableFrame(
            container,
            fg_color="transparent",
            corner_radius=0
        )
        scroll_frame.pack(fill="both", expand=True, padx=Theme.PAD_SM, pady=Theme.PAD_XS)

        has_poll = community_service.has_active_poll()
        if has_poll:
            self._build_poll_card(scroll_frame, community_service.cached_poll)

        items = announcement_service.cached_announcements
        if not items and not has_poll:
            empty_lbl = ctk.CTkLabel(
                scroll_frame,
                text="You're all caught up!\nNo new updates at this time.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MUTED,
                justify="center"
            )
            empty_lbl.pack(pady=Theme.PAD_XL)
            return

        for item in items:
            self._build_card(scroll_frame, item)

        # ── Bottom Helper Bar
        footer = ctk.CTkFrame(container, fg_color=Theme.SURFACE_INSET, height=32, corner_radius=0)
        footer.pack(fill="x", side="bottom")

        brand_lbl = ctk.CTkLabel(
            footer,
            text="Powered by The SurfBoard Ecosystem  •  Free Forever",
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_MUTED
        )
        brand_lbl.pack(pady=6)

    def _build_card(self, parent: ctk.CTkScrollableFrame, item: dict):
        card = ctk.CTkFrame(
            parent,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        card.pack(fill="x", pady=Theme.PAD_XS, padx=Theme.PAD_XS)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_MD)

        # Tag + Date row
        meta_row = ctk.CTkFrame(inner, fg_color="transparent")
        meta_row.pack(fill="x", pady=(0, 4))

        tag_txt = item.get("tag", "UPDATE").upper()
        tag_pill = ctk.CTkLabel(
            meta_row,
            text=f" {tag_txt} ",
            font=Theme.FONT_CAPTION,
            fg_color=Theme.SURFACE_PILL,
            text_color=Theme.BRAND_ACCENT,
            corner_radius=Theme.RADIUS_PILL,
            padx=8,
            pady=2
        )
        tag_pill.pack(side="left")

        date_lbl = ctk.CTkLabel(
            meta_row,
            text=item.get("date", ""),
            font=Theme.FONT_CAPTION,
            text_color=Theme.TEXT_MUTED
        )
        date_lbl.pack(side="right")

        # Title
        t_lbl = ctk.CTkLabel(
            inner,
            text=item.get("title", ""),
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=480
        )
        t_lbl.pack(fill="x", pady=(2, 4))

        # Description
        d_lbl = ctk.CTkLabel(
            inner,
            text=item.get("description", ""),
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
            justify="left",
            wraplength=480
        )
        d_lbl.pack(fill="x", pady=(0, Theme.PAD_SM))

        # CTA Link Button (if available)
        cta_url = item.get("cta_url")
        cta_text = item.get("cta_text", "Learn More")
        if cta_url:
            cta_btn = ctk.CTkButton(
                inner,
                text=f"{cta_text}  ↗",
                fg_color=Theme.BRAND_PRIMARY,
                hover_color=Theme.BRAND_HOVER,
                text_color=Theme.TEXT_ON_BRAND,
                font=Theme.FONT_BODY_BOLD,
                height=28,
                corner_radius=Theme.RADIUS_BUTTON,
                command=lambda u=cta_url: webbrowser.open(u)
            )
            cta_btn.pack(anchor="w")

    def _build_poll_card(self, parent: ctk.CTkScrollableFrame, poll: dict):
        """Displays active community roadmap poll inside the notification center."""
        card = ctk.CTkFrame(
            parent,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        card.pack(fill="x", pady=Theme.PAD_XS, padx=Theme.PAD_XS)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_MD)

        meta_row = ctk.CTkFrame(inner, fg_color="transparent")
        meta_row.pack(fill="x", pady=(0, 4))

        tag_pill = ctk.CTkLabel(
            meta_row,
            text=" COMMUNITY POLL ",
            font=Theme.FONT_CAPTION,
            fg_color=Theme.SURFACE_PILL,
            text_color=Theme.BRAND_ACCENT,
            corner_radius=Theme.RADIUS_PILL,
            padx=8,
            pady=2
        )
        tag_pill.pack(side="left")

        t_lbl = ctk.CTkLabel(
            inner,
            text=poll.get("title", "Community Roadmap Poll"),
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=480
        )
        t_lbl.pack(fill="x", pady=(2, 4))

        d_lbl = ctk.CTkLabel(
            inner,
            text=poll.get("description", "Cast your vote for upcoming power tools."),
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
            justify="left",
            wraplength=480
        )
        d_lbl.pack(fill="x", pady=(0, Theme.PAD_SM))

        btn_vote = ctk.CTkButton(
            inner,
            text="Vote in Poll  ›",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            text_color=Theme.TEXT_ON_BRAND,
            font=Theme.FONT_BODY_BOLD,
            height=28,
            corner_radius=Theme.RADIUS_BUTTON,
            command=self._open_poll_dialog
        )
        btn_vote.pack(anchor="w")

    def _open_poll_dialog(self):
        self._dismiss()
        CommunityPollModal(self.master)

    def _bind_keys(self):
        self.bind("<Escape>", lambda e: self._dismiss())

    def _dismiss(self):
        if self.on_close_cb:
            self.on_close_cb()
        self.destroy()
