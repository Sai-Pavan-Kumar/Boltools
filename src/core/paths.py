"""Centralized path resolution helper for development and PyInstaller frozen execution."""

import os
import sys


def get_base_dir() -> str:
    """Returns the root directory of the application bundle.
    
    Works seamlessly both in development (.py) and when frozen via PyInstaller (.exe).
    """
    if getattr(sys, "frozen", False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS,
        # or in one-dir mode the executable directory contains the assets.
        if hasattr(sys, "_MEIPASS"):
            return sys._MEIPASS
        return os.path.dirname(os.path.abspath(sys.executable))
    
    # In dev mode: src/core/paths.py -> go 2 levels up to software/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_asset_path(*subpaths) -> str:
    """Returns an absolute path to a file inside the assets directory."""
    return os.path.join(get_base_dir(), "assets", *subpaths)


def get_data_path(*subpaths) -> str:
    """Returns an absolute path to a file in the app bundle root (e.g. catalog.json, poll.json)."""
    return os.path.join(get_base_dir(), *subpaths)
