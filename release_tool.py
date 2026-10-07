"""Boltools Admin Tool Release & Staging CLI.

Usage:
  python release_tool.py <tool_id> --test
  python release_tool.py <tool_id> --publish
"""

import os
import sys
import json
import zipfile
import subprocess
import argparse

SOFTWARE_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINES_DIR = os.path.join(SOFTWARE_DIR, "engines")
BUNDLES_DIR = os.path.join(SOFTWARE_DIR, "release_bundles")
CATALOG_PATH = os.path.join(SOFTWARE_DIR, "catalog.json")
ANNOUNCEMENTS_PATH = os.path.join(SOFTWARE_DIR, "announcements.json")


def run_smoke_test(tool_id: str) -> bool:
    """Runs isolated engine smoke test by executing target with JSON payload."""
    engine_file = os.path.join(ENGINES_DIR, tool_id, "engine.py")
    if not os.path.exists(engine_file):
        print(f"[FAIL] Engine script not found: {engine_file}")
        return False

    print(f"[*] Running smoke test for {tool_id}...")
    try:
        proc = subprocess.Popen(
            [sys.executable, engine_file],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        out, err = proc.communicate("{}", timeout=6)
        print(f"[*] Engine output: {out.strip() or err.strip()}")
        if proc.returncode == 0:
            print(f"[PASS] Smoke test succeeded for {tool_id}!")
            return True
        else:
            print(f"[FAIL] Engine exited with code {proc.returncode}")
            return False
    except Exception as e:
        print(f"[FAIL] Smoke test encountered error: {e}")
        return False


def package_engine(tool_id: str) -> str:
    """Zips the isolated engine folder into a standalone distribution bundle."""
    os.makedirs(BUNDLES_DIR, exist_ok=True)
    engine_folder = os.path.join(ENGINES_DIR, tool_id)
    zip_path = os.path.join(BUNDLES_DIR, f"{tool_id}.zip")

    print(f"[*] Packaging engine: {engine_folder} -> {zip_path}")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, _, files in os.walk(engine_folder):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, engine_folder)
                z.write(full_path, rel_path)

    size_kb = os.path.getsize(zip_path) / 1024
    print(f"[PASS] Packaged {zip_path} ({size_kb:.1f} KB)")
    return zip_path


def publish_to_r2(tool_id: str, zip_path: str) -> bool:
    """Uploads tool engine zip to Cloudflare R2 bucket boltools-releases."""
    print(f"[*] Uploading {tool_id}.zip to Cloudflare R2...")
    r2_target = f"boltools-releases/engines/{tool_id}.zip"
    cmd = [
        "npx", "wrangler", "r2", "object", "put",
        r2_target,
        f"--file={zip_path}",
        "--remote"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"[PASS] Uploaded to R2: {r2_target}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Cloudflare R2 upload failed: {e.stderr or e.stdout}")
        return False


def update_catalog_and_announcements(tool_id: str):
    """Updates catalog.json status and prepends a release announcement."""
    if os.path.exists(CATALOG_PATH):
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                cat = json.load(f)
            # Find and set status to installed/available
            for item in cat.get("tools", []):
                if item.get("id") == tool_id or tool_id in item.get("id", ""):
                    item["status"] = "available"
                    item["is_implemented"] = True
            with open(CATALOG_PATH, "w", encoding="utf-8") as f:
                json.dump(cat, f, indent=2)
            print("[PASS] Synchronized catalog.json")
        except Exception as e:
            print(f"[WARN] Failed to update catalog.json: {e}")

    if os.path.exists(ANNOUNCEMENTS_PATH):
        try:
            with open(ANNOUNCEMENTS_PATH, "r", encoding="utf-8") as f:
                ann = json.load(f)
            title = tool_id.replace("_", " ").title()
            new_entry = {
                "id": f"release_{tool_id}",
                "date": "2026-10-07",
                "tag": "NEW TOOL",
                "title": f"New Utility Released: {title}",
                "description": f"{title} is now available for download and offline use in the Tool Hub.",
                "cta_text": "Open Tool Hub",
                "cta_url": ""
            }
            # Avoid duplicate
            ann = [x for x in ann if x.get("id") != new_entry["id"]]
            ann.insert(0, new_entry)
            with open(ANNOUNCEMENTS_PATH, "w", encoding="utf-8") as f:
                json.dump(ann, f, indent=2)
            print("[PASS] Announcement posted in announcements.json")
        except Exception as e:
            print(f"[WARN] Failed to update announcements.json: {e}")


def main():
    parser = argparse.ArgumentParser(description="Boltools Admin Tool Release CLI")
    parser.add_argument("tool_id", help="Directory name of tool in software/engines/")
    parser.add_argument("--test", action="store_true", help="Run automated smoke tests")
    parser.add_argument("--publish", action="store_true", help="Package and publish to Cloudflare R2")
    args = parser.parse_args()

    tool_id = args.tool_id.strip()

    if args.test:
        success = run_smoke_test(tool_id)
        sys.exit(0 if success else 1)

    if args.publish:
        if not run_smoke_test(tool_id):
            print("[ERROR] Smoke test failed. Aborting publish.")
            sys.exit(1)
        zip_path = package_engine(tool_id)
        if publish_to_r2(tool_id, zip_path):
            update_catalog_and_announcements(tool_id)
            print(f"\n✨ Tool '{tool_id}' successfully published to Cloudflare R2!")
            sys.exit(0)
        else:
            sys.exit(1)

    parser.print_help()


if __name__ == "__main__":
    main()
