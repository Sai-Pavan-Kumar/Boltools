"""Automated Production Build Script for Boltools Desktop Suite.

Generates:
- Standalone Windows Executable bundle in dist/Boltools/
- Native Windows multi-resolution icon embedding
- Bundles CustomTkinter JSON themes & typography fonts
- Packages 100-tool catalog & Edge API configuration
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def build():
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)

    print("=" * 64)
    print("   BOLTOOLS DESKTOP SUITE - PRODUCTION BUILD PIPELINE")
    print("=" * 64)

    # 1. Verify / Generate boltools.ico
    ico_path = script_dir / "assets" / "boltools.ico"
    if not ico_path.exists():
        print("[1/4] Generating Windows application icon (.ico)...")
        from PIL import Image
        logo_webp = script_dir / "assets" / "bolt_logo.webp"
        if logo_webp.exists():
            img = Image.open(logo_webp).convert("RGBA")
            img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            print("  [OK] Icon created at assets/boltools.ico")
    else:
        print("[1/4] Icon found: assets/boltools.ico")

    # 2. Prepare PyInstaller command arguments
    print("[2/4] Assembling PyInstaller build arguments...")
    python_exe = sys.executable

    pyinstaller_args = [
        python_exe,
        "-m",
        "PyInstaller",
        "--name=Boltools",
        "-y",
        "--noconsole",
        "--onedir",
        "--clean",
        f"--icon={ico_path}",
        "--add-data=assets;assets",
        "--add-data=catalog.json;.",
        "--add-data=poll.json;.",
        "--add-data=announcements.json;.",
        "--collect-all=customtkinter",
        "--collect-all=PIL",
        "--collect-all=pymupdf",
        "--hidden-import=src",
        "--hidden-import=src.app",
        "--hidden-import=src.core",
        "--hidden-import=src.components",
        "--hidden-import=src.modules",
        "--hidden-import=src.modules.video",
        "--hidden-import=src.modules.pdf",
        "--hidden-import=src.modules.image",
        "--hidden-import=src.modules.system",
        "--hidden-import=src.modules.windows",
        "main.py",
    ]

    # 3. Execute PyInstaller
    print("[3/4] Compiling Windows binary bundle (this may take 1-2 minutes)...")
    res = subprocess.run(pyinstaller_args)
    if res.returncode != 0:
        print(f"\n[FAIL] Build failed with return code {res.returncode}")
        sys.exit(res.returncode)

    # 4. Verify Built Artifacts
    dist_exe = script_dir / "dist" / "Boltools" / "Boltools.exe"
    if dist_exe.exists():
        exe_size_mb = dist_exe.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 64)
        print("  BUILD SUCCESSFUL!")
        print(f"   Binary:  {dist_exe}")
        print(f"   Size:    {exe_size_mb:.2f} MB")
        print("   Launch:  Run dist\\Boltools\\Boltools.exe to launch standalone app")
        print("=" * 64)
    else:
        print(f"\n[WARNING] Build completed but {dist_exe} was not found.")


if __name__ == "__main__":
    build()
