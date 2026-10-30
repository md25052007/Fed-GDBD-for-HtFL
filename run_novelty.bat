@echo off
REM ============================================================
REM  Novelty experiment: agreement-gated distillation.
REM  Usage: run_novelty.bat Cifar10 [seed]   or   run_novelty.bat Cifar100 [seed]
REM  seed 0 (default) = first run, logs in logs_novelty\ ; other seeds -> logs_novelty_seed<N>\
REM  Starts 3 runs IN PARALLEL (each in its own minimised window):
REM     FedGDBD-S   (control)        + validation-picked IKD teacher
REM     FedGDBD-AGC (gate per client) + validation-picked IKD teacher
REM     FedGDBD-AGS (gate per sample) + validation-picked IKD teacher
REM  Logs go to logs_novelty\  (the original experiments are untouched)
REM ============================================================
cd /d "%~dp0"
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
if "%NCL%"=="" ( echo Usage: run_novelty.bat Cifar10  or  Cifar100 & pause & exit /b 1 )

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
echo Started 3 novelty runs on %DATA%, seed %SEED% (%ROUNDS% rounds each). Logs: %LOGDIR%\
echo Do NOT close the 3 minimised windows. Keep the laptop plugged in and awake.
echo Double-click check_novelty.bat (seed 0) or check_novelty_seed1.bat (seed 1) to see progress.
pause
