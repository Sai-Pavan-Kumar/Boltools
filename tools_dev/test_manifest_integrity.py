"""Release guard: a stale fingerprint makes every user's install fail as "unsafe".

Engines are edited often; these checks fail the moment someone forgets to
refresh tools_manifest.json, instead of after a release.
"""

import hashlib
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SOFTWARE_MANIFEST = os.path.join(HERE, "..", "tools_manifest.json")
WEBSITE_ROOT = os.path.join(HERE, "..", "..", "website")
WEBSITE_MANIFEST = os.path.join(WEBSITE_ROOT, "tools_manifest.json")
BUNDLES = os.path.join(HERE, "..", "release_bundles")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class ManifestIntegrityTest(unittest.TestCase):
    def test_app_and_website_serve_the_same_list(self):
        if not os.path.exists(WEBSITE_MANIFEST):
            self.skipTest("website repo not next to software")
        self.assertEqual(load(SOFTWARE_MANIFEST), load(WEBSITE_MANIFEST))

    def test_list_has_rollback_counter(self):
        self.assertIsInstance(load(SOFTWARE_MANIFEST).get("sequence"), int)

    def test_every_fingerprint_matches_its_file(self):
        for tool in load(SOFTWARE_MANIFEST)["tools"]:
            with self.subTest(tool=tool["id"]):
                self.assertTrue(tool.get("sha256"), "missing sha256")
                if tool["engine_type"] == "python":
                    path = os.path.join(WEBSITE_ROOT, "engines", tool["engine_folder"], "engine.py")
                else:
                    path = os.path.join(BUNDLES, f"{tool['engine_folder']}-{tool['version']}.bolpack")
                if not os.path.exists(path):
                    self.skipTest(f"{path} not present")
                self.assertEqual(sha256_of(path), tool["sha256"])


if __name__ == "__main__":
    unittest.main()
