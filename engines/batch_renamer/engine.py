"""Batch Renamer Engine (Decoupled Process)."""

import os
import sys
import json
import shutil

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
    rule = options.get("rule", "Add Suffix")
    text1 = options.get("text1", "")
    text2 = options.get("text2", "")
    op_mode = options.get("op_mode", "Rename In-Place")

    if not input_files:
        send({"type": "error", "message": "No files selected."})
        return

    send({"type": "log", "message": f"Rule: {rule} | Operation: {op_mode}"})
    send({"type": "progress", "percent": 10.0, "status": "Preparing renaming batch..."})

    total = len(input_files)
    last_file = None

    try:
        for idx, file_p in enumerate(input_files):
            if not os.path.exists(file_p):
                continue
            parent = os.path.dirname(file_p)
            base_full = os.path.basename(file_p)
            name, ext = os.path.splitext(base_full)

            new_name = name
            if "Add Prefix" in rule:
                new_name = f"{text1}{name}"
            elif "Add Suffix" in rule:
                new_name = f"{name}{text1}"
            elif "Sequential Numbering" in rule:
                new_name = f"{name}_{idx+1:02d}"
            elif "Find & Replace" in rule:
                if text1:
                    new_name = name.replace(text1, text2)
            elif "Lowercase" in rule:
                new_name = name.lower()
            elif "UPPERCASE" in rule:
                new_name = name.upper()

            final_base = f"{new_name}{ext}"

            if op_mode == "Rename In-Place":
                target_p = os.path.join(parent, final_base)
                if target_p != file_p:
                    os.rename(file_p, target_p)
            else:
                dest_dir = output_dir or parent
                os.makedirs(dest_dir, exist_ok=True)
                target_p = os.path.join(dest_dir, final_base)
                shutil.copyfile(file_p, target_p)

            last_file = target_p
            pct = 10.0 + ((idx + 1) / total) * 85.0
            send({"type": "progress", "percent": round(pct, 1), "status": f"Processed {idx+1}/{total}..."})
            send({"type": "log", "message": f"'{base_full}' -> '{final_base}'"})

        send({"type": "done", "output_file": last_file or output_dir})

    except Exception as ex:
        send({"type": "error", "message": str(ex)})

if __name__ == "__main__":
    main()
