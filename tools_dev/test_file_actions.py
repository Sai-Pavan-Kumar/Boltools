"""Right-click mapping: each file type must only see the tools that can take it."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("software"))

from src.core.file_actions import menu_entries

MANIFEST = os.path.join(os.path.dirname(__file__), "..", "tools_manifest.json")


def ids_for(paths):
    with open(MANIFEST, encoding="utf-8") as f:
        tools = json.load(f)["tools"]
    return [e["id"] for e in menu_entries(tools, paths)]


class FileActionsTest(unittest.TestCase):
    def test_every_tool_declares_files_and_label(self):
        with open(MANIFEST, encoding="utf-8") as f:
            for tool in json.load(f)["tools"]:
                self.assertTrue(tool.get("accepts"), tool["id"])
                self.assertTrue(tool.get("menu_label"), tool["id"])

    def test_photo_never_gets_audio_or_pdf_tools(self):
        ids = ids_for(["C:/x/Trip.JPG"])
        self.assertIn("image_webp_compress", ids)
        self.assertNotIn("media_audio_extractor", ids)
        self.assertNotIn("pdf_compress", ids)
        self.assertEqual(ids[-1], "system_batch_rename")

    def test_song_gets_only_audio_and_rename(self):
        self.assertEqual(ids_for(["a.mp3"]), ["media_audio_extractor", "system_batch_rename"])

    def test_merge_needs_two_pdfs(self):
        self.assertNotIn("pdf_merge", ids_for(["a.pdf"]))
        self.assertIn("pdf_merge", ids_for(["a.pdf", "b.pdf"]))

    def test_mixed_selection_keeps_only_shared_tools(self):
        self.assertEqual(ids_for(["a.pdf", "b.mp4"]), ["system_batch_rename"])


if __name__ == "__main__":
    unittest.main()
