# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ('ui', 'ui'),
    ('assets', 'assets'),
    ('catalog.json', '.'),
    ('poll.json', '.'),
    ('announcements.json', '.'),
    # Offline first run: the bundled manifest feeds the Tool Hub before any network sync,
    # and the signed .bolpack files let tools install with no internet at all.
    ('tools_manifest.json', '.'),
    ('tools_manifest.sig', '.'),
    ('release_bundles', 'release_bundles'),
    # Licence texts for Settings -> About -> Licences (regenerate with tools_dev/collect_licences.py).
    ('licenses', 'licenses')
]
binaries = []
hiddenimports = [
    'runpy',
    'src',
    'src.desktop_bridge',
    'src.engine_runner'
]

# The fixed library set every Python tool may rely on (RULES: a tool needing anything
# else waits for a shell update or ships as an exe engine). pypdfium2 carries pdfium.dll.
for package in ('webview', 'PIL', 'pikepdf', 'pypdfium2', 'pypdfium2_raw'):
    tmp_ret = collect_all(package)
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # PyMuPDF is AGPL: excluded on purpose so it can never slip into a release.
    excludes=['tkinter', 'customtkinter', 'turtle', 'fitz', 'pymupdf'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Boltools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/boltools.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Boltools',
)
