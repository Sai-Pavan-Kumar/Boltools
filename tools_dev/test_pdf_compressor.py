import unittest
import os
import sys
import json


# Ensure software root is on sys.path
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("software"))

from src.desktop_bridge import desktop_bridge
from src.core.tool_store import tool_store_service

class TestPdfCompressor(unittest.TestCase):
    def setUp(self):
        tool_store_service.cached_manifest = tool_store_service._load_cached_manifest()
        tool_store_service.invalidate_cache()

    def test_pdf_compress_catalog_status(self):
        tools = desktop_bridge.get_catalog_summary()
        compress_tool = next((t for t in tools if t["id"] == "pdf_compress"), None)
        self.assertIsNotNone(compress_tool, "pdf_compress must be present in catalog summary")
        self.assertEqual(compress_tool["name"], "Compress PDF")
        self.assertEqual(compress_tool["category_id"], "pdf")
        self.assertEqual(compress_tool["status"], "installed", "pdf_compress engine must resolve as installed")

    def test_pdf_compress_engine_target(self):
        target = tool_store_service.get_engine_target("pdf_compress")
        self.assertIsNotNone(target, "Engine target for pdf_compress must resolve")
        self.assertTrue(os.path.exists(target), f"Engine target {target} must exist on disk")
        self.assertTrue(target.endswith("engine.py"))

    def test_all_nine_tools_in_catalog(self):
        tools = desktop_bridge.get_catalog_summary()
        self.assertEqual(len(tools), 9, f"Catalog must contain exactly 9 tools, got {len(tools)}")
        tool_ids = {t["id"] for t in tools}
        expected_ids = {
            "media_audio_extractor",
            "video_compressor",
            "pdf_merge",
            "pdf_split",
            "pdf_compress",
            "pdf_converter",
            "image_webp_compress",
            "system_batch_rename",
            "subtitle_animator"
        }
        self.assertEqual(tool_ids, expected_ids, "All 9 expected tools must be present")

if __name__ == "__main__":
    unittest.main()
