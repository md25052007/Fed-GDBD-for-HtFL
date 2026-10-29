@echo off
REM ============================================================
REM  Launch FedGDBD-S (stabilised Fed-GDBD) on one dataset.
REM  Usage: run_fedgdbd_s.bat Cifar10   or   run_fedgdbd_s.bat Cifar100
REM  Other runs and logs are left untouched.
REM ============================================================
cd /d "%~dp0"
set DATA=%1
set NCL=
if /I "%DATA%"=="Cifar10"  set NCL=10
if /I "%DATA%"=="Cifar100" set NCL=100
if "%NCL%"=="" ( echo Usage: run_fedgdbd_s.bat Cifar10  or  Cifar100 & pause & exit /b 1 )
set ROUNDS=50
call .venv\Scripts\activate.bat || ( echo Run setup.bat first & pause & exit /b 1 )
set COMMON=-data %DATA% -ncl %NCL% -m HtFE-img-4 -fd 512 -nc 20 -jr 1 -lbs 10 -lr 0.01 -ls 5 -gr %ROUNDS% -t 1 -go practical -did 0
cd system
start "FedGDBD-S-%DATA%" /min cmd /c "python -u main.py %COMMON% -algo FedGDBD-S > ..\logs\%DATA%_FedGDBD-S.log 2>&1"
cd ..
echo FedGDBD-S (stabilised) started on %DATA%.
pause
