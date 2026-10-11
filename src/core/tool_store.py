"""Modular In-App Tool Store & OTA Engine Updater for Boltools.

Architecture & Capabilities:
- Zero Installer Overhead: Tools and engine bug-fixes are delivered modularly Over-The-Air (OTA).
- Decentralized ₹0 Serverless CDN: Manifests & Python/EXE tool packs are fetched from Cloudflare Pages CDN
  (https://boltools.thesurfboard.in) with GitHub Raw automatic failover.
- Tool Pack v1 Architecture:
  * Pack format: <tool_id>-<version>.bolpack (standard ZIP)
  * Manifest: pack.json with id, name, version, min_app_version, runtime, entry, and files hash list.
  * Pack.json is excluded from its own files hash list.
  * Strict extraction security:
    - Zip-slip guard: reject "..", absolute paths, drive letters, backslashes, ":", Windows reserved names.
    - Symlink detection: checks ZipInfo mode bits in external_attr (0o120000).
    - Zip-bomb defense: count real bytes streamed during extraction (max 500 MB global ceiling + manifest size).
    - Limit file count (max 1000 files) and detect case-insensitive duplicates.
  * Atomic directory structure:
    ~/.boltools/engines/<tool_id>/
      ├── current.json (atomic pointer to active version: {"version": "1.0.0", "entry": "engine.py", "runtime": "python"})
      ├── v1.0.0/
      │    ├── pack.json
      │    └── engine.py
      └── v1.0.1/
  * Two-version retention: keeps current and previous version for instant rollback.
  * Staging: extracts to .staging-<token>, verifies every file SHA256, renames to v<version>/, then atomically writes current.json.
  * Leftover .staging-* wiped on startup. Single install lock per tool.
"""

import os
import sys
import json
import re
import io
import zipfile
import urllib.request
import threading
import hashlib
import uuid
import shutil
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime

from src.core.paths import get_data_path, get_base_dir
from src._build import IS_RELEASE, BUILD_MIN_SEQUENCE, APP_VERSION, EMBEDDED_PUBLIC_KEYS

try:
    import nacl.signing
    import nacl.exceptions
    HAS_PYNACL = True
except ImportError:
    HAS_PYNACL = False

PRIMARY_MANIFEST_URL = "https://boltools.thesurfboard.in/tools_manifest.json"
PRIMARY_SIG_URL = "https://boltools.thesurfboard.in/tools_manifest.sig"
FALLBACK_MANIFEST_URL = "https://raw.githubusercontent.com/Sai-Pavan-Kumar/Boltools/main/website/tools_manifest.json"
FALLBACK_SIG_URL = "https://raw.githubusercontent.com/Sai-Pavan-Kumar/Boltools/main/website/tools_manifest.sig"
MANIFEST_ENDPOINTS = [
    (PRIMARY_MANIFEST_URL, PRIMARY_SIG_URL),
    (FALLBACK_MANIFEST_URL, FALLBACK_SIG_URL)
]

# Security Limits
MAX_GLOBAL_PACK_SIZE = 150 * 1024 * 1024   # 150 MB max download ceiling
MAX_GLOBAL_EXTRACT_SIZE = 500 * 1024 * 1024 # 500 MB max extracted byte ceiling (zip bomb guard)
MAX_PACK_FILE_COUNT = 1000                 # Max 1000 files per pack

