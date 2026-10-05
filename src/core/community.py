"""Community Feedback, Voting & Modular Tool Management Service for Boltools.

Features:
- ₹0 Serverless Architecture: Fetches community polls from GitHub Raw / Edge API
- Client Anti-Spam Gate: Tracks 1-vote-per-PC in ~/.boltools/poll_state.json
- Direct Tool Request Submission: Saves locally and dispatches to edge webhook
- Smart 2-Tier Tool Lifecycle Management:
  * "Uninstall Tool Only": Frees disk space, preserves user data in ~/.boltools/tools_data/<id>/
  * "Delete Tool & Completely Purge": Erases tool + wipes user presets and history
"""

import os
import json
import urllib.request
import threading
from typing import List, Dict, Optional, Callable


import uuid
from src.core.paths import get_data_path

EDGE_API_BASE = "https://boltools-api.p-pavansiri.workers.dev"
PRIMARY_POLL_ENDPOINT = f"{EDGE_API_BASE}/api/poll"
FALLBACK_POLL_ENDPOINT = "https://raw.githubusercontent.com/Sai-Pavan-Kumar/Boltools/main/poll.json"

DEFAULT_POLL = {
    "poll_id": "poll_drop_2_priority",
    "title": "Community Vote: What should we release in Batch 2?",
    "description": "Vote for the next power tools you want unlocked in Boltools Drop 2.",
    "ends_at": "2026-10-20",
    "options": [
        {"id": "opt_audio_whisper", "label": "Local Whisper AI Speech-to-Text Transcriber (90+ Languages)", "votes": 342},
        {"id": "opt_video_trimmer", "label": "Instant Lossless Video Trimmer (Cut clips in <1 sec)", "votes": 289},
        {"id": "opt_audio_stems", "label": "AI Vocal & Instrumental Stem Separator (Karaoke Maker)", "votes": 412},
        {"id": "opt_design_qr", "label": "Offline Vector QR Code Studio (WiFi, Links, Custom Colors)", "votes": 195},
        {"id": "opt_system_dup", "label": "Deep Duplicate File Hunter (Free up disk space)", "votes": 220}
    ]
}


