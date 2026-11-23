#!/usr/bin/env python3
"""One-command setup / self-check for the portable ledger kit.

    python bootstrap.py --init       create config.json + data dir (never overwrite)
    python bootstrap.py --check      read-only environment check
    python bootstrap.py --selftest   run all three isolated regression suites

Stdlib only, Windows / Linux / macOS. This script never starts, stops or
connects to a production service; --check only looks at TCP port state.
"""
from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)          # find paths.py however this module is loaded
sys.path.insert(0, os.path.join(HERE, "gateway"))
TEMPLATE = os.path.join(HERE, "config.template.json")
CONFIG = os.path.join(HERE, "config.json")

REQUIRED = (
    "gateway/collector_proxy.py", "monitor/monitor_ext.py", "monitor/monitor.html",
    "monitor/monitor.js",
    "monitor/monitor.css", "monitor/monitor-sprite.svg",
    "monitor/ext.js", "reporting/daily_report.py", "reporting/html_report.py",
    "gateway/ledger_watchdog.py",
    "gateway/switch_proxy.py", "tests/selftest_proxy.py", "tests/selftest_watchdog.py",
    "tests/selftest_monitor.py", "tests/selftest_daily_report.py", "gateway/paths.py",
)


def say(tag, msg):
    print("  [%s] %s" % (tag, msg))


def port_state(host, port, timeout=0.4):
    """True = something is listening there."""
    h = "127.0.0.1" if host in ("0.0.0.0", "", "::", "localhost") else host
    try:
        s = socket.create_connection((h, int(port)), timeout)
        s.close()
        return True
    except OSError:
        return False


def do_init():
    if os.path.isfile(CONFIG):
        say("OK", "config.json 已存在，保持不动（不会覆盖你的配置）")
    else:
        with open(TEMPLATE, encoding="utf-8") as src:
            text = src.read()
        with open(CONFIG, "w", encoding="utf-8", newline="\n") as dst:
            dst.write(text)
        say("OK", "已生成 config.json（来自 config.template.json）")
    with open(CONFIG, encoding="utf-8") as f:
        cfg = json.load(f)
    from paths import expand_path
    out = expand_path(cfg.get("out_dir") or "@here/data", HERE)
    os.makedirs(out, exist_ok=True)
    say("OK", "数据目录就绪：%s" % out)
    say("下一步", "先按实际机器改 config.json 的 listen / upstream，再跑 --check")
    return 0


