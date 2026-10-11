"""Automated Test Suite for Tool Pack v1 Unpacker and Security Guards.

Verifies:
1. Zip-slip protection: rejects "..", absolute paths, drive letters, colons, Windows reserved names.
2. Symlink protection: detects symlink UNIX mode bits in ZipInfo.external_attr (0o120000).
3. Zip-bomb protection: aborts if streamed extracted bytes exceed limit.
4. Duplicate entry detection: rejects case-insensitive duplicate filenames.
5. Atomic staging & current.json pointer switching.
6. Two-version retention & instant rollback.
7. Clean uninstallation wipes tool folder.
"""

import os
import sys
import io
import json
import zipfile
import hashlib
import tempfile
import unittest

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("software"))

from src.core.tool_store import (
    ToolStoreService,
    validate_id,
    assert_inside_dir,
    WINDOWS_RESERVED_NAMES
)


class TestToolPackUnpacker(unittest.TestCase):
    def setUp(self):
        self.temp_root = tempfile.mkdtemp()
        self.service = ToolStoreService()
        # Point engines dir to isolated test sandbox
        self.service.engines_dir = os.path.join(self.temp_root, "engines")
        os.makedirs(self.service.engines_dir, exist_ok=True)

    def tearDown(self):
        try:
            import shutil
            shutil.rmtree(self.temp_root)
        except Exception:
            pass

    def _create_pack_zip(self, files_dict, pack_manifest=None):
        """Helper to create a valid or invalid .bolpack zip in memory."""
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            files_hash_map = {}
            for name, content in files_dict.items():
                zf.writestr(name, content)
                if name != "pack.json":
                    files_hash_map[name] = hashlib.sha256(content.encode("utf-8") if isinstance(content, str) else content).hexdigest().lower()

            if pack_manifest is not False:
                manifest = pack_manifest or {
                    "id": "test_pack",
                    "name": "Test Utility",
                    "version": "1.0.0",
                    "min_app_version": "1.0.0",
                    "runtime": "python",
                    "entry": "engine.py",
                    "files": files_hash_map
                }
                zf.writestr("pack.json", json.dumps(manifest))

        bio.seek(0)
        return bio.getvalue()

    def test_zip_slip_rejections(self):
        """Rejects paths with '..', leading slashes, colons, or Windows device names."""
        bad_paths = [
            "../escape.py",
            "folder/../../escape.py",
            "/absolute.py",
            "\\backslash.py",
            "C:/drive.py",
            "foo:bar.py",
            "CON",
            "sub/nul.txt",
            "com1.py"
        ]
        for bad in bad_paths:
            with self.assertRaises(ValueError, msg=f"Should reject: {bad}"):
                self.service.validate_zip_entry_path(bad)

    def test_symlink_rejection(self):
        """Rejects symlinks with 0o120000 mode bits in external_attr."""
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w") as zf:
            info = zipfile.ZipInfo("symlink.py")
            # Set symlink mode bits (0o120777 << 16)
            info.external_attr = 0o120777 << 16
            zf.writestr(info, "target.py")

        bio.seek(0)
        zip_bytes = bio.getvalue()

        target_dir = os.path.join(self.service.engines_dir, "test_symlink", "v1.0.0")
        with self.assertRaises(ValueError) as ctx:
            self.service.safe_extract_pack(zip_bytes, target_dir)
        self.assertIn("Symlinks are forbidden", str(ctx.exception))

    def test_zip_bomb_streaming_guard(self):
        """Streaming byte count aborts when extracted size exceeds limit."""
        # Create small compressed zip with 2MB uncompressed content
        large_content = b"0" * (2 * 1024 * 1024)
        zip_bytes = self._create_pack_zip({"engine.py": large_content})

        target_dir = os.path.join(self.service.engines_dir, "test_bomb", "v1.0.0")
        # Set max extract size to 500 KB to trigger bomb defense
        with self.assertRaises(ValueError) as ctx:
            self.service.safe_extract_pack(zip_bytes, target_dir, max_extract_size=500 * 1024)
        self.assertIn("Zip-bomb defense triggered", str(ctx.exception))

    def test_duplicate_case_insensitive_rejection(self):
        """Rejects zip with case-duplicate filenames (e.g. Engine.py and engine.py)."""
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w") as zf:
            zf.writestr("engine.py", "code 1")
            zf.writestr("Engine.py", "code 2")

        bio.seek(0)
        target_dir = os.path.join(self.service.engines_dir, "test_dup", "v1.0.0")
        with self.assertRaises(ValueError) as ctx:
            self.service.safe_extract_pack(bio.getvalue(), target_dir)
        self.assertIn("Case-insensitive duplicate", str(ctx.exception))

    def test_atomic_install_current_pointer_and_rollback(self):
        """Installs v1.0.0, updates to v1.0.1, verifies current.json pointer, and tests rollback."""
        v1_bytes = self._create_pack_zip(
            {"engine.py": "print('v1.0.0')"},
            pack_manifest={"id": "test_atomic", "name": "Atomic Tool", "version": "1.0.0", "min_app_version": "1.0.0", "runtime": "python", "entry": "engine.py", "files": {"engine.py": hashlib.sha256(b"print('v1.0.0')").hexdigest()}}
        )

        v2_bytes = self._create_pack_zip(
            {"engine.py": "print('v1.0.1')"},
            pack_manifest={"id": "test_atomic", "name": "Atomic Tool", "version": "1.0.1", "min_app_version": "1.0.0", "runtime": "python", "entry": "engine.py", "files": {"engine.py": hashlib.sha256(b"print('v1.0.1')").hexdigest()}}
        )

        # 1. Install v1.0.0
        self.service.cached_manifest = {
            "tools": [{
                "id": "test_atomic",
                "name": "Atomic Tool",
                "version": "1.0.0",
                "sha256": hashlib.sha256(v1_bytes).hexdigest()
            }]
        }

        # Mock urllib to return v1_bytes
        import unittest.mock as mock
        with mock.patch("urllib.request.urlopen") as mock_open:
            resp = io.BytesIO(v1_bytes)
            resp.status = 200
            mock_open.return_value = resp

            res = self.service.install_or_update_tool("test_atomic")
            self.assertTrue(res["success"])
            self.assertEqual(res["version"], "1.0.0")

        # Verify current.json
        ptr = self.service.get_active_pointer("test_atomic")
        self.assertIsNotNone(ptr)
        self.assertEqual(ptr["version"], "1.0.0")
        self.assertTrue(os.path.isfile(self.service.get_engine_target("test_atomic")))

        # 2. Update to v1.0.1
        self.service.cached_manifest["tools"][0]["version"] = "1.0.1"
        self.service.cached_manifest["tools"][0]["sha256"] = hashlib.sha256(v2_bytes).hexdigest()

        with mock.patch("urllib.request.urlopen") as mock_open:
            resp = io.BytesIO(v2_bytes)
            resp.status = 200
            mock_open.return_value = resp

            res2 = self.service.install_or_update_tool("test_atomic")
            self.assertTrue(res2["success"])
            self.assertEqual(res2["version"], "1.0.1")

        ptr2 = self.service.get_active_pointer("test_atomic")
        self.assertEqual(ptr2["version"], "1.0.1")

        # 3. Rollback to v1.0.0
        rb_res = self.service.rollback_tool("test_atomic")
        self.assertTrue(rb_res["success"])
        self.assertEqual(rb_res["version"], "1.0.0")

        ptr_rb = self.service.get_active_pointer("test_atomic")
        self.assertEqual(ptr_rb["version"], "1.0.0")

        # 4. Uninstall
        self.service.uninstall_tool("test_atomic")
        self.assertFalse(os.path.exists(os.path.join(self.service.engines_dir, "test_atomic")))


if __name__ == "__main__":
    unittest.main()
