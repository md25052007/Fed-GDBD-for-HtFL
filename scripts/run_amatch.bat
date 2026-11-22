@echo off
REM ============================================================
REM  Part B: matched-alpha control (see PROTOCOL.md). FedGDBD-S with one
REM  fixed alpha for every client, equal to the average alpha AGC used:
REM     Cifar10 -> alpha 0.58      Cifar100 -> alpha 0.49
REM
REM  Usage:  scripts\run_amatch.bat Cifar10 [seed]
REM          scripts\run_amatch.bat Cifar100 [seed]
REM  With a seed: runs that seed only (one window).
REM  Without a seed: seeds 0 to 3 in two windows (0 then 2, and 1 then 3),
REM  as we ran them; seed 4 was run later with: scripts\run_amatch.bat Cifar10 4
REM  Logs: <log folder of that seed>\<Data>_FedGDBD-S-amatch.log
REM  (logs_novelty\ for seed 0, logs_novelty_seed<N>\ for the others)
REM ============================================================
cd /d "%~dp0.."
set DATA=%1
set SEED=%2
set NCL=
set ALPHA=
if /I "%DATA%"=="Cifar10"  set NCL=10
if /I "%DATA%"=="Cifar10"  set ALPHA=0.58
if /I "%DATA%"=="Cifar100" set NCL=100
if /I "%DATA%"=="Cifar100" set ALPHA=0.49
if "%NCL%"=="" ( echo Usage: scripts\run_amatch.bat Cifar10^|Cifar100 [seed] & pause & exit /b 1 )

call .venv\Scripts\activate.bat || ( echo Run setup.bat first & pause & exit /b 1 )

cd dataset
python generate_%DATA%.py noniid - dir || ( echo Dataset generation failed & pause & exit /b 1 )
cd ..

set BASE=-data %DATA% -ncl %NCL% -m HtFE-img-4 -fd 512 -nc 20 -jr 1 -lbs 10 -lr 0.01 -ls 5 -gr 20 -t 1 -did 0 --gdbd_teacher val --gdbd_alpha %ALPHA% -algo FedGDBD-S
for %%S in (0 1 2 3 4) do call :cmd %%S

cd system
if "%SEED%"=="" (
  start "amatch-A-%DATA%" /min cmd /c "%R0% & %R2%"
  start "amatch-B-%DATA%" /min cmd /c "%R1% & %R3%"
) else (
  if "%SEED%"=="0" start "amatch-seed0-%DATA%" /min cmd /c "%R0%"
  if "%SEED%"=="1" start "amatch-seed1-%DATA%" /min cmd /c "%R1%"
  if "%SEED%"=="2" start "amatch-seed2-%DATA%" /min cmd /c "%R2%"
  if "%SEED%"=="3" start "amatch-seed3-%DATA%" /min cmd /c "%R3%"
  if "%SEED%"=="4" start "amatch-seed4-%DATA%" /min cmd /c "%R4%"
)
cd ..

echo.
echo Started the matched-alpha control on %DATA% (alpha %ALPHA%) in minimised windows.
echo Do NOT close them. Keep the laptop plugged in and awake.
echo Progress: scripts\check_progress.bat novelty ^<seed^>
pause
exit /b 0

REM ---- builds the command for one seed into R<seed> and creates its log folder ----
:cmd
set S=%1
set LOGDIR=logs_novelty
set GOAL=novelty_amatch
if not "%S%"=="0" set LOGDIR=logs_novelty_seed%S%
if not "%S%"=="0" set GOAL=novelty_seed%S%_amatch
if not exist %LOGDIR% mkdir %LOGDIR%
set R%S%=python -u main.py %BASE% -go %GOAL% --seed %S% ^> ..\%LOGDIR%\%DATA%_FedGDBD-S-amatch.log 2^>^&1
exit /b 0
