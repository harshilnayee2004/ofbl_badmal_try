@echo off
title MIPL AI Inspection - Dependency Installer
color 0A
echo ================================================================
echo        MIPL AI Inspection System - Dependency Installer
echo ================================================================
echo.
echo Step 1: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 2: Installing PyTorch (CUDA 12.1 or CPU)...
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
if %ERRORLEVEL% NEQ 0 (
    echo [Warning] CUDA install failed, falling back to standard PyTorch CPU...
    python -m pip install torch torchvision
)

echo.
echo Step 3: Installing Web and AI Server dependencies...
python -m pip install -r requirements.txt

echo.
echo ================================================================
echo All dependencies installed successfully!
echo You can now run "START_SYSTEM.bat" or start servers manually.
echo ================================================================
pause
