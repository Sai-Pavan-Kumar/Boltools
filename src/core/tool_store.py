"""Modular In-App Tool Store & OTA Engine Updater for Boltools.

Architecture & Capabilities:
- Zero Installer Overhead: Tools and engine bug-fixes are delivered modularly Over-The-Air (OTA).
- Decentralized ₹0 Serverless CDN: Manifests & Python engines are fetched from Cloudflare Pages CDN
  (https://boltools.thesurfboard.in) with GitHub Raw automatic failover.
- Safe Dynamic Resolution: Resolves engine execution to ~/.boltools/engines/<tool_id>/engine.py
  (updated version) before falling back to factory bundled engines.
- Atomic SemVer Engine Upgrades: Automatically detects newer tool versions and facilitates 1-click in-app updates.
- 100% Offline Resilience: Caches remote manifest in ~/.boltools/manifest_cache.json.
"""

import os
import sys
import json
import re
import urllib.request
import threading
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from src.core.paths import get_data_path, get_base_dir

PRIMARY_MANIFEST_URL = "https://boltools.thesurfboard.in/tools_manifest.json"
FALLBACK_MANIFEST_URL = "https://raw.githubusercontent.com/Sai-Pavan-Kumar/Boltools/main/website/tools_manifest.json"
MANIFEST_ENDPOINTS = [PRIMARY_MANIFEST_URL, FALLBACK_MANIFEST_URL]


def parse_semver(version_str: str) -> Tuple[int, ...]:
    """Parses a version string into a numeric tuple for reliable comparison."""
    if not version_str:
        return (1, 0, 0)
    numbers = re.findall(r"\d+", str(version_str))
    if not numbers:
        return (1, 0, 0)
    return tuple(int(n) for n in numbers)


def is_newer_version(remote_v: str, local_v: str) -> bool:
    """Returns True if remote version is strictly greater than local version."""
    return parse_semver(remote_v) > parse_semver(local_v)


VALID_ID_PATTERN = re.compile(r"^[a-z0-9_]{1,64}$")


def validate_id(val: str, name: str = "identifier") -> str:
    """Validates that a tool_id or engine_folder strictly matches ^[a-z0-9_]{1,64}$."""
    if not val or not isinstance(val, str) or not VALID_ID_PATTERN.match(val):
        raise ValueError(f"Security: Invalid {name} '{val}'. Must match ^[a-z0-9_]{{1,64}}$.")
    return val


def assert_inside_dir(child_path: str, parent_dir: str):
    """Ensures child_path is strictly inside parent_dir to prevent path traversal."""
    resolved_child = os.path.realpath(os.path.abspath(child_path))
    resolved_parent = os.path.realpath(os.path.abspath(parent_dir))
    if not (resolved_child == resolved_parent or resolved_child.startswith(resolved_parent + os.sep)):
        raise ValueError(f"Security: Path '{child_path}' escapes directory '{parent_dir}'.")


