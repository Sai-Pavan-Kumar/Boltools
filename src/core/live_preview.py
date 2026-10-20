"""Live previews: a tool marked "output": "live" redraws while the user types.

Starting an engine costs a second or more, far too slow per keystroke, so one
engine stays open per (tool, file) and gets each new set of options as a line
on stdin. It answers with images as data URLs; nothing touches the disk until
the user presses Save, which is an ordinary run into their folder.
"""

import json
import os
import queue
import subprocess
import sys
import threading
from typing import Any, Dict, List, Optional

from src.core import previews
from src.engine_runner import engine_command

FIRST_DRAW_TIMEOUT = 30.0  # engine start + opening a large image
REDRAW_TIMEOUT = 10.0
CREATE_NO_WINDOW = 0x08000000


class LivePreview:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._proc: Optional[subprocess.Popen] = None
        self._lines: "queue.Queue[Optional[str]]" = queue.Queue()
        self._key: Optional[tuple] = None

    def render(self, tool_id: str, engine_type: str, target: str, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            key = (tool_id, target, file_path)
            try:
                if self._key == key and self._alive():
                    self._send({"options": options})
                    return self._answer(REDRAW_TIMEOUT)
                self._close()
                self._start(engine_type, target, {"mode": "live", "tool_id": tool_id,
                                                  "input_files": [file_path], "options": options,
                                                  # An older engine ignores "live" and runs a normal job: keep its files private.
                                                  "output_dir": previews.new_preview_dir()})
                self._key = key
                return self._answer(FIRST_DRAW_TIMEOUT)
            except (OSError, ValueError) as err:
                self._close()
                return {"error": f"Could not draw the preview ({type(err).__name__})."}

    def stop(self) -> None:
        with self._lock:
            self._close()

    def _alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def _start(self, engine_type: str, target: str, payload: Dict[str, Any]) -> None:
        cmd = engine_command(engine_type, target)
        if not cmd:
            raise ValueError("unsupported engine")
        flags = CREATE_NO_WINDOW if sys.platform == "win32" else 0
        self._proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                                      creationflags=flags, bufsize=1)
        self._lines = queue.Queue()
        threading.Thread(target=self._pump, args=(self._proc, self._lines), daemon=True).start()
        self._send(payload)

    @staticmethod
    def _pump(proc: subprocess.Popen, lines: "queue.Queue[Optional[str]]") -> None:
        # A reader thread, because a blocking readline cannot time out on Windows pipes.
        try:
            for line in proc.stdout:
                lines.put(line)
        finally:
            lines.put(None)

    def _send(self, message: Dict[str, Any]) -> None:
        self._proc.stdin.write(json.dumps(message) + "\n")
        self._proc.stdin.flush()

    def _answer(self, timeout: float) -> Dict[str, Any]:
        while True:
            try:
                line = self._lines.get(timeout=timeout)
            except queue.Empty:
                self._close()
                return {"error": "The preview took too long. Try again."}
            if line is None:
                self._close()
                return {"error": "The preview stopped. Check that the tool is installed and up to date."}
            try:
                message = json.loads(line)
            except ValueError:
                continue
            if message.get("type") == "live":
                return {"images": _clean_images(message.get("images"))}
            if message.get("type") == "error":
                self._close()
                return {"error": str(message.get("message") or "Could not draw the preview.")}
            # An engine without live mode would run a normal job; stop it before it writes anything more.
            if message.get("type") == "done":
                self._close()
                return {"error": "Update this tool in Tool Store to see live previews."}

    def _close(self) -> None:
        proc, self._proc, self._key = self._proc, None, None
        if proc is None:
            return
        try:
            if proc.poll() is None:
                proc.stdin.write('{"cmd":"close"}\n')
                proc.stdin.flush()
                proc.stdin.close()
                proc.wait(timeout=1.0)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            proc.kill()


def _clean_images(images: Any) -> List[Dict[str, str]]:
    """Only image data URLs reach the screen, whatever an engine sends."""
    clean = []
    for item in images if isinstance(images, list) else []:
        data = str(item.get("data", "")) if isinstance(item, dict) else ""
        if data.startswith(("data:image/jpeg;base64,", "data:image/png;base64,")):
            clean.append({"label": str(item.get("label", ""))[:20], "data": data})
    return clean


live_preview = LivePreview()


def render_tool(tool_meta: Optional[Dict[str, Any]], target: Optional[str], file_path: Any, options: Any) -> Dict[str, Any]:
    """Checks the request from the screen before any engine starts."""
    if not tool_meta or tool_meta.get("output") != "live":
        return {"error": "This tool has no live preview."}
    if not target or not os.path.isfile(target):
        return {"error": "Install this tool in Tool Store first."}
    path = str(file_path or "")
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    accepts = tool_meta.get("accepts") or []
    if not os.path.isfile(path) or (accepts and "*" not in accepts and ext not in accepts):
        return {"error": "This file cannot be previewed here."}
    return live_preview.render(tool_meta["id"], tool_meta.get("engine_type", "python"), target,
                               path, options if isinstance(options, dict) else {})
