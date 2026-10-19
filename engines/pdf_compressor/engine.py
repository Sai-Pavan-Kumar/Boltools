"""PDF Compressor Engine: shrink the pictures, never the text.

Text, vector drawings and fonts stay exactly as they are (sharp at any zoom).
Only embedded images are touched: downscaled to what the screen or printer can
show, then re-encoded as JPEG when that is actually smaller. Built on pikepdf
(MPL-2.0) and Pillow, with no AGPL code.

Options:
  preset    "smallest" | "balanced" (default) | "best" | "lossless"
            (old labels like "72 DPI", "150 DPI (Balanced)", "200 DPI" still work)
  target_kb N -> walk down the presets until the file fits under N KB

A result is never bigger than the original, and a locked or broken file is
reported by name without stopping the rest of the batch.
"""

import json
import os
import shutil
import sys
import tempfile
from io import BytesIO

import pikepdf
from PIL import Image

# (longest image side in px, JPEG quality); ~1600 px fills an A4 page at ~190 DPI.
PRESETS = {
    "best": (2400, 82),
    "balanced": (1600, 70),
    "smallest": (1100, 55),
    "tiny": (800, 42),
}
TARGET_LADDER = ["balanced", "smallest", "tiny"]
SKIP_IMAGE_BYTES = 12 * 1024
UNSAFE_FILTERS = {"/JBIG2Decode", "/CCITTFaxDecode", "/JPXDecode"}


def send(data):
    print(json.dumps(data), flush=True)


def preset_from(label):
    text = str(label or "").lower()
    if "lossless" in text:
        return "lossless"
    if "72" in text or "smallest" in text or "extreme" in text:
        return "smallest"
    if "200" in text or "best" in text or "high" in text:
        return "best"
    return "balanced"


def filters_of(obj):
    raw = obj.get("/Filter")
    if raw is None:
        return set()
    return {str(f) for f in raw} if isinstance(raw, pikepdf.Array) else {str(raw)}


def shrink_image(obj, max_side, quality):
    """Re-encode one image XObject in place when it gets smaller. Returns bytes saved."""
    if obj.get("/ImageMask") or obj.get("/SMask") is not None or filters_of(obj) & UNSAFE_FILTERS:
        return 0
    original_size = len(obj.read_raw_bytes())
    if original_size < SKIP_IMAGE_BYTES:
        return 0
    try:
        pil = pikepdf.PdfImage(obj).as_pil_image()
    except Exception:
        return 0  # exotic colour spaces: leaving them alone is safer than guessing
    if pil.mode not in ("RGB", "L"):
        if pil.mode == "CMYK":
            return 0  # inverted-CMYK JPEGs render wrongly after conversion
        pil = pil.convert("RGB")
    if max(pil.size) > max_side:
        pil.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    buffer = BytesIO()
    pil.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True)
    data = buffer.getvalue()
    if len(data) >= original_size:
        return 0
    obj.write(data, filter=pikepdf.Name.DCTDecode)
    obj.Width, obj.Height = pil.size
    obj.ColorSpace = pikepdf.Name.DeviceGray if pil.mode == "L" else pikepdf.Name.DeviceRGB
    obj.BitsPerComponent = 8
    for key in ("/DecodeParms", "/Decode"):
        if key in obj:
            del obj[key]
    return original_size - len(data)


def compress_with(src, dst, preset):
    with pikepdf.open(src) as pdf:
        if preset != "lossless":
            max_side, quality = PRESETS[preset]
            seen = set()
            for page in pdf.pages:
                for _, image in page.get_images().items():
                    if image.objgen in seen:
                        continue
                    seen.add(image.objgen)
                    shrink_image(image, max_side, quality)
        pdf.remove_unreferenced_resources()
        pdf.save(dst, compress_streams=True, recompress_flate=True,
                 object_stream_mode=pikepdf.ObjectStreamMode.generate)
    return os.path.getsize(dst)


def compress_file(src, dst, preset, target_kb):
    """Writes the best result to dst and returns its size; falls back to the original bytes."""
    original = os.path.getsize(src)
    ladder = TARGET_LADDER if target_kb else [preset]
    best_size, work_dir = original, tempfile.mkdtemp(prefix="boltools_pdf_")
    try:
        for step in ladder:
            trial = os.path.join(work_dir, f"{step}.pdf")
            size = compress_with(src, trial, step)
            if size < best_size:
                best_size = size
                shutil.copyfile(trial, dst)
            if target_kb and size <= target_kb * 1024:
                break
        if best_size >= original:
            shutil.copyfile(src, dst)
        return best_size
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def output_path(src, out_dir, custom_name, many):
    if custom_name and not many:
        name = custom_name if custom_name.lower().endswith(".pdf") else f"{custom_name}.pdf"
    else:
        name = f"{os.path.splitext(os.path.basename(src))[0]}_compressed.pdf"
    path, stem = os.path.join(out_dir, name), os.path.splitext(name)[0]
    counter = 1
    while os.path.exists(path):
        path = os.path.join(out_dir, f"{stem} ({counter}).pdf")
        counter += 1
    return path


def reason_for(err):
    if isinstance(err, pikepdf.PasswordError):
        return "This PDF is password-protected."
    if isinstance(err, (pikepdf.PdfError, ValueError)):
        return "This PDF looks damaged and could not be read."
    return f"Could not compress this file ({type(err).__name__})."


def main():
    try:
        # readline, not read(): the runner keeps stdin open to deliver cancel commands
        payload = json.loads(sys.stdin.readline())
    except Exception as err:
        send({"type": "error", "message": f"Invalid payload: {err}"})
        return
    files = payload.get("input_files", [])
    if not files:
        send({"type": "error", "message": "No PDF files selected."})
        return
    options = payload.get("options", {})
    preset = preset_from(options.get("preset", "balanced"))
    try:
        target_kb = max(0, int(options.get("target_kb") or 0))
    except (TypeError, ValueError):
        target_kb = 0
    custom_name = str(options.get("custom_filename") or "").strip()
    out_dir = payload.get("output_dir") or os.path.dirname(files[0])
    os.makedirs(out_dir, exist_ok=True)
    send({"type": "log", "message": f"Goal: {f'under {target_kb} KB' if target_kb else preset} · text stays sharp"})

    outputs, failed, before_total, after_total = [], [], 0, 0
    for index, src in enumerate(files):
        name = os.path.basename(src)
        send({"type": "progress", "percent": round(5 + index / len(files) * 90, 1), "status": f"Compressing {name}…"})
        dst = output_path(src, out_dir, custom_name, len(files) > 1)
        try:
            size = compress_file(src, dst, preset, target_kb)
        except Exception as err:
            failed.append({"file": src, "reason": reason_for(err)})
            send({"type": "log", "message": f"{name}: {reason_for(err)}"})
            continue
        original = os.path.getsize(src)
        outputs.append(dst)
        before_total += original
        after_total += min(size, original)
        send({"type": "log", "message": f"{name}: {original // 1024} KB → {min(size, original) // 1024} KB"})

    if not outputs:
        send({"type": "error", "message": failed[0]["reason"] if failed else "No PDFs could be compressed."})
        sys.exit(1)
    stats = {"orig_size": before_total, "new_size": after_total, "failed": failed, "processed": len(outputs)}
    send({"type": "done", "outputs": outputs, "stats": stats})


if __name__ == "__main__":
    main()
