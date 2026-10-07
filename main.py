"""Boltools Desktop Application Root Entrypoint (Option 1: Modern Native WebView2 Shell).

Features:
- Native Windows Edge WebView2 Architecture
- 100% Offline Modern Web UI with Tailwind CSS & Lucide SVG Icons
- Decoupled, Language-Agnostic Process Runner for all Tool Engines
- Zero Tkinter artifacts, zero pixelated emoji glyphs, zero UI freezing
"""

import os
import sys

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


def main():
    ui_html_path = os.path.join(root_dir, "ui", "index.html")

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
    desktop_bridge.set_window(window)

    # Launch Edge Chromium (WebView2)
    webview.start(gui="edgechromium", debug=False)


if __name__ == "__main__":
    main()
