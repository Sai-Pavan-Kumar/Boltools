"""PDF & Document Converter Engine (Decoupled Process)."""

import os
import sys
import json
import pymupdf
from PIL import Image

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
    target_mode = options.get("mode", "PDF to Images (PNG)")

    if not input_files:
        send({"type": "error", "message": "No files selected."})
        return

    if not output_dir:
        output_dir = os.path.dirname(input_files[0])
    os.makedirs(output_dir, exist_ok=True)

    send({"type": "log", "message": f"Target: {target_mode}"})
    send({"type": "log", "message": f"Input files: {len(input_files)}"})
    send({"type": "progress", "percent": 10.0, "status": "Reading inputs..."})

    try:
        if target_mode in ["PDF to Images (PNG)", "PDF to Images (JPG)"]:
            ext = "png" if "PNG" in target_mode else "jpg"
            total_pages = 0
            for pdf_p in input_files:
                doc = pymupdf.open(pdf_p)
                total_pages += len(doc)
                doc.close()

            curr_page = 0
            last_file = None
            for pdf_p in input_files:
                base = os.path.splitext(os.path.basename(pdf_p))[0]
                doc = pymupdf.open(pdf_p)
                for i, page in enumerate(doc):
                    pix = page.get_pixmap(dpi=150)
                    out_img = os.path.join(output_dir, f"{base}_p{i+1}.{ext}")
                    pix.save(out_img)
                    curr_page += 1
                    last_file = out_img
                    pct = 10.0 + (curr_page / max(1, total_pages)) * 85.0
                    send({"type": "progress", "percent": round(pct, 1), "status": f"Page {curr_page}/{total_pages} rendered..."})
                    send({"type": "log", "message": f"Saved {os.path.basename(out_img)}"})
                doc.close()

            send({"type": "done", "output_file": last_file or output_dir})

        elif target_mode == "Images to PDF Document":
            out_pdf = os.path.join(output_dir, "combined_document.pdf")
            pil_images = []
            for idx, img_p in enumerate(input_files):
                pil_images.append(Image.open(img_p).convert("RGB"))
                pct = 10.0 + (idx / len(input_files)) * 70.0
                send({"type": "progress", "percent": round(pct, 1), "status": f"Loaded image {idx+1}/{len(input_files)}..."})

            send({"type": "progress", "percent": 85.0, "status": "Compiling PDF document..."})
            pil_images[0].save(out_pdf, save_all=True, append_images=pil_images[1:])
            send({"type": "log", "message": f"Compiled {len(pil_images)} images into {out_pdf}"})
            send({"type": "done", "output_file": out_pdf})

        elif target_mode == "PDF to Plain Text (.txt)":
            last_file = None
            for idx, pdf_p in enumerate(input_files):
                base = os.path.splitext(os.path.basename(pdf_p))[0]
                out_txt = os.path.join(output_dir, f"{base}_extracted.txt")
                doc = pymupdf.open(pdf_p)
                full_text = "\n".join([page.get_text() for page in doc])
                doc.close()
                with open(out_txt, "w", encoding="utf-8") as f:
                    f.write(full_text)
                last_file = out_txt
                pct = 10.0 + ((idx + 1) / len(input_files)) * 85.0
                send({"type": "progress", "percent": round(pct, 1), "status": f"Extracted {idx+1}/{len(input_files)}..."})
                send({"type": "log", "message": f"Extracted text to {os.path.basename(out_txt)}"})

            send({"type": "done", "output_file": last_file or output_dir})

        else:
            send({"type": "error", "message": f"Unsupported conversion mode: {target_mode}"})

    except Exception as ex:
        send({"type": "error", "message": str(ex)})

if __name__ == "__main__":
    main()
