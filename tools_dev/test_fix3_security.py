import unittest
import os
import sys

# Ensure software root is on sys.path
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

if __name__ == "__main__":
    unittest.main()
