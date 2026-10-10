"""Product Announcements and Remote Marketing Dispatch Service for Boltools.

Features:
- ₹0 Serverless Architecture: Fetches static announcements JSON from GitHub Raw / CDN
- Offline & Failure Safe: 3-second network timeout, silent fallback, zero UI freezing
- Local Read-State Tracking: Persists read IDs in user profile directory
"""

import os
import json
import urllib.request
import threading
from typing import List, Dict, Optional, Callable


DEFAULT_ANNOUNCEMENTS = []

# Remote endpoints pointing to announcements file (Cloudflare CDN primary, GitHub fallback)
ANNOUNCEMENT_ENDPOINTS = [
    "https://boltools.thesurfboard.in/announcements.json",
    "https://raw.githubusercontent.com/Sai-Pavan-Kumar/Boltools/main/announcements.json"
]


class AnnouncementService:
    """Manages remote announcement fetching and local unread badges."""

    def __init__(self):
        self.state_dir = os.path.join(os.path.expanduser("~"), ".boltools")
        os.makedirs(self.state_dir, exist_ok=True)
        self.state_file = os.path.join(self.state_dir, "announcements_state.json")
        
        self.read_ids = self._load_read_ids()
        self.cached_announcements: List[Dict] = self._load_initial_announcements()

        # Kick off background update fetch immediately upon startup
        self.fetch_async()

    def _load_initial_announcements(self) -> List[Dict]:
        """Loads bundled announcements.json as guaranteed instant local fallback."""
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "announcements.json"),
            os.path.join(os.getcwd(), "announcements.json"),
        ]
        for p in possible_paths:
            if os.path.isfile(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        items = json.load(f)
                        if isinstance(items, list) and len(items) > 0:
                            return items
                except Exception:
                    pass
        return DEFAULT_ANNOUNCEMENTS.copy()

    def _load_read_ids(self) -> set:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data.get("read_ids", []))
            except Exception:
                return set()
        return set()

    def _save_read_ids(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump({"read_ids": list(self.read_ids)}, f, indent=2)
        except Exception:
            pass

    def get_unread_count(self) -> int:
        """Returns the count of unread announcements."""
        unread = [a for a in self.cached_announcements if a.get("id") not in self.read_ids]
        return len(unread)

    def mark_all_read(self):
        """Marks all cached announcements as read and saves state."""
        for a in self.cached_announcements:
            aid = a.get("id")
            if aid:
                self.read_ids.add(aid)
        self._save_read_ids()

    def fetch_async(self, on_complete: Optional[Callable[[int], None]] = None):
        """Fetches remote announcements on a background worker thread."""
        def _fetch():
            unread_count = 0
            for endpoint in ANNOUNCEMENT_ENDPOINTS:
                try:
                    req = urllib.request.Request(
                        endpoint,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                    )
                    with urllib.request.urlopen(req, timeout=4.0) as response:
                        if response.status == 200:
                            raw = response.read().decode("utf-8")
                            items = json.loads(raw)
                            if isinstance(items, list) and len(items) > 0:
                                self.cached_announcements = items
                                break
                except Exception:
                    continue

            unread_count = self.get_unread_count()
            if on_complete:
                on_complete(unread_count)

        thread = threading.Thread(target=_fetch, daemon=True)
        thread.start()


# Global singleton instance
announcement_service = AnnouncementService()
