@echo off
rem Token 账本反代工具（Strata / Basalt 兼容） - Windows 启动（GBK + CRLF）
cd /d "%~dp0"
python bootstrap.py --init
if errorlevel 1 goto :fail
python bootstrap.py --check
if errorlevel 1 goto :fail
start "Token ledger watchdog" /min python gateway\ledger_watchdog.py
echo 已启动守护进程，由它负责拉起账本服务。
echo 查看状态： python switch_proxy.py --check
goto :eof
:fail
echo 自检未通过，没有启动任何服务。按上面的提示修好配置后重试。
exit /b 1
