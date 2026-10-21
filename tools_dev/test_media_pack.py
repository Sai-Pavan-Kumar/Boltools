"""Media pack download: only a pack that matches the signed list and its own pack.json is ever used."""

import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import zipfile
from unittest import mock

SOFTWARE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SOFTWARE_DIR)

from src.core import media_pack

FILES = {"ffmpeg.exe": b"MZ fake engine", "avcodec-63.dll": b"fake codec" * 50, "LICENSE.txt": b"GPL"}


def make_pack(version="9.0.2", files=None, listed=None, extra=None):
    files = dict(FILES if files is None else files)
    listed = {n: hashlib.sha256(d).hexdigest() for n, d in (listed or files).items()}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("pack.json", json.dumps({"version": version, "files": listed}))
        for name, data in {**files, **(extra or {})}.items():
            zf.writestr(name, data)
    return buf.getvalue()


def spec_for(data, version="9.0.2", **overrides):
    spec = {"version": version, "url": "https://example.test/media-pack.zip",
            "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}
    spec.update(overrides)
    return spec


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class TestMediaPack(unittest.TestCase):

    def setUp(self):
        self.media_dir = tempfile.mkdtemp(prefix="media_pack_")
        self.addCleanup(shutil.rmtree, self.media_dir, True)
        path_patch = mock.patch.dict(os.environ, {"PATH": r"C:\Windows", "BOLTOOLS_DEV": "0"})
        path_patch.start()
        self.addCleanup(path_patch.stop)
        self.cancel = threading.Event()

    def _install(self, data, spec):
        with mock.patch.object(media_pack.urllib.request, "urlopen", return_value=_Response(data)):
            return media_pack.install(spec, lambda *_: None, self.cancel, self.media_dir)

    def _assert_nothing_installed(self):
        self.assertIsNone(media_pack.installed_version(self.media_dir))
        self.assertEqual([n for n in os.listdir(self.media_dir) if n.startswith(".")], [])

    def test_good_pack_installs_and_goes_first_on_path(self):
        data = make_pack()
        self.assertEqual(self._install(data, spec_for(data)), "9.0.2")
        folder = media_pack.active_dir(self.media_dir)
        self.assertEqual(os.environ["PATH"].split(os.pathsep)[0], folder)
        for name, content in FILES.items():
            with open(os.path.join(folder, name), "rb") as f:
                self.assertEqual(f.read(), content)

    def test_wrong_download_fingerprint_is_refused(self):
        data = make_pack()
        with self.assertRaises(media_pack.PackError):
            self._install(data, spec_for(data, sha256="0" * 64))
        self._assert_nothing_installed()

    def test_file_not_matching_pack_json_is_refused(self):
        data = make_pack(listed={**FILES, "ffmpeg.exe": b"something else"})
        with self.assertRaises(media_pack.PackError):
            self._install(data, spec_for(data))
        self._assert_nothing_installed()

    def test_unlisted_extra_file_is_refused(self):
        data = make_pack(extra={"evil.dll": b"x"})
        with self.assertRaises(media_pack.PackError):
            self._install(data, spec_for(data))
        self._assert_nothing_installed()

    def test_version_mismatch_with_tools_list_is_refused(self):
        data = make_pack(version="8.0.0")
        with self.assertRaises(media_pack.PackError):
            self._install(data, spec_for(data, version="9.0.2"))
        self._assert_nothing_installed()

    def test_download_bigger_than_listed_is_stopped(self):
        data = make_pack()
        with self.assertRaises(media_pack.PackError):
            self._install(data, spec_for(data, size_bytes=len(data) - 1))
        self._assert_nothing_installed()

    def test_cancel_leaves_nothing_behind(self):
        data = make_pack()
        self.cancel.set()
        with self.assertRaises(media_pack.PackError):
            self._install(data, spec_for(data))
        self._assert_nothing_installed()

    def test_missing_or_unsafe_list_entry_is_refused(self):
        data = make_pack()
        local = spec_for(data, url="http://127.0.0.1:8000/p.zip")
        for bad in (None, spec_for(data, url="http://example.test/p.zip"), spec_for(data, version="../x"), local):
            with self.assertRaises(media_pack.PackError):
                self._install(data, bad)
        self._assert_nothing_installed()

    def test_pointer_to_folder_without_engine_counts_as_not_installed(self):
        os.makedirs(os.path.join(self.media_dir, "9.0.2"))
        with open(os.path.join(self.media_dir, "current.json"), "w") as f:
            json.dump({"version": "9.0.2"}, f)
        self.assertIsNone(media_pack.active_dir(self.media_dir))
        self.assertFalse(media_pack.activate(self.media_dir))


if __name__ == "__main__":
    unittest.main()
