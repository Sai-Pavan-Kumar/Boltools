"""One Boltools window at a time.

A right-click starts a new process. If Boltools is already open, that process
hands its request to the open window over a per-user named pipe and exits, so
the user never gets a second window (or a WebView profile clash).
"""

import getpass
import hashlib
import threading
from multiprocessing.connection import Client, Listener
from typing import Callable, Dict, Optional

_USER_TAG = hashlib.sha256(getpass.getuser().encode("utf-8")).hexdigest()[:12]
PIPE_NAME = rf"\\.\pipe\boltools-{_USER_TAG}"
# Stops other local programs from injecting requests; not a secret against the same user.
_AUTH_KEY = b"boltools-open-request-" + _USER_TAG.encode("ascii")


def hand_off(request: Optional[Dict]) -> bool:
    """True when another Boltools window took the request (this process should exit)."""
    try:
        # Explorer gave this process the right to take focus; pass it on to the open window.
        import ctypes
        ctypes.windll.user32.AllowSetForegroundWindow(-1)
    except Exception:
        pass
    try:
        with Client(PIPE_NAME, family="AF_PIPE", authkey=_AUTH_KEY) as conn:
            conn.send(request or {})
        return True
    except (OSError, EOFError, ConnectionError):
        return False


def listen(on_request: Callable[[Dict], None]) -> None:
    try:
        listener = Listener(PIPE_NAME, family="AF_PIPE", authkey=_AUTH_KEY)
    except OSError:
        return

    def _serve():
        while True:
            try:
                with listener.accept() as conn:
                    request = conn.recv()
                if isinstance(request, dict):
                    on_request(request)
            except Exception:
                continue

    threading.Thread(target=_serve, name="boltools-single-instance", daemon=True).start()


def parse_open_request(argv) -> Optional[Dict]:
    """Reads `--open-tool <tool_id> <file>...` (right-click) or a boltools:// link (notifications)."""
    if any(str(arg).lower().startswith("boltools://") for arg in argv[1:]):
        return {"view": "tool_hub"}
    if "--open-tool" not in argv:
        return None
    idx = argv.index("--open-tool")
    if idx + 1 >= len(argv):
        return None
    files = [a for a in argv[idx + 2:] if not a.startswith("--")]
    return {"tool_id": argv[idx + 1], "files": files}
