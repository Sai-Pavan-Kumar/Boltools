"""Subtitle Animation Maker Engine (FFmpeg libass-backed, Decoupled Process).

Features:
- Word-by-word viral animated captions (Hormozi Pop, Bounce, Minimal Box, Neon Glow).
- Custom font support (.ttf/.otf fonts via FFmpeg fontsdir).
- Full RGB color customization (Primary, Active Highlight, Outline, Shadow).
- Dual input mode: parses .srt/.vtt files or uses pre-edited subtitle cue payloads from UI.
- Real-time FFmpeg progress streaming and zero-crash process isolation.
"""

import os
import sys
import json
import subprocess
import re
import math
from typing import Dict, Any, List, Optional, Tuple


def send(data: dict):
    """Sends JSON line to stdout and flushes immediately for real-time IPC."""
    print(json.dumps(data), flush=True)


def hex_to_ass_color(hex_str: str, alpha: int = 0) -> str:
    """Converts a standard RGB hex color (#RRGGBB) to ASS color format &HAABBGGRR&."""
    hex_str = hex_str.strip().lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join(c * 2 for c in hex_str)
    if len(hex_str) != 6:
        hex_str = "FFFFFF"

    r = hex_str[0:2].upper()
    g = hex_str[2:4].upper()
    b = hex_str[4:6].upper()
    a = f"{alpha:02X}"
    return f"&H{a}{b}{g}{r}&"


def format_ass_time(seconds: float) -> str:
    """Formats seconds into ASS timestamp format H:MM:SS.cc."""
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def parse_timestamp_to_seconds(ts: str) -> float:
    """Parses SRT (00:00:01,234) or VTT (00:00:01.234) timestamp into seconds."""
    ts = ts.strip().replace(',', '.')
    parts = ts.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(parts[0])


def parse_srt_or_vtt(content: str) -> List[Dict[str, Any]]:
    """Parses SRT or WebVTT content into structured cues with interpolated word timings."""
    lines = content.strip().splitlines()
    cues = []
    i = 0
    cue_id = 1

    time_pattern = re.compile(r'(\d+:\d+:\d+[,\.]\d+|\d+:\d+[,\.]\d+)\s*-->\s*(\d+:\d+:\d+[,\.]\d+|\d+:\d+[,\.]\d+)')

    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith('WEBVTT') or line.startswith('NOTE'):
            i += 1
            continue

        m = time_pattern.search(line)
        if m:
            start_sec = parse_timestamp_to_seconds(m.group(1))
            end_sec = parse_timestamp_to_seconds(m.group(2))
            i += 1

            # Accumulate text until empty line or next timestamp
            text_lines = []
            while i < len(lines):
                t_line = lines[i].strip()
                if not t_line or time_pattern.search(t_line):
                    break
                text_lines.append(t_line)
                i += 1

            raw_text = ' '.join(text_lines)
            # Remove any existing HTML or ASS formatting tags
            clean_text = re.sub(r'<[^>]+>', '', raw_text)
            clean_text = re.sub(r'\{[^}]+\}', '', clean_text).strip()

            if clean_text:
                words = clean_text.split()
                w_count = len(words)
                dur = max(0.2, end_sec - start_sec)

                word_tokens = []
                for idx, w in enumerate(words):
                    w_start = start_sec + (idx / w_count) * dur
                    w_end = start_sec + ((idx + 1) / w_count) * dur
                    word_tokens.append({
                        "word": w,
                        "start": round(w_start, 2),
                        "end": round(w_end, 2)
                    })

                cues.append({
                    "id": cue_id,
                    "start": round(start_sec, 2),
                    "end": round(end_sec, 2),
                    "text": clean_text,
                    "words": word_tokens
                })
                cue_id += 1
        else:
            i += 1

    return cues


def chunk_words(words: List[Dict[str, Any]], max_per_chunk: int = 4) -> List[List[Dict[str, Any]]]:
    """Chunks word list into smaller phrases for punchy social media subtitle pacing."""
    if not words or max_per_chunk <= 0:
        return [words] if words else []

    chunks = []
    for i in range(0, len(words), max_per_chunk):
        chunks.append(words[i:i + max_per_chunk])
    return chunks


