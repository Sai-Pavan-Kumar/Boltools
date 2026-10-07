"""Language-Agnostic Tool Engine Runner for Boltools.

Features:
- Process Isolation: Each tool execution runs in a separate worker process.
- Multi-Language Support: Supports Python scripts, compiled binaries (.exe in Rust/Go/C++), and system commands (FFmpeg).
- Real-Time Streaming: Streams progress percentage, status updates, and logs over stdout.
- Clean Cancellation: Terminates the entire process tree on user abort.
- Zero Shared Memory: Engine crashes never compromise the desktop shell.
"""

import os
import sys
import json
import subprocess
import threading
import time
from typing import Dict, Any, List, Optional, Callable


class EngineRunner:
    """Manages asynchronous execution of decoupled tool engines."""

    def __init__(self, engines_dir: Optional[str] = None):
        if getattr(sys, "frozen", False):
            base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.engines_dir = engines_dir or os.path.join(base_dir, "engines")
        os.makedirs(self.engines_dir, exist_ok=True)

        self.current_process: Optional[subprocess.Popen] = None
        self.current_job_id: Optional[str] = None
        self.lock = threading.Lock()

    def run_engine(
        self,
        tool_id: str,
        engine_type: str,
        executable_target: str,
        input_files: List[str],
        options: Dict[str, Any],
        output_dir: str,
        on_progress: Callable[[float, str], None],
        on_log: Callable[[str], None],
        on_complete: Callable[[str], None],
        on_error: Callable[[str], None]
    ):
        """Dispatches an engine process asynchronously with real-time output monitoring."""
        def _worker():
            with self.lock:
                if self.current_process is not None:
                    on_error("Another tool operation is already running.")
                    return

            job_payload = {
                "tool_id": tool_id,
                "input_files": input_files,
                "options": options,
                "output_dir": output_dir
            }

            # Prepare command based on engine type
            cmd: List[str] = []
            if engine_type == "python":
                if getattr(sys, "frozen", False):
                    cmd = [sys.executable, "--engine-worker", executable_target]
                else:
                    cmd = [sys.executable, executable_target]
            elif engine_type in ["binary", "executable"]:
                cmd = [executable_target]
            elif engine_type == "command":
                cmd = executable_target.split()
            else:
                on_error(f"Unsupported engine type: {engine_type}")
                return

            payload_json = json.dumps(job_payload)

            try:
                on_log(f"Starting engine for {tool_id}...")
                on_progress(5.0, "Initializing engine...")

                # Launch process with piped stdout/stderr
                # Creationflag 0x08000000 (CREATE_NO_WINDOW) hides console on Windows
                creation_flags = 0x08000000 if sys.platform == "win32" else 0

                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=creation_flags,
                    bufsize=1
                )

                with self.lock:
                    self.current_process = proc
                    self.current_job_id = tool_id

                # Send payload JSON over stdin
                proc.stdin.write(payload_json + "\n")
                proc.stdin.flush()
                proc.stdin.close()

                # Read output in real time
                output_file = None
                error_msg = None

                for line in proc.stdout:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("{") and line.endswith("}"):
                        try:
                            msg = json.loads(line)
                            m_type = msg.get("type")
                            if m_type == "progress":
                                pct = float(msg.get("percent", 0.0))
                                status = msg.get("status", "Processing...")
                                on_progress(pct, status)
                            elif m_type == "log":
                                on_log(msg.get("message", ""))
                            elif m_type == "done":
                                output_file = msg.get("output_file")
                            elif m_type == "error":
                                error_msg = msg.get("message", "Engine reported error")
                        except Exception:
                            on_log(line)
                    else:
                        on_log(line)

                proc.wait()

                # Check stderr if returncode != 0
                if proc.returncode != 0 and not error_msg:
                    err_lines = proc.stderr.read()
                    error_msg = err_lines.strip() or f"Process exited with code {proc.returncode}"

                if error_msg:
                    on_error(error_msg)
                else:
                    on_progress(100.0, "Complete")
                    on_complete(output_file or output_dir)

            except Exception as e:
                on_error(f"Engine execution failed: {str(e)}")
            finally:
                with self.lock:
                    self.current_process = None
                    self.current_job_id = None

        threading.Thread(target=_worker, daemon=True).start()

    def cancel_active(self) -> bool:
        """Forcefully terminates the active engine process tree."""
        with self.lock:
            if self.current_process is None:
                return False
            try:
                pid = self.current_process.pid
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
                else:
                    self.current_process.kill()
                self.current_process = None
                self.current_job_id = None
                return True
            except Exception:
                return False


# Global Singleton
engine_runner = EngineRunner()
