"""Licences folder: complete, current with the venv, and unable to serve any other file."""

import os
import sys
import unittest
from importlib import metadata

SOFTWARE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SOFTWARE_DIR)

from src.core import licences

LICENCES_DIR = os.path.join(SOFTWARE_DIR, "licenses")
# Bundled by Boltools.spec; each must be credited (run tools_dev/collect_licences.py after changes).
MUST_LIST = {"python", "pywebview", "pillow", "pikepdf", "pypdfium2", "cryptography", "pynacl",
             "overused_grotesk", "geist_mono", "ffmpeg", "openssl", "webview2_sdk", "vc_runtime"}


class TestLicences(unittest.TestCase):

    def setUp(self):
        self.components = licences.list_components(LICENCES_DIR)["components"]

    def test_every_shipped_part_is_listed_with_its_files(self):
        ids = {c["id"] for c in self.components}
        self.assertTrue(MUST_LIST <= ids, f"missing: {MUST_LIST - ids}")
        for comp in self.components:
            for name in comp["files"]:
                self.assertTrue(os.path.isfile(os.path.join(LICENCES_DIR, comp["id"], name)), f"{comp['id']}/{name}")

    def test_versions_match_installed_packages(self):
        for comp in self.components:
            dist = {"pikepdf": "pikepdf", "pillow": "pillow", "pypdfium2": "pypdfium2", "pywebview": "pywebview",
                    "cryptography": "cryptography", "pynacl": "pynacl", "lxml": "lxml"}.get(comp["id"])
            if dist:
                self.assertEqual(comp["version"], metadata.version(dist),
                                 f"{comp['id']} is stale: run tools_dev/collect_licences.py")

    def test_listed_text_reads(self):
        text = licences.read_text("ffmpeg", "GPL-3.0.txt", LICENCES_DIR)
        self.assertIn("GNU GENERAL PUBLIC LICENSE", text)

    def test_anything_not_listed_is_refused(self):
        for comp_id, name in (("ffmpeg", "../index.json"), ("ffmpeg", "..\\..\\main.py"), ("../src", "licences.py"),
                              ("python", "GPL-3.0.txt"), ("nope", "LICENSE")):
            self.assertIsNone(licences.read_text(comp_id, name, LICENCES_DIR), f"{comp_id}/{name}")


if __name__ == "__main__":
    unittest.main()