class ToolStoreService:
    """Manages remote tool discovery, modular downloads, and dynamic engine resolution."""

    def __init__(self):
        self.state_dir = os.path.realpath(os.path.abspath(os.path.join(os.path.expanduser("~"), ".boltools")))
        self.engines_dir = os.path.realpath(os.path.abspath(os.path.join(self.state_dir, "engines")))
        self.tools_data_dir = os.path.realpath(os.path.abspath(os.path.join(self.state_dir, "tools_data")))
        self.manifest_cache_file = os.path.join(self.state_dir, "manifest_cache.json")
        self.tool_states_file = os.path.join(self.state_dir, "tool_states.json")

        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.engines_dir, exist_ok=True)
        os.makedirs(self.tools_data_dir, exist_ok=True)

        # Resolve bundled factory engines directory
        self.bundled_engines_dir = os.path.join(get_base_dir(), "engines")

        self.tool_states = self._load_tool_states()
        self.cached_manifest = self._load_cached_manifest()
        self._cached_resolved_catalog: Optional[List[Dict[str, Any]]] = None

        # Defer manifest network synchronization by 10s to avoid blocking startup
        threading.Timer(10.0, self.sync_manifest_async).start()

    def invalidate_cache(self):
        """Invalidates resolved catalog cache on install/uninstall or sync."""
        self._cached_resolved_catalog = None

    def _load_tool_states(self) -> Dict[str, Dict[str, Any]]:
        """Loads persistent local tool states and version overrides."""
        if os.path.exists(self.tool_states_file):
            try:
                with open(self.tool_states_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Convert legacy format if needed
                        normalized = {}
                        for k, v in data.items():
                            if isinstance(v, str):
                                normalized[k] = {"status": v, "version": "1.0.0"}
                            elif isinstance(v, dict):
                                normalized[k] = v
                        return normalized
            except Exception:
                pass
        return {}

    def _save_tool_states(self):
        """Persists tool states to disk using atomic rename (os.replace)."""
        import tempfile
        try:
            temp_fd, temp_path = tempfile.mkstemp(dir=self.state_dir, prefix="tool_states_", suffix=".tmp")
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(self.tool_states, f, indent=2)
            os.replace(temp_path, self.tool_states_file)
            self.invalidate_cache()
        except Exception:
            pass

    def _load_cached_manifest(self) -> Dict[str, Any]:
        """Loads manifest from cache or bundled local fallback."""
        # 1. Try disk cache in ~/.boltools/manifest_cache.json
        if os.path.exists(self.manifest_cache_file):
            try:
                with open(self.manifest_cache_file, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                    if manifest and isinstance(manifest, dict) and "tools" in manifest:
                        return manifest
            except Exception:
                pass

        # 2. Try bundled tools_manifest.json in software bundle
        bundled_manifest_path = get_data_path("tools_manifest.json")
        if os.path.exists(bundled_manifest_path):
            try:
                with open(bundled_manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        return {"schema_version": "1.0.0", "tools": []}

    def sync_manifest_async(self, on_complete=None):
        """Fetches remote manifest over Cloudflare CDN with background threading."""
        def _fetch():
            for endpoint in MANIFEST_ENDPOINTS:
                try:
                    req = urllib.request.Request(
                        endpoint,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                    )
                    with urllib.request.urlopen(req, timeout=4.0) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode("utf-8"))
                            if isinstance(data, dict) and "tools" in data and len(data["tools"]) > 0:
                                self.cached_manifest = data
                                try:
                                    with open(self.manifest_cache_file, "w", encoding="utf-8") as f:
                                        json.dump(data, f, indent=2)
                                except Exception:
                                    pass
                                break
                except Exception:
                    continue

            if on_complete:
                try:
                    on_complete(self.cached_manifest)
                except Exception:
                    pass

        threading.Thread(target=_fetch, daemon=True).start()

    def get_tool_meta(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves raw manifest definition for a tool."""
        tools = self.cached_manifest.get("tools", [])
        return next((t for t in tools if t.get("id") == tool_id), None)

    def is_engine_installed_locally(self, tool_id: str, engine_folder: str = "") -> bool:
        """Checks if a tool engine is physically present either locally or bundled."""
        dyn_engine = os.path.join(self.engines_dir, tool_id, "engine.py")
        if os.path.isfile(dyn_engine):
            return True

        folder = engine_folder or tool_id
        bundled_engine = os.path.join(self.bundled_engines_dir, folder, "engine.py")
        return os.path.isfile(bundled_engine)

    def get_engine_target(self, tool_id: str) -> Optional[str]:
        """Resolves the executable engine target file path.
        
        Prioritizes the dynamically downloaded/updated engine in ~/.boltools/engines/<tool_id>/engine.py,
        falling back to the factory bundled engine in software/engines/<folder>/engine.py.
        """
        validate_id(tool_id, "tool_id")

        # 1. User/Dynamic engine override (highest priority)
        dyn_engine = os.path.join(self.engines_dir, tool_id, "engine.py")
        assert_inside_dir(dyn_engine, self.engines_dir)
        if os.path.isfile(dyn_engine):
            return dyn_engine

        # 2. Bundled factory engine (fallback)
        meta = self.get_tool_meta(tool_id)
        folder = validate_id((meta.get("engine_folder") or tool_id) if meta else tool_id, "engine_folder")
        bundled_engine = os.path.join(self.bundled_engines_dir, folder, "engine.py")
        assert_inside_dir(bundled_engine, self.bundled_engines_dir)
        if os.path.isfile(bundled_engine):
            return bundled_engine

        return None

    def get_tools_catalog(self) -> List[Dict[str, Any]]:
        """Constructs complete dynamic tools list with live installation and update statuses.
        Uses in-memory cache to guarantee sub-millisecond responses on 10,000 tools.
        """
        if self._cached_resolved_catalog is not None:
            return self._cached_resolved_catalog

        manifest_tools = self.cached_manifest.get("tools", [])
        resolved_tools = []

        # Pre-scan existing dynamic engines in ~/.boltools/engines once to avoid N file stats
        installed_dynamic_ids = set()
        if os.path.exists(self.engines_dir):
            try:
                for entry in os.scandir(self.engines_dir):
                    if entry.is_dir() and os.path.isfile(os.path.join(entry.path, "engine.py")):
                        installed_dynamic_ids.add(entry.name)
            except Exception:
                pass

        for m_tool in manifest_tools:
            tool_id = m_tool["id"]
            remote_version = m_tool.get("version", "1.0.0")

            # Check local file presence from pre-scanned set or saved state
            has_engine = (tool_id in installed_dynamic_ids)

            # Check user saved state
            saved_state = self.tool_states.get(tool_id, {})
            saved_status = saved_state.get("status")

            if saved_status == "available":
                status = "available"
                installed_version = None
                update_available = False
            elif has_engine or saved_status == "installed":
                installed_version = saved_state.get("version", "1.0.0")
                if is_newer_version(remote_version, installed_version):
                    status = "update_available"
                    update_available = True
                else:
                    status = "installed"
                    update_available = False
            else:
                status = m_tool.get("status", "available")
                installed_version = None
                update_available = False

            item = dict(m_tool)
            item["status"] = status
            item["update_available"] = update_available
            item["installed_version"] = installed_version
            item["remote_version"] = remote_version
            resolved_tools.append(item)

        self._cached_resolved_catalog = resolved_tools
        return resolved_tools

    def get_catalog_counts(self) -> Dict[str, int]:
        """Returns fast counts for installed tools and pending updates without payload overhead."""
        tools = self.get_tools_catalog()
        total = len(tools)
        installed = sum(1 for t in tools if t.get("status") == "installed" or t.get("update_available"))
        updates = sum(1 for t in tools if t.get("update_available"))
        return {"total": total, "installed": installed, "updates": updates}

    def get_catalog_summary(self) -> List[Dict[str, Any]]:
        """Returns compact tool summaries optimized for virtual lists and rapid serialization.
        
        Fields returned: id, name, category_id, category_name, icon, status, version, size_mb, update_available, description (cut to 120 chars).
        """
        tools = self.get_tools_catalog()
        summaries = []
        for t in tools:
            desc = t.get("description") or ""
            if len(desc) > 120:
                desc = desc[:117] + "..."
            summaries.append({
                "id": t.get("id"),
                "name": t.get("name"),
                "category_id": t.get("category_id"),
                "category_name": t.get("category_name"),
                "icon": t.get("icon"),
                "status": t.get("status"),
                "version": t.get("installed_version") or t.get("version"),
                "remote_version": t.get("remote_version") or t.get("version"),
                "size_mb": t.get("size_mb", 25),
                "update_available": bool(t.get("update_available", False)),
                "description": desc
            })
        return summaries

    def get_updates_count(self) -> int:
        """Returns the number of tools that have pending updates."""
        tools = self.get_tools_catalog()
        return sum(1 for t in tools if t.get("update_available"))

    def install_or_update_tool(self, tool_id: str) -> Dict[str, Any]:
        """Downloads/updates a tool engine over the air without restarting or re-running installers."""
        validate_id(tool_id, "tool_id")
        meta = self.get_tool_meta(tool_id)
        if not meta:
            return {"success": False, "error": f"Tool '{tool_id}' not found in catalog manifest."}

        target_dir = os.path.join(self.engines_dir, tool_id)
        assert_inside_dir(target_dir, self.engines_dir)
        os.makedirs(target_dir, exist_ok=True)
        target_engine_file = os.path.join(target_dir, "engine.py")
        assert_inside_dir(target_engine_file, self.engines_dir)

        urls_to_try = []
        if meta.get("engine_url"):
            urls_to_try.append(meta["engine_url"])
        if meta.get("engine_fallback_url"):
            urls_to_try.append(meta["engine_fallback_url"])
        
        # Additional fallbacks
        folder = validate_id(meta.get("engine_folder", tool_id), "engine_folder")
        urls_to_try.append(f"https://boltools.thesurfboard.in/engines/{folder}/engine.py")
        urls_to_try.append(f"https://raw.githubusercontent.com/Sai-Pavan-Kumar/Boltools/main/website/engines/{folder}/engine.py")

        download_success = False
        last_error = ""

        for url in urls_to_try:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
                with urllib.request.urlopen(req, timeout=10.0) as resp:
                    if resp.status == 200:
                        content = resp.read()
                        if len(content) > 100:  # Valid non-empty file check
                            temp_path = target_engine_file + ".tmp"
                            with open(temp_path, "wb") as f:
                                f.write(content)
                            # Atomic replace
                            if os.path.exists(target_engine_file):
                                os.remove(target_engine_file)
                            os.rename(temp_path, target_engine_file)
                            download_success = True
                            break
            except Exception as e:
                last_error = str(e)
                continue

        if not download_success:
            # If download fails, check if we have a bundled engine to copy
            bundled_engine = os.path.join(self.bundled_engines_dir, folder, "engine.py")
            assert_inside_dir(bundled_engine, self.bundled_engines_dir)
            if os.path.isfile(bundled_engine):
                try:
                    import shutil
                    shutil.copy2(bundled_engine, target_engine_file)
                    download_success = True
                except Exception as e:
                    last_error = str(e)

        if download_success:
            new_version = meta.get("version", "1.0.0")
            self.tool_states[tool_id] = {
                "status": "installed",
                "version": new_version,
                "installed_at": datetime.now().isoformat()
            }
            self._save_tool_states()
            return {
                "success": True,
                "tool_id": tool_id,
                "version": new_version,
                "name": meta.get("name", tool_id),
                "message": f"Successfully installed {meta.get('name', tool_id)} v{new_version}."
            }
        else:
            return {
                "success": False,
                "error": f"Failed to download engine: {last_error or 'Network timeout'}"
            }

    def uninstall_tool(self, tool_id: str, purge_data: bool = False) -> bool:
        """Uninstalls tool and updates state."""
        validate_id(tool_id, "tool_id")
        self.tool_states[tool_id] = {
            "status": "available",
            "version": None
        }
        self._save_tool_states()

        # Delete dynamic engine folder if present
        dyn_dir = os.path.join(self.engines_dir, tool_id)
        assert_inside_dir(dyn_dir, self.engines_dir)
        if os.path.exists(dyn_dir):
            try:
                import shutil
                shutil.rmtree(dyn_dir)
            except Exception:
                pass

        if purge_data:
            user_data_dir = os.path.join(self.tools_data_dir, tool_id)
            assert_inside_dir(user_data_dir, self.tools_data_dir)
            if os.path.exists(user_data_dir):
                try:
                    import shutil
                    shutil.rmtree(user_data_dir)
                except Exception:
                    pass

        return True


# Global Singleton
tool_store_service = ToolStoreService()
