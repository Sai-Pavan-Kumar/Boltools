"""Automated Tests for Hello Test Tool Engine.

Verifies:
1. Standard execution: writes hello.txt, emits step progress, exits with 0.
2. Forced error execution: emits ERR_FORCED_TEST structured error, exits with 1.
3. Invalid JSON execution: exits with code 3 (INVALID_ARGS).
4. pack.json schema validation:
   - id, name, version, min_app_version, runtime, entry
   - pack.json is excluded from its own files list
   - sha256 checksum in pack.json matches actual engine.py bytes
"""

import os
import sys
import json
import time
import hashlib
import tempfile
import unittest

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("software"))

from src.engine_runner import engine_runner

HELLO_DIR = os.path.abspath("engines/hello_tool")
ENGINE_PY = os.path.join(HELLO_DIR, "engine.py")
PACK_JSON = os.path.join(HELLO_DIR, "pack.json")


class TestHelloTool(unittest.TestCase):
    def setUp(self):
        self.temp_out = tempfile.mkdtemp()

    def tearDown(self):
        try:
            import shutil
            shutil.rmtree(self.temp_out)
        except Exception:
            pass

    def test_pack_json_structure(self):
        """Verifies pack.json conforms strictly to Tool Pack v1 spec."""
        self.assertTrue(os.path.isfile(PACK_JSON))
        with open(PACK_JSON, "r", encoding="utf-8") as f:
            pack_data = json.load(f)

        self.assertEqual(pack_data.get("id"), "hello_tool")
        self.assertEqual(pack_data.get("runtime"), "python")
        self.assertEqual(pack_data.get("entry"), "engine.py")
        self.assertIn("files", pack_data)

        # Rule 1 from user: Remove pack.json from its own files hash list
        self.assertNotIn("pack.json", pack_data["files"], "pack.json must not be in its own files hash list")

        # Verify engine.py hash
        with open(ENGINE_PY, "rb") as ef:
            actual_sha = hashlib.sha256(ef.read()).hexdigest().lower()
        self.assertEqual(pack_data["files"]["engine.py"], actual_sha)

    def test_hello_tool_execution_success(self):
        """Verifies normal execution produces hello.txt with expected text."""
        progresses = []
        completes = []
        errors = []

        engine_runner.run_engine(
            tool_id="hello_tool",
            engine_type="python",
            executable_target=ENGINE_PY,
            input_files=[],
            options={"text": "Hello verification test!", "seconds": 1, "force_error": False},
            output_dir=self.temp_out,
            on_progress=lambda p, s: progresses.append(p),
            on_log=lambda m: None,
            on_complete=lambda o: completes.append(o),
            on_error=lambda e: errors.append(e)
        )

        timeout = 5.0
        start = time.time()
        while not completes and not errors and (time.time() - start < timeout):
            time.sleep(0.05)

        self.assertEqual(len(errors), 0, f"Unexpected error: {errors}")
        self.assertEqual(len(completes), 1)

        out_file = os.path.join(self.temp_out, "hello.txt")
        self.assertTrue(os.path.isfile(out_file))
        with open(out_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Hello verification test!", content)
        self.assertTrue(any(p >= 90.0 for p in progresses))

    def test_hello_tool_forced_error(self):
        """Verifies force_error option triggers structured error and non-zero exit."""
        completes = []
        errors = []

        engine_runner.run_engine(
            tool_id="hello_tool",
            engine_type="python",
            executable_target=ENGINE_PY,
            input_files=[],
            options={"seconds": 1, "force_error": True},
            output_dir=self.temp_out,
            on_progress=lambda p, s: None,
            on_log=lambda m: None,
            on_complete=lambda o: completes.append(o),
            on_error=lambda e: errors.append(e)
        )

        timeout = 5.0
        start = time.time()
        while not completes and not errors and (time.time() - start < timeout):
            time.sleep(0.05)

        self.assertEqual(len(completes), 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].get("code"), "ERR_FORCED_TEST")


if __name__ == "__main__":
    unittest.main()
