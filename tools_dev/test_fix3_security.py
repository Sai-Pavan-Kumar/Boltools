import unittest
import os
import sys

# Ensure software root is on sys.path
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("software"))

from src.desktop_bridge import desktop_bridge, validate_identifier
from src.core.tool_store import tool_store_service, validate_id, assert_inside_dir

class TestFix3Validation(unittest.TestCase):
    def test_valid_ids(self):
        valid = ["pdf_converter", "tool_123", "a", "x" * 64, "video_compressor_v2"]
        for v in valid:
            self.assertEqual(validate_identifier(v), v)
            self.assertEqual(validate_id(v), v)

    def test_invalid_ids(self):
        invalid = [
            "",
            "../escape",
            "foo/bar",
            "tool-name",       # hyphen not in [a-z0-9_]
            "ToolName",       # uppercase not allowed
            "tool;rm -rf",
            "x" * 65,          # >64 chars
            None,
            123,
            "../../etc/passwd",
            "engine\\traversal"
        ]
        for inv in invalid:
            with self.assertRaises(ValueError):
                validate_identifier(inv)
            with self.assertRaises(ValueError):
                validate_id(inv)

    def test_bridge_methods_reject_invalid(self):
        bad_id = "../evil_tool"
        with self.assertRaises(ValueError):
            desktop_bridge.toggle_favorite(bad_id)

        with self.assertRaises(ValueError):
            desktop_bridge.install_tool(bad_id)

        with self.assertRaises(ValueError):
            desktop_bridge.install_or_update_tool(bad_id)

        with self.assertRaises(ValueError):
            desktop_bridge.uninstall_tool(bad_id)

        with self.assertRaises(ValueError):
            desktop_bridge.get_tool_details(bad_id)

    def test_path_confinement_assertions(self):
        parent = tool_store_service.engines_dir
        safe_child = os.path.join(parent, "valid_tool", "engine.py")
        assert_inside_dir(safe_child, parent)  # Should succeed

        escaped_child = os.path.join(parent, "..", "system32", "cmd.exe")
        with self.assertRaises(ValueError):
            assert_inside_dir(escaped_child, parent)

    def test_refuse_install_missing_sha256(self):
        """Refuses to install if sha256 checksum is missing and BOLTOOLS_DEV != 1."""
        old_env = os.environ.get("BOLTOOLS_DEV")
        try:
            if "BOLTOOLS_DEV" in os.environ:
                del os.environ["BOLTOOLS_DEV"]
            tool_store_service.cached_manifest = {
                "tools": [
                    {
                        "id": "test_unsigned_tool",
                        "name": "Unsigned Tool",
                        "engine_folder": "test_unsigned_tool"
                        # No sha256
                    }
                ]
            }
            res = tool_store_service.install_or_update_tool("test_unsigned_tool")
            self.assertFalse(res["success"])
            self.assertIn("Missing sha256 checksum", res["error"])
        finally:
            if old_env is not None:
                os.environ["BOLTOOLS_DEV"] = old_env

    def test_refuse_install_html_and_wrong_sha256(self):
        """Rejects download payloads starting with '<' (HTML) or with wrong sha256."""
        import unittest.mock as mock
        import urllib.request
        import io

        tool_store_service.cached_manifest = {
            "tools": [
                {
                    "id": "test_html_tool",
                    "name": "HTML Tool",
                    "engine_url": "https://example.com/engine.py",
                    "sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
                }
            ]
        }

        # Mock HTML error response (starts with b"<")
        def mock_html_urlopen(req, timeout=10.0):
            bio = io.BytesIO(b"<!DOCTYPE html><html><body>404 Not Found</body></html>")
            bio.status = 200
            return bio

        with mock.patch("urllib.request.urlopen", side_effect=mock_html_urlopen):
            res = tool_store_service.install_or_update_tool("test_html_tool")
            self.assertFalse(res["success"])
            self.assertIn("received HTML response", res["error"])

        # Mock valid script but mismatched hash
        def mock_mismatch_urlopen(req, timeout=10.0):
            bio = io.BytesIO(b"# valid python script\nprint('hello')\n" + b" " * 100)
            bio.status = 200
            return bio

        with mock.patch("urllib.request.urlopen", side_effect=mock_mismatch_urlopen):
            res = tool_store_service.install_or_update_tool("test_html_tool")
            self.assertFalse(res["success"])
            self.assertIn("SHA256 mismatch", res["error"])

    def test_atomic_replace_on_successful_download(self):
        """Verifies successful download uses atomic os.replace."""
        import unittest.mock as mock
        import hashlib
        import io

        script_bytes = b"# valid python script\nprint('success')\n" + b" " * 100
        valid_sha = hashlib.sha256(script_bytes).hexdigest()

        tool_store_service.cached_manifest = {
            "tools": [
                {
                    "id": "test_atomic_tool",
                    "name": "Atomic Tool",
                    "engine_url": "https://example.com/engine.py",
                    "sha256": valid_sha
                }
            ]
        }

        script_response = io.BytesIO(script_bytes)
        script_response.status = 200

        with mock.patch("urllib.request.urlopen", return_value=script_response):
            with mock.patch("os.replace") as mock_replace:
                res = tool_store_service.install_or_update_tool("test_atomic_tool")
                self.assertTrue(res["success"])
                self.assertTrue(mock_replace.called, "os.replace must be called for atomic file installation")

if __name__ == "__main__":
    unittest.main()
