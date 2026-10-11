"""Boltools Admin Tool Release, Packaging & Manifest Signing CLI.

Usage:
  python release_tool.py <tool_id> --test
  python release_tool.py <tool_id> --pack
  python release_tool.py <tool_id> --publish
  python release_tool.py --gen-key <output_key_path>
  python release_tool.py --sign-manifest [--key-id key_1]
"""

import os
import sys
import json
import zipfile
import subprocess
import argparse
import hashlib
import getpass
from typing import Optional, Tuple

SOFTWARE_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINES_DIR = os.path.join(SOFTWARE_DIR, "engines")
BUNDLES_DIR = os.path.join(SOFTWARE_DIR, "release_bundles")
CATALOG_PATH = os.path.join(SOFTWARE_DIR, "catalog.json")
TOOLS_MANIFEST_PATH = os.path.join(SOFTWARE_DIR, "tools_manifest.json")
TOOLS_MANIFEST_SIG_PATH = os.path.join(SOFTWARE_DIR, "tools_manifest.sig")
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


def pack_engine_v1(tool_id: str) -> Tuple[str, str, int]:
    """Packages an engine directory into a strict .bolpack ZIP archive.

    1. Validates or creates pack.json.
    2. Computes sha256 for all tool payload files (excluding pack.json itself).
    3. Writes archive to release_bundles/<tool_id>-<version>.bolpack.
    4. Computes and returns (bolpack_path, bolpack_sha256, bolpack_size_bytes).
    """
    os.makedirs(BUNDLES_DIR, exist_ok=True)
    engine_folder = os.path.join(ENGINES_DIR, tool_id)
    if not os.path.isdir(engine_folder):
        raise FileNotFoundError(f"Engine folder not found: {engine_folder}")

    pack_json_path = os.path.join(engine_folder, "pack.json")
    if os.path.isfile(pack_json_path):
        with open(pack_json_path, "r", encoding="utf-8") as f:
            pack_meta = json.load(f)
    else:
        pack_meta = {
            "id": tool_id,
            "name": tool_id.replace("_", " ").title(),
            "version": "1.0.0",
            "min_app_version": "1.0.0",
            "runtime": "python",
            "entry": "engine.py",
            "files": {}
        }

    version = pack_meta.get("version", "1.0.0")
    files_map = {}

    # Scan and hash all payload files excluding pack.json
    for root, _, filenames in os.walk(engine_folder):
        for fname in filenames:
            if fname.lower() == "pack.json":
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, engine_folder).replace("\\", "/")
            with open(full_path, "rb") as bf:
                f_hash = hashlib.sha256(bf.read()).hexdigest().lower()
            files_map[rel_path] = f_hash

    pack_meta["files"] = files_map
    with open(pack_json_path, "w", encoding="utf-8") as f:
        json.dump(pack_meta, f, indent=2)

    bolpack_filename = f"{tool_id}-{version}.bolpack"
    bolpack_path = os.path.join(BUNDLES_DIR, bolpack_filename)

    with zipfile.ZipFile(bolpack_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # 1. pack.json
        zf.write(pack_json_path, "pack.json")
        # 2. payload files
        for rel_path in sorted(files_map.keys()):
            full_p = os.path.join(engine_folder, rel_path.replace("/", os.sep))
            zf.write(full_p, rel_path)

    with open(bolpack_path, "rb") as bf:
        bolpack_bytes = bf.read()
        bolpack_sha256 = hashlib.sha256(bolpack_bytes).hexdigest().lower()
        bolpack_size = len(bolpack_bytes)

    print(f"[PASS] Packaged {bolpack_filename} ({bolpack_size / 1024:.1f} KB, sha256: {bolpack_sha256[:16]}...)")
    return bolpack_path, bolpack_sha256, bolpack_size


def generate_keypair(output_key_path: str, passphrase: Optional[str] = None):
    """Generates an Ed25519 private key, encrypted with PKCS8 and AES-256."""
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization

    if not passphrase:
        passphrase = getpass.getpass("Enter passphrase to encrypt private key: ")
        confirm = getpass.getpass("Confirm passphrase: ")
        if passphrase != confirm:
            raise ValueError("Passphrases do not match.")
        if not passphrase:
            raise ValueError("Passphrase cannot be empty.")

    priv_key = ed25519.Ed25519PrivateKey.generate()
    enc_algorithm = serialization.BestAvailableEncryption(passphrase.encode("utf-8"))

    pem_bytes = priv_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=enc_algorithm
    )

    out_dir = os.path.dirname(os.path.abspath(output_key_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_key_path, "wb") as f:
        f.write(pem_bytes)

    pub_hex = priv_key.public_key().public_bytes_raw().hex()
    print(f"\n[PASS] Encrypted private key saved to: {output_key_path}")
    print(f"[*] Public Key (Hex): {pub_hex}")
    print(f"[*] Add this public key to software/src/_build.py EMBEDDED_PUBLIC_KEYS.\n")
    return pub_hex


def load_private_key(key_path: str, passphrase: Optional[str] = None):
    """Loads an encrypted Ed25519 private key from PEM file."""
    from cryptography.hazmat.primitives import serialization

    if not os.path.isfile(key_path):
        raise FileNotFoundError(f"Private key file not found: {key_path}")

    if not passphrase:
        passphrase = os.environ.get("BOLTOOLS_KEY_PASSPHRASE")
    if not passphrase:
        passphrase = getpass.getpass(f"Enter passphrase for private key '{key_path}': ")

    with open(key_path, "rb") as f:
        key_data = f.read()

    priv_key = serialization.load_pem_private_key(
        key_data,
        password=passphrase.encode("utf-8") if passphrase else None
    )
    return priv_key


def sign_manifest(key_path: Optional[str] = None, passphrase: Optional[str] = None, key_id: str = "key_1") -> str:
    """Signs raw bytes of tools_manifest.json with Ed25519 and increments sequence number."""
    if not key_path:
        key_path = os.environ.get("BOLTOOLS_SIGNING_KEY_FILE")
    if not key_path:
        raise ValueError("Missing signing key path. Specify via --key-file or BOLTOOLS_SIGNING_KEY_FILE.")

    priv_key = load_private_key(key_path, passphrase)

    # Load and increment sequence in manifest
    with open(TOOLS_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    manifest_data["sequence"] = manifest_data.get("sequence", 0) + 1
    # Pretty-print with fixed indent for canonical formatting
    formatted_json = json.dumps(manifest_data, indent=2) + "\n"
    raw_manifest_bytes = formatted_json.encode("utf-8")

    # Write updated manifest back to disk
    with open(TOOLS_MANIFEST_PATH, "wb") as f:
        f.write(raw_manifest_bytes)

    # Sign exact raw manifest bytes
    sig_bytes = priv_key.sign(raw_manifest_bytes)

    # Write binary signature to tools_manifest.sig
    with open(TOOLS_MANIFEST_SIG_PATH, "wb") as sf:
        sf.write(sig_bytes)

    print(f"[PASS] Successfully signed tools_manifest.json (Sequence: {manifest_data['sequence']})")
    print(f"[*] Signature written to: {TOOLS_MANIFEST_SIG_PATH} ({len(sig_bytes)} bytes)")
    return sig_bytes.hex()


def publish_to_r2(tool_id: str, bundle_path: str) -> bool:
    """Uploads tool bundle to Cloudflare R2 bucket."""
    filename = os.path.basename(bundle_path)
    print(f"[*] Uploading {filename} to Cloudflare R2...")
    r2_target = f"boltools-releases/engines/{tool_id}/{filename}"
    cmd = [
        "npx", "wrangler", "r2", "object", "put",
        r2_target,
        f"--file={bundle_path}",
        "--remote"
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"[PASS] Uploaded to R2: {r2_target}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Cloudflare R2 upload failed: {e.stderr or e.stdout}")
        return False


def update_catalog_and_announcements(tool_id: str, version: str = "1.0.0"):
    """Updates catalog.json status and prepends a release announcement."""
    if os.path.exists(CATALOG_PATH):
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                cat = json.load(f)
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
                "id": f"release_{tool_id}_v{version.replace('.', '_')}",
                "date": "2026-10-11",
                "tag": "NEW TOOL",
                "title": f"New Utility Released: {title}",
                "description": f"{title} v{version} is now available in the Tool Hub.",
                "cta_text": "Open Tool Hub",
                "cta_url": ""
            }
            ann = [x for x in ann if x.get("id") != new_entry["id"]]
            ann.insert(0, new_entry)
            with open(ANNOUNCEMENTS_PATH, "w", encoding="utf-8") as f:
                json.dump(ann, f, indent=2)
            print("[PASS] Announcement posted in announcements.json")
        except Exception as e:
            print(f"[WARN] Failed to update announcements.json: {e}")


def main():
    parser = argparse.ArgumentParser(description="Boltools Admin Tool Release CLI")
    parser.add_argument("tool_id", nargs="?", default="", help="Directory name of tool in software/engines/")
    parser.add_argument("--test", action="store_true", help="Run automated smoke tests")
    parser.add_argument("--pack", action="store_true", help="Package tool into .bolpack v1 format")
    parser.add_argument("--publish", action="store_true", help="Pack and publish to Cloudflare R2")
    parser.add_argument("--gen-key", metavar="KEY_PATH", help="Generate encrypted Ed25519 signing keypair")
    parser.add_argument("--sign-manifest", action="store_true", help="Sign tools_manifest.json with Ed25519")
    parser.add_argument("--key-file", help="Path to encrypted private key file")
    parser.add_argument("--key-id", default="key_1", help="Key identifier (key_1 or key_2)")
    args = parser.parse_args()

    if args.gen_key:
        generate_keypair(args.gen_key)
        sys.exit(0)

    if args.sign_manifest:
        sign_manifest(key_path=args.key_file, key_id=args.key_id)
        sys.exit(0)

    tool_id = args.tool_id.strip()
    if not tool_id:
        parser.print_help()
        sys.exit(1)

    if args.test:
        success = run_smoke_test(tool_id)
        sys.exit(0 if success else 1)

    if args.pack:
        if not run_smoke_test(tool_id):
            print("[ERROR] Smoke test failed. Aborting pack.")
            sys.exit(1)
        pack_path, pack_sha, pack_size = pack_engine_v1(tool_id)
        # Update manifest entry with new hash and size
        if os.path.exists(TOOLS_MANIFEST_PATH):
            with open(TOOLS_MANIFEST_PATH, "r", encoding="utf-8") as f:
                mdata = json.load(f)
            updated = False
            for t in mdata.get("tools", []):
                if t.get("id") == tool_id:
                    t["sha256"] = pack_sha
                    t["size_bytes"] = pack_size
                    updated = True
            if updated:
                with open(TOOLS_MANIFEST_PATH, "w", encoding="utf-8") as f:
                    json.dump(mdata, f, indent=2)
                print(f"[PASS] Updated tools_manifest.json with {tool_id} hash & size.")
        sys.exit(0)

    if args.publish:
        if not run_smoke_test(tool_id):
            print("[ERROR] Smoke test failed. Aborting publish.")
            sys.exit(1)
        pack_path, pack_sha, pack_size = pack_engine_v1(tool_id)
        if publish_to_r2(tool_id, pack_path):
            update_catalog_and_announcements(tool_id)
            print(f"\n✨ Tool '{tool_id}' successfully published to Cloudflare R2!")
            sys.exit(0)
        else:
            sys.exit(1)

    parser.print_help()


if __name__ == "__main__":
    main()
