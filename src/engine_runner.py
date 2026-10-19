"""Language-Agnostic Tool Engine Runner for Boltools.

Features:
- Process Isolation: Each tool execution runs in a separate worker process.
- Windows Job Object: Child process tree is assigned to a Win32 Job Object configured
  with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE so child processes terminate if the host shell dies.
- JSON-Lines Stdout Contract:
    {"type": "progress", "percent": N, "message": "..."}
    {"type": "log", "message": "..."}
    {"type": "done", "outputs": ["..."]}
    {"type": "error", "code": "...", "message": "..."}
- Clean Cancellation: Terminates the entire process tree on user abort.
- Exit Codes Documented:
    0: Success
    1: Runtime Error
    2: Cancelled / Aborted
    3: Invalid Arguments / Schema Error
"""

import os
import sys
import json
import subprocess
import threading
from typing import Dict, Any, List, Optional, Callable

# Exit code definitions
EXIT_SUCCESS = 0
EXIT_RUNTIME_ERROR = 1
EXIT_CANCELLED = 2
EXIT_INVALID_ARGS = 3

# Optional Windows Job Object setup for leak-free child process management
_HAS_WIN32_JOB = False
if sys.platform == "win32":
    try:
        import ctypes
        from ctypes import wintypes

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
                ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryLimit", ctypes.c_size_t),
                ("PeakJobMemoryLimit", ctypes.c_size_t),
            ]

        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
        JobObjectExtendedLimitInformation = 9

        _kernel32 = ctypes.windll.kernel32
        _HAS_WIN32_JOB = True
    except Exception:
        _HAS_WIN32_JOB = False


def _create_win32_job():
    """Creates a Windows Job Object configured to kill child processes on close."""
    if not _HAS_WIN32_JOB:
        return None
    try:
        job = _kernel32.CreateJobObjectW(None, None)
        if not job:
            return None
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        res = _kernel32.SetInformationJobObject(
            job,
            JobObjectExtendedLimitInformation,
            ctypes.byref(info),
            ctypes.sizeof(info)
        )
        if not res:
            _kernel32.CloseHandle(job)
            return None
        return job
    except Exception:
        return None


