"""Decides which actions fit a set of files.

The right-click menu and the in-app file picker both ask this module, and it
reads only the tools list. A tool offers either one-click "quick_actions" (run
in place with fixed settings) or a single entry that opens the app because it
needs the user's input first. A new tool therefore shows up for the right files
without anyone touching menu code.

Menu keys: "tool_id" opens the app, "tool_id@N" runs quick action N.
"""

import os
from typing import Dict, Iterable, List, Optional, Tuple

ANY_FILE = "*"
QUICK_SEPARATOR = "@"


def file_extension(path: str) -> str:
    return os.path.splitext(path)[1].lstrip(".").lower()


def menu_items(tools: Iterable[Dict]) -> List[Dict]:
    """Every menu entry the tools list offers, before looking at any files."""
    items = []
    for tool in tools:
        accepts = tool.get("accepts") or []
        if not accepts or not tool.get("is_implemented", True):
            continue
        min_files = int(tool.get("min_files", 1))
        quick = tool.get("quick_actions") or []
        for index, action in enumerate(quick):
            items.append({
                "key": f"{tool['id']}{QUICK_SEPARATOR}{index}",
                "label": action["label"],
                "accepts": action.get("accepts") or accepts,
                "min_files": int(action.get("min_files", min_files)),
            })
        if not quick:
            items.append({
                "key": tool["id"],
                "label": tool.get("menu_label") or tool.get("name") or tool["id"],
                "accepts": accepts,
                "min_files": min_files,
            })
    return items


def item_fits(item: Dict, paths: List[str]) -> bool:
    accepts = item["accepts"]
    if not paths or len(paths) < item["min_files"]:
        return False
    if ANY_FILE in accepts:
        return True
    return all(file_extension(p) in accepts for p in paths)


def menu_entries(tools: Iterable[Dict], paths: List[str]) -> List[Dict]:
    """Entries for these files, in tools-list order; "any file" entries go last."""
    fits = [i for i in menu_items(tools) if item_fits(i, paths)]
    return sorted(fits, key=lambda i: ANY_FILE in i["accepts"])


def resolve_key(tools: Iterable[Dict], key: str) -> Tuple[Optional[Dict], Optional[Dict]]:
    """(tool, quick action) for a menu key; the action is None for "open the app" keys."""
    tool_id, _, index = key.partition(QUICK_SEPARATOR)
    tool = next((t for t in tools if t.get("id") == tool_id), None)
    if not tool or not index:
        return tool, None
    quick = tool.get("quick_actions") or []
    if not index.isdigit() or int(index) >= len(quick):
        return tool, None
    return tool, quick[int(index)]
