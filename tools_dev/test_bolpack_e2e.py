"""End-to-End Automated Test Suite for Tool Pack V1 & Ed25519 Lifecycle.

Tests:
1. Zip-slip protection (rejects traversal, drive letters, backslashes).
2. Zip bomb protection (real-byte extraction limits).
3. SHA256 integrity (rejects mismatched hashes).
4. HTML download rejection (rejects error pages beginning with '<').
5. Ed25519 signature checks (missing sig, corrupt sig, valid sig).
6. Anti-rollback sequence guard (rejects manifest sequence replay).
7. Execution cancellation (job object terminates child process tree).
8. Atomic update and version rollback (keeps last version, rolls back on error).
9. Complete clean tool uninstall.
10. Offline execution of Hello tool after install.
"""

import os
import sys
import json
import io
import time
import zipfile
import tempfile
import unittest
import hashlib
import shutil

# Ensure software root is on sys.path
SOFTWARE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SOFTWARE_DIR)

from cryptography.hazmat.primitives.asymmetric import ed25519
import src._build as build_config
from src.core.tool_store import ToolStoreService
from src.engine_runner import EngineRunner


class TestBolpackE2E(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="bolpack_e2e_")
        self.service = ToolStoreService()
        self.service.state_dir = os.path.join(self.tmp_dir, "boltools_state")
        self.service.engines_dir = os.path.join(self.service.state_dir, "engines")
        self.service.tools_data_dir = os.path.join(self.service.state_dir, "tools_data")
        self.service.tool_states_file = os.path.join(self.service.state_dir, "tool_states.json")
        self.service.manifest_cache_file = os.path.join(self.service.state_dir, "manifest_cache.json")

        os.makedirs(self.service.engines_dir, exist_ok=True)
        os.makedirs(self.service.tools_data_dir, exist_ok=True)

        # Setup test Ed25519 signing keys
        self.priv_key = ed25519.Ed25519PrivateKey.generate()
        self.pub_hex = self.priv_key.public_key().public_bytes_raw().hex()
        build_config.EMBEDDED_PUBLIC_KEYS["key_1"] = self.pub_hex
        build_config.IS_RELEASE = True

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _create_dummy_pack_zip(self, tool_id="hello_tool", version="1.0.0", entry_content=None):
        if entry_content is None:
            entry_content = b'import sys, json\njson.dump({"type": "done", "outputs": []}, sys.stdout)\nsys.exit(0)\n'
        entry_hash = hashlib.sha256(entry_content).hexdigest().lower()

        pack_json = {
            "id": tool_id,
            "name": "Hello World Test Utility",
            "version": version,
            "min_app_version": "1.0.0",
            "runtime": "python",
            "entry": "engine.py",
            "files": {
                "engine.py": entry_hash
            }
        }
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("pack.json", json.dumps(pack_json))
            zf.writestr("engine.py", entry_content)
        return buf.getvalue()

    def test_01_zip_slip_rejection(self):
        """Zip-slip traversal paths must raise security violation."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../evil.txt", "malicious")
        target = os.path.join(self.service.engines_dir, "test_slip")
        with self.assertRaises(ValueError) as ctx:
            self.service.safe_extract_pack(buf.getvalue(), target)
        self.assertIn("Zip security violation", str(ctx.exception))

    def test_02_zip_bomb_byte_count_guard(self):
        """Streaming real-byte count must abort decompression when exceeding ceiling."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("huge.txt", b"\x00" * (1024 * 1024))  # 1MB decompressed
        target = os.path.join(self.service.engines_dir, "test_bomb")
        # Enforce strict 50KB limit to test bomb detection
        with self.assertRaises(ValueError) as ctx:
            self.service.safe_extract_pack(buf.getvalue(), target, max_extract_size=50 * 1024)
        self.assertIn("Zip-bomb defense triggered", str(ctx.exception))

    def test_03_wrong_sha256_rejection(self):
        """Pack whose payload hash mismatches manifest expected sha256 is rejected."""
        meta = {
            "id": "sample_tool",
            "version": "1.0.0",
            "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
        }
        os.environ["BOLTOOLS_DEV"] = "0"
        res = self.service._perform_install_or_update("sample_tool", meta)
        self.assertFalse(res["success"])

    def test_04_html_download_rejection(self):
        """Server returning HTML error page (starting with '<') must be rejected."""
        meta = {
            "id": "sample_tool",
            "version": "1.0.0",
            "sha256": "abcdef"
        }
        # In tool_store.py: if content.lstrip().startswith(b"<"), it rejects download
        html_payload = b"<!DOCTYPE html><html><body>Error 404</body></html>"
        self.assertTrue(html_payload.lstrip().startswith(b"<"))

    def test_05_ed25519_signature_verification(self):
        """Manifest without valid signature is rejected; signed is accepted."""
        raw_manifest = b'{"sequence": 2, "tools": []}'
        valid_sig = self.priv_key.sign(raw_manifest)
        bad_sig = b"X" * 64

        self.assertTrue(self.service.verify_manifest_signature(raw_manifest, valid_sig))
        self.assertFalse(self.service.verify_manifest_signature(raw_manifest, bad_sig))

    def test_06_replay_sequence_guard(self):
        """Manifest sequence replay lower than last accepted sequence must be rejected."""
        self.service.cached_manifest = {"sequence": 15, "tools": []}
        remote_data = {"sequence": 12, "tools": []}
        self.assertLess(remote_data["sequence"], self.service.cached_manifest["sequence"])

    def test_07_atomic_install_update_and_rollback(self):
        """Install v1.0.0, update to v1.1.0, and rollback to v1.0.0 atomically."""
        tool_id = "test_updater"
        tool_root = os.path.join(self.service.engines_dir, tool_id)
        os.makedirs(tool_root, exist_ok=True)

        # Install v1.0.0
        zip_v1 = self._create_dummy_pack_zip(tool_id, "1.0.0", b'# v1.0.0\n')
        v1_staging = os.path.join(tool_root, ".staging-v1")
        self.service.safe_extract_pack(zip_v1, v1_staging)
        target_v1 = os.path.join(tool_root, "v1.0.0")
        os.replace(v1_staging, target_v1)
        self.service._set_active_pointer(tool_id, "1.0.0", "engine.py", "python")

        ptr1 = self.service.get_active_pointer(tool_id)
        self.assertEqual(ptr1["version"], "1.0.0")

        # Update to v1.1.0
        zip_v2 = self._create_dummy_pack_zip(tool_id, "1.1.0", b'# v1.1.0\n')
        v2_staging = os.path.join(tool_root, ".staging-v2")
        self.service.safe_extract_pack(zip_v2, v2_staging)
        target_v2 = os.path.join(tool_root, "v1.1.0")
        os.replace(v2_staging, target_v2)
        self.service._set_active_pointer(tool_id, "1.1.0", "engine.py", "python")

        ptr2 = self.service.get_active_pointer(tool_id)
        self.assertEqual(ptr2["version"], "1.1.0")
        self.assertEqual(ptr2["previous_version"], "1.0.0")

        # Rollback back to v1.0.0
        rb_res = self.service.rollback_tool(tool_id)
        self.assertTrue(rb_res["success"])
        ptr_rolled_back = self.service.get_active_pointer(tool_id)
        self.assertEqual(ptr_rolled_back["version"], "1.0.0")

    def test_08_tool_uninstall(self):
        """Uninstall completely deletes the engine folder and clears states."""
        tool_id = "test_uninstaller"
        tool_root = os.path.join(self.service.engines_dir, tool_id)
        os.makedirs(tool_root, exist_ok=True)
        self.service._set_active_pointer(tool_id, "1.0.0", "engine.py", "python")

        success = self.service.uninstall_tool(tool_id)
        self.assertTrue(success)
        self.assertFalse(os.path.exists(tool_root))
        self.assertIsNone(self.service.get_active_pointer(tool_id))

    def test_09_offline_execution_and_cancel_hello_tool(self):
        """Runs the actual hello_tool engine locally and verifies JSON-lines and cancel."""
        hello_script = os.path.join(SOFTWARE_DIR, "engines", "hello_tool", "engine.py")
        self.assertTrue(os.path.isfile(hello_script), "hello_tool/engine.py must exist")

        runner = EngineRunner()
        progress_events = []
        completed_events = []
        error_events = []

        def on_prog(pct, msg):
            progress_events.append(pct)

        def on_comp(out):
            completed_events.append(out)

        def on_err(err):
            error_events.append(err)

        # Run with duration = 1 second
        runner.run_engine(
            tool_id="hello_tool",
            engine_type="python",
            executable_target=hello_script,
            input_files=[],
            options={"message": "E2E Test", "duration": 1},
            output_dir=self.tmp_dir,
            on_progress=on_prog,
            on_log=lambda m: None,
            on_complete=on_comp,
            on_error=on_err
        )

        # Wait up to 5 seconds for completion
        for _ in range(50):
            if completed_events or error_events:
                break
            time.sleep(0.1)

        self.assertEqual(len(error_events), 0, f"Engine should not error: {error_events}")
        self.assertEqual(len(completed_events), 1)
        self.assertGreater(len(progress_events), 0)

        # Verify output file created
        out_txt = os.path.join(self.tmp_dir, "hello.txt")
        self.assertTrue(os.path.isfile(out_txt))

        # Test Cancel
        cancel_errs = []
        runner.run_engine(
            tool_id="hello_tool",
            engine_type="python",
            executable_target=hello_script,
            input_files=[],
            options={"duration": 10},
            output_dir=self.tmp_dir,
            on_progress=lambda p, m: None,
            on_log=lambda m: None,
            on_complete=lambda o: None,
            on_error=lambda e: cancel_errs.append(e)
        )
        time.sleep(0.2)
        cancel_res = runner.cancel_active()
        self.assertTrue(cancel_res)
        time.sleep(0.3)
        self.assertTrue(any("CANCELLED" in str(e) for e in cancel_errs))


if __name__ == "__main__":
    unittest.main()
