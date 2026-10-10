"""Boltools Desktop Application Root Entrypoint (Option 1: Modern Native WebView2 Shell).

Features:
- Native Windows Edge WebView2 Architecture
- 100% Offline Modern Web UI with Tailwind CSS & Lucide SVG Icons
- Decoupled, Language-Agnostic Process Runner for all Tool Engines
- Zero Tkinter artifacts, zero pixelated emoji glyphs, zero UI freezing
"""

import os
import sys

# Set explicit Windows AppUserModelID so taskbar binds window to Boltools app icon
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("TheSurfBoard.Boltools.App.1.0")
    except Exception:
        pass

# Subprocess worker hook for decoupled tool engines in frozen mode
if "--engine-worker" in sys.argv:
    idx = sys.argv.index("--engine-worker")
    if idx + 1 < len(sys.argv):
        worker_script = sys.argv[idx + 1]
        try:
            import runpy
            sys.argv = [worker_script] + sys.argv[idx + 2:]
            runpy.run_path(worker_script, run_name="__main__")
        except Exception as e:
            import json
            print(json.dumps({"type": "error", "message": f"Worker crashed: {e}"}), flush=True)
    sys.exit(0)

# Resolve root directory (handles both frozen PyInstaller and source runs)
if getattr(sys, 'frozen', False):
    root_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
else:
    root_dir = os.path.dirname(os.path.abspath(__file__))

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import webview
from src.desktop_bridge import desktop_bridge


def _get_icon_path():
    """Finds the absolute path to boltools.ico across frozen or source environments."""
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else root_dir
    possible = [
        os.path.join(exe_dir, "boltools.ico"),
        os.path.join(root_dir, "assets", "boltools.ico"),
        os.path.join(exe_dir, "assets", "boltools.ico"),
        os.path.join(exe_dir, "_internal", "assets", "boltools.ico"),
        os.path.join(root_dir, "ui", "assets", "boltools.ico"),
    ]
    for p in possible:
        if os.path.isfile(p):
            return p
    return None


def _apply_win_icon(window):
    """Sets custom taskbar and titlebar icon via Win32 API to override Python runtime icon."""
    try:
        import time
        import ctypes
        time.sleep(0.3)
        icon_path = _get_icon_path()
        if icon_path:
            hwnd = ctypes.windll.user32.FindWindowW(None, "Boltools")
            if hwnd:
                h_icon_big = ctypes.windll.user32.LoadImageW(None, icon_path, 1, 32, 32, 0x00000010)
                h_icon_small = ctypes.windll.user32.LoadImageW(None, icon_path, 1, 16, 16, 0x00000010)
                if h_icon_big:
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, h_icon_big) # ICON_BIG
                if h_icon_small:
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, h_icon_small) # ICON_SMALL
    except Exception:
        pass


def main():
    ui_html_path = os.path.join(root_dir, "ui", "index.html")
    icon_path = _get_icon_path()

    # Create native Windows WebView2 window
    window = webview.create_window(
        title="Boltools",
        url=ui_html_path,
        width=1280,
        height=840,
        min_size=(1024, 680),
        js_api=desktop_bridge,
        text_select=False
    )
    if window is None:
        raise RuntimeError("Failed to create webview window.")

    desktop_bridge.set_window(window)

    # Ensure persistent storage directory for Edge WebView2 user data (theme, localStorage, recents)
    storage_dir = os.path.join(os.path.expanduser("~"), ".boltools", "webview2_data")
    os.makedirs(storage_dir, exist_ok=True)

    # Launch Edge Chromium (WebView2) with custom window icon and persistent session
    webview.start(
        _apply_win_icon,
        (window,),
        icon=icon_path if (icon_path and os.path.exists(icon_path)) else None,
        gui="edgechromium",
        debug=False,
        private_mode=False,
        storage_path=storage_dir
    )


if __name__ == "__main__":
    main()
