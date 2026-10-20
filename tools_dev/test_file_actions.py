"""Right-click mapping: each file type must only see the actions that can take it."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("software"))

from src.core.file_actions import menu_entries, resolve_key

MANIFEST = os.path.join(os.path.dirname(__file__), "..", "tools_manifest.json")


def load_tools():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)["tools"]


def keys_for(paths):
    return [e["key"] for e in menu_entries(load_tools(), paths)]


class FileActionsTest(unittest.TestCase):
    def test_every_tool_declares_files_and_an_entry(self):
        for tool in load_tools():
            self.assertTrue(tool.get("accepts"), tool["id"])
            self.assertTrue(tool.get("quick_actions") or tool.get("menu_label"), tool["id"])

    def test_photo_never_gets_audio_or_pdf_tools(self):
        keys = keys_for(["C:/x/Trip.JPG"])
        self.assertIn("image_webp_compress@1", keys)
        self.assertIn("pdf_converter@1", keys)
        self.assertNotIn("pdf_converter@0", keys)
        self.assertNotIn("media_audio_extractor@0", keys)
        self.assertEqual(keys[-1], "system_batch_rename")

    def test_song_gets_only_audio_and_rename(self):
        self.assertEqual(keys_for(["a.mp3"]), ["media_audio_extractor@0", "system_batch_rename"])

    def test_merge_needs_two_pdfs(self):
        self.assertNotIn("pdf_merge@0", keys_for(["a.pdf"]))
        self.assertIn("pdf_merge@0", keys_for(["a.pdf", "b.pdf"]))

    def test_mixed_selection_keeps_only_shared_tools(self):
        self.assertEqual(keys_for(["a.pdf", "b.mp4"]), ["system_batch_rename"])

    def test_keys_resolve_to_quick_or_open(self):
        tools = load_tools()
        tool, action = resolve_key(tools, "image_webp_compress@1")
        self.assertEqual((tool["id"], action["options"]["target_kb"]), ("image_webp_compress", 50))
        self.assertIsNone(resolve_key(tools, "system_batch_rename")[1])
        self.assertIsNone(resolve_key(tools, "pdf_merge@9")[1])
        self.assertIsNone(resolve_key(tools, "nope@0")[0])


if __name__ == "__main__":
    unittest.main()
