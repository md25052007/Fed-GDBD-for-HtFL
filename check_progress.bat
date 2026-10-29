@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python progress.py
echo.
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv
pause
