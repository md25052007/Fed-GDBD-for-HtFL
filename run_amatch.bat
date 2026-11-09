@echo off
REM ============================================================
REM  Fixed-alpha control (see PROTOCOL.md): FedGDBD-S with one smaller alpha
REM  for every client, matched to the average alpha that AGC used.
REM     Cifar10  -> alpha 0.58      Cifar100 -> alpha 0.49
REM  Usage: run_amatch.bat Cifar10        (seeds 0, 1, 2, 3)
REM         run_amatch.bat Cifar10 4      (also seed 4, only if seed 4 was run)
REM  Starts 2 windows, each runs its seeds one after the other:
REM     window A: seed 0, then seed 2 (then seed 4 if asked)
REM     window B: seed 1, then seed 3
REM  Logs: logs_novelty\<Data>_FedGDBD-S-amatch.log for seed 0,
REM        logs_novelty_seed<N>\<Data>_FedGDBD-S-amatch.log for the others.
REM ============================================================
cd /d "%~dp0"
set DATA=%1
set EXTRA=%2
set NCL=
set ALPHA=
if /I "%DATA%"=="Cifar10"  set NCL=10
if /I "%DATA%"=="Cifar10"  set ALPHA=0.58
if /I "%DATA%"=="Cifar100" set NCL=100
if /I "%DATA%"=="Cifar100" set ALPHA=0.49
if "%NCL%"=="" ( echo Usage: run_amatch.bat Cifar10  or  Cifar100 & pause & exit /b 1 )

call .venv\Scripts\activate.bat || ( echo Run setup.bat first & pause & exit /b 1 )

cd dataset
python generate_%DATA%.py noniid - dir || ( echo Dataset generation failed & pause & exit /b 1 )
cd ..
for %%S in (1 2 3 4) do if not exist logs_novelty_seed%%S mkdir logs_novelty_seed%%S
if not exist logs_novelty mkdir logs_novelty

set BASE=-data %DATA% -ncl %NCL% -m HtFE-img-4 -fd 512 -nc 20 -jr 1 -lbs 10 -lr 0.01 -ls 5 -gr 20 -t 1 -did 0 --gdbd_teacher val --gdbd_alpha %ALPHA% -algo FedGDBD-S
set R0=python -u main.py %BASE% -go novelty_amatch --seed 0 ^> ..\logs_novelty\%DATA%_FedGDBD-S-amatch.log 2^>^&1
set R1=python -u main.py %BASE% -go novelty_seed1_amatch --seed 1 ^> ..\logs_novelty_seed1\%DATA%_FedGDBD-S-amatch.log 2^>^&1
set R2=python -u main.py %BASE% -go novelty_seed2_amatch --seed 2 ^> ..\logs_novelty_seed2\%DATA%_FedGDBD-S-amatch.log 2^>^&1
set R3=python -u main.py %BASE% -go novelty_seed3_amatch --seed 3 ^> ..\logs_novelty_seed3\%DATA%_FedGDBD-S-amatch.log 2^>^&1
set R4=python -u main.py %BASE% -go novelty_seed4_amatch --seed 4 ^> ..\logs_novelty_seed4\%DATA%_FedGDBD-S-amatch.log 2^>^&1

cd system
if "%EXTRA%"=="4" (
  start "amatch-A-%DATA%" /min cmd /c "%R0% & %R2% & %R4%"
) else (
  start "amatch-A-%DATA%" /min cmd /c "%R0% & %R2%"
)
start "amatch-B-%DATA%" /min cmd /c "%R1% & %R3%"
cd ..

echo.
echo Started the fixed-alpha control on %DATA% (alpha %ALPHA%) in 2 minimised windows.
echo Do NOT close them. Keep the laptop plugged in and awake.
echo Progress: check_novelty.bat (seed 0) or check_novelty_seed1/2/3.bat
pause
