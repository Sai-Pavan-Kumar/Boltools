<#
  One command for a release installer: dist_installer/Boltools_Setup.exe

  Release mode is switched on only for the build and switched back afterwards,
  so run.bat keeps working in dev mode. The build refuses to start if the
  tools list is not signed with the key inside the app: an installer with a
  bad signature would reject every update.

  Run:  powershell -ExecutionPolicy Bypass -File build_release.ps1
#>
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$buildFlags = Join-Path $PSScriptRoot 'src\_build.py'

& $python -c @'
import sys
import nacl.signing
from src._build import EMBEDDED_PUBLIC_KEYS
key = nacl.signing.VerifyKey(bytes.fromhex(EMBEDDED_PUBLIC_KEYS["key_1"]))
try:
    key.verify(open("tools_manifest.json", "rb").read(), open("tools_manifest.sig", "rb").read())
except Exception:
    sys.exit("tools_manifest.json is not signed with this key. Run: release_tool.py --sign-manifest --key-file <key>")
print("Signature OK")
'@
if ($LASTEXITCODE -ne 0) { throw 'Signature check failed.' }

& $python -m unittest discover -s tools_dev -p 'test_*.py'
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }

$original = Get-Content $buildFlags -Raw
try {
    $original.Replace('IS_RELEASE: bool = False', 'IS_RELEASE: bool = True') |
        Set-Content $buildFlags -NoNewline -Encoding utf8
    & $python -m PyInstaller Boltools.spec -y --clean
    if ($LASTEXITCODE -ne 0) { throw 'App build failed.' }
}
finally {
    Set-Content $buildFlags $original -NoNewline -Encoding utf8
}

& (Join-Path $PSScriptRoot 'shell_menu\build_menu.ps1') -Destination (Join-Path $PSScriptRoot 'dist\Boltools') -Executable 'Boltools.exe'

$iscc = Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
if (-not (Test-Path $iscc)) { $iscc = 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' }
& $iscc /Q installer.iss
if ($LASTEXITCODE -ne 0) { throw 'Installer build failed.' }

$setup = Get-Item (Join-Path $PSScriptRoot '..\dist_installer\Boltools_Setup.exe')
$hash = (Get-FileHash $setup.FullName -Algorithm SHA256).Hash.ToLower()
Write-Host "Built $($setup.FullName)"
Write-Host "Size:   $($setup.Length) bytes"
Write-Host "SHA256: $hash"
