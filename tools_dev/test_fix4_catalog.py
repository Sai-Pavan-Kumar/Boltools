import unittest
import os
import sys

# Ensure software root is on sys.path
sys.path.insert(0, os.path.abspath("software"))

from src.desktop_bridge import desktop_bridge
from src.core.tool_store import tool_store_service

class TestFix4CatalogOptimization(unittest.TestCase):
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

if __name__ == "__main__":
    unittest.main()
