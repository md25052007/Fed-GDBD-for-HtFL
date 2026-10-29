@echo off
REM ============================================================
REM  Re-launch ONLY Fed-GDBD (fixed IKD loss) on one dataset.
REM  Usage: run_fedgdbd_only.bat Cifar10   or   run_fedgdbd_only.bat Cifar100
REM  The other two runs keep going untouched.
REM ============================================================
cd /d "%~dp0"
set DATA=%1
set NCL=
if /I "%DATA%"=="Cifar10"  set NCL=10
if /I "%DATA%"=="Cifar100" set NCL=100
if "%NCL%"=="" ( echo Usage: run_fedgdbd_only.bat Cifar10  or  Cifar100 & pause & exit /b 1 )
set ROUNDS=50

call .venv\Scripts\activate.bat || ( echo Run setup.bat first & pause & exit /b 1 )
if not exist logs\old mkdir logs\old
if exist logs\%DATA%_FedGDBD.log move /Y logs\%DATA%_FedGDBD.log logs\old\%DATA%_FedGDBD_v1.txt >nul

set COMMON=-data %DATA% -ncl %NCL% -m HtFE-img-4 -fd 512 -nc 20 -jr 1 -lbs 10 -lr 0.01 -ls 5 -gr %ROUNDS% -t 1 -go practical -did 0
cd system
start "FedGDBD-%DATA%" /min cmd /c "python -u main.py %COMMON% -algo FedGDBD > ..\logs\%DATA%_FedGDBD.log 2>&1"
cd ..
echo Fed-GDBD (fixed) restarted on %DATA%. Old log saved in logs\old\
pause
