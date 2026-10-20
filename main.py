"""Boltools Desktop Application Root Entrypoint (Option 1: Modern Native WebView2 Shell).

Features:
- Native Windows Edge WebView2 Architecture
- 100% Offline Modern Web UI with Tailwind CSS & Lucide SVG Icons
- Decoupled, Language-Agnostic Process Runner for all Tool Engines
- Zero Tkinter artifacts, zero pixelated emoji glyphs, zero UI freezing
"""

import os
import sys
import time

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

# Right-click launches in dev mode carry --dev, because Explorer has no BOLTOOLS_DEV.
if "--dev" in sys.argv:
    os.environ["BOLTOOLS_DEV"] = "1"

import webview
from src.desktop_bridge import desktop_bridge
from src._build import IS_RELEASE
from src.core import single_instance
from src.core.explorer_menu import write_menu_file
from src.core.file_actions import resolve_key
from src.core.ui_port import main_window_port
from src.core import new_tools, toast
from src.core.ui_dispatcher import ui_dispatcher
from src.core.launch_requests import launch_requests
from src.core.tool_store import tool_store_service


def _sync_explorer_menu():
    """Rewrites the right-click menu from the tools list; a failure only costs the menu."""
    try:
        tools = (tool_store_service.cached_manifest or {}).get("tools", [])
        is_dev = not IS_RELEASE and os.environ.get("BOLTOOLS_DEV") == "1"
        write_menu_file(tools, root_dir, is_dev)
    except Exception as err:
        print(f"[explorer-menu] could not write menu file: {err}", file=sys.stderr)


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


def _announce_new_tools(manifest):
    """Each new store tool gets one Windows notification, plus the bell and the Tool Hub dot."""
    fresh = new_tools.take_unannounced((manifest or {}).get("tools", []))
    if fresh:
        toast.announce_new_tools(fresh)
    ui_dispatcher.send("onNewTools", [t["id"] for t in fresh])


def _run_quick_action(request) -> bool:
    """Right-click one-click actions finish in a small card; False means open the app."""
    if "tool_id" not in request:
        return False
    tools = (tool_store_service.cached_manifest or {}).get("tools", [])
    tool, action = resolve_key(tools, request["tool_id"])
    files = [f for f in request["files"] if os.path.isfile(f)]
    if not tool or not action or not files:
        if tool:
            request["tool_id"] = tool["id"]
        return False
    from src.quick_run import run_quick
    run_quick(tool, action, files, root_dir, desktop_bridge, _get_icon_path())
    return True


def main():
    launch_request = single_instance.parse_open_request(sys.argv)
    if launch_request and _run_quick_action(launch_request):
        return
    # Automated test copies run beside the founder's window and must not hand off to it.
    is_test_copy = bool(os.environ.get("BOLTOOLS_WEBVIEW_DATA"))
    if not is_test_copy and single_instance.hand_off(launch_request):
        return
    launch_requests.set_initial(launch_request)
    _sync_explorer_menu()
    # A tool added online joins the right-click menu at once, not after a restart.
    tool_store_service.add_manifest_listener(lambda _manifest: _sync_explorer_menu())
    toast.register(_get_icon_path() or "")
    tool_store_service.add_manifest_listener(_announce_new_tools)
    _announce_new_tools(tool_store_service.cached_manifest or {})

    # WebView2 keeps an HTTP cache in storage_path and happily served a stale index.html
    # after updates, so new scripts never loaded. A per-launch URL forces a fresh page;
    # the ?v= stamps on scripts and styles still let those be cached between launches.
    launch_stamp = int(time.time())
    ui_html_path = f"{os.path.join(root_dir, 'ui', 'index.html')}?shell=native&launch={launch_stamp}"
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
    launch_requests.set_window(window)
    if not is_test_copy:
        single_instance.listen(launch_requests.deliver)

    # Guarantee native shell flag injection regardless of query string mangling by WebView2
    def _on_loaded():
        try:
            window.evaluate_js("window.__BOLTOOLS_NATIVE_SHELL__ = true;")
        except Exception:
            pass

    window.events.loaded += _on_loaded

    # Ensure persistent storage directory for Edge WebView2 user data (theme, localStorage, recents)
    storage_dir = os.path.join(os.path.expanduser("~"), ".boltools", "webview2_data")
    # Dev-only: a second instance (automated UI checks) needs its own WebView2 profile,
    # otherwise it fails to start while the founder's window is open.
    if not IS_RELEASE and os.environ.get("BOLTOOLS_DEV") == "1" and os.environ.get("BOLTOOLS_WEBVIEW_DATA"):
        storage_dir = os.environ["BOLTOOLS_WEBVIEW_DATA"]
    os.makedirs(storage_dir, exist_ok=True)

    # Launch Edge Chromium (WebView2) with custom window icon and persistent session
    webview.start(
        _apply_win_icon,
        (window,),
        icon=icon_path if (icon_path and os.path.exists(icon_path)) else None,
        gui="edgechromium",
        debug=False,
        private_mode=False,
        storage_path=storage_dir,
        http_port=main_window_port()
    )


if __name__ == "__main__":
    main()
