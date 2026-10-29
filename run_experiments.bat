@echo off
REM ============================================================
REM  Usage:   run_experiments.bat Cifar10      (Sai's laptop)
REM           run_experiments.bat Cifar100     (friend's laptop)
REM
REM  Starts 3 runs IN PARALLEL on the GPU (practical setting,
REM  Dirichlet beta=0.1, 20 clients, 4 heterogeneous models):
REM      Fed-GDBD, FedProto, LG-FedAvg
REM  Each run opens in its own minimised window. Logs go to logs\
REM ============================================================
cd /d "%~dp0"
set DATA=%1
if "%DATA%"=="" (
    echo Please give the dataset:  run_experiments.bat Cifar10   or   run_experiments.bat Cifar100
    pause & exit /b 1
)
if /I "%DATA%"=="Cifar10"  set NCL=10
if /I "%DATA%"=="Cifar100" set NCL=100
if "%NCL%"=="" ( echo Unknown dataset %DATA% & pause & exit /b 1 )

REM ---- Number of global rounds (paper uses 100; 50 to fit the time budget) ----
set ROUNDS=50

call .venv\Scripts\activate.bat || ( echo Run setup.bat first & pause & exit /b 1 )

REM ---- 1. Build the federated dataset split (downloads ~170 MB once) ----
cd dataset
python generate_%DATA%.py noniid - dir || ( echo Dataset generation failed & pause & exit /b 1 )
cd ..

if not exist logs mkdir logs

REM ---- 2. Common settings from the paper (Sec. 5.1) ----
set COMMON=-data %DATA% -ncl %NCL% -m HtFE-img-4 -fd 512 -nc 20 -jr 1 -lbs 10 -lr 0.01 -ls 5 -gr %ROUNDS% -t 1 -go practical -did 0

REM ---- 3. Launch the 3 methods in parallel ----
cd system
start "FedGDBD-%DATA%"  /min cmd /c "python -u main.py %COMMON% -algo FedGDBD > ..\logs\%DATA%_FedGDBD.log 2>&1"
start "FedProto-%DATA%" /min cmd /c "python -u main.py %COMMON% -algo FedProto -lam 10 > ..\logs\%DATA%_FedProto.log 2>&1"
start "LGFedAvg-%DATA%" /min cmd /c "python -u main.py %COMMON% -algo LG-FedAvg > ..\logs\%DATA%_LG-FedAvg.log 2>&1"
cd ..

echo.
echo Started 3 runs on %DATA% (%ROUNDS% rounds each).
echo Do NOT close the 3 minimised windows. Keep the laptop plugged in.
echo Double-click check_progress.bat any time to see accuracy and time left.
pause
