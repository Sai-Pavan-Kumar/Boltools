"""Which local port serves the app's screens.

pywebview serves ui/ from 127.0.0.1:42001 so the WebView origin (and with it
localStorage: theme, recents) stays the same between launches. But when a
second Boltools process (a right-click card, a dev copy, an old window during
an update) asks for the same port, Windows lets it share the port and its
window silently loads the OTHER process's files. Each process therefore checks
the port first and takes a free one when it is in use.
"""

import socket

SHARED_UI_PORT = 42001


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        # Exclusive bind: unlike the default, this fails while another process holds the port.
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            probe.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def main_window_port() -> int:
    """The shared port when nobody holds it (keeps saved settings), else a free one."""
    return SHARED_UI_PORT if _port_is_free(SHARED_UI_PORT) else free_port()
