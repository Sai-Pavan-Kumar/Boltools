"""Rebuilds software/licenses/ from the packages in this venv: run it whenever a dependency changes.

Every component the app or the media pack ships gets an entry. Texts are copied from
what each project publishes itself (dist-info licence files, Python's LICENSE.txt,
the font OFL files), never retyped. Versions come from the installed metadata, and
tools_dev/test_licences.py fails when the folder falls behind the venv.

Usage: .venv/Scripts/python.exe tools_dev/collect_licences.py
"""

import json
import os
import shutil
import ssl
import sys
from importlib import metadata

SOFTWARE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(SOFTWARE_DIR, "licenses")
FONTS_DIR = os.path.join(SOFTWARE_DIR, "ui", "assets", "fonts")
HAND_KEPT = os.path.join(SOFTWARE_DIR, "tools_dev", "licence_texts")
MEDIA_SOURCE_URL = "https://github.com/Sai-Pavan-Kumar/Boltools/releases/tag/media-pack-9.0.2"

# (id, name, what it does in Boltools, licence, project url, source)
# source: ("dist", name) copies that package's licence files; ("files", [paths]) copies those.
COMPONENTS = [
    ("python", "Python", "Runs the app and its tools", "PSF-2.0", "https://www.python.org",
     ("files", [os.path.join(sys.base_prefix, "LICENSE.txt")])),
    ("pywebview", "pywebview", "App window", "BSD-3-Clause", "https://pywebview.flowrl.com", ("dist", "pywebview")),
    ("webview2_sdk", "Microsoft WebView2 SDK", "App window", "BSD-3-Clause", "https://aka.ms/webview2",
     ("files", [os.path.join(HAND_KEPT, "webview2-sdk-LICENSE.txt")])),
    ("pythonnet", "pythonnet", "Connects the app to Windows", "MIT", "https://github.com/pythonnet/pythonnet", ("dist", "pythonnet")),
    ("clr_loader", "clr_loader", "Connects the app to Windows", "MIT", "https://github.com/pythonnet/clr-loader", ("dist", "clr_loader")),
    ("bottle", "Bottle", "App window", "MIT", "https://bottlepy.org", ("dist", "bottle")),
    ("proxy_tools", "proxy_tools", "App window", "MIT", "https://github.com/jtushman/proxy_tools",
     ("files", [os.path.join(HAND_KEPT, "proxy_tools-NOTE.txt")])),
    ("pillow", "Pillow", "Pictures", "MIT-CMU", "https://python-pillow.org", ("dist", "pillow")),
    ("pikepdf", "pikepdf, with qpdf", "PDF tools", "MPL-2.0 (qpdf: Apache-2.0)", "https://github.com/pikepdf/pikepdf", ("dist", "pikepdf")),
    ("pypdfium2", "pypdfium2, with PDFium", "PDF pages and pictures", "Apache-2.0 / BSD-3-Clause", "https://github.com/pypdfium2-team/pypdfium2", ("dist", "pypdfium2")),
    ("lxml", "lxml, with libxml2 and libxslt", "PDF tools", "BSD-3-Clause", "https://lxml.de", ("dist", "lxml")),
    ("cryptography", "cryptography", "Checks that tools are genuine", "Apache-2.0 OR BSD-3-Clause", "https://cryptography.io", ("dist", "cryptography")),
    ("openssl", "OpenSSL", "Secure downloads", "Apache-2.0", "https://www.openssl.org",
     ("files", [("pikepdf", "openssl.txt")])),
    ("pynacl", "PyNaCl, with libsodium", "Checks that tools are genuine", "Apache-2.0 (libsodium: ISC)", "https://github.com/pyca/pynacl", ("dist", "pynacl")),
    ("cffi", "cffi", "Checks that tools are genuine", "MIT-0", "https://cffi.readthedocs.io", ("dist", "cffi")),
    ("pycparser", "pycparser", "Checks that tools are genuine", "BSD-3-Clause", "https://github.com/eliben/pycparser", ("dist", "pycparser")),
    ("packaging", "packaging", "Version checks", "Apache-2.0 OR BSD-2-Clause", "https://github.com/pypa/packaging", ("dist", "packaging")),
    ("typing_extensions", "typing_extensions", "Runs the app", "PSF-2.0", "https://github.com/python/typing_extensions", ("dist", "typing_extensions")),
    ("setuptools", "setuptools", "Runs the app", "MIT", "https://github.com/pypa/setuptools", ("dist", "setuptools")),
    ("vc_runtime", "Microsoft Visual C++ Runtime", "Runs the app", "Microsoft redistribution terms", "https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist",
     ("files", [("pikepdf", "microsoft-visual-cpp-runtime.txt")])),
    ("overused_grotesk", "Overused Grotesk", "App font", "OFL-1.1", "https://github.com/RandomMaerks/Overused-Grotesk",
     ("files", [os.path.join(FONTS_DIR, "OFL-OverusedGrotesk.txt")])),
    ("geist_mono", "Geist Mono", "App font", "OFL-1.1", "https://github.com/vercel/geist-font",
     ("files", [os.path.join(FONTS_DIR, "OFL-GeistMono.txt")])),
    ("ffmpeg", "FFmpeg, with x264 (media pack)", "Video and audio tools, downloaded once on first use", "GPL-3.0", MEDIA_SOURCE_URL,
     ("files", [os.path.join(HAND_KEPT, "ffmpeg-NOTE.txt"), os.path.join(HAND_KEPT, "GPL-3.0.txt")])),
]
FIXED_VERSIONS = {"python": "{}.{}.{}".format(*sys.version_info[:3]), "webview2_sdk": "1.0.3856.49", "ffmpeg": "9.0.2",
                  "openssl": ssl.OPENSSL_VERSION.split()[1]}