# Windows Reserved Device Names
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}


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
    """Manages remote tool discovery, modular downloads, zip verification, and atomic versioning."""

    def __init__(self):
        self.state_dir = os.path.realpath(os.path.abspath(os.path.join(os.path.expanduser("~"), ".boltools")))
        self.engines_dir = os.path.realpath(os.path.abspath(os.path.join(self.state_dir, "engines")))
        self.tools_data_dir = os.path.realpath(os.path.abspath(os.path.join(self.state_dir, "tools_data")))
        self.manifest_cache_file = os.path.join(self.state_dir, "manifest_cache.json")
        self.tool_states_file = os.path.join(self.state_dir, "tool_states.json")

        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.engines_dir, exist_ok=True)
        os.makedirs(self.tools_data_dir, exist_ok=True)

        # Cleanup leftover .staging-* directories from interrupted installs on startup
        self._cleanup_leftover_staging()

        # Resolve bundled factory engines directory
        self.bundled_engines_dir = os.path.join(get_base_dir(), "engines")

        self.tool_states = self._load_tool_states()
        self.cached_manifest = self._load_cached_manifest()
        self._cached_resolved_catalog: Optional[List[Dict[str, Any]]] = None

        # Lock dictionary for synchronizing concurrent installs per tool
        self._tool_locks: Dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()

        # Defer manifest network synchronization by 10s to avoid blocking startup
        threading.Timer(10.0, self.sync_manifest_async).start()

    def _get_tool_lock(self, tool_id: str) -> threading.Lock:
        """Retrieves or creates a thread lock for a given tool_id."""
        with self._global_lock:
            if tool_id not in self._tool_locks:
                self._tool_locks[tool_id] = threading.Lock()
            return self._tool_locks[tool_id]

    def _cleanup_leftover_staging(self):
        """Scans engine directories and removes any lingering .staging-* folders."""
        try:
            if os.path.exists(self.engines_dir):
                for tool_name in os.listdir(self.engines_dir):
                    t_dir = os.path.join(self.engines_dir, tool_name)
                    if os.path.isdir(t_dir):
                        for sub in os.listdir(t_dir):
                            if sub.startswith(".staging-"):
                                staging_path = os.path.join(t_dir, sub)
                                try:
                                    shutil.rmtree(staging_path)
                                except Exception:
                                    pass
        except Exception:
            pass

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
        if os.path.exists(self.manifest_cache_file):
            try:
                with open(self.manifest_cache_file, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                    if manifest and isinstance(manifest, dict) and "tools" in manifest:
                        return manifest
            except Exception:
                pass

        bundled_manifest_path = get_data_path("tools_manifest.json")
        if os.path.exists(bundled_manifest_path):
            try:
                with open(bundled_manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        return {"schema_version": "1.0.0", "tools": []}

    def verify_manifest_signature(self, manifest_bytes: bytes, sig_bytes: bytes, key_id: str = "key_1") -> bool:
        """Verifies Ed25519 signature against exact raw manifest bytes BEFORE parsing JSON."""
        # Development bypass: only allowed when NOT in a release build
        if not IS_RELEASE and os.environ.get("BOLTOOLS_DEV") == "1":
            return True

        if not HAS_PYNACL:
            return False

        pub_key_hex = EMBEDDED_PUBLIC_KEYS.get(key_id) or EMBEDDED_PUBLIC_KEYS.get("key_1")
        if not pub_key_hex or len(pub_key_hex) != 64:
            return False

        try:
            pub_raw = bytes.fromhex(pub_key_hex)
            verify_key = nacl.signing.VerifyKey(pub_raw)
            verify_key.verify(manifest_bytes, sig_bytes)
            return True
        except Exception:
            return False

    def sync_manifest_async(self, on_complete=None):
        """Fetches remote manifest and companion .sig over CDN with Ed25519 verification."""
        def _fetch():
            last_accepted_seq = self.cached_manifest.get("sequence", BUILD_MIN_SEQUENCE) if isinstance(self.cached_manifest, dict) else BUILD_MIN_SEQUENCE

            for manifest_url, sig_url in MANIFEST_ENDPOINTS:
                try:
                    # 1. Fetch raw manifest bytes
                    m_req = urllib.request.Request(
                        manifest_url,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                    )
                    with urllib.request.urlopen(m_req, timeout=4.0) as m_resp:
                        if m_resp.status != 200:
                            continue
                        manifest_bytes = m_resp.read()

                    # 2. Fetch signature bytes
                    sig_bytes = b""
                    try:
                        s_req = urllib.request.Request(
                            sig_url,
                            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                        )
                        with urllib.request.urlopen(s_req, timeout=4.0) as s_resp:
                            if s_resp.status == 200:
                                sig_bytes = s_resp.read()
                    except Exception:
                        pass

                    # 3. Verify signature BEFORE parsing JSON
                    is_dev_bypass = (not IS_RELEASE) and (os.environ.get("BOLTOOLS_DEV") == "1")
                    if not is_dev_bypass:
                        if not sig_bytes:
                            # Signature missing: reject and retain cached manifest
                            continue

                        # Check signature with key_id
                        if not self.verify_manifest_signature(manifest_bytes, sig_bytes):
                            continue

                    # 4. Safe parsing after cryptographic verification
                    data = json.loads(manifest_bytes.decode("utf-8"))
                    if not isinstance(data, dict) or "tools" not in data:
                        continue

                    # 5. Anti-rollback sequence guard
                    remote_seq = data.get("sequence", 0)
                    if remote_seq < last_accepted_seq:
                        # Replay attack: older sequence than previously accepted
                        continue

                    # Accepted new verified manifest
                    self.cached_manifest = data
                    self.invalidate_cache()
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

    # ── Active Version Pointer Resolution (current.json) ──────────────────────
    def get_active_pointer(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Reads current.json pointer for a tool to find active version and entry target."""
        validate_id(tool_id, "tool_id")
        pointer_file = os.path.join(self.engines_dir, tool_id, "current.json")
        if os.path.isfile(pointer_file):
            try:
                with open(pointer_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "version" in data and "entry" in data:
                        return data
            except Exception:
                pass
        return None

    def _set_active_pointer(self, tool_id: str, version: str, entry: str, runtime: str = "python") -> bool:
        """Atomically writes current.json pointer using os.replace."""
        validate_id(tool_id, "tool_id")
        tool_dir = os.path.join(self.engines_dir, tool_id)
        os.makedirs(tool_dir, exist_ok=True)
        pointer_file = os.path.join(tool_dir, "current.json")
        temp_pointer = os.path.join(tool_dir, f".current_{uuid.uuid4().hex[:8]}.tmp")

        payload = {
            "version": version,
            "entry": entry,
            "runtime": runtime,
            "updated_at": datetime.now().isoformat()
        }
        try:
            with open(temp_pointer, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            os.replace(temp_pointer, pointer_file)
            return True
        except Exception:
            if os.path.exists(temp_pointer):
                try:
                    os.remove(temp_pointer)
                except Exception:
                    pass
            return False

    def is_engine_installed_locally(self, tool_id: str, engine_folder: str = "") -> bool:
        """Checks if a tool engine is physically present either locally or bundled."""
        target = self.get_engine_target(tool_id)
        return bool(target and os.path.isfile(target))

    def get_engine_target(self, tool_id: str) -> Optional[str]:
        """Resolves the executable engine target file path.
        
        Priority:
        1. Dynamic version folder resolved via ~/.boltools/engines/<tool_id>/current.json
        2. Legacy flat ~/.boltools/engines/<tool_id>/engine.py
        3. Factory bundled engine in software/engines/<folder>/engine.py
        """
        validate_id(tool_id, "tool_id")

        # 1. Versioned current.json resolution
        pointer = self.get_active_pointer(tool_id)
        if pointer:
            v_folder = f"v{pointer['version']}"
            entry_file = pointer.get("entry", "engine.py")
            target_path = os.path.join(self.engines_dir, tool_id, v_folder, entry_file)
            assert_inside_dir(target_path, self.engines_dir)
            if os.path.isfile(target_path):
                return target_path

        # 2. User/Dynamic legacy engine override (fallback)
        dyn_engine = os.path.join(self.engines_dir, tool_id, "engine.py")
        if os.path.isfile(dyn_engine):
            assert_inside_dir(dyn_engine, self.engines_dir)
            return dyn_engine

        # 3. Bundled factory engine (fallback)
        meta = self.get_tool_meta(tool_id)
        folder = validate_id((meta.get("engine_folder") or tool_id) if meta else tool_id, "engine_folder")
        bundled_engine = os.path.join(self.bundled_engines_dir, folder, "engine.py")
        if os.path.isfile(bundled_engine):
            assert_inside_dir(bundled_engine, self.bundled_engines_dir)
            return bundled_engine

        return None

    def get_tools_catalog(self) -> List[Dict[str, Any]]:
        """Constructs complete dynamic tools list with live installation and update statuses."""
        if self._cached_resolved_catalog is not None:
            return self._cached_resolved_catalog

        manifest_tools = self.cached_manifest.get("tools", [])
        resolved_tools = []

        # Pre-scan installed tool ids
        installed_ids = set()
        if os.path.exists(self.engines_dir):
            try:
                for entry in os.scandir(self.engines_dir):
                    if entry.is_dir():
                        pointer_file = os.path.join(entry.path, "current.json")
                        legacy_file = os.path.join(entry.path, "engine.py")
                        if os.path.isfile(pointer_file) or os.path.isfile(legacy_file):
                            installed_ids.add(entry.name)
            except Exception:
                pass

        for m_tool in manifest_tools:
            tool_id = m_tool["id"]
            # Exclude engines/hello_tool from user catalog unless BOLTOOLS_DEV is set in a dev build
            if tool_id == "hello_tool":
                is_dev = (not IS_RELEASE) and (os.environ.get("BOLTOOLS_DEV") == "1")
                if not is_dev:
                    continue

            remote_version = m_tool.get("version", "1.0.0")

            has_engine = (tool_id in installed_ids)
            saved_state = self.tool_states.get(tool_id, {})
            saved_status = saved_state.get("status")

            # Check version from current.json if available
            pointer = self.get_active_pointer(tool_id)
            active_version = pointer.get("version") if pointer else saved_state.get("version", "1.0.0")

            if saved_status == "available":
                status = "available"
                installed_version = None
                update_available = False
            elif has_engine or saved_status == "installed":
                installed_version = active_version
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
        """Returns compact tool summaries optimized for virtual lists and rapid serialization."""
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

    # ── Safe ZIP Extraction & Verification Engine ─────────────────────────────
    @staticmethod
    def _is_symlink(zip_info: zipfile.ZipInfo) -> bool:
        """Detects if a ZipInfo entry is a symlink via UNIX mode bits in external_attr."""
        mode = zip_info.external_attr >> 16
        # S_IFLNK mode bit is 0o120000 (0xA000)
        return (mode & 0o170000) == 0o120000

    @classmethod
    def validate_zip_entry_path(cls, filename: str):
        """Strictly validates entry paths against zip-slip, drive letters, reserved names, and colons."""
        if not filename or filename.startswith("/") or filename.startswith("\\"):
            raise ValueError(f"Zip security violation: Entry starts with root/slash: {filename}")

        if "\\" in filename:
            raise ValueError(f"Zip security violation: Backslash in entry path: {filename}")

        if ":" in filename:
            raise ValueError(f"Zip security violation: Colon/drive letter in path: {filename}")

        parts = filename.split("/")
        for part in parts:
            if not part or part == ".":
                continue
            if part == "..":
                raise ValueError(f"Zip security violation: Directory traversal '..' in entry: {filename}")

            base = part.split(".")[0].upper()
            if base in WINDOWS_RESERVED_NAMES:
                raise ValueError(f"Zip security violation: Windows reserved device name '{part}' in path: {filename}")

    def safe_extract_pack(self, zip_bytes: bytes, target_dir: str, max_extract_size: int = MAX_GLOBAL_EXTRACT_SIZE) -> Dict[str, Any]:
        """Extracts tool pack with zip-slip guard, symlink rejection, and byte-counted zip-bomb guard."""
        os.makedirs(target_dir, exist_ok=True)
        assert_inside_dir(target_dir, self.engines_dir)

        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                infolist = zf.infolist()
                if len(infolist) > MAX_PACK_FILE_COUNT:
                    raise ValueError(f"Zip security violation: Tool pack contains {len(infolist)} files (max {MAX_PACK_FILE_COUNT}).")

                # Detect case-insensitive duplicates
                seen_lower: Set[str] = set()
                total_extracted_bytes = 0

                for info in infolist:
                    norm_name = info.filename.rstrip("/")
                    if not norm_name:
                        continue

                    lower_name = norm_name.lower()
                    if lower_name in seen_lower:
                        raise ValueError(f"Zip security violation: Case-insensitive duplicate entry '{norm_name}'.")
                    seen_lower.add(lower_name)

                    # Validate path traversal and forbidden characters
                    self.validate_zip_entry_path(info.filename)

                    # Symlink detection via mode bits
                    if self._is_symlink(info):
                        raise ValueError(f"Zip security violation: Symlinks are forbidden in tool packs: {info.filename}")

                # Extract files with byte-counting streaming guard
                for info in infolist:
                    if info.is_dir():
                        dir_path = os.path.join(target_dir, info.filename)
                        assert_inside_dir(dir_path, target_dir)
                        os.makedirs(dir_path, exist_ok=True)
                        continue

                    dest_file = os.path.join(target_dir, info.filename)
                    assert_inside_dir(dest_file, target_dir)
                    os.makedirs(os.path.dirname(dest_file), exist_ok=True)

                    # Stream extract and count real bytes
                    with zf.open(info) as src, open(dest_file, "wb") as dst:
                        while True:
                            chunk = src.read(64 * 1024)
                            if not chunk:
                                break
                            total_extracted_bytes += len(chunk)
                            if total_extracted_bytes > max_extract_size:
                                raise ValueError(f"Zip-bomb defense triggered: Extracted bytes exceeded limit ({max_extract_size} bytes).")
                            dst.write(chunk)

            # Read and parse pack.json
            pack_json_path = os.path.join(target_dir, "pack.json")
            if not os.path.isfile(pack_json_path):
                raise ValueError("Tool pack missing mandatory pack.json manifest.")

            with open(pack_json_path, "r", encoding="utf-8") as f:
                pack_manifest = json.load(f)

            # Verify every file listed in pack.json
            files_map = pack_manifest.get("files", {})
            for rel_path, expected_hash in files_map.items():
                self.validate_zip_entry_path(rel_path)
                f_path = os.path.join(target_dir, rel_path)
                assert_inside_dir(f_path, target_dir)
                if not os.path.isfile(f_path):
                    raise ValueError(f"Tool pack integrity error: Missing file '{rel_path}' listed in pack.json.")

                with open(f_path, "rb") as ef:
                    actual_hash = hashlib.sha256(ef.read()).hexdigest().lower()
                if actual_hash != expected_hash.lower().strip():
                    raise ValueError(f"File integrity mismatch for '{rel_path}': expected {expected_hash}, got {actual_hash}")

            return {
                "success": True,
                "pack_manifest": pack_manifest,
                "total_bytes": total_extracted_bytes
            }

        except Exception as e:
            # Wipe partially extracted contents on failure
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir, ignore_errors=True)
            raise e

    # ── Tool Installation & Rollback Lifecycle ────────────────────────────────
    def install_or_update_tool(self, tool_id: str) -> Dict[str, Any]:
        """Downloads, verifies, unpacks, and atomically activates a tool pack."""
        validate_id(tool_id, "tool_id")
        meta = self.get_tool_meta(tool_id)
        if not meta:
            return {"success": False, "error": f"Tool '{tool_id}' not found in catalog manifest."}

        # Single install lock per tool
        lock = self._get_tool_lock(tool_id)
        if not lock.acquire(blocking=False):
            return {"success": False, "error": f"Installation already in progress for '{tool_id}'."}

        try:
            return self._perform_install_or_update(tool_id, meta)
        finally:
            lock.release()

    def _perform_install_or_update(self, tool_id: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        expected_sha256 = meta.get("sha256")
        if not expected_sha256 and os.environ.get("BOLTOOLS_DEV") != "1":
            return {
                "success": False,
                "error": f"Refusing to install tool '{tool_id}': Missing sha256 checksum in manifest entry. Set BOLTOOLS_DEV=1 to bypass."
            }

        # Validate min_app_version requirement
        min_app_v = meta.get("min_app_version")
        if min_app_v:
            from packaging.version import parse as parse_version
            try:
                if parse_version(APP_VERSION) < parse_version(min_app_v):
                    return {
                        "success": False,
                        "error": f"Tool '{tool_id}' requires Boltools app version {min_app_v} or higher (current: {APP_VERSION}). Please update the app."
                    }
            except Exception:
                # Fallback simple tuple comparison if packaging is not available
                def _tuple_ver(v_str):
                    return tuple(int(x) for x in re.sub(r'[^0-9.]', '', str(v_str)).split('.') if x)
                if _tuple_ver(APP_VERSION) < _tuple_ver(min_app_v):
                    return {
                        "success": False,
                        "error": f"Tool '{tool_id}' requires Boltools app version {min_app_v} or higher (current: {APP_VERSION}). Please update the app."
                    }

        tool_root_dir = os.path.join(self.engines_dir, tool_id)
        assert_inside_dir(tool_root_dir, self.engines_dir)
        os.makedirs(tool_root_dir, exist_ok=True)

        # Build candidate download URLs
        urls_to_try = []
        if meta.get("pack_url"):
            urls_to_try.append(meta["pack_url"])
        if meta.get("engine_url"):
            urls_to_try.append(meta["engine_url"])
        if meta.get("engine_fallback_url"):
            urls_to_try.append(meta["engine_fallback_url"])

        folder = validate_id(meta.get("engine_folder", tool_id), "engine_folder")
        remote_version = meta.get("version", "1.0.0")
        urls_to_try.append(f"https://boltools.thesurfboard.in/engines/{folder}/{tool_id}-{remote_version}.bolpack")
        urls_to_try.append(f"https://raw.githubusercontent.com/Sai-Pavan-Kumar/Boltools/main/website/engines/{folder}/engine.py")

        download_bytes: Optional[bytes] = None
        last_error = ""

        # Enforce size limits: use size_bytes from manifest + global ceiling
        manifest_size = meta.get("size_bytes") or (meta.get("size_mb", 25) * 1024 * 1024)
        max_download_allowed = min(MAX_GLOBAL_PACK_SIZE, int(manifest_size * 2))

        for url in urls_to_try:
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                )
                with urllib.request.urlopen(req, timeout=12.0) as resp:
                    if resp.status == 200:
                        content = resp.read(max_download_allowed + 1024)
                        if len(content) > max_download_allowed:
                            last_error = f"Download exceeded size ceiling ({max_download_allowed} bytes)."
                            continue

                        # Reject HTML error pages
                        if content.lstrip().startswith(b"<"):
                            last_error = f"Invalid response from {url}: received HTML response instead of tool payload."
                            continue

                        if len(content) > 100:
                            if expected_sha256:
                                actual_sha = hashlib.sha256(content).hexdigest().lower()
                                if actual_sha != expected_sha256.lower().strip():
                                    last_error = f"SHA256 mismatch for {tool_id}: expected {expected_sha256}, got {actual_sha}"
                                    continue

                            download_bytes = content
                            break
            except Exception as e:
                last_error = str(e)
                continue

        # If download failed, check if we have a bundled engine fallback
        if not download_bytes:
            bundled_engine = os.path.join(self.bundled_engines_dir, folder, "engine.py")
            if os.path.isfile(bundled_engine):
                assert_inside_dir(bundled_engine, self.bundled_engines_dir)
                try:
                    with open(bundled_engine, "rb") as f:
                        download_bytes = f.read()
                except Exception as e:
                    last_error = str(e)

        if not download_bytes:
            return {"success": False, "error": f"Failed to download tool package: {last_error or 'Network timeout'}"}

        # Staging directory for atomic extraction
        staging_dir = os.path.join(tool_root_dir, f".staging-{uuid.uuid4().hex[:8]}")
        previous_pointer = self.get_active_pointer(tool_id)

        try:
            # Check if payload is a .bolpack ZIP archive or a raw single engine.py
            is_zip = download_bytes.startswith(b"PK\x03\x04")

            if is_zip:
                # Safe ZIP extraction & pack.json hash verification
                extract_res = self.safe_extract_pack(download_bytes, staging_dir)
                pack_manifest = extract_res["pack_manifest"]
                version = pack_manifest.get("version", remote_version)
                entry = pack_manifest.get("entry", "engine.py")
                runtime = pack_manifest.get("runtime", "python")
            else:
                # Raw engine.py fallback compatibility
                os.makedirs(staging_dir, exist_ok=True)
                dest_engine = os.path.join(staging_dir, "engine.py")
                with open(dest_engine, "wb") as f:
                    f.write(download_bytes)

                version = remote_version
                entry = "engine.py"
                runtime = meta.get("engine_type", "python")

                # Synthetic pack.json for uniformity
                pack_manifest = {
                    "id": tool_id,
                    "name": meta.get("name", tool_id),
                    "version": version,
                    "min_app_version": "1.0.0",
                    "runtime": runtime,
                    "entry": entry,
                    "files": {
                        "engine.py": hashlib.sha256(download_bytes).hexdigest().lower()
                    }
                }
                with open(os.path.join(staging_dir, "pack.json"), "w", encoding="utf-8") as f:
                    json.dump(pack_manifest, f, indent=2)

            # Target version folder
            target_v_folder = os.path.join(tool_root_dir, f"v{version}")

            # If target version folder exists, remove it atomically before replacing
            if os.path.exists(target_v_folder):
                shutil.rmtree(target_v_folder)

            os.replace(staging_dir, target_v_folder)

            # Switch current.json pointer atomically
            switch_ok = self._set_active_pointer(tool_id, version, entry, runtime)
            if not switch_ok:
                raise RuntimeError("Failed to switch current.json active version pointer.")

            # Prune old versions (keep current and previous version only)
            self._prune_old_versions(tool_root_dir, keep_versions={version, previous_pointer.get("version") if previous_pointer else None})

            # Update tool_states.json
            self.tool_states[tool_id] = {
                "status": "installed",
                "version": version,
                "installed_at": datetime.now().isoformat()
            }
            self._save_tool_states()

            return {
                "success": True,
                "tool_id": tool_id,
                "version": version,
                "name": meta.get("name", tool_id),
                "message": f"Successfully installed {meta.get('name', tool_id)} v{version}."
            }

        except Exception as e:
            # Clean up staging directory
            if os.path.exists(staging_dir):
                shutil.rmtree(staging_dir, ignore_errors=True)

            # Rollback: restore previous version pointer if it was affected
            if previous_pointer:
                self._set_active_pointer(
                    tool_id,
                    previous_pointer["version"],
                    previous_pointer["entry"],
                    previous_pointer.get("runtime", "python")
                )

            return {
                "success": False,
                "error": f"Tool installation failed: {str(e)}"
            }

    def _prune_old_versions(self, tool_root_dir: str, keep_versions: Set[Optional[str]]):
        """Retains only active and immediately previous version folders for rollback."""
        valid_keep = {f"v{v}" for v in keep_versions if v}
        try:
            for item in os.listdir(tool_root_dir):
                item_path = os.path.join(tool_root_dir, item)
                if os.path.isdir(item_path) and item.startswith("v") and item not in valid_keep:
                    shutil.rmtree(item_path, ignore_errors=True)
        except Exception:
            pass

    def rollback_tool(self, tool_id: str) -> Dict[str, Any]:
        """Rolls back tool to the previous installed version if available."""
        validate_id(tool_id, "tool_id")
        tool_root_dir = os.path.join(self.engines_dir, tool_id)
        if not os.path.isdir(tool_root_dir):
            return {"success": False, "error": f"Tool '{tool_id}' is not installed."}

        current_ptr = self.get_active_pointer(tool_id)
        curr_v = f"v{current_ptr['version']}" if current_ptr else None

        # Find available version folders
        versions = []
        for item in os.listdir(tool_root_dir):
            if os.path.isdir(os.path.join(tool_root_dir, item)) and item.startswith("v"):
                versions.append(item)

        candidates = [v for v in versions if v != curr_v]
        if not candidates:
            return {"success": False, "error": "No previous version available for rollback."}

        # Pick latest previous version
        candidates.sort(key=lambda x: parse_semver(x[1:]), reverse=True)
        target_v_str = candidates[0][1:]
        target_v_dir = os.path.join(tool_root_dir, candidates[0])

        pack_json_file = os.path.join(target_v_dir, "pack.json")
        entry = "engine.py"
        runtime = "python"
        if os.path.isfile(pack_json_file):
            try:
                with open(pack_json_file, "r", encoding="utf-8") as f:
                    p = json.load(f)
                    entry = p.get("entry", "engine.py")
                    runtime = p.get("runtime", "python")
            except Exception:
                pass

        if self._set_active_pointer(tool_id, target_v_str, entry, runtime):
            self.tool_states[tool_id] = {
                "status": "installed",
                "version": target_v_str,
                "installed_at": datetime.now().isoformat()
            }
            self._save_tool_states()
            return {"success": True, "version": target_v_str, "message": f"Successfully rolled back to v{target_v_str}."}

        return {"success": False, "error": "Failed to switch rollback pointer."}

    def uninstall_tool(self, tool_id: str, purge_data: bool = False) -> bool:
        """Uninstalls tool by deleting engine folder and updating state."""
        validate_id(tool_id, "tool_id")
        self.tool_states[tool_id] = {
            "status": "available",
            "version": None
        }
        self._save_tool_states()

        # Delete dynamic engine folder
        tool_dir = os.path.join(self.engines_dir, tool_id)
        assert_inside_dir(tool_dir, self.engines_dir)
        if os.path.exists(tool_dir):
            try:
                shutil.rmtree(tool_dir)
            except Exception:
                pass

        if purge_data:
            user_data_dir = os.path.join(self.tools_data_dir, tool_id)
            assert_inside_dir(user_data_dir, self.tools_data_dir)
            if os.path.exists(user_data_dir):
                try:
                    shutil.rmtree(user_data_dir)
                except Exception:
                    pass

        return True


# Global Singleton
tool_store_service = ToolStoreService()