def do_check():
    if not os.path.isfile(CONFIG):
        say("FAIL", "还没有 config.json，请先跑 python bootstrap.py --init")
        return 2
    from paths import load_config
    try:
        cfg = load_config(CONFIG)
    except Exception as e:
        say("FAIL", "config.json 读不了：%s" % e)
        return 2

    fails, warns = [], []
    say("OK", "Python %s · %s" % (sys.version.split()[0], sys.platform))

    missing = [f for f in REQUIRED if not os.path.isfile(os.path.join(HERE, f))]
    if missing:
        fails.append("缺文件：%s" % ", ".join(missing))
    else:
        say("OK", "必需文件齐全（%d 个）" % len(REQUIRED))

    out = cfg.get("out_dir") or ""
    if not out:
        fails.append("out_dir 为空")
    else:
        try:
            os.makedirs(out, exist_ok=True)
            probe = os.path.join(out, ".write-test")
            with open(probe, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(probe)
            say("OK", "数据目录可写：%s" % out)
        except OSError as e:
            fails.append("数据目录不可写：%s (%s)" % (out, e))

    listen = str(cfg.get("listen") or "")
    if ":" not in listen:
        fails.append("listen 格式不对，应写成 0.0.0.0:8080 或 [::]:8080")
    else:
        host, _, port = listen.rpartition(":")
        host = host.strip("[]") or "0.0.0.0"
        try:
            int(port)
        except ValueError:
            fails.append("listen 端口不是数字：%s" % port)
        else:
            if port_state(host, port):
                warns.append("团队端口 %s 已经有程序在监听——确认是本工具的服务，或把 listen 换成别的端口" % port)
            else:
                say("OK", "团队端口 %s 空闲" % port)

    up = str(cfg.get("upstream") or "")
    if not up.startswith(("http://", "https://")):
        fails.append("upstream 必须写成 http://主机:端口 或 https://...")
    else:
        from urllib.parse import urlparse
        u = urlparse(up)
        hp = u.hostname or "127.0.0.1"
        pp = u.port or (443 if u.scheme == "https" else 80)
        if port_state(hp, pp, 1.0):
            say("OK", "引擎上游可达：%s:%s" % (hp, pp))
        else:
            warns.append("引擎上游 %s:%s 现在连不上（引擎还没起？确认端口再启动本工具）" % (hp, pp))

    lock = cfg.get("lock_port")
    if lock and port_state("127.0.0.1", lock):
        warns.append("防重复端口 %s 已被占用——可能已经有一个实例在跑" % lock)
    elif lock:
        say("OK", "防重复端口 %s 空闲" % lock)

    # R-3: the two single-instance markers must never collide.
    watchdog_lock = cfg.get("watchdog_lock_port")
    if (lock not in (None, "") and watchdog_lock not in (None, "")
            and str(lock) == str(watchdog_lock)):
        fails.append("lock_port 与 watchdog_lock_port 相同（%s）——反代与看门狗会抢同一个防重复端口，请把两者改成不同值" % lock)

    web = cfg.get("web_root") or ""
    if web:
        say("注意", "web_root 已不再使用：监控页现在自带在 http://<主机>:<端口>/monitor，"
                    "不再往任何外部页面里注入脚本。可以从 config.json 删掉这个字段（留着也不报错）：%s" % web)
    else:
        say("OK", "监控页自带在 /monitor，无需 web_root（数据接口 /ext.json、/health 始终可用）")

    # key_labels validation is READ-ONLY: it only inspects config.json.
    labels = cfg.get("key_labels")
    if not isinstance(labels, dict) or not labels:
        warns.append("key_labels 缺失或为空：所有请求会显示成 8 位指纹码，报表看着像多出匿名身份或撞车，其实只是没登记姓名，请按 README 第三节填")
    else:
        bad_keys = [str(k) for k, _ in labels.items()
                    if not isinstance(k, str) or not re.fullmatch(r"[0-9a-f]{8}", k)]
        bad_vals = [str(k) for k, v in labels.items()
                    if not isinstance(v, str) or not v.strip()]
        if bad_keys:
            fails.append("key_labels 的键必须是 8 位小写 hex 指纹，大写 hex 也不合格，请改成小写：%s" % ", ".join(bad_keys))
        if bad_vals:
            fails.append("key_labels 的值必须是非空姓名字符串：%s" % ", ".join(bad_vals))
        by_name = {}
        for k, v in labels.items():
            if isinstance(v, str) and v.strip():
                by_name.setdefault(v.strip(), []).append(str(k))
        merged = ["%s <- %s" % (name, "/".join(ks))
                  for name, ks in by_name.items() if len(ks) > 1]
        if merged:
            warns.append("多个不同指纹映射到同一姓名（%s）：可能是一人多 key，也可能是填错；合并后历史数据无法拆开，请核对" % "; ".join(merged))
        say("OK", "key_labels 校验完成（%d 条映射）" % len(labels))

    try:
        import psutil  # noqa: F401
        say("OK", "psutil 可用（内存/磁盘/网卡监控齐全）")
    except ImportError:
        warns.append("没装 psutil：显卡仍可看，内存/磁盘/网卡会缺项；记账不受影响")

    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=index,name", "--format=csv,noheader"],
                           capture_output=True, text=True, timeout=4)
        n = len([x for x in (r.stdout or "").splitlines() if x.strip()])
        say("OK", "nvidia-smi 可用，发现 %d 张显卡" % n) if n else warns.append("nvidia-smi 没返回显卡：监控会缺 GPU 项，记账不受影响")
    except Exception:
        warns.append("没有 nvidia-smi：监控会缺 GPU 项，记账不受影响")

    print("")
    for w in warns:
        say("注意", w)
    for f in fails:
        say("不合格", f)
    if fails:
        print("\n结论：%d 项不合格，先修好再启动。" % len(fails))
        return 2
    print("\n结论：可以启动（%d 条注意事项，不影响记账）。" % len(warns))
    return 0


def do_selftest():
    total_fail = 0
    for name in ("tests/selftest_proxy.py", "tests/selftest_watchdog.py", "tests/selftest_monitor.py"):
        print("\n=== %s ===" % name)
        try:
            r = subprocess.run([sys.executable, os.path.join(HERE, name)],
                               cwd=HERE, timeout=300)
            if r.returncode != 0:
                total_fail += 1
                say("FAIL", "%s 退出码 %d" % (name, r.returncode))
            else:
                say("OK", "%s 通过" % name)
        except Exception as e:
            total_fail += 1
            say("FAIL", "%s 跑不起来：%s" % (name, e))
    print("\n结论：%s" % ("三套回归全部通过" if total_fail == 0 else "%d 套回归未通过" % total_fail))
    return 0 if total_fail == 0 else 1


def main():
    args = sys.argv[1:]
    print("Token 账本反代工具（Strata / Basalt 兼容） · 便携式安装自检")
    print("目录：%s\n" % HERE)
    if "--init" in args:
        return do_init()
    if "--check" in args:
        return do_check()
    if "--selftest" in args:
        return do_selftest()
    print("用法：\n"
          "  python bootstrap.py --init       生成配置与数据目录\n"
          "  python bootstrap.py --check      只读自检（不启动/不停止任何服务）\n"
          "  python bootstrap.py --selftest   临时端口跑三套回归自测\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
