@echo off
REM ============================================================
REM  Shows every run in a log folder: rounds done, best and last accuracy,
REM  minutes per round, time left, and whether it finished or crashed.
REM
REM  Usage:  scripts\check_progress.bat                 Part A runs (logs\)
REM          scripts\check_progress.bat novelty [seed]  Part B runs of that seed (0 if left out)
REM          scripts\check_progress.bat <folder>        any log folder, e.g. experiments\cifar10\logs
REM ============================================================
cd /d "%~dp0.."
call .venv\Scripts\activate.bat || ( echo Run setup.bat first & pause & exit /b 1 )
set LOGDIR=logs
if not "%1"=="" set LOGDIR=%1
if /I "%1"=="novelty" (
  set LOGDIR=logs_novelty
  if not "%2"=="" if not "%2"=="0" set LOGDIR=logs_novelty_seed%2
)
python scripts\progress.py %LOGDIR%
echo.
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv
pause
