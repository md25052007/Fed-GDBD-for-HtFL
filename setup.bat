@echo off
REM ============================================================
REM  One-time setup: creates a Python virtual env and installs
REM  PyTorch (CUDA 12.8 build - works on RTX 3050 and RTX 5060)
REM ============================================================
cd /d "%~dp0"

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv || goto :fail
)
call .venv\Scripts\activate.bat

python -m pip install --upgrade pip
echo.
echo Installing PyTorch with CUDA (about 3 GB download, be patient)...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 (
    echo cu128 build failed, trying cu130...
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130 || goto :fail
)
pip install -r requirements.txt || goto :fail

echo.
echo ===================== GPU CHECK =====================
python -c "import torch; ok=torch.cuda.is_available(); print('CUDA available:', ok); print('GPU:', torch.cuda.get_device_name(0) if ok else 'NONE - something is wrong'); import torch.nn as nn; x=torch.randn(64,3,32,32,device='cuda'); print('Test conv OK:', nn.Conv2d(3,8,3).cuda()(x).shape)"
echo =====================================================
echo If you see "CUDA available: True" and your GPU name above, setup is done.
pause
exit /b 0

:fail
echo.
echo SETUP FAILED - send a screenshot of this window to Claude.
pause
exit /b 1