DIST_OF = {"pywebview": "pywebview", "pythonnet": "pythonnet", "clr_loader": "clr_loader", "bottle": "bottle",
           "proxy_tools": "proxy_tools", "pillow": "pillow", "pikepdf": "pikepdf", "pypdfium2": "pypdfium2", "lxml": "lxml",
           "cryptography": "cryptography", "pynacl": "pynacl", "cffi": "cffi", "pycparser": "pycparser",
           "packaging": "packaging", "typing_extensions": "typing_extensions", "setuptools": "setuptools"}


def is_licence_file(path: str) -> bool:
    norm = path.replace("\\", "/")
    name = norm.rsplit("/", 1)[-1]
    in_dist_info = ".dist-info/" in norm and "/_vendor/" not in norm
    return in_dist_info and not name.endswith(".py") and (
        name.upper().startswith(("LICEN", "COPYING", "NOTICE")) or "/licenses/" in norm.lower())


def dist_file(dist_name: str, file_name: str) -> str:
    dist = metadata.distribution(dist_name)
    match = next(f for f in dist.files if is_licence_file(str(f)) and f.name == file_name)
    return str(dist.locate_file(match))


def source_paths(source) -> list:
    kind, value = source
    if kind == "dist":
        dist = metadata.distribution(value)
        return [str(dist.locate_file(f)) for f in dist.files or [] if is_licence_file(str(f))]
    return [dist_file(*item) if isinstance(item, tuple) else item for item in value]


def unique_name(path: str, taken: set) -> str:
    # Several packages call their files LICENSE; keep the folder they came from in the name.
    base = os.path.basename(path)
    if base not in taken:
        return base
    parent = os.path.basename(os.path.dirname(path))
    return f"{parent}-{base}"


def main() -> None:
    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)  # generated folder: rebuilt from scratch so removed packages disappear
    index = []
    for comp_id, name, used_for, licence, url, source in COMPONENTS:
        folder = os.path.join(OUT_DIR, comp_id)
        os.makedirs(folder)
        files, taken = [], set()
        for path in source_paths(source):
            target = unique_name(path, taken)
            taken.add(target)
            shutil.copyfile(path, os.path.join(folder, target))
            files.append(target)
        if not files:
            raise SystemExit(f"No licence text found for {comp_id}")
        # Fonts and the C++ runtime carry no version we can read; they show none.
        version = FIXED_VERSIONS.get(comp_id) or (metadata.version(DIST_OF[comp_id]) if comp_id in DIST_OF else "")
        index.append({"id": comp_id, "name": name, "version": version, "used_for": used_for,
                      "licence": licence, "url": url, "files": files})
    with open(os.path.join(OUT_DIR, "index.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"components": index}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"{len(index)} components, {sum(len(c['files']) for c in index)} licence files -> {OUT_DIR}")


if __name__ == "__main__":
    main()
