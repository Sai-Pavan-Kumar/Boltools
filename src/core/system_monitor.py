"""Native Windows System Monitor Service for Boltools.

Provides real-time CPU, RAM, and Disk metrics via native Windows Win32 APIs
and standard library with zero external dependencies and zero main-thread overhead.
"""

import sys
import time
import shutil
import ctypes
import threading
from typing import Tuple, Callable, Optional


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", ctypes.c_uint), ("dwHighDateTime", ctypes.c_uint)]


def _filetime_to_int(ft: FILETIME) -> int:
    return (ft.dwHighDateTime << 32) + ft.dwLowDateTime


class SystemMonitor:
    """Background monitor providing lightweight CPU, RAM, and Disk statistics."""

    def __init__(self, interval_sec: float = 5.0):
        self.interval = interval_sec
        self.cpu_pct: int = 12
        self.ram_pct: int = 42
        self.disk_pct: int = 35
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._subscribers: list[Callable[[int, int, int], None]] = []

        # Read initial values immediately
        self._sample_ram_disk()
        self.start()

    def subscribe(self, callback: Callable[[int, int, int], None]):
        """Registers a callback to receive (cpu, ram, disk) updates."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)
            callback(self.cpu_pct, self.ram_pct, self.disk_pct)

    def unsubscribe(self, callback: Callable[[int, int, int], None]):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def get_stats(self) -> Tuple[int, int, int]:
        return (self.cpu_pct, self.ram_pct, self.disk_pct)

    def _sample_ram_disk(self):
        try:
            # Disk
            disk = shutil.disk_usage("C:\\")
            self.disk_pct = max(1, min(100, int((disk.used / disk.total) * 100)))
        except Exception:
            pass

        try:
            # RAM via Win32 GlobalMemoryStatusEx
            if sys.platform.startswith("win"):
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
                self.ram_pct = max(1, min(100, int(stat.dwMemoryLoad)))
        except Exception:
            pass

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _worker_loop(self):
        prev_idle = FILETIME()
        prev_kernel = FILETIME()
        prev_user = FILETIME()

        is_win = sys.platform.startswith("win")
        if is_win:
            try:
                ctypes.windll.kernel32.GetSystemTimes(
                    ctypes.byref(prev_idle),
                    ctypes.byref(prev_kernel),
                    ctypes.byref(prev_user)
                )
            except Exception:
                is_win = False

        while self._running:
            time.sleep(self.interval)
            if not self._running:
                break

            # CPU calculation
            if is_win:
                try:
                    now_idle = FILETIME()
                    now_kernel = FILETIME()
                    now_user = FILETIME()
                    ctypes.windll.kernel32.GetSystemTimes(
                        ctypes.byref(now_idle),
                        ctypes.byref(now_kernel),
                        ctypes.byref(now_user)
                    )

                    idle_diff = _filetime_to_int(now_idle) - _filetime_to_int(prev_idle)
                    kernel_diff = _filetime_to_int(now_kernel) - _filetime_to_int(prev_kernel)
                    user_diff = _filetime_to_int(now_user) - _filetime_to_int(prev_user)

                    prev_idle = now_idle
                    prev_kernel = now_kernel
                    prev_user = now_user

                    total = kernel_diff + user_diff
                    if total > 0:
                        cpu = int(((total - idle_diff) / total) * 100)
                        self.cpu_pct = max(0, min(100, cpu))
                except Exception:
                    pass

            self._sample_ram_disk()

            # Notify listeners
            for cb in list(self._subscribers):
                try:
                    cb(self.cpu_pct, self.ram_pct, self.disk_pct)
                except Exception:
                    pass


# Singleton instance
system_monitor = SystemMonitor()
