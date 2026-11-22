@echo off
REM ============================================================
REM  Part A: reproduction of Fed-GDBD (practical setting, Dir 0.1,
REM  20 clients, 4 model architectures, 50 rounds).
REM
REM  Usage:  scripts\run_reproduction.bat Cifar10            FedGDBD, FedProto and LG-FedAvg in parallel
REM          scripts\run_reproduction.bat Cifar10 FedGDBD-S  only that method (any of the four)
REM  Same for Cifar100. Methods: FedGDBD, FedProto, LG-FedAvg, FedGDBD-S
REM  We ran the three methods together, then FedGDBD-S on its own.
REM
REM  Each run gets its own minimised window. Logs go to logs\<Data>_<Method>.log.
REM  An existing log for the same run is moved to logs\old\ first.
REM ============================================================
cd /d "%~dp0.."
set DATA=%1
set ONLY=%2
set NCL=
if /I "%DATA%"=="Cifar10"  set NCL=10
if /I "%DATA%"=="Cifar100" set NCL=100
if "%NCL%"=="" ( echo Usage: scripts\run_reproduction.bat Cifar10^|Cifar100 [method] & pause & exit /b 1 )

REM ---- 50 rounds (the paper uses 100; 50 fitted our time budget) ----
set ROUNDS=50

call .venv\Scripts\activate.bat || ( echo Run setup.bat first & pause & exit /b 1 )

REM ---- build the 20-client split (downloads CIFAR once) ----
cd dataset
python generate_%DATA%.py noniid - dir || ( echo Dataset generation failed & pause & exit /b 1 )
cd ..
if not exist logs\old mkdir logs\old

set COMMON=-data %DATA% -ncl %NCL% -m HtFE-img-4 -fd 512 -nc 20 -jr 1 -lbs 10 -lr 0.01 -ls 5 -gr %ROUNDS% -t 1 -go practical -did 0

if "%ONLY%"=="" (
  call :launch FedGDBD
  call :launch FedProto
  call :launch LG-FedAvg
) else (
  call :launch %ONLY%
)

echo.
echo Started on %DATA% (%ROUNDS% rounds). Logs: logs\
echo Do NOT close the minimised windows. Keep the laptop plugged in and awake.
echo Progress: scripts\check_progress.bat
pause
exit /b 0

:launch
set ALGO=%1
set EXTRA=
if /I "%ALGO%"=="FedProto" set EXTRA=-lam 10
if exist logs\%DATA%_%ALGO%.log move /Y logs\%DATA%_%ALGO%.log logs\old\%DATA%_%ALGO%.log >nul
cd system
start "%ALGO%-%DATA%" /min cmd /c "python -u main.py %COMMON% -algo %ALGO% %EXTRA% > ..\logs\%DATA%_%ALGO%.log 2>&1"
cd ..
exit /b 0
