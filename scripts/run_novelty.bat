@echo off
REM ============================================================
REM  Part B: agreement-gated distillation, one seed.
REM
REM  Usage:  scripts\run_novelty.bat Cifar10 [seed]      (seed 0 if left out; we ran seeds 0 to 4)
REM          scripts\run_novelty.bat Cifar100 [seed]
REM
REM  Starts 3 runs in parallel, 20 rounds each, each in a minimised window:
REM     FedGDBD-S   (control)
REM     FedGDBD-AGC (gate per client)
REM     FedGDBD-AGS (gate per sample)
REM  All three pick the IKD teacher on a validation slice (--gdbd_teacher val).
REM  Logs: logs_novelty\ for seed 0, logs_novelty_seed<N>\ for the others.
REM  The matched-alpha control is started separately: scripts\run_amatch.bat
REM ============================================================
cd /d "%~dp0.."
set DATA=%1
set SEED=%2
if "%SEED%"=="" set SEED=0
set LOGDIR=logs_novelty
if not "%SEED%"=="0" set LOGDIR=logs_novelty_seed%SEED%
set GOAL=novelty
if not "%SEED%"=="0" set GOAL=novelty_seed%SEED%
set NCL=
if /I "%DATA%"=="Cifar10"  set NCL=10
if /I "%DATA%"=="Cifar100" set NCL=100
if "%NCL%"=="" ( echo Usage: scripts\run_novelty.bat Cifar10^|Cifar100 [seed] & pause & exit /b 1 )

REM ---- 20 rounds: FedGDBD-S was within 1 pt of its best by round 2-5 ----
set ROUNDS=20

call .venv\Scripts\activate.bat || ( echo Run setup.bat first & pause & exit /b 1 )

if /I "%DATA%"=="Cifar10"  if not exist dataset\Cifar10\rawdata\cifar-10-python.tar.gz  if not exist dataset\Cifar10\rawdata\cifar-10-batches-py  ( echo Put cifar-10-python.tar.gz in dataset\Cifar10\rawdata\ first & pause & exit /b 1 )
if /I "%DATA%"=="Cifar100" if not exist dataset\Cifar100\rawdata\cifar-100-python.tar.gz if not exist dataset\Cifar100\rawdata\cifar-100-python ( echo Put cifar-100-python.tar.gz in dataset\Cifar100\rawdata\ first & pause & exit /b 1 )

cd dataset
python generate_%DATA%.py noniid - dir || ( echo Dataset generation failed & pause & exit /b 1 )
cd ..
if not exist %LOGDIR% mkdir %LOGDIR%

set COMMON=-data %DATA% -ncl %NCL% -m HtFE-img-4 -fd 512 -nc 20 -jr 1 -lbs 10 -lr 0.01 -ls 5 -gr %ROUNDS% -t 1 -go %GOAL% -did 0 --gdbd_teacher val --seed %SEED%

cd system
start "S-control-%DATA%-seed%SEED%" /min cmd /c "python -u main.py %COMMON% -algo FedGDBD-S   > ..\%LOGDIR%\%DATA%_FedGDBD-S.log 2>&1"
start "AGC-%DATA%-seed%SEED%" /min cmd /c "python -u main.py %COMMON% -algo FedGDBD-AGC > ..\%LOGDIR%\%DATA%_FedGDBD-AGC.log 2>&1"
start "AGS-%DATA%-seed%SEED%" /min cmd /c "python -u main.py %COMMON% -algo FedGDBD-AGS > ..\%LOGDIR%\%DATA%_FedGDBD-AGS.log 2>&1"
cd ..

echo.
echo Started 3 runs on %DATA%, seed %SEED% (%ROUNDS% rounds each). Logs: %LOGDIR%\
echo Do NOT close the 3 minimised windows. Keep the laptop plugged in and awake.
echo Progress: scripts\check_progress.bat novelty %SEED%
pause
