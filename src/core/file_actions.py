"""Decides which tools fit a set of files.

The right-click menu and the in-app file picker both ask this module, and it
reads only the tools list ("accepts", "min_files", "menu_label"). A new tool
therefore shows up for the right files without anyone touching menu code.
"""

import os
from typing import Dict, Iterable, List

ANY_FILE = "*"


def file_extension(path: str) -> str:
    return os.path.splitext(path)[1].lstrip(".").lower()


def tool_fits(tool: Dict, paths: List[str]) -> bool:
    accepts = tool.get("accepts") or []
    if not paths or not accepts or not tool.get("is_implemented", True):
        return False
    if len(paths) < int(tool.get("min_files", 1)):
        return False
    if ANY_FILE in accepts:
        return True
    return all(file_extension(p) in accepts for p in paths)


def matching_tools(tools: Iterable[Dict], paths: List[str]) -> List[Dict]:
    """Tools that can take every selected file, in tools-list order.

    "Any file" tools (like Rename) go last so the specific actions stay on top.
    """
    fits = [t for t in tools if tool_fits(t, paths)]
    return sorted(fits, key=lambda t: ANY_FILE in (t.get("accepts") or []))


def menu_entries(tools: Iterable[Dict], paths: List[str]) -> List[Dict[str, str]]:
    return [
        {"id": t["id"], "label": t.get("menu_label") or t.get("name", t["id"])}
        for t in matching_tools(tools, paths)
    ]
