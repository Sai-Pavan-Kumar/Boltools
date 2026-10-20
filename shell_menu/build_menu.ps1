<#
  Builds the Windows 11 right-click menu: BoltoolsMenu.dll + BoltoolsMenu.msix.
  The C compiler is a pinned Zig release, SHA-256 checked, so no Visual Studio
  or paid signing is needed. Output goes to -Destination (next to Boltools.exe).

  Dev:      powershell -File shell_menu/build_menu.ps1
  Release:  powershell -File shell_menu/build_menu.ps1 -Destination dist/Boltools -Executable Boltools.exe
#>
param(
    [string]$Destination = (Join-Path $PSScriptRoot 'bin'),
    [string]$Executable = 'BoltoolsMenuHost.exe'
)
$ErrorActionPreference = 'Stop'

$cache = Join-Path $PSScriptRoot '.cache'
$zigName = 'zig-x86_64-windows-0.16.0'
$zigSha256 = '68659EB5F1E4EB1437A722F1DD889C5A322C9954607F5EDCF337BC3684A75A7E'
$zig = Join-Path $cache "$zigName\zig.exe"

if (-not (Test-Path $zig)) {
    New-Item -ItemType Directory -Force -Path $cache | Out-Null
    $zip = Join-Path $cache "$zigName.zip"
    if (-not (Test-Path $zip)) {
        & curl.exe --fail -L -sS -o $zip "https://ziglang.freetls.fastly.net/$zigName.zip"
    }
    if ((Get-FileHash $zip -Algorithm SHA256).Hash -ne $zigSha256) {
        Remove-Item $zip
        throw "Zig download failed its fingerprint check."
    }
    Expand-Archive $zip -DestinationPath $cache -Force
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null
$src = $PSScriptRoot

& $zig cc -shared -O2 -target x86_64-windows-gnu -o (Join-Path $Destination 'BoltoolsMenu.dll') `
    (Join-Path $src 'boltools_menu.c') (Join-Path $src 'menu_config.c') (Join-Path $src 'boltools_menu.def') `
    -lole32 -lshell32 -lshlwapi -luuid -luser32
if ($LASTEXITCODE -ne 0) { throw 'DLL build failed.' }

if ($Executable -eq 'BoltoolsMenuHost.exe') {
    & $zig cc -O2 -target x86_64-windows-gnu -o (Join-Path $Destination $Executable) (Join-Path $src 'host_stub.c')
    if ($LASTEXITCODE -ne 0) { throw 'Stub build failed.' }
}

# Pack the sparse package with Microsoft's makeappx (Windows SDK).
$makeappx = Get-ChildItem 'C:\Program Files (x86)\Windows Kits\10\bin\*\x64\makeappx.exe' |
    Sort-Object FullName -Descending | Select-Object -First 1
if (-not $makeappx) { throw 'makeappx.exe not found (install the Windows SDK).' }

$layout = Join-Path $cache 'layout'
Remove-Item $layout -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path (Join-Path $layout 'Assets') | Out-Null
(Get-Content (Join-Path $src 'AppxManifest.xml') -Raw).Replace('__EXE__', $Executable) |
    Set-Content (Join-Path $layout 'AppxManifest.xml') -Encoding utf8
Copy-Item (Join-Path $src 'Logo.png') (Join-Path $layout 'Assets\Logo.png')

& $makeappx.FullName pack /o /nv /d $layout /p (Join-Path $Destination 'BoltoolsMenu.msix') | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Packing failed.' }
Write-Host "Built menu into $Destination"