def _assign_process_to_job(job_handle, proc_handle):
    """Assigns a running process to a Job Object."""
    if not _HAS_WIN32_JOB or not job_handle:
        return False
    try:
        return bool(_kernel32.AssignProcessToJobObject(job_handle, proc_handle))
    except Exception:
        return False


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
        self.current_win_job = None
        self.is_cancelled = False
        # True between accepting a run and having its Popen handle, so a Cancel
        # pressed during engine startup is not silently lost.
        self.is_starting = False
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
        on_complete: Callable[[Any], None],
        on_error: Callable[[Dict[str, Any]], None]
    ):
        """Dispatches an engine process asynchronously with real-time JSON-lines output monitoring."""
        def _worker():
            with self.lock:
                # A process that already exited is a leftover from a worker that never
                # reached its cleanup; it must not block every run after it.
                if self.current_process is not None and self.current_process.poll() is not None:
                    self.current_process = None
                if self.current_process is not None or self.is_starting:
                    on_error({"code": "BUSY", "message": "Another tool operation is already running."})
                    return
                self.is_cancelled = False
                self.is_starting = True

            job_payload = {
                "tool_id": tool_id,
                "input_files": input_files,
                "options": options,
                "output_dir": output_dir
            }

            # Prepare command based on runtime
            cmd: List[str] = []
            if engine_type in ["python", "py"]:
                if getattr(sys, "frozen", False):
                    cmd = [sys.executable, "--engine-worker", executable_target]
                else:
                    cmd = [sys.executable, executable_target]
            elif engine_type in ["binary", "executable", "exe"]:
                cmd = [executable_target]
            elif engine_type == "command":
                cmd = executable_target.split()
            else:
                with self.lock:
                    self.is_starting = False
                on_error({"code": "UNSUPPORTED_ENGINE", "message": f"Unsupported engine type: {engine_type}"})
                return

            payload_json = json.dumps(job_payload)
            proc = None

            try:
                on_log(f"Starting engine for {tool_id}...")
                on_progress(5.0, "Initializing engine...")

                creation_flags = 0
                if sys.platform == "win32":
                    creation_flags = 0x08000000  # CREATE_NO_WINDOW

                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=creation_flags,
                    bufsize=1
                )

                win_job = None
                if sys.platform == "win32" and _HAS_WIN32_JOB:
                    win_job = _create_win32_job()
                    if win_job:
                        # Convert pid to handle
                        p_handle = _kernel32.OpenProcess(0x1F0FFF, False, proc.pid)
                        if p_handle:
                            _assign_process_to_job(win_job, p_handle)
                            _kernel32.CloseHandle(p_handle)

                with self.lock:
                    self.current_process = proc
                    self.current_job_id = tool_id
                    self.current_win_job = win_job
                    self.is_starting = False
                    cancelled_during_start = self.is_cancelled
                if cancelled_during_start:
                    self.cancel_active()

                # Drain stderr in parallel: an engine (or FFmpeg behind it) that fills the
                # stderr pipe while we only read stdout would block forever. Keep the tail for errors.
                stderr_tail: List[str] = []

                def _drain_stderr():
                    try:
                        for err_line in proc.stderr:
                            stderr_tail.append(err_line)
                            if len(stderr_tail) > 200:
                                del stderr_tail[:100]
                    except Exception:
                        pass

                stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
                stderr_thread.start()

                # Send single JSON-line request to stdin (keep stdin open for cancel commands)
                proc.stdin.write(payload_json + "\n")
                proc.stdin.flush()

                # Process JSON-lines on stdout
                outputs = None
                structured_error = None
                output_stats = None

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
                                status = msg.get("message") or msg.get("status", "Processing...")
                                on_progress(pct, status)
                            elif m_type == "log":
                                on_log(msg.get("message", ""))
                            elif m_type == "done":
                                outputs = msg.get("outputs") or [msg.get("output_file")]
                                output_stats = msg.get("stats")
                            elif m_type == "error":
                                structured_error = {
                                    "code": msg.get("code", "ENGINE_ERROR"),
                                    "message": msg.get("message", "Engine reported error")
                                }
                        except Exception:
                            on_log(line)
                    else:
                        on_log(line)

                proc.wait()

                # Handle cancellation explicitly
                with self.lock:
                    cancelled = self.is_cancelled

                if cancelled:
                    on_error({"code": "CANCELLED", "message": "Operation cancelled by user."})
                    return

                # Check process exit code
                if proc.returncode != EXIT_SUCCESS and not structured_error:
                    stderr_thread.join(timeout=2.0)
                    err_lines = "".join(stderr_tail[-20:]).strip()
                    structured_error = {
                        "code": f"EXIT_{proc.returncode}",
                        "message": err_lines or f"Engine exited with status code {proc.returncode}"
                    }

                if structured_error:
                    on_error(structured_error)
                else:
                    on_progress(100.0, "Complete")
                    if output_stats:
                        on_complete({"outputs": outputs or [output_dir], "stats": output_stats})
                    else:
                        on_complete(outputs or [output_dir])

            except Exception as e:
                with self.lock:
                    if self.is_cancelled:
                        on_error({"code": "CANCELLED", "message": "Operation cancelled by user."})
                        return
                on_error({"code": "PROCESS_FAILED", "message": f"Engine execution failed: {str(e)}"})
            finally:
                if proc is None:
                    with self.lock:
                        self.is_starting = False
                        self.is_cancelled = False
                    return
                try:
                    if proc.stdin and not proc.stdin.closed:
                        proc.stdin.close()
                except Exception:
                    pass
                try:
                    if proc.stdout:
                        proc.stdout.close()
                    if proc.stderr:
                        proc.stderr.close()
                except Exception:
                    pass
                with self.lock:
                    # The busy check may already have handed the slot to a newer run;
                    # only tear down state that still belongs to this worker.
                    if self.current_process is not proc:
                        return
                    if self.current_win_job and sys.platform == "win32" and _HAS_WIN32_JOB:
                        try:
                            _kernel32.CloseHandle(self.current_win_job)
                        except Exception:
                            pass
                    self.current_win_job = None
                    self.current_process = None
                    self.current_job_id = None
                    self.is_cancelled = False

        threading.Thread(target=_worker, daemon=True).start()

    def cancel_active(self) -> bool:
        """Sends {"cmd":"cancel"} on stdin, waits up to 3s, then forcefully terminates process tree."""
        with self.lock:
            if self.current_process is None:
                if self.is_starting:
                    self.is_cancelled = True
                    return True
                return False
            proc = self.current_process
            if proc.poll() is not None:
                # Engine is gone already; free the slot so the user can run again.
                self.current_process = None
                return True
            self.is_cancelled = True

        # 1. Graceful cancel via stdin
        try:
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.write('{"cmd":"cancel"}\n')
                proc.stdin.flush()
        except Exception:
            pass

        # 2. Wait up to 3.0s for engine to cleanly exit
        def _wait_and_kill():
            try:
                proc.wait(timeout=3.0)
            except Exception:
                # Force kill if not exited after 3 seconds
                try:
                    pid = proc.pid
                    if sys.platform == "win32":
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
                    else:
                        proc.kill()
                except Exception:
                    pass

        threading.Thread(target=_wait_and_kill, daemon=True).start()
        return True


# Global Singleton
engine_runner = EngineRunner()
