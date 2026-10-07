"""Live Automated Test Suite for Tool 01: Universal Media & Audio Extractor."""

import os
import sys
import time
import shutil
import tempfile
import threading
import subprocess

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.engine_runner import engine_runner
from src.desktop_bridge import desktop_bridge


def assert_check(condition: bool, msg: str):
    if condition:
        print(f"  [PASS] {msg}")
    else:
        print(f"  [FAIL] {msg}")
        raise AssertionError(msg)


def run_tests():
    start = time.time()
    work_dir = tempfile.mkdtemp(prefix="boltools_audio_test_")
    print(f"Test scratch directory: {work_dir}")

    try:
        # Step 1: Generate synthetic video with audio stream
        sample_video = os.path.join(work_dir, "test_clip.mp4")
        print("\n[STEP 1] Generating synthetic video test clip (640x360 H.264 + 48kHz AAC)...")
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=size=640x360:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=880:sample_rate=48000",
            "-t", "3",
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
            sample_video
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert_check(os.path.exists(sample_video), f"Created sample video: {os.path.getsize(sample_video)} bytes")

        engine_path = os.path.join(BASE_DIR, "engines", "audio_extractor", "engine.py")
        assert_check(os.path.exists(engine_path), f"Audio extractor engine exists: {engine_path}")

        # Step 2: Test formats
        test_formats = [
            ("MP3 (320 kbps Studio Quality)", ".mp3"),
            ("WAV (Lossless 16-bit PCM)", ".wav"),
            ("AAC (High-Efficiency M4A)", ".m4a"),
            ("FLAC (Lossless Master)", ".flac"),
            ("Direct Stream Copy (Ultra-Fast 1-Sec)", ".aac")
        ]

        for fmt_label, expected_ext in test_formats:
            print(f"\n[STEP 2] Testing extraction format: '{fmt_label}'...")
            out_dir = os.path.join(work_dir, f"out_{expected_ext.strip('.')}")
            os.makedirs(out_dir, exist_ok=True)

            done_evt = threading.Event()
            result_bag = {}
            logs_bag = []

            def _on_prog(p, s):
                pass

            def _on_log(m):
                logs_bag.append(m)

            def _on_comp(out):
                result_bag["output"] = out
                done_evt.set()

            def _on_err(e):
                result_bag["error"] = e
                done_evt.set()

            engine_runner.run_engine(
                tool_id="media_audio_extractor",
                engine_type="python",
                executable_target=engine_path,
                input_files=[sample_video],
                options={"format": fmt_label},
                output_dir=out_dir,
                on_progress=_on_prog,
                on_log=_on_log,
                on_complete=_on_comp,
                on_error=_on_err
            )

            done_evt.wait(timeout=15.0)
            assert_check("output" in result_bag and not result_bag.get("error"), f"Engine completed for {fmt_label}")
            out_file = result_bag.get("output")
            assert_check(os.path.exists(out_file), f"Output file exists on disk: {out_file}")
            assert_check(out_file.endswith(expected_ext), f"File has expected extension {expected_ext}")
            sz_kb = os.path.getsize(out_file) / 1024
            assert_check(sz_kb > 2.0, f"File size is valid audio stream: {sz_kb:.1f} KB")

        # Step 3: Verify Desktop Bridge Manifest
        print("\n[STEP 3] Verifying Desktop Bridge Manifest contains 'media_audio_extractor'...")
        initial_data = desktop_bridge.get_initial_data()
        tool_ids = [t["id"] for t in initial_data["tools"]]
        assert_check("media_audio_extractor" in tool_ids, f"'media_audio_extractor' present in bridge tools: {tool_ids}")

        elapsed = time.time() - start
        print(f"\n{'='*70}\n>>> UNIVERSAL MEDIA & AUDIO EXTRACTOR FULLY VERIFIED IN {elapsed:.2f}s <<<\n{'='*70}\n")
        return True

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
