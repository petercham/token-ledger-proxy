#!/usr/bin/env python3
r"""Regression selftest for ledger_watchdog.py (temporary ports only).

Never touches production 8080 / 43176 / 43177. Spins up a fake listener on a
free loopback port, points the watchdog at it via --launch-cmd, and checks the
two 2026-11-09 hardening features: live interval reload and instant wake flag.

Run:  python usage/selftest_watchdog.py
"""
import importlib.util
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
from datetime import datetime
import time

# Resolve from this file: works unchanged on Windows / Linux / macOS.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # tests/ -> project root
WD_SCRIPT = os.path.join(ROOT, "gateway", "ledger_watchdog.py")
PORT = 19080
EPORT = 19090
LOCK = 43976
KILL_SIG = getattr(signal, "SIGKILL", 9)
PASS, FAIL = [], []


def rec(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print("  %-4s %-52s %s" % ("PASS" if ok else "FAIL", name, detail))


def port_up(port, timeout=0.3):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    except OSError:
        return False
    finally:
        try:
            s.close()
        except OSError:
            pass


FAKE_SERVICE = r'''
import os, socket, sys, time
port = int(sys.argv[1]); pidfile = sys.argv[2]
with open(pidfile, "a", encoding="utf-8") as f:
    f.write(str(os.getpid()) + "\n")
s = socket.socket()
s.bind(("127.0.0.1", port))
s.listen(8)
while True:
    time.sleep(1)
'''


def main():
    tmp = tempfile.mkdtemp(prefix="wd-selftest-")
    cfg = os.path.join(tmp, "config.json")
    fake = os.path.join(tmp, "fake_service.py")
    pidfile = os.path.join(tmp, "fake.pid")
    wdlog = os.path.join(tmp, "watchdog.log")
    flag = os.path.join(tmp, "relaunch-now.flag")
    with open(fake, "w", encoding="utf-8") as f:
        f.write(FAKE_SERVICE)

    def write_cfg(**kw):
        with open(cfg, "w", encoding="utf-8") as f:
            json.dump(kw, f)

    def wdlog_text():
        try:
            with open(wdlog, encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""

    def fake_pids():
        try:
            with open(pidfile, encoding="utf-8") as f:
                return [int(x) for x in f.read().split()]
        except (OSError, ValueError):
            return []

    spec = importlib.util.spec_from_file_location("wd", WD_SCRIPT)
    wd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wd)

    print("=== unit checks ===")
    write_cfg()
    rec("default interval/cooldown = 5/5", wd.read_settings(cfg) == (5.0, 5.0),
        str(wd.read_settings(cfg)))
    write_cfg(watchdog_interval_s=2, watchdog_relaunch_cooldown_s=1)
    rec("config values are read live", wd.read_settings(cfg) == (2.0, 1.0),
        str(wd.read_settings(cfg)))
    write_cfg(watchdog_interval_s=0, watchdog_relaunch_cooldown_s=99999)
    rec("out-of-range values fall back", wd.read_settings(cfg) == (5.0, 5.0),
        str(wd.read_settings(cfg)))
    with open(cfg, "w", encoding="utf-8") as f:
        f.write("{ broken json")
    rec("broken config does not crash", wd.read_settings(cfg) == (5.0, 5.0))
    rec("port_is_up on a closed port is False", wd.port_is_up("127.0.0.1", PORT) is False)

    print("=== engine guard unit checks (rev17) ===")
    write_cfg()
    g = wd.read_engine_settings(cfg)
    rec("engine guard default off", g[0] is False and g[2] is None, str(g[:3]))
    write_cfg(guard_engine=True)
    g = wd.read_engine_settings(cfg)
    rec("guard on without cmd stays off", g[0] is False, str(g[:3]))
    write_cfg(guard_engine=True, engine_backend="Basalt",
              upstream="http://127.0.0.1:19099/",
              engine_launch={"cmd": [sys.executable, "-c", "pass"], "cwd": tmp},
              engine_grace_s=7)
    g = wd.read_engine_settings(cfg)
    rec("guard parses backend/port/cwd/grace",
        g[0] is True and g[1] == "basalt" and g[3] == os.path.normpath(tmp)
        and g[4] == 7.0 and g[5] == 19099, str(g[1:]))
    write_cfg(guard_engine=True, upstream="http://host:7000/v1",
              engine_launch={"cmd": ["x"]})
    g = wd.read_engine_settings(cfg)
    rec("upstream trailing port parse with path", g[5] == 7000, str(g[5]))
    write_cfg(guard_engine=True, upstream="http://[::1]:8787",
              engine_launch={"cmd": ["x"]})
    g = wd.read_engine_settings(cfg)
    rec("upstream IPv6 bracket port parse", g[5] == 8787, str(g[5]))
    write_cfg(guard_engine=True, engine_launch={"cmd": ["ok", 123]})
    g = wd.read_engine_settings(cfg)
    rec("non-string cmd token -> guard stays off", g[0] is False, str(g[:3]))
    write_cfg(guard_engine=True, engine_launch={"cmd": []})
    g = wd.read_engine_settings(cfg)
    rec("empty cmd -> guard stays off", g[0] is False, str(g[:3]))
    with open(cfg, "w", encoding="utf-8") as f:
        f.write("{ broken json")
    g = wd.read_engine_settings(cfg)
    rec("broken config -> engine guard off, no crash", g[0] is False)

    logs = []
    state = [0.0]
    t0 = time.monotonic()
    woken = wd.wait_cycle(1.2, os.path.join(tmp, "absent.flag"), state, logs.append)
    rec("wait_cycle without flag sleeps full cycle", not woken and time.monotonic() - t0 >= 1.1,
        "%.2fs" % (time.monotonic() - t0))
    with open(flag, "w", encoding="utf-8") as f:
        f.write("wake")
    time.sleep(0.05)
    state = [0.0]
    t0 = time.monotonic()
    woken = wd.wait_cycle(3.0, flag, state, logs.append)
    rec("wake flag interrupts wait immediately", woken and time.monotonic() - t0 < 0.6,
        "%.2fs" % (time.monotonic() - t0))

    print("=== integration (temporary port %d, lock %d) ===" % (PORT, LOCK))
    write_cfg(watchdog_interval_s=2, watchdog_relaunch_cooldown_s=1)
    launch_cmd = '"%s" "%s" %d "%s"' % (sys.executable, fake, PORT, pidfile)
    wd_cmd = [sys.executable, WD_SCRIPT, "--config", cfg, "--port", str(PORT),
              "--lock-port", str(LOCK), "--log", wdlog, "--launch-cmd", launch_cmd]
    proc = subprocess.Popen(wd_cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, close_fds=True)
    rec("watchdog process started", proc.poll() is None, "pid=%d" % proc.pid)

    ok = False
    for _ in range(40):
        if port_up(PORT):
            ok = True
            break
        time.sleep(0.2)
    rec("down port detected -> fake service relaunched", ok,
        "log=%s" % wdlog_text().strip().splitlines()[-1:] if wdlog_text() else "no log")
    rec("startup log shows live 2s interval", "interval=2s (live from config)" in wdlog_text())
    rec("relaunched pid is the fake service", bool(fake_pids()) and
        ("relaunch issued: pid=%d" % fake_pids()[-1]) in wdlog_text(),
        "fake pid=%s" % (fake_pids()[-1:] or "none"))

    # live reload: change the interval while the watchdog is running
    time.sleep(0.3)
    write_cfg(watchdog_interval_s=3, watchdog_relaunch_cooldown_s=1)
    reloaded = False
    for _ in range(20):
        if "settings reloaded: interval=3s" in wdlog_text():
            reloaded = True
            break
        time.sleep(0.3)
    rec("interval change takes effect without restart", reloaded)

    # duplicate watchdog must not run a second probe loop
    dup = subprocess.run(wd_cmd, capture_output=True, text=True, timeout=10)
    rec("second watchdog leaves quietly", "another watchdog already runs" in
        (dup.stdout + wdlog_text()), "rc=%d" % dup.returncode)

    # instant relaunch: kill fake, touch flag, expect a fast recovery
    time.sleep(1.2)                          # let the cooldown expire
    before = len(fake_pids())
    for pid in set(fake_pids()):
        try:
            os.kill(pid, KILL_SIG)
        except OSError:
            pass
    down = False
    for _ in range(20):
        if not port_up(PORT):
            down = True
            break
        time.sleep(0.1)
    rec("fake service stopped", down)
    with open(flag, "a", encoding="utf-8") as f:
        f.write("wake again\n")
    os.utime(flag, None)
    t0 = time.monotonic()
    back = False
    for _ in range(20):
        if port_up(PORT):
            back = True
            break
        time.sleep(0.1)
    rec("wake flag triggers fast relaunch", back and time.monotonic() - t0 < 1.5,
        "%.2fs" % (time.monotonic() - t0))
    rec("a new fake pid was issued", len(fake_pids()) > before,
        "%d -> %d" % (before, len(fake_pids())))

    print("=== engine guard integration (rev17, temporary port %d) ===" % EPORT)
    rec("startup log states guard was off by default",
        "engine guard off (guard_engine not true in config)" in wdlog_text())
    fake2 = os.path.join(tmp, "fake_engine.py")
    with open(fake2, "w", encoding="utf-8") as f:
        f.write(FAKE_SERVICE)
    epidfile = os.path.join(tmp, "engine.pid")
    # hot-enable: the RUNNING watchdog must pick this up next cycle, no restart
    write_cfg(watchdog_interval_s=2, watchdog_relaunch_cooldown_s=1,
              guard_engine=True, engine_backend="basalt",
              upstream="http://127.0.0.1:%d/" % EPORT,
              engine_launch={"cmd": [sys.executable, fake2, str(EPORT), epidfile],
                             "cwd": tmp},
              engine_grace_s=3)
    guarded = False
    for _ in range(30):
        if "engine guard settings: backend=basalt" in wdlog_text():
            guarded = True
            break
        time.sleep(0.2)
    rec("guard hot-enabled from config without restart", guarded)
    ok = False
    for _ in range(40):
        if port_up(EPORT):
            ok = True
            break
        time.sleep(0.2)
    rec("down engine port -> fake engine launched", ok)
    rec("engine launch logged", "engine relaunch issued" in wdlog_text())

    # kill the engine right after its launch: grace window must suppress a
    # second launch, then after grace expires one relaunch must follow.
    epids = []
    try:
        with open(epidfile, encoding="utf-8") as f:
            epids = [int(x) for x in f.read().split()]
    except OSError:
        pass
    for pid in set(epids):
        try:
            os.kill(pid, KILL_SIG)
        except OSError:
            pass
    seen_grace = False
    t0 = time.monotonic()
    while time.monotonic() - t0 < 2.6:
        if "launch grace" in wdlog_text():
            seen_grace = True
            break
        time.sleep(0.2)
    rec("engine relaunch suppressed inside grace", seen_grace
        and wdlog_text().count("engine relaunch issued") == 1,
        "relaunches=%d" % wdlog_text().count("engine relaunch issued"))
    second = False
    for _ in range(40):
        if wdlog_text().count("engine relaunch issued") >= 2 and port_up(EPORT):
            second = True
            break
        time.sleep(0.3)
    rec("after grace a single relaunch follows", second,
        "relaunches=%d" % wdlog_text().count("engine relaunch issued"))
    rec("ledger fake survived the whole engine-guard test", port_up(PORT))

    print("--- watchdog log (for attribution) ---")
    for line in wdlog_text().strip().splitlines():
        print("   ", line)
    print("--- end log ---")

    print("=== cleanup ===")
    try:
        proc.kill()
    except OSError:
        pass
    for pid in set(fake_pids()):
        try:
            os.kill(pid, KILL_SIG)
        except OSError:
            pass
    try:
        with open(epidfile, encoding="utf-8") as f:
            for pid in set(int(x) for x in f.read().split()):
                try:
                    os.kill(pid, KILL_SIG)
                except OSError:
                    pass
    except OSError:
        pass
    time.sleep(0.2)
    shutil.rmtree(tmp, ignore_errors=True)
    print("\nRESULT: %d passed, %d failed" % (len(PASS), len(FAIL)))
    if FAIL:
        for name in FAIL:
            print("  FAILED: %s" % name)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
