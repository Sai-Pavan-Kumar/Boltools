"""Desktop Bridge API for Boltools WebView2 Shell.

Provides asynchronous interface between the modern frontend and OS/engine services:
- Language-Agnostic Process Execution
- Native File/Folder Dialogs (via webview native Win32 dialogs)
- Windows Explorer integration (os.startfile)
- Real-time Hardware System Resource streaming
- Persistent Favorites and 2-Tier Modular Tool Management
"""

import os
import sys
import json
import shutil
import subprocess
from typing import Dict, Any, List, Optional
import webview

from src.core.system_monitor import system_monitor
from src.core.favorites import favorites_service
from src.core.community import community_service
from src.core.announcements import announcement_service
from src.engine_runner import engine_runner


class DesktopBridge:
    """JS-accessible API exposed to the WebView2 frontend via window.pywebview.api."""

    def __init__(self):
        self.window: Optional[webview.Window] = None
        if getattr(sys, "frozen", False):
            self.base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        else:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.engines_dir = os.path.join(self.base_dir, "engines")

    def set_window(self, window: webview.Window):
        self.window = window

    # ── Initial State Dispatcher ─────────────────────────────────────────────
    def get_initial_data(self) -> Dict[str, Any]:
        """Provides full catalog, installed status, favorites, and system metrics to frontend."""
        # 5 Implemented Engines + Catalog Metadata
        tools = [
            {
                "id": "media_audio_extractor",
                "name": "Universal Media & Audio Extractor",
                "category_id": "video",
                "category_name": "Media & Video",
                "description": "Extract clean, lossless MP3, WAV, AAC, or FLAC audio tracks from any video container without re-encoding frames.",
                "icon": "music",
                "is_implemented": True,
                "engine_type": "python",
                "target": os.path.join(self.engines_dir, "audio_extractor", "engine.py")
            },
            {
                "id": "video_compressor",
                "name": "Target Video Size Compressor",
                "category_id": "video",
                "category_name": "Media & Video",
                "description": "Mathematically compress videos to fit exact upload caps (WhatsApp 16MB, Discord 25MB) without bitrate guesswork.",
                "icon": "video",
                "is_implemented": True,
                "engine_type": "python",
                "target": os.path.join(self.engines_dir, "video_compressor", "engine.py")
            },
            {
                "id": "pdf_converter",
                "name": "PDF to Editable Word / DOCX Converter",
                "category_id": "pdf",
                "category_name": "PDF Studio",
                "description": "Convert PDF documents into clean, fully editable Word DOCX files preserving paragraph flows and tables.",
                "icon": "file-text",
                "is_implemented": True,
                "engine_type": "python",
                "target": os.path.join(self.engines_dir, "pdf_converter", "engine.py")
            },
            {
                "id": "image_webp_compress",
                "name": "Lossless WebP & JPG Compressor",
                "category_id": "image",
                "category_name": "Image Studio",
                "description": "Shrink image file footprints by 60%–85% with zero perceptible quality drop using multi-thread compression.",
                "icon": "image",
                "is_implemented": True,
                "engine_type": "python",
                "target": os.path.join(self.engines_dir, "webp_compressor", "engine.py")
            },
            {
                "id": "system_batch_rename",
                "name": "Bulk File & Folder Renamer",
                "category_id": "system",
                "category_name": "System & Files",
                "description": "Batch rename files with rule-based prefix, suffix, sequence numbering, and find-and-replace locally.",
                "icon": "sliders",
                "is_implemented": True,
                "engine_type": "python",
                "target": os.path.join(self.engines_dir, "batch_renamer", "engine.py")
            }
        ]

        # Sync tool installation state with user overrides
        for t in tools:
            st = community_service.get_tool_status(t["id"], "installed" if t["is_implemented"] else "available")
            t["status"] = st

        categories = [
            {"id": "video", "name": "Media & Video", "desc": "Fast offline video compression, extraction, and formatting", "icon": "video", "accent": "#2563EB"},
            {"id": "pdf", "name": "PDF Studio", "desc": "Offline conversion, splitting, merging, and document protection", "icon": "file-text", "accent": "#DC2626"},
            {"id": "image", "name": "Image Studio", "desc": "Batch WebP compression, target sizing, and format switching", "icon": "image", "accent": "#059669"},
            {"id": "system", "name": "System & Files", "desc": "Power file renaming, extension repair, and organization", "icon": "sliders", "accent": "#475569"}
        ]

        cpu, ram, disk = system_monitor.get_stats()

        return {
            "categories": categories,
            "tools": tools,
            "favorites": favorites_service.get_all(),
            "announcements": announcement_service.cached_announcements,
            "system_stats": {"cpu": cpu, "ram": ram, "disk": disk},
            "default_downloads": os.path.join(os.path.expanduser("~"), "Downloads")
        }

    # ── Engine Execution (Language-Agnostic) ──────────────────────────────────
    def execute_tool(self, tool_id: str, input_files: List[str], options: Dict[str, Any], output_dir: str):
        """Executes tool engine in a clean, isolated background process."""
        initial_data = self.get_initial_data()
        tool_meta = next((t for t in initial_data["tools"] if t["id"] == tool_id), None)

        if not tool_meta:
            self._notify_frontend("onToolError", f"Unknown tool: {tool_id}")
            return

        engine_type = tool_meta.get("engine_type", "python")
        target = tool_meta.get("target", "")

        def _on_progress(pct: float, status: str):
            self._notify_frontend("onToolProgress", {"percent": pct, "status": status})

        def _on_log(msg: str):
            self._notify_frontend("onToolLog", msg)

        def _on_complete(out_path: str):
            self._notify_frontend("onToolComplete", {"output_file": out_path})

        def _on_error(err_msg: str):
            self._notify_frontend("onToolError", err_msg)

        engine_runner.run_engine(
            tool_id=tool_id,
            engine_type=engine_type,
            executable_target=target,
            input_files=input_files,
            options=options,
            output_dir=output_dir,
            on_progress=_on_progress,
            on_log=_on_log,
            on_complete=_on_complete,
            on_error=_on_error
        )

    def cancel_tool(self) -> bool:
        """Stops active engine process cleanly."""
        res = engine_runner.cancel_active()
        if res:
            self._notify_frontend("onToolLog", "Operation cancelled by user.")
            self._notify_frontend("onToolError", "Operation cancelled.")
        return res

    # ── Native Dialogs & System Explorer ─────────────────────────────────────
    def browse_files(self, file_types: Optional[List[str]] = None) -> List[str]:
        """Opens native Windows file dialog and returns selected file paths."""
        if not self.window:
            return []
        try:
            cleaned_filters: List[str] = []
            if file_types:
                for ft in file_types:
                    try:
                        # Clean filter description to match pywebview's ^([\w ]+) requirements
                        if "(" in ft and ft.endswith(")"):
                            desc, exts = ft.split("(", 1)
                            desc_clean = "".join(c for c in desc if c.isalnum() or c == " ").strip()
                            cleaned_filters.append(f"{desc_clean} ({exts}")
                        else:
                            cleaned_filters.append(ft)
                    except Exception:
                        pass
            if not cleaned_filters:
                cleaned_filters = ["All Files (*.*)"]

            result = self.window.create_file_dialog(
                dialog_type=webview.OPEN_DIALOG,
                allow_multiple=True,
                file_types=tuple(cleaned_filters)
            )
            return list(result) if result else []
        except Exception:
            # Fallback without file type constraints to ensure file picker never gets blocked
            try:
                result = self.window.create_file_dialog(
                    dialog_type=webview.OPEN_DIALOG,
                    allow_multiple=True
                )
                return list(result) if result else []
            except Exception:
                return []

    def browse_directory(self) -> str:
        """Opens native Windows folder selection dialog."""
        if not self.window:
            return ""
        try:
            result = self.window.create_file_dialog(dialog_type=webview.FOLDER_DIALOG)
            if result and len(result) > 0:
                return result[0]
            return ""
        except Exception:
            return ""

    def open_file(self, target_path: str):
        """Opens the specified file directly in the OS default application."""
        if not target_path or not os.path.exists(target_path):
            return
        try:
            norm = os.path.normpath(target_path)
            os.startfile(norm)
        except Exception:
            pass

    def reveal_file(self, target_path: str):
        """Opens the exact containing directory in Windows Explorer and selects the file."""
        if not target_path:
            return
        norm = os.path.normpath(target_path)
        if not os.path.exists(norm):
            parent = os.path.dirname(norm)
            if os.path.exists(parent):
                try:
                    os.startfile(parent)
                except Exception:
                    pass
            return
        try:
            if os.path.isfile(norm):
                subprocess.Popen(f'explorer /select,"{norm}"', shell=True)
            else:
                os.startfile(norm)
        except Exception:
            try:
                folder = os.path.dirname(norm) if os.path.isfile(norm) else norm
                os.startfile(folder)
            except Exception:
                pass

    def open_path(self, target_path: str):
        """Legacy helper for backwards compatibility."""
        if not target_path or not os.path.exists(target_path):
            return
        if os.path.isfile(target_path):
            self.reveal_file(target_path)
        else:
            self.open_file(target_path)

    # ── Favorites & Lifecycle Services ───────────────────────────────────────
    def toggle_favorite(self, tool_id: str) -> List[str]:
        favorites_service.toggle_favorite(tool_id)
        return favorites_service.get_all()

    def install_tool(self, tool_id: str) -> bool:
        return community_service.install_tool(tool_id)

    def uninstall_tool(self, tool_id: str, purge_data: bool = False) -> bool:
        return community_service.uninstall_tool(tool_id, purge_data=purge_data)

    def clean_cache(self) -> Dict[str, Any]:
        """Cleans temporary logs/caches without touching presets."""
        state_dir = os.path.join(os.path.expanduser("~"), ".boltools")
        cleaned = 0
        if os.path.exists(state_dir):
            for fname in os.listdir(state_dir):
                if fname.endswith(".tmp") or fname.endswith(".log"):
                    try:
                        os.remove(os.path.join(state_dir, fname))
                        cleaned += 1
                    except Exception:
                        pass
        return {"success": True, "cleaned_files": cleaned}

    def get_system_stats(self) -> Dict[str, int]:
        cpu, ram, disk = system_monitor.get_stats()
        return {"cpu": cpu, "ram": ram, "disk": disk}

    # ── Helper for Frontend Dispatch ─────────────────────────────────────────
    def _notify_frontend(self, handler_name: str, payload: Any):
        if not self.window:
            return
        payload_json = json.dumps(payload)
        js_code = f"if (window.{handler_name}) {{ window.{handler_name}({payload_json}); }}"
        self.window.evaluate_js(js_code)


desktop_bridge = DesktopBridge()
