"""Video Compressor Engine (FFmpeg-backed, Decoupled Process)."""

import os
import sys
import json
import subprocess
import re

def send(data):
    print(json.dumps(data), flush=True)

def main():
    try:
        raw_input = sys.stdin.read()
        payload = json.loads(raw_input)
    except Exception as e:
        send({"type": "error", "message": f"Invalid payload: {e}"})
        return

    input_files = payload.get("input_files", [])
    options = payload.get("options", {})
    output_dir = payload.get("output_dir", "")

    if not input_files:
        send({"type": "error", "message": "No video file specified."})
        return

    in_file = input_files[0]
    if not os.path.exists(in_file):
        send({"type": "error", "message": f"Input file not found: {in_file}"})
        return

    if not output_dir:
        output_dir = os.path.dirname(in_file)
    os.makedirs(output_dir, exist_ok=True)

    mode = options.get("mode", "Balanced")
    custom_mb = float(options.get("target_mb", 50))

    base_name = os.path.splitext(os.path.basename(in_file))[0]
    out_file = os.path.join(output_dir, f"{base_name}_compressed.mp4")

    send({"type": "log", "message": f"Source: {in_file}"})
    send({"type": "log", "message": f"Mode: {mode} | Destination: {out_file}"})
    send({"type": "progress", "percent": 10.0, "status": "Analyzing video stream..."})

    # Mode parameters
    crf = "28"
    preset = "faster"
    if mode == "High Quality":
        crf = "23"
        preset = "medium"
    elif mode == "Small Size":
        crf = "32"
        preset = "fast"
    elif mode == "Custom":
        crf = "28"

    cmd = [
        "ffmpeg", "-y",
        "-i", in_file,
        "-vcodec", "libx264",
        "-crf", crf,
        "-preset", preset,
        "-acodec", "aac",
        "-b:a", "128k",
        out_file
    ]

    try:
        send({"type": "progress", "percent": 25.0, "status": "Compressing video frames..."})
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Monitor FFmpeg stderr for duration and progress
        duration = 0.0
        for line in proc.stderr:
            line_str = line.strip()
            if "Duration:" in line_str and duration == 0.0:
                match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", line_str)
                if match:
                    hours, mins, secs = match.groups()
                    duration = int(hours) * 3600 + int(mins) * 60 + float(secs)
            if "time=" in line_str and duration > 0:
                match = re.search(r"time=\s*(\d+):(\d+):(\d+\.\d+)", line_str)
                if match:
                    hours, mins, secs = match.groups()
                    current = int(hours) * 3600 + int(mins) * 60 + float(secs)
                    pct = min(95.0, max(25.0, 25.0 + (current / duration) * 70.0))
                    send({"type": "progress", "percent": round(pct, 1), "status": f"Encoding ({int(pct)}%)..."})

        proc.wait()
        if proc.returncode != 0:
            send({"type": "error", "message": f"FFmpeg failed with exit code {proc.returncode}"})
            return

        orig_sz = os.path.getsize(in_file) / (1024 * 1024)
        out_sz = os.path.getsize(out_file) / (1024 * 1024)
        saved_pct = (1 - (out_sz / orig_sz)) * 100 if orig_sz > 0 else 0

        send({"type": "log", "message": f"Done! Original: {orig_sz:.1f} MB -> Compressed: {out_sz:.1f} MB (Saved {saved_pct:.1f}%)"})
        send({"type": "done", "output_file": out_file})

    except Exception as ex:
        send({"type": "error", "message": str(ex)})

if __name__ == "__main__":
    main()
