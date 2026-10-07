"""Modular Tool Registry & Discovery Provider for Boltools.

Enforces:
- Strict decoupling of tool registration from application shell
- No fake tools, no unreleased placeholders
- Pure registration API for modular offline utilities
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Type
import customtkinter as ctk


@dataclass
class ToolDefinition:
    id: str
    name: str
    category_id: str
    category_name: str
    description: str
    keywords: List[str]
    factory: Optional[Callable[[], Type[ctk.CTkFrame]]] = None
    is_implemented: bool = True
    icon: str = "⚡"
    version: str = "1.0.0"


class ToolRegistry:
    """Central registry and search provider for active tools."""

    CATEGORIES = {
        "video": {"name": "Video & Media", "desc": "Fast offline video compression, extraction, and formatting"},
        "pdf": {"name": "Documents & PDF", "desc": "Offline conversion, splitting, merging, and document protection"},
        "image": {"name": "Images & Visuals", "desc": "Batch WebP compression, target sizing, and color extraction"},
        "system": {"name": "System & Files", "desc": "Power file renaming, extension repair, and organization"},
    }

    _tools: Dict[str, ToolDefinition] = {}

    @classmethod
    def register(cls, tool: ToolDefinition):
        cls._tools[tool.id] = tool

    @classmethod
    def get(cls, tool_id: str) -> Optional[ToolDefinition]:
        return cls._tools.get(tool_id)

    @classmethod
    def get_all(cls) -> List[ToolDefinition]:
        return list(cls._tools.values())

    @classmethod
    def get_by_category(cls, category_id: str) -> List[ToolDefinition]:
        return [t for t in cls._tools.values() if t.category_id == category_id]

    @classmethod
    def search(cls, query: str) -> List[ToolDefinition]:
        if not query:
            return cls.get_all()
        q = query.lower().strip()
        results = []
        for t in cls._tools.values():
            if (
                q in t.name.lower()
                or q in t.description.lower()
                or any(q in kw.lower() for kw in t.keywords)
                or q in t.category_name.lower()
            ):
                results.append(t)
        return results


# ── Register Gold-Standard Benchmark Tools ───────────────────────────────────

def _load_video_compressor():
    from src.tools.video_compressor import VideoCompressorTool
    return VideoCompressorTool

def _load_pdf_converter():
    from src.tools.pdf_converter import PdfConverterTool
    return PdfConverterTool

def _load_webp_compressor():
    from src.tools.webp_compressor import WebpCompressorTool
    return WebpCompressorTool

def _load_batch_renamer():
    from src.tools.batch_renamer import BatchRenamerTool
    return BatchRenamerTool


ToolRegistry.register(
    ToolDefinition(
        id="video_compressor",
        name="Video Compressor",
        category_id="video",
        category_name="Video & Media",
        description="Reduce video file size while maintaining great quality. Supports MP4, MKV, MOV, and WebM.",
        keywords=["video", "compress", "mp4", "mkv", "size", "ffmpeg", "discord", "whatsapp"],
        factory=_load_video_compressor,
        is_implemented=True,
        icon="▶"
    )
)

ToolRegistry.register(
    ToolDefinition(
        id="pdf_converter",
        name="Document Converter",
        category_id="pdf",
        category_name="Documents & PDF",
        description="Convert PDF documents to high-resolution images, plain text, Word, or combine photos into PDF.",
        keywords=["pdf", "convert", "images", "png", "jpg", "word", "docx", "text", "combine"],
        factory=_load_pdf_converter,
        is_implemented=True,
        icon="📄"
    )
)

ToolRegistry.register(
    ToolDefinition(
        id="image_webp_compress",
        name="WebP Compressor",
        category_id="image",
        category_name="Images & Visuals",
        description="Bulk compress images into high-efficiency WebP with automatic photo vs graphic optimization.",
        keywords=["image", "compress", "webp", "photo", "png", "jpg", "batch", "resize"],
        factory=_load_webp_compressor,
        is_implemented=True,
        icon="🖼"
    )
)

ToolRegistry.register(
    ToolDefinition(
        id="system_batch_rename",
        name="Batch File Renamer",
        category_id="system",
        category_name="System & Files",
        description="Batch rename files with rule-based prefix, suffix, sequence numbering, and find-and-replace.",
        keywords=["rename", "batch", "files", "prefix", "suffix", "numbering", "replace"],
        factory=_load_batch_renamer,
        is_implemented=True,
        icon="⚡"
    )
)
