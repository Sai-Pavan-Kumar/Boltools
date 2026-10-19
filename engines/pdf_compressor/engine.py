"""PDF Compressor Engine (Decoupled Process).

High-performance offline PDF document compression powered by PyMuPDF.
Supports:
- Balanced (150 DPI - Preserves vector text & crushes images)
- Extreme (72 DPI - Government & university portal scan crush <200 KB)
- High Quality (200 DPI - Crisp office print quality)
- Lossless (Deflate streams, clean garbage objects, lossless fonts/images)
"""

import os
import sys
import json
import pymupdf


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
    preset = options.get("preset", "150 DPI (Balanced)")
    custom_filename = options.get("custom_filename") or options.get("output_filename")

    if not input_files:
        send({"type": "error", "message": "No files selected."})
        return

    if not output_dir:
        output_dir = os.path.dirname(input_files[0])
    os.makedirs(output_dir, exist_ok=True)

    send({"type": "log", "message": f"Starting PDF Compression with preset: {preset}"})
    send({"type": "log", "message": f"Total files to process: {len(input_files)}"})
    send({"type": "progress", "percent": 5.0, "status": "Initializing engine..."})

    total_orig_bytes = 0
    total_new_bytes = 0
    output_files = []

    try:
        for idx, pdf_path in enumerate(input_files):
            if not os.path.isfile(pdf_path):
                continue

            orig_sz = os.path.getsize(pdf_path)
            total_orig_bytes += orig_sz
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]

            if len(input_files) == 1 and custom_filename:
                out_name = custom_filename if custom_filename.lower().endswith(".pdf") else f"{custom_filename}.pdf"
            else:
                out_name = f"{base_name}_compressed.pdf"

            out_pdf = os.path.join(output_dir, out_name)

            send({"type": "log", "message": f"Processing [{idx + 1}/{len(input_files)}]: {os.path.basename(pdf_path)} ({orig_sz / 1024:.1f} KB)..."})

            doc = pymupdf.open(pdf_path)
            total_pages = len(doc)

            # Check text presence to decide best compression strategy
            has_text = any(len(page.get_text().strip()) > 0 for page in doc)

            if "Lossless" in preset:
                doc.save(out_pdf, garbage=4, clean=True, deflate=True, deflate_images=True, deflate_fonts=True)
                doc.close()
            elif "72 DPI" in preset or not has_text:
                target_dpi = 72 if "72 DPI" in preset else (150 if "150" in preset else 200)
                quality = 65 if target_dpi == 72 else (75 if target_dpi == 150 else 85)
                new_doc = pymupdf.open()
                for p_idx, page in enumerate(doc):
                    rect = page.rect
                    pix = page.get_pixmap(dpi=target_dpi)
                    img_bytes = pix.tobytes("jpeg", jpg_quality=quality)
                    new_page = new_doc.new_page(width=rect.width, height=rect.height)
                    new_page.insert_image(rect, stream=img_bytes)

                    page_pct = 10.0 + ((idx + (p_idx + 1) / max(1, total_pages)) / len(input_files)) * 80.0
                    send({"type": "progress", "percent": round(page_pct, 1), "status": f"Compressed page {p_idx + 1}/{total_pages}..."})

                new_doc.save(out_pdf, garbage=4, clean=True, deflate=True)
                new_doc.close()
                doc.close()
            else:
                # Document has vector text and user selected Balanced or High Quality
                target_dpi = 150 if "150" in preset else 200
                quality = 75 if target_dpi == 150 else 85
                try:
                    doc.rewrite_images(dpi_threshold=target_dpi + 1, dpi_target=target_dpi, quality=quality)
                except Exception:
                    pass
                doc.save(out_pdf, garbage=4, clean=True, deflate=True, deflate_images=True, deflate_fonts=True)
                doc.close()

            new_sz = os.path.getsize(out_pdf) if os.path.exists(out_pdf) else orig_sz
            total_new_bytes += new_sz
            output_files.append(out_pdf)

            saved_bytes = max(0, orig_sz - new_sz)
            saved_pct = round((saved_bytes / max(1, orig_sz)) * 100, 1)
            send({"type": "log", "message": f"Completed: {os.path.basename(out_pdf)} ({new_sz / 1024:.1f} KB, saved {saved_pct}%)"})

            pct = 10.0 + ((idx + 1) / len(input_files)) * 85.0
            send({"type": "progress", "percent": round(pct, 1), "status": f"Completed file {idx + 1}/{len(input_files)}"})

        total_saved_pct = round((max(0, total_orig_bytes - total_new_bytes) / max(1, total_orig_bytes)) * 100, 1) if total_orig_bytes > 0 else 0
        send({"type": "progress", "percent": 100.0, "status": "Compression complete!"})
        send({
            "type": "done",
            "output_file": output_files[0] if output_files else output_dir,
            "outputs": output_files,
            "stats": {
                "orig_size": total_orig_bytes,
                "new_size": total_new_bytes,
                "saved_pct": total_saved_pct
            }
        })

    except Exception as ex:
        send({"type": "error", "message": str(ex)})


if __name__ == "__main__":
    main()
