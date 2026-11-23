@echo off
rem start-proxy.bat - human entry for the 8080 ledger proxy (rev17b).
rem The watchdog relaunches the proxy through THIS script too, so one script
rem defines one service everywhere (manual boot == watchdog boot).
setlocal
set "PY=C:\Work\LLM\Strata\terminal\python\python.exe"
if not exist "%PY%" set "PY=python"
cd /d "%~dp0"
echo [start-proxy] proxy on 8080
"%PY%" gateway\collector_proxy.py --config "%~dp0config.json"
if "%~1"=="--no-pause" exit /b %ERRORLEVEL%
echo [start-proxy] proxy exited. Window stays open so you can read errors.
pause
