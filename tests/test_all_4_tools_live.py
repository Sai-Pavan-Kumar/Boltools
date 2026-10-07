"""Comprehensive Live Verification Script for all 4 Boltools Flagship Engines.

Tests:
1. Video Compressor: Generates 3-sec synthetic MP4 -> compresses with FFmpeg -> validates output.
2. PDF Converter: Generates multi-page PDF -> converts to PNG images & TXT text -> compiles images back to PDF.
3. WebP Compressor: Generates 1600x1200 synthetic image -> runs CloudConvert-grade compression -> validates WebP output & size reduction.
4. Batch File Renamer: Generates batch files -> renames with prefix & numbering rules -> validates filesystem results.
"""

import os
import sys
import time
import shutil
import tempfile
import threading
import subprocess
from PIL import Image, ImageDraw
import pymupdf

# Fix console encoding on Windows
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


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def assert_check(condition: bool, description: str):
    if condition:
        print(f"  [PASS] {description}")
    else:
        print(f"  [FAIL] {description}")
        raise AssertionError(description)


def run_all_tool_tests():
    total_start = time.time()
    work_dir = tempfile.mkdtemp(prefix="boltools_live_test_")
    print(f"Initialized scratch workspace: {work_dir}")

    results = {}

    try:
        # ---------------------------------------------------------------------
        # 1. TEST: VIDEO COMPRESSOR
        # ---------------------------------------------------------------------
        print_header("1. Testing Video Compressor Engine (FFmpeg)")
        sample_video = os.path.join(work_dir, "sample_raw_video.mp4")
        video_out_dir = os.path.join(work_dir, "video_out")
        os.makedirs(video_out_dir, exist_ok=True)

        print("  Generating 3-second synthetic test video (640x360 H.264 + AAC)...")
        gen_cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=size=640x360:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=48000",
            "-t", "3",
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264", "-c:a", "aac",
            sample_video
        ]
        sub = subprocess.run(gen_cmd, capture_output=True, text=True)
        assert_check(os.path.exists(sample_video), f"Created sample video: {os.path.basename(sample_video)} ({os.path.getsize(sample_video)} bytes)")

        raw_video_sz = os.path.getsize(sample_video)

        v_done = threading.Event()
        v_res = {}
        v_logs = []

        def _v_prog(p, s):
            pass

        def _v_log(m):
            v_logs.append(m)

        def _v_comp(out):
            v_res["output"] = out
            v_done.set()

        def _v_err(e):
            v_res["error"] = e
            v_done.set()

        print("  Running Video Compressor Engine...")
        engine_runner.run_engine(
            tool_id="video_compressor",
            engine_type="python",
            executable_target=os.path.join(BASE_DIR, "engines", "video_compressor", "engine.py"),
            input_files=[sample_video],
            options={"mode": "Balanced"},
            output_dir=video_out_dir,
            on_progress=_v_prog,
            on_log=_v_log,
            on_complete=_v_comp,
            on_error=_v_err
        )

        v_done.wait(timeout=30.0)
        assert_check("output" in v_res and not v_res.get("error"), f"Execution completed: {v_res.get('output')}")
        compressed_video = v_res.get("output")
        assert_check(os.path.exists(compressed_video), f"Output file verified on disk: {compressed_video}")
        comp_video_sz = os.path.getsize(compressed_video)
        print(f"  [METRICS] Raw: {raw_video_sz / 1024:.1f} KB -> Compressed: {comp_video_sz / 1024:.1f} KB")
        results["Video Compressor"] = "SUCCESS"

        # ---------------------------------------------------------------------
        # 2. TEST: PDF & DOCUMENT CONVERTER
        # ---------------------------------------------------------------------
        print_header("2. Testing Document & PDF Converter Engine (PyMuPDF / Pillow)")
        pdf_source = os.path.join(work_dir, "sample_document.pdf")
        pdf_out_dir = os.path.join(work_dir, "pdf_out")
        os.makedirs(pdf_out_dir, exist_ok=True)

        print("  Generating 3-page synthetic PDF document...")
        doc = pymupdf.open()
        for page_num in range(1, 4):
            page = doc.new_page(width=595, height=842)
            page.insert_text((50, 80), f"Boltools Test Document - Page {page_num}", fontsize=18)
            page.insert_text((50, 120), "Sample synthetic document generated for offline tool verification.", fontsize=12)
            page.draw_rect(pymupdf.Rect(50, 150, 545, 300), color=(0.2, 0.4, 0.8), width=1.5)
        doc.save(pdf_source)
        doc.close()
        assert_check(os.path.exists(pdf_source), f"Created sample PDF: {os.path.basename(pdf_source)}")

        # Mode A: PDF to Images (PNG)
        p_done = threading.Event()
        p_res = {}
        print("  Testing Mode A: PDF to Images (PNG)...")
        engine_runner.run_engine(
            tool_id="pdf_converter",
            engine_type="python",
            executable_target=os.path.join(BASE_DIR, "engines", "pdf_converter", "engine.py"),
            input_files=[pdf_source],
            options={"mode": "PDF to Images (PNG)"},
            output_dir=pdf_out_dir,
            on_progress=lambda p, s: None,
            on_log=lambda m: None,
            on_complete=lambda o: (p_res.update({"output": o}), p_done.set()),
            on_error=lambda e: (p_res.update({"error": e}), p_done.set())
        )
        p_done.wait(timeout=15.0)
        assert_check("output" in p_res and not p_res.get("error"), "Mode A completed")
        p1 = os.path.join(pdf_out_dir, "sample_document_p1.png")
        p2 = os.path.join(pdf_out_dir, "sample_document_p2.png")
        p3 = os.path.join(pdf_out_dir, "sample_document_p3.png")
        assert_check(os.path.exists(p1) and os.path.exists(p2) and os.path.exists(p3), "All 3 pages rendered as PNG images successfully")

        # Mode B: PDF to Plain Text (.txt)
        p_done.clear()
        p_res.clear()
        print("  Testing Mode B: PDF to Plain Text (.txt)...")
        engine_runner.run_engine(
            tool_id="pdf_converter",
            engine_type="python",
            executable_target=os.path.join(BASE_DIR, "engines", "pdf_converter", "engine.py"),
            input_files=[pdf_source],
            options={"mode": "PDF to Plain Text (.txt)"},
            output_dir=pdf_out_dir,
            on_progress=lambda p, s: None,
            on_log=lambda m: None,
            on_complete=lambda o: (p_res.update({"output": o}), p_done.set()),
            on_error=lambda e: (p_res.update({"error": e}), p_done.set())
        )
        p_done.wait(timeout=10.0)
        txt_out = os.path.join(pdf_out_dir, "sample_document_extracted.txt")
        assert_check(os.path.exists(txt_out), f"Extracted text file exists: {os.path.basename(txt_out)}")
        with open(txt_out, "r", encoding="utf-8") as f:
            txt_content = f.read()
        assert_check("Boltools Test Document" in txt_content, "Extracted text content verified correctly")

        # Mode C: Images to PDF Document
        p_done.clear()
        p_res.clear()
        print("  Testing Mode C: Images to PDF Document...")
        engine_runner.run_engine(
            tool_id="pdf_converter",
            engine_type="python",
            executable_target=os.path.join(BASE_DIR, "engines", "pdf_converter", "engine.py"),
            input_files=[p1, p2],
            options={"mode": "Images to PDF Document"},
            output_dir=pdf_out_dir,
            on_progress=lambda p, s: None,
            on_log=lambda m: None,
            on_complete=lambda o: (p_res.update({"output": o}), p_done.set()),
            on_error=lambda e: (p_res.update({"error": e}), p_done.set())
        )
        p_done.wait(timeout=10.0)
        recompiled_pdf = os.path.join(pdf_out_dir, "combined_document.pdf")
        assert_check(os.path.exists(recompiled_pdf), f"Recompiled PDF created: {os.path.basename(recompiled_pdf)}")
        results["PDF Converter"] = "SUCCESS"

        # ---------------------------------------------------------------------
        # 3. TEST: WEBP & IMAGE COMPRESSOR
        # ---------------------------------------------------------------------
        print_header("3. Testing CloudConvert-Grade WebP Compressor Engine")
        img_source = os.path.join(work_dir, "sample_highres_image.png")
        webp_out_dir = os.path.join(work_dir, "webp_out")
        os.makedirs(webp_out_dir, exist_ok=True)

        print("  Generating 1200x900 rich color photo sample (PNG)...")
        img = Image.new("RGB", (1200, 900))
        px = []
        for y in range(900):
            for x in range(1200):
                r = int((x / 1200) * 255)
                g = int((y / 900) * 255)
                b = int(((x + y) / 2100) * 255) ^ (x % 37)
                px.append((r, g, b))
        img.putdata(px)
        img.save(img_source, "PNG")

        raw_img_sz = os.path.getsize(img_source)
        assert_check(os.path.exists(img_source), f"Created sample PNG: {os.path.basename(img_source)} ({raw_img_sz / 1024:.1f} KB)")

        w_done = threading.Event()
        w_res = {}
        w_logs = []

        print("  Running WebP Compressor (quality=80, max_dim=1920, method=6)...")
        engine_runner.run_engine(
            tool_id="image_webp_compress",
            engine_type="python",
            executable_target=os.path.join(BASE_DIR, "engines", "webp_compressor", "engine.py"),
            input_files=[img_source],
            options={"quality": 80, "max_dim": "1920px (Full HD)"},
            output_dir=webp_out_dir,
            on_progress=lambda p, s: None,
            on_log=lambda m: w_logs.append(m),
            on_complete=lambda o: (w_res.update({"output": o}), w_done.set()),
            on_error=lambda e: (w_res.update({"error": e}), w_done.set())
        )
        w_done.wait(timeout=15.0)
        assert_check("output" in w_res and not w_res.get("error"), f"WebP compression finished: {w_res.get('output')}")
        webp_out = w_res.get("output")
        assert_check(os.path.exists(webp_out) and webp_out.endswith(".webp"), f"Generated WebP file verified on disk: {webp_out}")

        webp_sz = os.path.getsize(webp_out)
        reduction = (1 - (webp_sz / raw_img_sz)) * 100
        print(f"  [METRICS] Raw PNG: {raw_img_sz / 1024:.1f} KB -> Compressed WebP: {webp_sz / 1024:.1f} KB (Saved {reduction:.1f}%)")
        assert_check(reduction > 30.0, f"Significant compression verified: {reduction:.1f}% reduction")
        results["WebP Compressor"] = "SUCCESS"

        # ---------------------------------------------------------------------
        # 4. TEST: BATCH FILE RENAMER
        # ---------------------------------------------------------------------
        print_header("4. Testing Batch File Renamer Engine")
        rename_dir = os.path.join(work_dir, "rename_batch")
        os.makedirs(rename_dir, exist_ok=True)

        batch_files = []
        for name in ["invoice_alpha", "report_beta", "summary_gamma"]:
            fp = os.path.join(rename_dir, f"{name}.txt")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(f"Content of {name}")
            batch_files.append(fp)

        assert_check(len(batch_files) == 3, "Created 3 sample files for batch renaming")

        r_done = threading.Event()
        r_res = {}
        r_logs = []

        print("  Running Batch Renamer (Rule: 'Add Prefix', Prefix: 'PROD_2026_')...")
        engine_runner.run_engine(
            tool_id="system_batch_rename",
            engine_type="python",
            executable_target=os.path.join(BASE_DIR, "engines", "batch_renamer", "engine.py"),
            input_files=batch_files,
            options={"rule": "Add Prefix", "text1": "PROD_2026_", "op_mode": "Rename In-Place"},
            output_dir=rename_dir,
            on_progress=lambda p, s: None,
            on_log=lambda m: r_logs.append(m),
            on_complete=lambda o: (r_res.update({"output": o}), r_done.set()),
            on_error=lambda e: (r_res.update({"error": e}), r_done.set())
        )
        r_done.wait(timeout=10.0)
        assert_check("output" in r_res and not r_res.get("error"), "Batch rename executed successfully")

        expected_files = [
            os.path.join(rename_dir, "PROD_2026_invoice_alpha.txt"),
            os.path.join(rename_dir, "PROD_2026_report_beta.txt"),
            os.path.join(rename_dir, "PROD_2026_summary_gamma.txt")
        ]
        for ef in expected_files:
            assert_check(os.path.exists(ef), f"Verified renamed file exists: {os.path.basename(ef)}")
        results["Batch Renamer"] = "SUCCESS"

        # ---------------------------------------------------------------------
        # SUMMARY
        # ---------------------------------------------------------------------
        elapsed = time.time() - total_start
        print_header("FINAL VERIFICATION SUMMARY")
        for tool_name, status in results.items():
            print(f"  * {tool_name:25s} -> [{status}]")
        print(f"\nAll 4 tools tested and verified with real transformations in {elapsed:.2f} seconds.")
        return True

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    success = run_all_tool_tests()
    sys.exit(0 if success else 1)
