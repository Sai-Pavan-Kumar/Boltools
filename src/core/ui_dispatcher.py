"""Fire-and-forget delivery of engine events to the WebView.

pywebview's evaluate_js blocks until the page answers. When it was called
straight from the engine worker thread, one slow or stuck UI call froze the
worker, so the runner never released its slot: every later run failed with
"already running" and Cancel had nothing left to clear. Engine threads now
only drop messages into a queue; one daemon thread talks to the UI.
"""

import json
import queue
import sys
import threading
from typing import Any

_MAX_PENDING = 500


class UiDispatcher:
    def __init__(self):
        self._window = None
        self._queue: "queue.Queue[str]" = queue.Queue(maxsize=_MAX_PENDING)
        threading.Thread(target=self._pump, daemon=True, name="ui-dispatcher").start()

    def attach(self, window) -> None:
        self._window = window

    def send(self, handler_name: str, payload: Any) -> None:
        js_code = f"if (window.{handler_name}) {{ window.{handler_name}({json.dumps(payload)}); }}"
        try:
            self._queue.put_nowait(js_code)
        except queue.Full:
            # A UI that has fallen this far behind only needs the latest state; drop the oldest.
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(js_code)
            except (queue.Empty, queue.Full):
                pass

    def _pump(self) -> None:
        while True:
            js_code = self._queue.get()
            window = self._window
            if window is None:
                continue
            try:
                window.evaluate_js(js_code)
            except Exception as err:
                print(f"[ui-dispatcher] evaluate_js failed: {err}", file=sys.stderr)


ui_dispatcher = UiDispatcher()
