@echo off
chcp 936
cls
title Token Ledger 总控看护
cd /d C:\Work\LLM\token-ledger-proxy\gateway
echo.
echo   Token Ledger 总控看护
echo   网关 8080 / 引擎 8787 / ComfyUI 门面 8188(清单自报)
echo   服务没在跑会自动启动; 日志: ledger-watchdog.log 与 guard-*.log
echo   关闭此窗口 = 停止看护, 下次开机自动再起
echo.
"C:\Work\LLM\Strata\terminal\python\python.exe" "C:\Work\LLM\token-ledger-proxy\gateway\watchdog-launcher.py"
pause
