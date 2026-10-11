"""Hello World Test Utility Engine (Boltools Test Spec).

Adheres to:
1. Python Standard Library only (zero third-party dependencies).
2. Input payload over stdin (JSON):
   - options.text: text to write to hello.txt
   - options.seconds: duration in seconds
   - options.force_error: boolean to trigger test error
3. Output stream over stdout (JSON-lines):
   - {"type": "log", "message": "..."}
   - {"type": "progress", "percent": N, "message": "..."}
   - {"type": "done", "outputs": ["<output_file>"]}
   - {"type": "error", "code": "...", "message": "..."}
4. Graceful cancellation handling and standard exit codes:
   - 0: Success
   - 1: Runtime Error
   - 2: Cancelled
   - 3: Invalid Arguments
"""

import os
import sys
import json
import time
import threading

EXIT_SUCCESS = 0
EXIT_RUNTIME_ERROR = 1
EXIT_CANCELLED = 2
EXIT_INVALID_ARGS = 3

is_cancelled = False


def emit(data: dict):
    """Writes a single JSON line to stdout and flushes immediately."""
    sys.stdout.write(json.dumps(data) + "\n")
    sys.stdout.flush()


def cancel_listener():
    global is_cancelled
    try:
        for line in sys.stdin:
            line = line.strip()
            if line:
                try:
                    msg = json.loads(line)
                    if msg.get("cmd") == "cancel":
                        is_cancelled = True
                        emit({"type": "error", "code": "CANCELLED", "message": "Operation cancelled by user."})
                        sys.exit(EXIT_CANCELLED)
                except Exception:
                    pass
    except Exception:
        pass


def main():
    global is_cancelled
    try:
        raw_input = sys.stdin.readline()
        if not raw_input:
            emit({"type": "error", "code": "ERR_NO_INPUT", "message": "No input payload received on stdin."})
            sys.exit(EXIT_INVALID_ARGS)

        payload = json.loads(raw_input)
    except Exception as e:
        emit({"type": "error", "code": "ERR_INVALID_JSON", "message": f"Failed to parse input JSON: {str(e)}"})
        sys.exit(EXIT_INVALID_ARGS)

    # Spawn cancel listener thread on remaining stdin lines
    listener = threading.Thread(target=cancel_listener, daemon=True)
    listener.start()

    options = payload.get("options", {})
    output_dir = payload.get("output_dir", os.getcwd())
    text_content = options.get("text", "Hello from Boltools Native Shell!")
    seconds = int(options.get("seconds") or options.get("duration") or 2)
    force_error = bool(options.get("force_error", False))

    emit({"type": "log", "message": f"Starting Hello Tool: duration={seconds}s, force_error={force_error}"})
    emit({"type": "progress", "percent": 5.0, "message": "Initializing test environment..."})

    # Test forced error mode
    if force_error:
        time.sleep(0.3)
        emit({"type": "error", "code": "ERR_FORCED_TEST", "message": "Forced error triggered by test parameter."})
        sys.exit(EXIT_RUNTIME_ERROR)

    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "hello.txt")

    # Step-by-step progress simulation
    steps = max(1, seconds * 5)  # 5 ticks per second
    interval = seconds / steps

    for step in range(1, steps + 1):
        if is_cancelled:
            sys.exit(EXIT_CANCELLED)
        time.sleep(interval)
        if is_cancelled:
            sys.exit(EXIT_CANCELLED)
        pct = 5.0 + (step / steps) * 90.0
        emit({"type": "progress", "percent": round(pct, 1), "message": f"Processing step {step}/{steps}..."})
        if step % 5 == 0:
            emit({"type": "log", "message": f"Elapsed: {step // 5}s of {seconds}s"})

    # Write output file
    try:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(text_content + "\n")
            f.write(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    except Exception as e:
        emit({"type": "error", "code": "ERR_WRITE_FAILED", "message": f"Failed to write output file: {str(e)}"})
        sys.exit(EXIT_RUNTIME_ERROR)

    emit({"type": "progress", "percent": 100.0, "message": "Completed successfully."})
    emit({"type": "log", "message": f"Wrote {os.path.getsize(out_file)} bytes to {out_file}"})
    emit({"type": "done", "outputs": [os.path.abspath(out_file)]})
    sys.exit(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
