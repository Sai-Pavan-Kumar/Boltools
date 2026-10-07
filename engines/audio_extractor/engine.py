"""Universal Media & Audio Extractor Engine (Decoupled Process).

Extracts bit-perfect, studio-grade audio (MP3, WAV, AAC, FLAC, OGG, or Direct Stream Copy)
from any container (MP4, MKV, MOV, WebM, AVI, FLV, WMV, M4V, TS) using FFmpeg.
"""

import os
import sys
import json
import subprocess
import re


def send(data: dict):
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
    fmt_choice = options.get("format", "MP3 (320 kbps Studio Quality)")

    if not input_files:
        send({"type": "error", "message": "No media files selected."})
        return

    if not output_dir:
        output_dir = os.path.dirname(input_files[0])
    os.makedirs(output_dir, exist_ok=True)

    send({"type": "log", "message": f"Target format: {fmt_choice}"})
    send({"type": "log", "message": f"Queue: {len(input_files)} file(s) -> {output_dir}"})
    send({"type": "progress", "percent": 5.0, "status": "Initializing FFmpeg audio extraction..."})

    total = len(input_files)
    last_file = None

    try:
        for idx, in_file in enumerate(input_files):
            if not os.path.exists(in_file):
                send({"type": "log", "message": f"Skipped (not found): {in_file}"})
                continue

            base_name = os.path.splitext(os.path.basename(in_file))[0]
            in_size_mb = os.path.getsize(in_file) / (1024 * 1024)

            # Determine audio format, extension, and FFmpeg flags
            if "320 kbps" in fmt_choice:
                out_path = os.path.join(output_dir, f"{base_name}.mp3")
                audio_flags = ["-vn", "-c:a", "libmp3lame", "-b:a", "320k"]
            elif "192 kbps" in fmt_choice:
                out_path = os.path.join(output_dir, f"{base_name}.mp3")
                audio_flags = ["-vn", "-c:a", "libmp3lame", "-b:a", "192k"]
            elif "128 kbps" in fmt_choice:
                out_path = os.path.join(output_dir, f"{base_name}.mp3")
                audio_flags = ["-vn", "-c:a", "libmp3lame", "-b:a", "128k"]
            elif "WAV" in fmt_choice:
                out_path = os.path.join(output_dir, f"{base_name}.wav")
                audio_flags = ["-vn", "-c:a", "pcm_s16le"]
            elif "AAC" in fmt_choice or "M4A" in fmt_choice:
                out_path = os.path.join(output_dir, f"{base_name}.m4a")
                audio_flags = ["-vn", "-c:a", "aac", "-b:a", "256k"]
            elif "FLAC" in fmt_choice:
                out_path = os.path.join(output_dir, f"{base_name}.flac")
                audio_flags = ["-vn", "-c:a", "flac"]
            elif "OGG" in fmt_choice:
                out_path = os.path.join(output_dir, f"{base_name}.ogg")
                audio_flags = ["-vn", "-c:a", "libvorbis", "-q:a", "6"]
            elif "Direct Stream Copy" in fmt_choice:
                out_path = os.path.join(output_dir, f"{base_name}.aac")
                audio_flags = ["-vn", "-c:a", "copy"]
            else:
                out_path = os.path.join(output_dir, f"{base_name}.mp3")
                audio_flags = ["-vn", "-c:a", "libmp3lame", "-b:a", "320k"]

            send({"type": "log", "message": f"[{idx+1}/{total}] Extracting: {os.path.basename(in_file)} ({in_size_mb:.1f} MB)..."})

            cmd = ["ffmpeg", "-y", "-i", in_file, *audio_flags, out_path]

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            duration = 0.0
            base_pct = 5.0 + (idx / total) * 90.0
            slice_pct = 90.0 / total

            if proc.stderr:
                for line in proc.stderr:
                    line_str = line.strip()
                    if "Duration:" in line_str and duration == 0.0:
                        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", line_str)
                        if match:
                            h, m, s = match.groups()
                            duration = int(h) * 3600 + int(m) * 60 + float(s)

                    if "time=" in line_str and duration > 0:
                        match = re.search(r"time=\s*(\d+):(\d+):(\d+\.\d+)", line_str)
                        if match:
                            h, m, s = match.groups()
                            current = int(h) * 3600 + int(m) * 60 + float(s)
                            sub_pct = min(1.0, current / duration)
                            cur_pct = base_pct + (sub_pct * slice_pct)
                            send({
                                "type": "progress",
                                "percent": round(cur_pct, 1),
                                "status": f"Extracting [{idx+1}/{total}] ({int(sub_pct * 100)}%)..."
                            })

            proc.wait()

            if proc.returncode == 0 and os.path.exists(out_path):
                out_size_mb = os.path.getsize(out_path) / (1024 * 1024)
                send({
                    "type": "log",
                    "message": f"✓ Saved: {os.path.basename(out_path)} ({out_size_mb:.2f} MB)"
                })
                last_file = out_path
            else:
                send({
                    "type": "log",
                    "message": f"⚠ Warning: Extraction issue for {os.path.basename(in_file)} (code {proc.returncode})"
                })

            pct_after = 5.0 + ((idx + 1) / total) * 90.0
            send({"type": "progress", "percent": round(pct_after, 1), "status": f"Completed {idx+1}/{total}..."})

        send({"type": "done", "output_file": last_file or output_dir})

    except Exception as ex:
        send({"type": "error", "message": str(ex)})


if __name__ == "__main__":
    main()
