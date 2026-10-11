@echo off
setlocal enabledelayedexpansion

echo ==============================================================================
echo BOLTOOLS PACK FORMAT V1 ^& ED25519 CLEAN-PC MANUAL SMOKE TEST SCRIPT
echo ==============================================================================
echo This script walks through testing the tool lifecycle on a fresh/clean setup:
echo 1. Generate Ed25519 signing keypair
echo 2. Package Hello tool into .bolpack v1 format
echo 3. Sign manifest with Ed25519 key
echo 4. Run automated test suite
echo 5. Launch app in development mode with Hello tool enabled
echo ==============================================================================
echo.

set PYTHON_BIN=.\.venv\Scripts\python.exe
if not exist "%PYTHON_BIN%" (
    echo [ERROR] Virtualenv Python not found at %PYTHON_BIN%. Run python -m venv .venv first.
    pause
    exit /b 1
)

:: Clear stale manifest cache so newly registered tools reflect immediately
del /f /q "%USERPROFILE%\.boltools\manifest_cache.json" 2>nul

echo [STEP 1] Generating sample test Ed25519 signing keypair...
set SMOKE_KEY=%TEMP%\smoke_test_key.pem
set BOLTOOLS_KEY_PASSPHRASE=BoltoolsSmokePass123!
"%PYTHON_BIN%" release_tool.py --gen-key "%SMOKE_KEY%"
if %errorlevel% neq 0 (
    echo [FAIL] Key generation failed.
    pause
    exit /b 1
)
echo [PASS] Key generated at %SMOKE_KEY%.
echo.

echo [STEP 2] Packaging engines/hello_tool into .bolpack archive...
"%PYTHON_BIN%" release_tool.py hello_tool --pack
if %errorlevel% neq 0 (
    echo [FAIL] Packaging hello_tool failed.
    pause
    exit /b 1
)
echo [PASS] hello_tool packaged successfully.
echo.

echo [STEP 3] Signing tools_manifest.json with Ed25519...
set BOLTOOLS_SIGNING_KEY_FILE=%SMOKE_KEY%
"%PYTHON_BIN%" release_tool.py --sign-manifest
if %errorlevel% neq 0 (
    echo [FAIL] Manifest signing failed.
    pause
    exit /b 1
)
echo [PASS] tools_manifest.json signed and sequence incremented.
echo.

echo [STEP 4] Executing End-to-End automated validation suite...
"%PYTHON_BIN%" tools_dev\test_bolpack_e2e.py
if %errorlevel% neq 0 (
    echo [FAIL] Automated tests failed!
    pause
    exit /b 1
)
echo [PASS] All automated e2e tests passed.
echo.

echo [STEP 5] Launching Boltools Desktop App in dev mode with Hello tool visible...
echo (BOLTOOLS_DEV=1 allows the Hello tool to appear in the catalog for testing)
set BOLTOOLS_DEV=1
start "" "%PYTHON_BIN%" main.py

echo.
echo ==============================================================================
echo Manual Check Steps in the Opened App:
echo   1. Navigate to Tool Hub.
echo   2. Verify 'Hello World Test Utility' appears under System ^& Files or Search.
echo   3. Click 'Install' - observe spinner and confirmation toast.
echo   4. Launch Hello Tool Studio - test 1s run, check hello.txt in outputs.
echo   5. Test Cancel button during 10s run - observe immediate cancel.
echo   6. Uninstall the tool from settings/card menu.
echo ==============================================================================
echo Smoke test preparation complete.
pause
