"""Release builds must refuse unsigned tools lists and engines that miss their fingerprint.

tool_store copies IS_RELEASE at import time, so patching src._build alone tests dev
mode by accident; these tests patch the flag on tool_store itself.
"""

import os
import sys
import tempfile
import shutil
import unittest
from unittest import mock

SOFTWARE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SOFTWARE_DIR)

import src.core.tool_store as tool_store_module
from src.core.tool_store import ToolStoreService

GOOD_ENGINE = b"# real engine\n" + b"x" * 200
WRONG_SHA = "0" * 64


class _FakeResponse:
    status = 200

    def __init__(self, body):
        self._body = body

    def read(self, *_):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class TestReleaseEngineGuard(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="release_guard_")
        self.service = ToolStoreService()
        self.service.engines_dir = os.path.join(self.tmp_dir, "engines")
        self.service.release_bundles_dir = os.path.join(self.tmp_dir, "bundles")
        self.service.bundled_engines_dir = os.path.join(self.tmp_dir, "bundled")
        self.service.manifest_cache_file = os.path.join(self.tmp_dir, "manifest_cache.json")
        os.makedirs(os.path.join(self.service.bundled_engines_dir, "sample"), exist_ok=True)
        with open(os.path.join(self.service.bundled_engines_dir, "sample", "engine.py"), "wb") as f:
            f.write(GOOD_ENGINE)
        patches = [
            mock.patch.object(tool_store_module, "IS_RELEASE", True),
            mock.patch.dict(os.environ, {"BOLTOOLS_DEV": "1"}),  # must be ignored in release
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _offline(self):
        return mock.patch.object(tool_store_module.urllib.request, "urlopen", side_effect=OSError("offline"))

    def test_missing_fingerprint_is_refused(self):
        res = self.service._perform_install_or_update("sample", {"id": "sample", "engine_folder": "sample"})
        self.assertFalse(res["success"])
        self.assertIn("sha256", res["error"])

    def test_bundled_engine_with_wrong_fingerprint_is_refused(self):
        meta = {"id": "sample", "engine_folder": "sample", "version": "1.0.0", "sha256": WRONG_SHA}
        with self._offline():
            res = self.service._perform_install_or_update("sample", meta)
        self.assertFalse(res["success"])
        self.assertFalse(os.path.exists(os.path.join(self.service.engines_dir, "sample", "v1.0.0")))

    def test_unsigned_tools_list_is_ignored(self):
        self.service.cached_manifest = {"sequence": 5, "tools": []}
        unsigned = b'{"sequence": 99, "tools": [{"id": "evil"}]}'

        def fake_urlopen(req, timeout=None):
            if req.full_url.endswith(".sig"):
                raise OSError("no signature")
            return _FakeResponse(unsigned)

        with mock.patch.object(tool_store_module.urllib.request, "urlopen", side_effect=fake_urlopen):
            with mock.patch.object(tool_store_module.threading, "Thread") as thread_cls:
                self.service.sync_manifest_async()
                thread_cls.call_args.kwargs["target"]()
        self.assertEqual(self.service.cached_manifest["sequence"], 5)


if __name__ == "__main__":
    unittest.main()