def generate_ass_script(
    cues: List[Dict[str, Any]],
    options: Dict[str, Any],
    play_res_x: int = 1920,
    play_res_y: int = 1080
) -> str:
    """Generates a complete Advanced SubStation Alpha (.ass) script with dynamic word-level animations."""
    style_preset = options.get("style", "hormozi").lower()
    font_name = options.get("font_name", "Montserrat")
    font_size = int(options.get("font_size", 54))
    primary_hex = options.get("primary_color", "#FFFFFF")
    highlight_hex = options.get("highlight_color", "#FFE600")
    outline_hex = options.get("outline_color", "#000000")
    outline_width = float(options.get("outline_width", 4.0))
    shadow_depth = float(options.get("shadow_depth", 1.5))
    position = options.get("position", "bottom").lower()
    all_caps = bool(options.get("all_caps", True))
    chunk_size = int(options.get("chunk_size", 4))

    # ASS Color formatting
    ass_primary = hex_to_ass_color(primary_hex)
    ass_highlight = hex_to_ass_color(highlight_hex)
    ass_outline = hex_to_ass_color(outline_hex)
    ass_back = "&H80000000&"  # 50% translucent black shadow/box

    # Alignment & margins (Numpad standard: 2=bottom, 5=middle, 8=top)
    if position == "top":
        alignment = 8
        margin_v = 100
    elif position == "middle":
        alignment = 5
        margin_v = 0
    else:  # default bottom
        alignment = 2
        margin_v = 110

    # Preset specific styling tweaks
    bold = -1
    border_style = 1
    if style_preset == "white_box":
        border_style = 3  # Opaque background box behind text
        ass_primary = hex_to_ass_color(primary_hex or "#000000")
        ass_back = hex_to_ass_color(outline_hex or "#FFFFFF", alpha=0)  # Solid opaque white box
        ass_outline = ass_back
        outline_width = 8.0  # Box padding in ASS
        shadow_depth = 0.0
    elif style_preset == "minimal":
        border_style = 3  # Opaque background box behind text
        ass_primary = hex_to_ass_color(primary_hex or "#FFFFFF")
        ass_back = hex_to_ass_color(outline_hex or "#0F172A", alpha=40)  # Box background
        ass_outline = ass_back
        outline_width = 6.0
        shadow_depth = 0.0
    elif style_preset == "bounce":
        border_style = 1
        outline_width = 3.5
    else:  # default hormozi
        border_style = 1
        outline_width = 4.0

    # Header section
    ass_header = f"""[Script Info]
Title: Boltools Viral Animated Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{ass_primary},{ass_highlight},{ass_outline},{ass_back},{bold},0,0,0,100,100,1.0,0,{border_style},{outline_width},{shadow_depth},{alignment},20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines = []

    for cue in cues:
        raw_words = cue.get("words", [])
        raw_text = cue.get("text", "")
        if all_caps:
            raw_text = raw_text.upper()

        start_ts = format_ass_time(cue.get("start", 0))
        end_ts = format_ass_time(cue.get("end", 0))

        # For box styles (white_box, minimal), render clean solid subtitle lines without word-by-word flashing
        if style_preset in ("white_box", "minimal"):
            ass_text = raw_text.replace("\r\n", "\\N").replace("\n", "\\N")
            dialogue_lines.append(f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{ass_text}")
            continue

        if not raw_words:
            # Fallback if no word breakdown
            dialogue_lines.append(f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{raw_text}")
            continue

        # Chunk words for short-form rhythm
        chunks = chunk_words(raw_words, max_per_chunk=chunk_size if chunk_size > 0 else len(raw_words))

        for chunk in chunks:
            if not chunk:
                continue

            # Each word inside this chunk gets its moment of active glory
            for active_idx, target_word in enumerate(chunk):
                w_start = target_word.get("start", chunk[0]["start"])
                w_end = target_word.get("end", chunk[-1]["end"])
                if w_end <= w_start:
                    w_end = w_start + 0.2

                w_start_ts = format_ass_time(w_start)
                w_end_ts = format_ass_time(w_end)

                # Assemble line with active word highlighted
                line_parts = []
                for idx, w_item in enumerate(chunk):
                    word_str = w_item["word"]
                    if all_caps:
                        word_str = word_str.upper()

                    if idx == active_idx:
                        # Active Highlight Token based on Preset
                        if style_preset == "hormozi":
                            # Punchy 114% pop scale + glowing highlight color
                            part = f"{{\\c{ass_highlight}\\fscx114\\fscy114}}{word_str}{{\\r}}"
                        elif style_preset == "bounce":
                            # Dynamic spring bounce animation tag
                            part = f"{{\\c{ass_highlight}\\t(0,100,\\fscx122\\fscy122)\\t(100,220,\\fscx100\\fscy100)}}{word_str}{{\\r}}"
                        else:
                            part = f"{{\\c{ass_highlight}}}{word_str}{{\\r}}"
                    else:
                        # Base color for inactive words
                        part = f"{{\\c{ass_primary}}}{word_str}{{\\r}}"

                    line_parts.append(part)

                full_line = " ".join(line_parts)
                dialogue_lines.append(f"Dialogue: 0,{w_start_ts},{w_end_ts},Default,,0,0,0,,{full_line}")

    return ass_header + "\n".join(dialogue_lines) + "\n"


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
        send({"type": "error", "message": "No media files provided."})
        return

    # Identify video file and optional subtitle file from inputs
    video_exts = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".flv", ".wmv", ".m4v"}
    sub_exts = {".srt", ".vtt", ".ass", ".sub"}

    video_file = None
    sub_file_from_input = None

    for f in input_files:
        ext = os.path.splitext(f)[1].lower()
        if ext in video_exts and not video_file:
            video_file = f
        elif ext in sub_exts and not sub_file_from_input:
            sub_file_from_input = f

    if not video_file:
        send({"type": "error", "message": "No video file found in selection."})
        return

    if not os.path.exists(video_file):
        send({"type": "error", "message": f"Video file not found: {video_file}"})
        return

    if not output_dir:
        output_dir = os.path.dirname(video_file)
    os.makedirs(output_dir, exist_ok=True)

    send({"type": "log", "message": f"Source video: {os.path.basename(video_file)}"})
    send({"type": "progress", "percent": 5.0, "status": "Preparing subtitle cues and styles..."})

    # Subtitles resolution: 1) options.subtitles (edited in UI), 2) input sub file, 3) error
    cues = []
    if "subtitles" in options and isinstance(options["subtitles"], list) and len(options["subtitles"]) > 0:
        send({"type": "log", "message": f"Using {len(options['subtitles'])} edited subtitle cues from Studio."})
        cues = options["subtitles"]
    elif sub_file_from_input and os.path.exists(sub_file_from_input):
        send({"type": "log", "message": f"Parsing subtitle file: {os.path.basename(sub_file_from_input)}"})
        try:
            with open(sub_file_from_input, "r", encoding="utf-8", errors="ignore") as sf:
                cues = parse_srt_or_vtt(sf.read())
        except Exception as ex:
            send({"type": "error", "message": f"Failed to parse subtitle file: {ex}"})
            return
    else:
        send({"type": "error", "message": "No subtitle content found. Please provide .srt/.vtt file or add cues in Studio."})
        return

    if not cues:
        send({"type": "error", "message": "Subtitle cue list is empty."})
        return

    # Check for custom font path
    custom_font_path = options.get("font_path", "").strip()
    custom_fonts_dir = ""
    if custom_font_path and os.path.exists(custom_font_path):
        custom_fonts_dir = os.path.dirname(custom_font_path)
        send({"type": "log", "message": f"Loaded custom font file: {os.path.basename(custom_font_path)}"})

    # Generate ASS file in output directory
    video_base = os.path.splitext(os.path.basename(video_file))[0]
    ass_file_path = os.path.join(output_dir, f"{video_base}_subtitles_temp.ass")
    out_video_path = os.path.join(output_dir, f"{video_base}_animated_subs.mp4")

    try:
        ass_content = generate_ass_script(cues, options)
        with open(ass_file_path, "w", encoding="utf-8") as f:
            f.write(ass_content)
        send({"type": "log", "message": f"Generated vector subtitle script ({len(cues)} cues)."})
    except Exception as ex:
        send({"type": "error", "message": f"Failed to generate subtitle script: {ex}"})
        return

    send({"type": "progress", "percent": 15.0, "status": "Initializing FFmpeg libass renderer..."})

    # Prepare FFmpeg ass filter argument with forward slashes and escaped colons
    escaped_ass = ass_file_path.replace("\\", "/").replace(":", "\\:")
    vf_arg = f"ass='{escaped_ass}'"
    if custom_fonts_dir:
        escaped_fonts_dir = custom_fonts_dir.replace("\\", "/").replace(":", "\\:")
        vf_arg += f":fontsdir='{escaped_fonts_dir}'"

    cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-vf", vf_arg,
        "-c:v", "libx264",
        "-preset", "faster",
        "-crf", "21",
        "-c:a", "copy",
        out_video_path
    ]

    send({"type": "log", "message": f"Encoding video frames: {os.path.basename(out_video_path)}"})

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        duration = 0.0
        for line in proc.stderr:
            line_str = line.strip()
            if "Duration:" in line_str and duration == 0.0:
                m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", line_str)
                if m:
                    h, mins, s = m.groups()
                    duration = int(h) * 3600 + int(mins) * 60 + float(s)
            if "time=" in line_str and duration > 0:
                m = re.search(r"time=\s*(\d+):(\d+):(\d+\.\d+)", line_str)
                if m:
                    h, mins, s = m.groups()
                    current = int(h) * 3600 + int(mins) * 60 + float(s)
                    pct = min(96.0, max(15.0, 15.0 + (current / duration) * 80.0))
                    send({
                        "type": "progress",
                        "percent": round(pct, 1),
                        "status": f"Rendering animated subtitles ({int(pct)}%)..."
                    })

        proc.wait()

        # Clean up temporary ASS file
        if os.path.exists(ass_file_path):
            try:
                os.remove(ass_file_path)
            except Exception:
                pass

        if proc.returncode != 0:
            send({"type": "error", "message": f"FFmpeg failed with exit code {proc.returncode}."})
            return

        if not os.path.exists(out_video_path):
            send({"type": "error", "message": "Output video file was not generated."})
            return

        out_size_mb = os.path.getsize(out_video_path) / (1024 * 1024)
        send({"type": "log", "message": f"✓ Complete: {os.path.basename(out_video_path)} ({out_size_mb:.2f} MB)"})
        send({"type": "done", "output_file": out_video_path})

    except Exception as ex:
        # Clean up temporary ASS file
        if os.path.exists(ass_file_path):
            try:
                os.remove(ass_file_path)
            except Exception:
                pass
        send({"type": "error", "message": str(ex)})


if __name__ == "__main__":
    main()
