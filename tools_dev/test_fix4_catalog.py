import unittest
import os
import sys

# Ensure software root is on sys.path
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("software"))

from src.desktop_bridge import desktop_bridge
from src.core.tool_store import tool_store_service

class TestFix4CatalogOptimization(unittest.TestCase):
    def setUp(self):
        tool_store_service.cached_manifest = tool_store_service._load_cached_manifest()
        tool_store_service.invalidate_cache()

    def test_get_initial_data_is_lightweight(self):
        data = desktop_bridge.get_initial_data()
        self.assertIn("counts", data)
        self.assertIn("favorites", data)
        self.assertIn("settings", data.get("default_downloads") and data)
        self.assertIn("announcements", data)
        self.assertNotIn("tools", data, "get_initial_data must not contain full tools catalog")

    def test_get_catalog_summary(self):
        summaries = desktop_bridge.get_catalog_summary()
        self.assertIsInstance(summaries, list)
        for s in summaries:
            self.assertIn("id", s)
            self.assertIn("name", s)
            self.assertIn("category_id", s)
            self.assertIn("status", s)
            self.assertIn("version", s)
            self.assertIn("size_mb", s)
            self.assertIn("update_available", s)
            self.assertIn("description", s)
            # Check description cut to at most 120 chars
            self.assertLessEqual(len(s["description"]), 120)

    def test_search_tools_deleted_from_bridge(self):
        self.assertFalse(hasattr(desktop_bridge, "search_tools"), "search_tools must be deleted from desktop_bridge")

    def test_pdf_category_and_tools(self):
        # 1. Category check
        init_data = desktop_bridge.get_initial_data()
        pdf_cat = next((c for c in init_data["categories"] if c["id"] == "pdf"), None)
        self.assertIsNotNone(pdf_cat, "PDF Studio category must be present in get_initial_data")
        self.assertEqual(pdf_cat["name"], "PDF Studio")

        # 2. Tool resolution for pdf_merge and pdf_split
        for tool_id in ["pdf_merge", "pdf_split"]:
            meta = tool_store_service.get_tool_meta(tool_id)
            self.assertIsNotNone(meta, f"Tool {tool_id} must have manifest metadata")
            self.assertEqual(meta.get("category_id"), "pdf")
            self.assertEqual(meta.get("engine_folder"), "pdf_studio")
            self.assertEqual(meta.get("entry"), "pdf_engine.exe")

            target = tool_store_service.get_engine_target(tool_id)
            self.assertIsNotNone(target, f"Engine target for {tool_id} must resolve")
            self.assertTrue(os.path.exists(target), f"Target {target} must exist on disk")
            self.assertTrue(target.endswith("pdf_engine.exe"))

        # 3. Backwards compatibility for legacy pdf_studio
        legacy_meta = tool_store_service.get_tool_meta("pdf_studio")
        self.assertIsNotNone(legacy_meta)
        legacy_target = tool_store_service.get_engine_target("pdf_studio")
        self.assertIsNotNone(legacy_target)
        self.assertTrue(os.path.exists(legacy_target))

if __name__ == "__main__":
    unittest.main()
