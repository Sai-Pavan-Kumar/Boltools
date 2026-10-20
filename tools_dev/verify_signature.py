"""Release gate: the bundled tools list must be signed with the key inside the app.

An installer with a bad signature would reject every update, so build_release.ps1
stops here instead of shipping one.
"""

import os
import sys

import nacl.signing

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src._build import EMBEDDED_PUBLIC_KEYS  # noqa: E402


def main() -> int:
    with open(os.path.join(ROOT, "tools_manifest.json"), "rb") as f:
        manifest = f.read()
    with open(os.path.join(ROOT, "tools_manifest.sig"), "rb") as f:
        signature = f.read()
    key = nacl.signing.VerifyKey(bytes.fromhex(EMBEDDED_PUBLIC_KEYS["key_1"]))
    try:
        key.verify(manifest, signature)
    except Exception:
        print("tools_manifest.json is not signed with this key. Run: release_tool.py --sign-manifest --key-file <key>")
        return 1
    print("Signature OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
