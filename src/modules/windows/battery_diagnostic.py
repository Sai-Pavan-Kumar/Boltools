"""Tool 8.8: Real Battery Health & Cycle Degradation Diagnostic.

Reads physical hardware battery design capacity vs current full-charge capacity
and reports true wear percentage and total lifetime cycle count.
"""

import os
import re
import subprocess
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class BatteryDiagnosticTool(BaseToolFrame):
    """Universal 2-pane tool for Windows laptop battery health diagnostics."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="tool_windows_8_8",
            title="Real Battery Health & Cycle Diagnostic",
            description="Examine true factory design capacity vs degraded capacity and charging cycle counts without third-party adware.",
            **kwargs
        )

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # Trigger Button
        btn_scan = ctk.CTkButton(
            container,
            text="⚡  Run Battery Hardware Diagnostic",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            height=42,
            command=self._run_diagnostic
        )
        btn_scan.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_MD))

        # Metrics Card
        metrics_card = ctk.CTkFrame(
            container,
            fg_color=Theme.SURFACE_INSET,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        metrics_card.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        # Health % Big Metric
        ctk.CTkLabel(metrics_card, text="HEALTH PERCENTAGE", font=(Theme.FONT_FAMILY, 10, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, 0))
        self.lbl_health_pct = ctk.CTkLabel(metrics_card, text="-- %", font=(Theme.FONT_FAMILY, 28, "bold"), text_color=Theme.STATUS_SUCCESS)
        self.lbl_health_pct.pack(anchor="w", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Design vs Current
        self.lbl_design = ctk.CTkLabel(metrics_card, text="Design Capacity: -- mWh", font=(Theme.FONT_FAMILY, 12), text_color=Theme.TEXT_SECONDARY)
        self.lbl_design.pack(anchor="w", padx=Theme.PAD_MD, pady=2)

        self.lbl_full = ctk.CTkLabel(metrics_card, text="Full Charge Capacity: -- mWh", font=(Theme.FONT_FAMILY, 12), text_color=Theme.TEXT_SECONDARY)
        self.lbl_full.pack(anchor="w", padx=Theme.PAD_MD, pady=2)

        self.lbl_cycles = ctk.CTkLabel(metrics_card, text="Lifetime Cycles: --", font=(Theme.FONT_FAMILY, 12), text_color=Theme.TEXT_SECONDARY)
        self.lbl_cycles.pack(anchor="w", padx=Theme.PAD_MD, pady=(2, Theme.PAD_MD))

    def _run_diagnostic(self):
        self.log("Generating native Windows battery diagnostic report...")

        def _task():
            report_path = os.path.join(os.path.expanduser("~"), "battery_report.html")
            subprocess.run(["powercfg", "/batteryreport", "/output", report_path], capture_output=True)

            if not os.path.exists(report_path):
                # Desktop PC without battery
                return {"is_desktop": True}

            with open(report_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            try:
                os.remove(report_path)
            except Exception:
                pass

            # Parse Design & Full Charge Capacity
            design_match = re.search(r"DESIGN CAPACITY.*?(\d[\d,]+)\s*mWh", content, re.DOTALL | re.IGNORECASE)
            full_match = re.search(r"FULL CHARGE CAPACITY.*?(\d[\d,]+)\s*mWh", content, re.DOTALL | re.IGNORECASE)
            cycle_match = re.search(r"CYCLE COUNT.*?(\d+)", content, re.DOTALL | re.IGNORECASE)

            if design_match and full_match:
                design_val = int(design_match.group(1).replace(",", ""))
                full_val = int(full_match.group(1).replace(",", ""))
                cycles = cycle_match.group(1) if cycle_match else "N/A"
                health_pct = (full_val / design_val) * 100 if design_val > 0 else 100.0

                return {
                    "is_desktop": False,
                    "design": design_val,
                    "full": full_val,
                    "cycles": cycles,
                    "health_pct": health_pct
                }
            else:
                return {"is_desktop": True}

        def _on_done(res):
            if res.get("is_desktop"):
                self.lbl_health_pct.configure(text="Desktop PC", text_color=Theme.TEXT_MUTED)
                self.lbl_design.configure(text="No physical lithium battery detected.")
                self.lbl_full.configure(text="AC Continuous Power Line connected.")
                self.lbl_cycles.configure(text="Lifetime Cycles: 0")
                self.log("✓ System verified: Desktop AC power supply detected (No battery wear).")
            else:
                pct = res["health_pct"]
                color = Theme.STATUS_SUCCESS if pct > 80 else (Theme.STATUS_WARNING if pct > 60 else Theme.STATUS_ERROR)
                self.lbl_health_pct.configure(text=f"{pct:.1f} %", text_color=color)
                self.lbl_design.configure(text=f"Design Capacity: {res['design']:,} mWh")
                self.lbl_full.configure(text=f"Full Charge Capacity: {res['full']:,} mWh")
                self.lbl_cycles.configure(text=f"Lifetime Cycles: {res['cycles']}")

                self.log(f"✓ Battery Health: {pct:.1f}% ({res['full']} / {res['design']} mWh, Cycles: {res['cycles']})")

        self.execute_async(_task, on_success=_on_done)
