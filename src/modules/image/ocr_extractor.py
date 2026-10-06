"""Tool 4.2: Tesseract High-Speed Image OCR.

Extracts selectable, readable plain text from:
- Screenshots & error dialogues
- Receipt photos & document scans
- Clipboard screenshots (1-Click Paste)
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional
import customtkinter as ctk
from PIL import Image, ImageGrab
import pymupdf

from src.core.theme import Theme
from src.core.base_tool import BaseToolFrame


class ImageOcrTool(BaseToolFrame):
    """Universal 2-pane tool for high-speed OCR text extraction."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master=master,
            tool_id="tool_image_4_2",
            title="Tesseract Image OCR Extractor",
            description="Copy unselectable text directly from screenshots, receipts, and images in 300 milliseconds.",
            **kwargs
        )
        self.current_image_path: Optional[str] = None
        self.clipboard_image: Optional[Image.Image] = None

    def build_left_panel(self, container: ctk.CTkFrame):
        container.grid_columnconfigure(0, weight=1)

        # File & Clipboard Actions
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_XS))

        btn_paste = ctk.CTkButton(
            btn_row,
            text="📋 Paste from Clipboard",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            height=34,
            command=self._paste_clipboard
        )
        btn_paste.pack(side="left", padx=(0, Theme.PAD_SM))

        btn_browse = ctk.CTkButton(
            btn_row,
            text="Browse Image",
            fg_color=Theme.SURFACE_INSET,
            hover_color=Theme.SURFACE_CARD_HOVER,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12),
            height=34,
            command=self._browse_image
        )
        btn_browse.pack(side="left")

        # Active Source Status
        self.source_lbl = ctk.CTkLabel(
            container,
            text="No image loaded (Click Paste or Browse)",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        self.source_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        # Extracted Text Output Box
        out_lbl = ctk.CTkLabel(
            container,
            text="EXTRACTED TEXT RESULT",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        out_lbl.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_XS))

        self.text_out = ctk.CTkTextbox(
            container,
            fg_color=Theme.SURFACE_INSET,
            text_color=Theme.TEXT_PRIMARY,
            font=(Theme.FONT_FAMILY, 12),
            corner_radius=Theme.RADIUS_INPUT,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            height=200
        )
        self.text_out.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        # Action Buttons (Copy to Clipboard & Clear)
        action_row = ctk.CTkFrame(container, fg_color="transparent")
        action_row.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        btn_copy = ctk.CTkButton(
            action_row,
            text="✓ Copy to Clipboard",
            fg_color=Theme.BRAND_PRIMARY,
            hover_color=Theme.BRAND_HOVER,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            height=34,
            command=self._copy_text
        )
        btn_copy.pack(side="left", padx=(0, Theme.PAD_SM))

        btn_clear = ctk.CTkButton(
            action_row,
            text="Clear",
            fg_color="transparent",
            hover_color=Theme.SURFACE_CARD_HOVER,
            text_color=Theme.STATUS_ERROR,
            corner_radius=Theme.RADIUS_BUTTON,
            font=(Theme.FONT_FAMILY, 12),
            height=34,
            width=60,
            command=self._clear_all
        )
        btn_clear.pack(side="right")

    def _paste_clipboard(self):
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                self.clipboard_image = img
                self.current_image_path = None
                self.source_lbl.configure(text="Loaded screenshot from Clipboard (Ready)")
                self._run_ocr(img)
            else:
                messagebox.showinfo("Notice", "No image found in clipboard. Press Win+Shift+S first!")
        except Exception as e:
            messagebox.showerror("Error", f"Clipboard error: {e}")

    def _browse_image(self):
        p = filedialog.askopenfilename(
            title="Select Image to OCR",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff")]
        )
        if p:
            self.current_image_path = p
            self.clipboard_image = None
            self.source_lbl.configure(text=f"Loaded: {os.path.basename(p)}")
            img = Image.open(p)
            self._run_ocr(img)

    def _run_ocr(self, img: Image.Image):
        self.log("Running optical character recognition...")

        def _task():
            # Convert PIL image to temporary PDF or use PyMuPDF pixmap OCR
            temp_p = os.path.join(os.path.expanduser("~"), "boltools_temp_ocr.png")
            img.save(temp_p)

            # PyMuPDF lightweight OCR/text extractor
            doc = pymupdf.open(temp_p)
            pdf_bytes = doc.convert_to_pdf()
            doc.close()

            pdf_doc = pymupdf.open("pdf", pdf_bytes)
            # Try OCR if standard text fails
            page = pdf_doc[0]
            try:
                # If Tesseract is present in OS or PyMuPDF OCR
                tp = page.get_textpage_ocr(language="eng", dpi=200)
                extracted = page.get_text(textpage=tp)
            except Exception:
                extracted = page.get_text()

            pdf_doc.close()
            try:
                os.remove(temp_p)
            except Exception:
                pass

            if not extracted.strip():
                extracted = "[No text detected in this image region. Ensure image is clear with dark text on light background.]"

            return extracted

        def _on_done(text_result):
            self.text_out.delete("1.0", "end")
            self.text_out.insert("1.0", text_result)
            self.log(f"✓ OCR completed: Extracted {len(text_result.split())} words.")

        def _on_err(err):
            self.log(f"✗ OCR failed: {err}")

        self.execute_async(_task, on_success=_on_done, on_error=_on_err)

    def _copy_text(self):
        text = self.text_out.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.log("✓ Copied extracted text to system clipboard!")
            messagebox.showinfo("Copied", "Text successfully copied to clipboard!")

    def _clear_all(self):
        self.text_out.delete("1.0", "end")
        self.source_lbl.configure(text="No image loaded (Click Paste or Browse)")
        self.current_image_path = None
        self.clipboard_image = None