class CommunityService:
    """Manages community polls, tool requests, and local tool installation states."""

    def __init__(self):
        self.state_dir = os.path.join(os.path.expanduser("~"), ".boltools")
        self.tools_data_dir = os.path.join(self.state_dir, "tools_data")
        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.tools_data_dir, exist_ok=True)

        self.poll_state_file = os.path.join(self.state_dir, "poll_state.json")
        self.requests_state_file = os.path.join(self.state_dir, "requests_state.json")
        self.tool_states_file = os.path.join(self.state_dir, "tool_states.json")
        self.client_id_file = os.path.join(self.state_dir, "client_id.txt")

        self.client_id = self._get_or_create_client_id()
        self.cached_poll: Dict = DEFAULT_POLL.copy()
        self.voted_polls = self._load_voted_polls()
        self.tool_overrides = self._load_tool_overrides()

    def _get_or_create_client_id(self) -> str:
        """Retrieves or creates an anonymous persistent hardware/installation UUID."""
        if os.path.exists(self.client_id_file):
            try:
                with open(self.client_id_file, "r", encoding="utf-8") as f:
                    cid = f.read().strip()
                    if cid:
                        return cid
            except Exception:
                pass
        cid = str(uuid.uuid4())
        try:
            with open(self.client_id_file, "w", encoding="utf-8") as f:
                f.write(cid)
        except Exception:
            pass
        return cid

    # ── Poll & Voting System ──
    def _load_voted_polls(self) -> Dict[str, str]:
        if os.path.exists(self.poll_state_file):
            try:
                with open(self.poll_state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_voted_polls(self):
        try:
            with open(self.poll_state_file, "w", encoding="utf-8") as f:
                json.dump(self.voted_polls, f, indent=2)
        except Exception:
            pass

    def has_voted(self, poll_id: str) -> bool:
        return poll_id in self.voted_polls

    def get_user_vote(self, poll_id: str) -> Optional[str]:
        return self.voted_polls.get(poll_id)

    def fetch_poll(self, on_complete: Optional[Callable[[Dict], None]] = None):
        """Asynchronously fetches active poll with Cloudflare Edge -> GitHub Raw -> Local fallback."""
        def _fetch():
            # First load local poll.json
            local_poll = get_data_path("poll.json")
            if os.path.exists(local_poll):
                try:
                    with open(local_poll, "r", encoding="utf-8") as f:
                        self.cached_poll = json.load(f)
                except Exception:
                    pass

            # 1. Try Primary Cloudflare Edge API
            fetched = False
            for endpoint in [PRIMARY_POLL_ENDPOINT, FALLBACK_POLL_ENDPOINT]:
                try:
                    req = urllib.request.Request(endpoint, headers={"User-Agent": "Boltools-Client/1.0"})
                    with urllib.request.urlopen(req, timeout=3.5) as resp:
                        if resp.status == 200:
                            remote = json.loads(resp.read().decode("utf-8"))
                            if isinstance(remote, dict) and "options" in remote:
                                self.cached_poll = remote
                                fetched = True
                                break
                except Exception:
                    continue

            if on_complete:
                on_complete(self.cached_poll)

        t = threading.Thread(target=_fetch, daemon=True)
        t.start()

    def cast_vote(self, poll_id: str, option_id: str) -> bool:
        """Records vote locally and dispatches to Cloudflare Edge API in background."""
        if self.has_voted(poll_id):
            return False

        # Mark voted locally immediately
        self.voted_polls[poll_id] = option_id
        self._save_voted_polls()

        # Increment in local cache for instant UI feedback
        if self.cached_poll.get("poll_id") == poll_id:
            for opt in self.cached_poll.get("options", []):
                if opt.get("id") == option_id:
                    opt["votes"] = opt.get("votes", 0) + 1
                    break

        # Also update local poll.json if present
        local_poll = get_data_path("poll.json")
        if os.path.exists(local_poll):
            try:
                with open(local_poll, "w", encoding="utf-8") as f:
                    json.dump(self.cached_poll, f, indent=2)
            except Exception:
                pass

        # Dispath to Cloudflare Edge API asynchronously
        def _dispatch_vote():
            try:
                url = f"{EDGE_API_BASE}/api/poll/vote"
                payload = json.dumps({
                    "poll_id": poll_id,
                    "option_id": option_id,
                    "client_id": self.client_id
                }).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "Boltools-Client/1.0"})
                urllib.request.urlopen(req, timeout=4.0)
            except Exception:
                pass

        threading.Thread(target=_dispatch_vote, daemon=True).start()
        return True

    # ── Tool Request System ──
    def submit_tool_request(self, tool_name: str, description: str, platform: str = "Windows 11") -> bool:
        """Stores tool request locally and dispatches to Cloudflare Edge API in background."""
        req_entry = {
            "tool_name": tool_name.strip(),
            "description": description.strip(),
            "platform": platform,
            "timestamp": "2026-10-05"
        }

        # Save to local requests history
        requests_list = []
        if os.path.exists(self.requests_state_file):
            try:
                with open(self.requests_state_file, "r", encoding="utf-8") as f:
                    requests_list = json.load(f)
            except Exception:
                pass

        requests_list.append(req_entry)
        try:
            with open(self.requests_state_file, "w", encoding="utf-8") as f:
                json.dump(requests_list, f, indent=2)
        except Exception:
            pass

        # Dispatch to Cloudflare Edge API
        def _dispatch_request():
            try:
                url = f"{EDGE_API_BASE}/api/request"
                payload = json.dumps({
                    "tool_name": tool_name.strip(),
                    "description": description.strip(),
                    "platform": platform,
                    "client_id": self.client_id
                }).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "Boltools-Client/1.0"})
                urllib.request.urlopen(req, timeout=4.0)
            except Exception:
                pass

        threading.Thread(target=_dispatch_request, daemon=True).start()
        return True

    # ── Smart 2-Tier Tool State Management ──
    def _load_tool_overrides(self) -> Dict[str, str]:
        if os.path.exists(self.tool_states_file):
            try:
                with open(self.tool_states_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_tool_overrides(self):
        try:
            with open(self.tool_states_file, "w", encoding="utf-8") as f:
                json.dump(self.tool_overrides, f, indent=2)
        except Exception:
            pass

    def get_tool_status(self, tool_id: str, default_status: str) -> str:
        """Returns installed/available status taking user overrides into account."""
        return self.tool_overrides.get(tool_id, default_status)

    def install_tool(self, tool_id: str) -> bool:
        """Installs or unlocks tool module."""
        self.tool_overrides[tool_id] = "installed"
        self._save_tool_overrides()
        return True

    def uninstall_tool(self, tool_id: str, purge_data: bool = False) -> bool:
        """Uninstalls tool with 2-tier data persistence handling."""
        self.tool_overrides[tool_id] = "available"
        self._save_tool_overrides()

        # If user selected complete purge, wipe tool data directory
        if purge_data:
            tool_dir = os.path.join(self.tools_data_dir, tool_id)
            if os.path.exists(tool_dir):
                try:
                    import shutil
                    shutil.rmtree(tool_dir)
                except Exception:
                    pass

        return True


# Global Singleton
community_service = CommunityService()
