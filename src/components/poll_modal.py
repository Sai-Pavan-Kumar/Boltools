"""Community Poll & Feature Voting Modal for Boltools."""

import tkinter as tk
from typing import Callable, Optional
import customtkinter as ctk

from src.core.theme import Theme
from src.core.community import community_service


class CommunityPollModal(ctk.CTkToplevel):
    """Presents active community roadmap poll with live voting and anti-spam protection."""

    def __init__(self, master, on_close: Optional[Callable[[], None]] = None):
        super().__init__(master)

        self.on_close_cb = on_close
        self.title("Community Roadmap Poll")
        self.geometry("560x540")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # Center on parent window
        self.update_idletasks()
        pw = master.winfo_width()
        ph = master.winfo_height()
        px = master.winfo_x()
        py = master.winfo_y()
        cx = px + (pw - 560) // 2
        cy = py + (ph - 540) // 2
        self.geometry(f"560x540+{max(0, cx)}+{max(0, cy)}")

        self.configure(fg_color=Theme.SURFACE_BASE)

        self.poll = community_service.cached_poll
        self.poll_id = self.poll.get("poll_id", "default")
        self.already_voted = community_service.has_voted(self.poll_id)
        self.selected_opt = tk.StringVar()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(
            self,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=Theme.RADIUS_MODAL,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        container.pack(fill="both", expand=True, padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        # Header Bar
        top_bar = ctk.CTkFrame(container, fg_color="transparent")
        top_bar.pack(fill="x", padx=Theme.PAD_LG, pady=(Theme.PAD_LG, Theme.PAD_XS))

        title_lbl = ctk.CTkLabel(
            top_bar,
            text="Community Roadmap Vote",
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
            command=self.destroy
        )
        btn_close.pack(side="right")

        # Question / Subtitle
        desc_lbl = ctk.CTkLabel(
            container,
            text=self.poll.get("title", "Vote for the next power tools:"),
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        desc_lbl.pack(fill="x", padx=Theme.PAD_LG, pady=(0, 2))

        sub_lbl = ctk.CTkLabel(
            container,
            text=self.poll.get("description", "Choose which tools get unlocked in the next batch release drop.") + " (1 vote per PC)",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        sub_lbl.pack(fill="x", padx=Theme.PAD_LG, pady=(0, Theme.PAD_MD))

        # Options Container (Scrollable)
        opts_frame = ctk.CTkScrollableFrame(
            container,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            height=250
        )
        opts_frame.pack(fill="both", expand=True, padx=Theme.PAD_LG, pady=(0, Theme.PAD_MD))

        options = self.poll.get("options", [])
        total_votes = sum(o.get("votes", 0) for o in options) or 1
        user_voted_opt = community_service.get_user_vote(self.poll_id)

        for opt in options:
            oid = opt.get("id")
            label = opt.get("label")
            votes = opt.get("votes", 0)
            pct = int((votes / total_votes) * 100)

            row = ctk.CTkFrame(opts_frame, fg_color=Theme.SURFACE_CARD, corner_radius=Theme.RADIUS_BUTTON)
            row.pack(fill="x", padx=Theme.PAD_SM, pady=Theme.PAD_XS)

            if not self.already_voted:
                rb = ctk.CTkRadioButton(
                    row,
                    text=label,
                    value=oid,
                    variable=self.selected_opt,
                    font=Theme.FONT_BODY,
                    text_color=Theme.TEXT_PRIMARY,
                    fg_color=Theme.BRAND_PRIMARY,
                    hover_color=Theme.BRAND_HOVER
                )
                rb.pack(side="left", padx=Theme.PAD_MD, pady=Theme.PAD_SM, fill="x", expand=True)
            else:
                is_user_pick = (oid == user_voted_opt)
                prefix = "✓ Your Vote: " if is_user_pick else ""
                opt_lbl = ctk.CTkLabel(
                    row,
                    text=f"{prefix}{label}",
                    font=Theme.FONT_BODY_BOLD if is_user_pick else Theme.FONT_BODY,
                    text_color=Theme.BRAND_PRIMARY if is_user_pick else Theme.TEXT_PRIMARY,
                    anchor="w"
                )
                opt_lbl.pack(side="left", padx=Theme.PAD_MD, pady=Theme.PAD_SM, fill="x", expand=True)

                pct_lbl = ctk.CTkLabel(
                    row,
                    text=f"{pct}% ({votes})",
                    font=Theme.FONT_CAPTION,
                    text_color=Theme.TEXT_MUTED
                )
                pct_lbl.pack(side="right", padx=Theme.PAD_MD)

        # Footer Actions
        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(fill="x", padx=Theme.PAD_LG, pady=(0, Theme.PAD_MD))

        if not self.already_voted:
            self.btn_vote = ctk.CTkButton(
                footer,
                text="Cast Vote 🗳️",
                font=Theme.FONT_BODY_BOLD,
                fg_color=Theme.BRAND_PRIMARY,
                hover_color=Theme.BRAND_HOVER,
                corner_radius=Theme.RADIUS_BUTTON,
                height=38,
                command=self._cast_vote
            )
            self.btn_vote.pack(fill="x")
        else:
            done_lbl = ctk.CTkLabel(
                footer,
                text="✓ Your vote has been recorded! Results update live across the network.",
                font=Theme.FONT_BODY_BOLD,
                text_color=Theme.STATUS_SUCCESS
            )
            done_lbl.pack(fill="x")

    def _cast_vote(self):
        chosen = self.selected_opt.get()
        if not chosen:
            return

        community_service.cast_vote(self.poll_id, chosen)
        self.destroy()
        # Reopen in voted state to show bars
        CommunityPollModal(self.master, self.on_close_cb)
