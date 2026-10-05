"""Tool Registry & Lazy-Loader for Boltools.

Maintains metadata for all 57 tools across 7 functional domains.
Enforces the strict UI Anti-Tech Name Rule (no raw engine names exposed).
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
    icon: str = "⚡"
    is_implemented: bool = False


class ToolRegistry:
    """Central registry and fuzzy-search provider for Boltools."""
    
    CATEGORIES = {
        "video": {"name": "Video & Media", "glyph": "▶", "icon": "🎥", "desc": "Trim clips, extract audio, and convert video formats"},
        "audio": {"name": "Voice & Audio", "glyph": "●", "icon": "🎙️", "desc": "Transcribe speech, clean noise, and isolate vocals"},
        "pdf": {"name": "PDF Studio", "glyph": "▤", "icon": "📄", "desc": "Merge documents, split pages, lock with passwords, and convert"},
        "image": {"name": "Image & Photos", "glyph": "◈", "icon": "🖼️", "desc": "Compress photos, resize by KB/MB, and switch formats"},
        "creator": {"name": "Creator Tools", "glyph": "✦", "icon": "📊", "desc": "Download videos, save HD thumbnails, and grab subtitles"},
        "design": {"name": "Design & Text", "glyph": "⬡", "icon": "🎨", "desc": "Make QR codes, check color contrast, and edit text"},
        "system": {"name": "Files & System", "glyph": "⚙", "icon": "🛠️", "desc": "Batch rename files, fix file extensions, and organize folders"},
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
        """Performs fast search across names, categories, descriptions, and keywords."""
        q = query.strip().lower()
        if not q:
            return cls.get_all()

        results = []
        for tool in cls._tools.values():
            score = 0
            if q in tool.name.lower():
                score += 10
            if q in tool.category_name.lower():
                score += 5
            if any(q in kw.lower() for kw in tool.keywords):
                score += 8
            if q in tool.description.lower():
                score += 3
            if score > 0:
                results.append((score, tool))

        results.sort(key=lambda x: x[0], reverse=True)
        return [tool for _, tool in results]


# Initialize the 57-Tool Catalog with consumer-grade names (Zero Tech Leaks)
def _init_catalog():
    R = ToolRegistry.register
    
    # ── Category 1: Video & Media
    c = "video"
    c_name = "Video & Media"
    R(ToolDefinition("video_joiner", "Bulk Playlist Video Joiner", c, c_name, "Merge multi-gigabyte video clips losslessly in seconds", ["merge", "join", "concat", "combine", "playlist"]))
    R(ToolDefinition("video_shorts_conv", "Smart 9:16 Vertical Video Formatter", c, c_name, "Convert landscape videos to vertical reels with aesthetic blurred bars", ["shorts", "reels", "tiktok", "vertical", "16:9", "9:16"]))
    R(ToolDefinition("video_compressor", "Target Size Video Compressor", c, c_name, "Compress videos precisely under WhatsApp (16MB/64MB) or Discord (25MB) limits", ["compress", "size", "whatsapp", "discord", "mb"]))
    R(ToolDefinition("video_gif", "Ultra-HQ Lossless GIF Studio", c, c_name, "Generate smooth, high-fps 256-color animated GIFs from any video", ["gif", "animation", "palette"]))
    R(ToolDefinition("video_trimmer", "Instant Lossless Video Trimmer", c, c_name, "Cut snippets with zero re-encoding in under 1 second", ["cut", "trim", "snip", "lossless"]))
    R(ToolDefinition("video_audio_swap", "Audio Stripper & Sound Replacer", c, c_name, "Mute original audio or swap background tracks instantly", ["mute", "replace", "bgm", "soundtrack", "strip"]))
    R(ToolDefinition("video_sub_burner", "Hardcode Subtitle Burner", c, c_name, "Permanently burn SRT subtitles with custom typography and highlights", ["subtitles", "burn", "srt", "captions"]))
    R(ToolDefinition(
        "video_extractor",
        "Video to Audio Extractor",
        c, c_name,
        "Extract clean MP3, WAV, or AAC audio from any video in seconds",
        ["extract", "audio", "mp3", "wav", "sound", "mpverter"],
        factory=lambda: __import__("src.modules.video.audio_extractor", fromlist=["AudioExtractorTool"]).AudioExtractorTool,
        is_implemented=True
    ))
    R(ToolDefinition("video_chunker", "Auto Video Chunker & Status Splitter", c, c_name, "Slice long videos into 30s status clips or equal parts instantly", ["chunk", "status", "whatsapp status", "slice", "split"]))

    # ── Category 2: AI Speech & Audio Studio
    c = "audio"
    c_name = "AI Speech & Audio"
    R(ToolDefinition("audio_transcribe", "AI Voice-to-Text & Subtitle Studio", c, c_name, "Offline transcription generating timestamped SRT captions in 90+ languages", ["transcribe", "voice to text", "subtitles", "speech"]))
    R(ToolDefinition("audio_tts", "Natural Voice Speech Generator", c, c_name, "Generate lifelike human speech and voiceovers with zero API keys", ["tts", "speech", "voiceover", "narrator", "ai voice"]))
    R(ToolDefinition("audio_stem_split", "AI Vocal & Instrumental Stem Separator", c, c_name, "Isolate clean acapella vocals, instrumental karaoke, bass and drums", ["stems", "vocals", "karaoke", "acapella", "isolate"]))
    R(ToolDefinition("audio_denoise", "AI Studio Voice Enhancer & Noise Purger", c, c_name, "Restore muffled recordings and eradicate fan, hum and room echo", ["noise", "clean", "enhance", "reverb", "clarity"]))
    R(ToolDefinition("audio_jumpcut", "Auto-Silence & Dead-Air Remover", c, c_name, "Automatically splice out awkward pauses and breaths for snappy pacing", ["silence", "jumpcut", "dead air", "podcast cut"]))
    R(ToolDefinition("audio_lufs_norm", "Broadcast Loudness Leveler (-14 LUFS)", c, c_name, "Auto-level volume to official platform loudness ceilings without distortion", ["loudness", "normalize", "lufs", "volume level"]))
    R(ToolDefinition("audio_offline_tts", "Offline Pocket Voice Synthesizer", c, c_name, "Generate speech completely offline on local CPU", ["offline tts", "local speech", "voice"]))
    R(ToolDefinition("audio_pitch_shift", "Lossless Audio Pitch & Tempo Shifter", c, c_name, "Shift musical keys by semitones or adjust BPM without pitch warping", ["pitch", "key", "bpm", "tempo", "semitone"]))
    R(ToolDefinition("audio_srt_translate", "Subtitle Multi-Language Translator", c, c_name, "Translate captions while strictly preserving millisecond timestamps", ["translate", "srt", "captions", "languages"]))
    R(ToolDefinition("audio_id3_tagger", "Batch Audio Tag & Album Art Studio", c, c_name, "Bulk update track metadata, artist credits and embed cover art", ["id3", "tags", "metadata", "album art", "mp3 tag"]))

    # ── Category 3: PDF Master Studio
    c = "pdf"
    c_name = "PDF Master Studio"
    R(ToolDefinition(
        "pdf_first_page",
        "First-Page Document Extractor & Auto-Printer",
        c, c_name,
        "Batch extract page 1 from multiple documents, merge and auto-spool to printer",
        ["print", "first page", "invoice", "spool", "batch print"],
        factory=lambda: __import__("src.modules.pdf.first_page_printer", fromlist=["FirstPagePrinterTool"]).FirstPagePrinterTool,
        is_implemented=True
    ))
    R(ToolDefinition(
        "pdf_split_merge",
        "Master Document Split & Merge Hub",
        c, c_name,
        "Combine unlimited documents or extract custom page ranges",
        ["merge", "split", "combine", "extract pages"],
        factory=lambda: __import__("src.modules.pdf.split_merge", fromlist=["PdfSplitMergeTool"]).PdfSplitMergeTool,
        is_implemented=True
    ))
    R(ToolDefinition(
        "pdf_page_manager",
        "Document Page Manager & Deskewer",
        c, c_name,
        "Rotate upside-down pages, delete blank sheets and reorder effortlessly",
        ["rotate", "delete pages", "reorder", "deskew"],
        factory=lambda: __import__("src.modules.pdf.page_manager", fromlist=["PdfPageManagerTool"]).PdfPageManagerTool,
        is_implemented=True
    ))
    R(ToolDefinition(
        "pdf_security",
        "Document Security & Encryption Hub",
        c, c_name,
        "Lock confidential documents with AES passwords or unlock protected sheets",
        ["lock", "unlock", "password", "encrypt", "decrypt"],
        factory=lambda: __import__("src.modules.pdf.security", fromlist=["PdfSecurityTool"]).PdfSecurityTool,
        is_implemented=True
    ))
    R(ToolDefinition(
        "pdf_converter",
        "Universal Document Converter",
        c, c_name,
        "Convert bidirectional between PDF, Word, Excel, PowerPoint and Images",
        ["convert", "word", "excel", "powerpoint", "docx", "images"],
        factory=lambda: __import__("src.modules.pdf.converter", fromlist=["PdfConverterTool"]).PdfConverterTool,
        is_implemented=True
    ))
    R(ToolDefinition("pdf_watermark", "Document Watermark & Number Stamper", c, c_name, "Stamp confidential marks or dynamic 'Page X of Y' headers and footers", ["watermark", "page numbers", "stamp", "footer"]))
    R(ToolDefinition("pdf_ocr_search", "Searchable Document OCR Converter", c, c_name, "Inject selectable, searchable text layer into scanned paper PDFs", ["ocr", "searchable", "scanned", "selectable text"]))
    R(ToolDefinition("pdf_ebook_conv", "Universal eBook & Publication Converter", c, c_name, "Convert novels and books between EPUB, MOBI and cleanly styled PDF", ["epub", "mobi", "kindle", "ebook", "book"]))
    R(ToolDefinition("pdf_compressor", "Smart Lossless Document Compressor", c, c_name, "Shrink multi-megabyte PDFs down to email-ready size with crisp text", ["compress pdf", "shrink", "downsample", "email size"]))

    # ── Category 4: Image & Visual Graphics
    c = "image"
    c_name = "Image & Visuals"
    R(ToolDefinition("image_bg_remove", "AI Background Remover & Cutout Studio", c, c_name, "One-click portrait, product and asset cutout with transparent PNG export", ["remove bg", "background", "transparent", "cutout"]))
    R(ToolDefinition("image_ocr", "Smart Text Scanner (OCR)", c, c_name, "Extract unselectable text from screenshots, graphics and photos instantly", ["ocr", "read text", "screenshot to text", "extract text"]))
    R(ToolDefinition(
        "image_webp_compress",
        "Smart WebP Batch Compressor",
        c, c_name,
        "Bulk compress photos with automatic illustration vs photo detection",
        ["webp", "compress", "batch images", "optimize"],
        factory=lambda: __import__("src.modules.image.webp_compressor", fromlist=["WebpCompressorTool"]).WebpCompressorTool,
        is_implemented=True
    ))
    R(ToolDefinition(
        "image_target_size",
        "Target Size (KB/MB) & Dimension Resizer",
        c, c_name,
        "Fit images exactly under strict job portal and passport byte limits",
        ["target size", "kb", "passport size", "resize dimension"],
        factory=lambda: __import__("src.modules.image.target_size_resizer", fromlist=["TargetSizeResizerTool"]).TargetSizeResizerTool,
        is_implemented=True
    ))
    R(ToolDefinition(
        "image_format_switch",
        "Universal Image Format Switcher",
        c, c_name,
        "Lossless cross-conversion among PNG, JPG, WebP, BMP, TIFF and ICO",
        ["convert image", "png to jpg", "ico", "webp to png"],
        factory=lambda: __import__("src.modules.image.format_switcher", fromlist=["ImageFormatSwitcherTool"]).ImageFormatSwitcherTool,
        is_implemented=True
    ))
    R(ToolDefinition("image_watermark", "Batch Logo & Watermark Stamper", c, c_name, "Batch stamp transparent branding across 100+ photos with corner anchoring", ["watermark image", "logo stamp", "brand photos"]))
    R(ToolDefinition("image_upscale_4k", "AI 4K Super-Resolution Image Upscaler", c, c_name, "Upscale low-resolution 480p/720p graphics 4x into crisp 4K detail", ["upscale", "super resolution", "enhance photo", "4k"]))
    R(ToolDefinition(
        "image_palette_harvest",
        "Dominant Color Palette Harvester",
        c, c_name,
        "Extract top 5 aesthetic colors with one-click Hex, RGB and CSS variables",
        ["colors", "palette", "hex", "swatch", "eyedropper"],
        factory=lambda: __import__("src.modules.image.palette_harvester", fromlist=["PaletteHarvesterTool"]).PaletteHarvesterTool,
        is_implemented=True
    ))
    R(ToolDefinition("image_vectorize", "Raster to Scalable Vector Converter", c, c_name, "Trace pixelated icons, sketches and logos into infinitely scalable SVG", ["vectorize", "svg", "trace", "vector"]))
    R(ToolDefinition("image_app_icon_gen", "Multi-Platform App Icon & Favicon Studio", c, c_name, "Export all required iOS, Android, Windows and Web icon sizes from one image", ["icon", "favicon", "app icon", "manifest", "android icon"]))
    R(ToolDefinition("image_heic_fixer", "Mobile HEIC to JPG/PNG Bulk Converter", c, c_name, "Batch convert smartphone HEIC photos to standard formats with full metadata", ["heic", "iphone photos", "heic to jpg", "apple photos"]))
    R(ToolDefinition("image_lut_stamper", "Cinematic Color Grade & Filter Stamper", c, c_name, "Apply consistent 3D color grade aesthetics across dozens of images in seconds", ["lut", "filter", "color grade", "aesthetic", "cube"]))
    R(ToolDefinition("image_boundary_eraser", "Smart Contiguous Background Eraser", c, c_name, "Erase solid backdrops while keeping subject interiors (teeth, rings, gaps) intact", ["magic wand", "contiguous", "ring hole", "solid color eraser"]))

    # ── Category 5: Creator Intel & Growth Radar
    c = "creator"
    c_name = "Creator Intel"
    R(ToolDefinition("creator_stats_radar", "Channel & Competitor Intel Radar", c, c_name, "Analyze channels, engagement metrics and identify viral outlier videos", ["competitor", "stats", "viral outlier", "youtube radar", "intel"]))
    R(ToolDefinition(
        "creator_bolt_down",
        "Web Video Downloader",
        c, c_name,
        "Download videos, shorts, and playlists up to 4K 60fps or save audio directly",
        ["download video", "bolt", "stream", "4k download", "playlist"],
        factory=lambda: __import__("src.modules.creator.stream_harvester", fromlist=["StreamHarvesterTool"]).StreamHarvesterTool,
        is_implemented=True
    ))
    R(ToolDefinition(
        "creator_thumb_grab",
        "YouTube Thumbnail Downloader",
        c, c_name,
        "Preview and download official full-HD video thumbnails with 1-click save",
        ["thumbnail", "maxres", "tags", "metadata grab"],
        factory=lambda: __import__("src.modules.creator.thumbnail_grabber", fromlist=["ThumbnailGrabberTool"]).ThumbnailGrabberTool,
        is_implemented=True
    ))
    R(ToolDefinition(
        "creator_trans_harvest",
        "YouTube Subtitle & Transcript Downloader",
        c, c_name,
        "Download video subtitles and spoken transcripts in 20+ languages as .txt or .srt files",
        ["transcript", "captions", "ytranscripter", "subtitles download"],
        factory=lambda: __import__("src.modules.creator.transcript_harvester", fromlist=["TranscriptHarvesterTool"]).TranscriptHarvesterTool,
        is_implemented=True
    ))
    R(ToolDefinition("creator_fullpage_cap", "Full-Page Scrolling Webpage Capture", c, c_name, "Capture entire top-to-bottom long webpage screenshots or crisp PDFs", ["screenshot", "full page", "scrolling capture", "web to pdf"]))
    R(ToolDefinition("creator_feed_tester", "Feed & Mobile Viewport Mockup Tester", c, c_name, "Simulate live mobile feeds to test thumbnail contrast and legibility", ["mockup", "mrbeast test", "thumbnail test", "mobile preview"]))
    R(ToolDefinition("creator_auto_chapters", "Auto Video Chapter & Timestamp Generator", c, c_name, "Analyze transcripts to generate copy-paste description chapters", ["chapters", "timestamps", "youtube description", "segments"]))
    R(ToolDefinition("creator_teleprompter", "Floating Camera-Eye Teleprompter", c, c_name, "Semi-transparent overlay prompter floating directly beside your webcam", ["teleprompter", "prompter", "speech notes", "script overlay"]))

    # ── Category 6: Design, Text & Everyday Utilities
    c = "design"
    c_name = "Design & Text"
    R(ToolDefinition("design_contrast_lab", "Hex Color Studio & Accessibility Inspector", c, c_name, "Real-time WCAG contrast ratios, color conversions and CSS snippets", ["contrast", "wcag", "color picker", "hex", "accessibility"]))
    R(ToolDefinition("design_text_lab", "Quick Text Lab & Word Counter", c, c_name, "Real-time word, character, speaking time metrics and case converters", ["words", "chars", "counter", "case converter", "slug"]))
    R(ToolDefinition("design_qr_studio", "Offline Secure QR Code Studio", c, c_name, "Permanent direct-link QR codes for URLs, Wi-Fi keys, and text with custom styling", ["qr code", "wifi qr", "direct link", "offline qr"]))
    R(ToolDefinition("design_markdown_pdf", "Markdown to Styled Document Studio", c, c_name, "Render technical notes into publication-grade styled PDFs or clean HTML", ["markdown", "md to pdf", "syntax highlight", "docs"]))
    R(ToolDefinition("design_data_studio", "Offline JSON, YAML & Data Format Studio", c, c_name, "Validate, format and convert data structures without external network leaks", ["json", "yaml", "xml", "formatter", "beautify"]))
    R(ToolDefinition("design_diff_compare", "Side-by-Side Visual Script & Text Diff Comparator", c, c_name, "Compare script drafts and code revisions with side-by-side color highlights", ["diff", "compare text", "revisions", "changes"]))

    # ── Category 7: System, File & Security Utilities
    c = "system"
    c_name = "System & Files"
    R(ToolDefinition("system_exif_strip", "Privacy Guard & EXIF Metadata Purger", c, c_name, "Inspect and permanently scrub GPS home tags and camera serials from media", ["exif", "privacy", "gps wipe", "metadata stripper"]))
    R(ToolDefinition(
        "system_batch_rename",
        "Power Batch File Renamer",
        c, c_name,
        "Batch prefix, suffix, sequence numbering and find-and-replace with live preview",
        ["rename", "batch rename", "numbering", "prefix"],
        factory=lambda: __import__("src.modules.system.batch_renamer", fromlist=["BatchRenamerTool"]).BatchRenamerTool,
        is_implemented=True
    ))
    R(ToolDefinition(
        "system_ext_switcher",
        "Smart File Extension Corrector",
        c, c_name,
        "Detect true file headers and safely repair damaged or misnamed extensions",
        ["extension", "extenger", "fix extension", "file type"],
        factory=lambda: __import__("src.modules.system.ext_switcher", fromlist=["ExtensionCorrectorTool"]).ExtensionCorrectorTool,
        is_implemented=True
    ))
    R(ToolDefinition(
        "system_tree_scaffold",
        "Project Tree Structure Scaffolder",
        c, c_name,
        "Paste any ASCII project tree diagram and automatically generate all folders & files on disk",
        ["foldermaker", "tree", "scaffold", "project structure", "folders"],
        factory=lambda: __import__("src.modules.system.tree_scaffolder", fromlist=["TreeScaffolderTool"]).TreeScaffolderTool,
        is_implemented=True
    ))
    R(ToolDefinition("system_dup_hunter", "Deep Storage Duplicate File Hunter", c, c_name, "Byte-level hash scanner to identify exact duplicate files and reclaim storage", ["duplicate", "clean disk", "free storage", "hash match"]))
    R(ToolDefinition("system_link_unshorten", "Safe Link Destination & Redirect Inspector", c, c_name, "Uncover final scam/redirect destinations of shortened URLs safely", ["unshorten", "safe link", "redirect trace", "url check"]))
    R(ToolDefinition("system_net_ping", "Ad-Free Network Ping & Connection Monitor", c, c_name, "Zero-ad instant latency, jitter and bandwidth diagnostic in under 5 seconds", ["speed test", "ping", "latency", "network"]))
    R(ToolDefinition("system_file_vault", "Encrypted File & Folder Vault", c, c_name, "Lock private files into encrypted vault containers with instant in-app restore", ["vault", "encrypt folder", "lock files", "secure"]))
    R(ToolDefinition("system_clean_empty", "Zero-Byte & Empty Directory Sweeper", c, c_name, "Recursively purge empty ghost directories and orphaned zero-byte files", ["empty folders", "clean ssd", "zero byte", "sweep"]))

_init_catalog()
