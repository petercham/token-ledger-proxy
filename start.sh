#!/usr/bin/env bash
# Token 账本反代工具（Strata / Basalt 兼容） · Linux / macOS 启动
# 【仅交互式试跑】本脚本用 exec 把守护进程放到终端前台：关掉终端、SSH 断开
# 或会话被清理，守护进程和它拉起的服务会一起消失。生产必须安装
# service-examples/ 里的 systemd / launchd 自启件，让守护进程脱离会话常驻。
# 只拉起守护进程，由守护进程负责把服务拉起来。
set -e
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" bootstrap.py --init
"$PY" bootstrap.py --check
echo "启动守护进程……（仅交互式试跑：Ctrl+C 或关掉终端即结束；长期运行必须装 service-examples 自启件）"
exec "$PY" gateway/ledger_watchdog.py
