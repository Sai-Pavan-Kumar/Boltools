"""Keeps the Windows right-click menu in step with the tools list.

The menu DLL (shell_menu/) knows nothing about tools; it reads the file written
here on every launch. Format is documented at the top of boltools_menu.c.
"""

import os
import sys
from typing import Dict, Iterable

from src.core.file_actions import menu_items

MENU_FILE = os.path.join(os.path.expanduser("~"), ".boltools", "explorer-menu.txt")


def _launch_line(root_dir: str, is_dev: bool):
    if getattr(sys, "frozen", False):
        exe = sys.executable
        return f'"{exe}"', os.path.dirname(exe), f"{exe},0"
    # pythonw has no console window, so a right-click never flashes a black box.
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.isfile(pythonw):
        pythonw = sys.executable
    command = f'"{pythonw}" "{os.path.join(root_dir, "main.py")}"' + (" --dev" if is_dev else "")
    return command, root_dir, os.path.join(root_dir, "assets", "boltools.ico")


def _clean(text: str) -> str:
    return str(text).replace("|", " ").replace("\n", " ").strip()


def write_menu_file(tools: Iterable[Dict], root_dir: str, is_dev: bool) -> None:
    command, work_dir, icon = _launch_line(root_dir, is_dev)
    lines = [command, work_dir, icon]
    for item in menu_items(tools):
        lines.append("|".join([
            _clean(item["key"]), _clean(item["label"]), str(item["min_files"]),
            ",".join(_clean(e).lower() for e in item["accepts"]),
        ]))
    os.makedirs(os.path.dirname(MENU_FILE), exist_ok=True)
    temp = MENU_FILE + ".tmp"
    with open(temp, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    # Replace in one step so Explorer never reads a half-written file.
    os.replace(temp, MENU_FILE)
