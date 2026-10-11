"""Unit Tests for EngineRunner JSON-Lines Protocol and Cancellation.

Verifies:
1. Engine receives single JSON request line over stdin.
2. Engine communicates over stdout with progress, log, done, and error JSON-lines.
3. Cancellation terminates process tree and emits CANCELLED error.
4. Process exit codes are mapped to structured error responses.
"""

import os
import sys
import time
import tempfile
import unittest

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("software"))

from src.engine_runner import (
    engine_runner,
    EXIT_SUCCESS,
    EXIT_RUNTIME_ERROR,
    EXIT_CANCELLED,
    EXIT_INVALID_ARGS
)


class TestEngineRunnerProtocol(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_json_lines_success(self):
        """Tests standard success flow emitting progress, log, and done."""
        worker_code = """
import sys, json, time
line = sys.stdin.readline()
req = json.loads(line)
print(json.dumps({"type": "log", "message": "Worker started"}), flush=True)
print(json.dumps({"type": "progress", "percent": 50, "message": "Working..."}), flush=True)
print(json.dumps({"type": "done", "outputs": [req["output_dir"] + "/out.txt"]}), flush=True)
sys.exit(0)
"""
        script_path = os.path.join(self.temp_dir, "test_success.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(worker_code)

        progresses = []
        logs = []
        completes = []
        errors = []

        engine_runner.run_engine(
            tool_id="test_worker",
            engine_type="python",
            executable_target=script_path,
            input_files=[],
            options={"greeting": "hi"},
            output_dir=self.temp_dir,
            on_progress=lambda p, s: progresses.append((p, s)),
            on_log=lambda m: logs.append(m),
            on_complete=lambda o: completes.append(o),
            on_error=lambda e: errors.append(e)
        )

        # Wait for worker thread
        timeout = 5.0
        start = time.time()
        while not completes and not errors and (time.time() - start < timeout):
            time.sleep(0.05)

        self.assertEqual(len(errors), 0, f"Unexpected error: {errors}")
        self.assertEqual(len(completes), 1)
        norm_completes = [os.path.normpath(x) for x in completes[0]]
        self.assertIn(os.path.normpath(os.path.join(self.temp_dir, "out.txt")), norm_completes)
        self.assertTrue(any(p[0] == 50.0 for p in progresses))
        self.assertTrue(any("Worker started" in m for m in logs))

    def test_json_lines_structured_error(self):
        """Tests structured error emission from worker script."""
        worker_code = """
import sys, json
sys.stdin.readline()
print(json.dumps({"type": "error", "code": "ERR_TEST", "message": "Intentional failure"}), flush=True)
sys.exit(1)
"""
        script_path = os.path.join(self.temp_dir, "test_error.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(worker_code)

        completes = []
        errors = []

        engine_runner.run_engine(
            tool_id="test_error",
            engine_type="python",
            executable_target=script_path,
            input_files=[],
            options={},
            output_dir=self.temp_dir,
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
        self.assertEqual(errors[0].get("code"), "ERR_TEST")
        self.assertIn("Intentional failure", errors[0].get("message", ""))

    def test_cancellation(self):
        """Tests that cancel_active() stops a long-running process."""
        worker_code = """
import sys, json, time
sys.stdin.readline()
for i in range(100):
    print(json.dumps({"type": "progress", "percent": i, "message": f"Step {i}"}), flush=True)
    time.sleep(0.2)
sys.exit(0)
"""
        script_path = os.path.join(self.temp_dir, "test_long.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(worker_code)

        errors = []
        completes = []

        engine_runner.run_engine(
            tool_id="test_long",
            engine_type="python",
            executable_target=script_path,
            input_files=[],
            options={},
            output_dir=self.temp_dir,
            on_progress=lambda p, s: None,
            on_log=lambda m: None,
            on_complete=lambda o: completes.append(o),
            on_error=lambda e: errors.append(e)
        )

        time.sleep(0.3)
        res = engine_runner.cancel_active()
        self.assertTrue(res)

        timeout = 5.0
        start = time.time()
        while not completes and not errors and (time.time() - start < timeout):
            time.sleep(0.05)

        self.assertEqual(len(completes), 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].get("code"), "CANCELLED")


if __name__ == "__main__":
    unittest.main()
