"""Which tools in the store are new to this user.

~/.boltools/seen_tools.json keeps two lists:
  seen      tools the user has had a chance to see in the store (clears the dot)
  notified  tool id -> date it was announced (Windows notification + bell), so
            each new tool is announced exactly once, whether the app or the daily
            check found it first; the bell keeps the notice for BELL_DAYS.
The first time this file is created, every current tool counts as seen and
notified: an existing user is not flooded with "new" tools that are not new.
"""

import json
import os
import threading
from datetime import date, timedelta
from typing import Dict, List

BELL_DAYS = 30

STATE_FILE = os.path.join(os.path.expanduser("~"), ".boltools", "seen_tools.json")
_lock = threading.Lock()


def _read() -> Dict:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    notified = data.get("notified", {})
    if isinstance(notified, list):  # first version kept a plain list
        notified = {tool_id: "" for tool_id in notified}
    return {"seen": list(data.get("seen", [])), "notified": dict(notified)}


def _write(data: Dict) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    temp = STATE_FILE + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(temp, STATE_FILE)


def _released(tools: List[Dict]) -> List[Dict]:
    return [t for t in tools if t.get("id") and t.get("is_implemented", True)]


def _state_for(tools: List[Dict]) -> Dict:
    data = _read()
    if not data:
        ids = [t["id"] for t in _released(tools)]
        data = {"seen": ids, "notified": {tool_id: "" for tool_id in ids}}
        _write(data)
    return data


def unseen(tools: List[Dict]) -> List[Dict]:
    """New tools the user has not looked at in the store yet (drives the dot)."""
    with _lock:
        seen = set(_state_for(tools)["seen"])
    return [t for t in _released(tools) if t["id"] not in seen]


def take_unannounced(tools: List[Dict]) -> List[Dict]:
    """New tools not announced yet; marks them announced so they are told once."""
    with _lock:
        data = _state_for(tools)
        fresh = [t for t in _released(tools) if t["id"] not in data["notified"]]
        if fresh:
            today = date.today().isoformat()
            data["notified"].update({t["id"]: today for t in fresh})
            _write(data)
    return fresh


def mark_store_seen(tools: List[Dict]) -> None:
    with _lock:
        data = _state_for(tools)
        data["seen"] = sorted(set(data["seen"]) | {t["id"] for t in _released(tools)})
        _write(data)


def bell_items(tools: List[Dict]) -> List[Dict]:
    """Bell notices for tools announced in the last BELL_DAYS, newest first (announcements.json shape)."""
    with _lock:
        notified = _state_for(tools)["notified"]
    cutoff = (date.today() - timedelta(days=BELL_DAYS)).isoformat()
    recent = [t for t in _released(tools) if notified.get(t["id"], "") >= cutoff and notified.get(t["id"])]
    recent.sort(key=lambda t: notified[t["id"]], reverse=True)
    return [{
        "id": f"local_new_tool_{t['id']}",
        "date": notified[t["id"]],
        "tag": "NEW TOOL",
        "title": f"{t.get('name', t['id'])} is available",
        "description": f"{t.get('description', '')} Download it from Tool Hub whenever you like.".strip(),
        "cta_text": "Open Tool Hub",
        "cta_action": "navigate_hub",
    } for t in recent]
