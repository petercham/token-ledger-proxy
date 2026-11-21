#!/usr/bin/env python3
r"""Strata token-ledger watchdog - keep the 8080 ledger proxy alive across sessions.

This is a standalone resident loop (stdlib only). On Windows it is started at
logon by the Startup-folder VBS; on Linux/macOS use systemd / launchd with the
same command. It is deliberately NOT tied to any WorkBuddy conversation: once
launched it keeps running until logoff/shutdown, so ending a chat session can
never take the team's accounting endpoint down with it.

Since 2026-11-09 the process it guards also serves the hardware monitor (all
GPUs, RAM, disks, NICs) on the same 8080 origin, so one port probe keeps both
accounting and the web monitor alive. The old 8089 collector is gone.

PORTABILITY: there are NO hard-coded drive letters, user names, Python versions
or absolute project paths in this file. Everything resolves from __file__,
os.path.expanduser("~"), sys.executable, or an explicit override
(STRATA_COLLECTOR_PATH / config.json "collector_script"). Windows use of
creation flags is guarded by os.name. Runs unchanged on Windows / Linux / macOS.

Hardening 2026-11-09 (two mandatory fixes after the 13:42 outage):
  1. The probe interval is no longer a hard-coded 30 s. It is read from
     config.json EVERY cycle (watchdog_interval_s / watchdog_relaunch_cooldown_s,
     both default 5 s), so tuning the value never requires a restart.
     A closed loopback port answers with RST immediately, so PROBE_TIMEOUT_S
     is 0.5 s rather than 2 s (which only added 2 s to every recovery).
  2. A wake flag (relaunch-now.flag next to config.json) interrupts the wait
     immediately, so switch_proxy.py can ask for an instant relaunch after
     stopping the old 8080 instead of waiting up to a full probe cycle.
     --lock-wait allows a zero-gap handoff: a replacement watchdog can start
     while the old one still holds the marker, and take over the moment it exits.

THE WATCHDOG NEVER RESTARTS A HEALTHY 8080. It only ever starts a proxy when the
port is closed, and every proxy it starts is its OWN CHILD. That is the whole
point of `switch_proxy.py`: a proxy launched directly from a chat session dies
with that session, one launched by this watchdog does not.

Every cycle it probes 127.0.0.1:8080 with a raw TCP connect (socket.connect_ex),
so the machine's HTTP_PROXY environment variable cannot fake a 502. If the port
is closed it relaunches collector_proxy.py detached (DETACHED_PROCESS |
CREATE_NEW_PROCESS_GROUP on Windows) with stdout/stderr appended to the watchdog
log. collector_proxy.py's own 127.0.0.1:43177 single-instance lock makes
duplicate launches harmless; a relaunch cooldown additionally keeps the log
from being spammed. Any exception in a cycle is logged and the loop continues.

This watchdog itself holds 127.0.0.1:43176 as its own single-instance lock:
both the Startup-folder VBS and start-strata.bat may try to launch it, and a
second copy must leave quietly instead of running a duplicate probe loop.

ENGINE GUARD (rev17, 2026-11-22): the watchdog can also guard the backend the
proxy talks to (Strata or Basalt), so ONE startup-folder entry brings up the
whole chain: watchdog -> ledger proxy + engine. Controlled by config.json keys
(read fresh every cycle, like the interval — no restart needed to change them):
  "guard_engine": false        # default OFF: byte-identical pre-rev17 behaviour
  "engine_backend": "basalt"   # "strata" | "basalt" (labelled in the log)
  "engine_launch": {"cmd": [...], "cwd": "..."}   # argv list; cwd optional,
                               # supports @here/@pkg/~ expansion
  "engine_grace_s": 120        # after an engine launch, stay quiet this long
                               # (model loading holds the port closed for a while)
The engine probe is the TCP port parsed from config.json "upstream" (same
raw-socket probe as 8080). Same rules as the proxy: a healthy port is never
touched, every engine it starts is its own detached child, duplicate launches
are bounded by cooldown + grace, and failures never take the proxy loop down.

  python ledger_watchdog.py       # use a console interpreter, not pythonw.exe

Selftest / temporary-port overrides (never used in production):
  --config PATH  --port N  --lock-port N  --log PATH  --launch-cmd "..."  --cycles N
"""
import argparse
import json
import os
import shlex
import socket
import subprocess
import sys
import time
import traceback
from datetime import datetime

# ---- Resolve everything from this file; no absolute paths baked in ----------
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)              # find paths.py however this module is loaded
CONFIG_PATH = os.path.join(HERE, "config.json")
LOG_PATH = os.path.join(HERE, "ledger-watchdog.log")
CHILD_LOG_NAME = "collector-proxy.log"   # the proxy's own console output
ENGINE_LOG_NAME = "engine-child.log"     # the guarded engine's own console output
WAKE_FLAG_NAME = "relaunch-now.flag"

LEDGER_HOST = "127.0.0.1"
LEDGER_PORT = 8080
WATCHDOG_LOCK_PORT = 43176       # our own single-instance lock (8080 proxy owns 43177)
DEFAULT_INTERVAL_S = 5.0
DEFAULT_COOLDOWN_S = 5.0
MIN_S = 1.0
MAX_S = 300.0
PROBE_TIMEOUT_S = 0.5            # loopback only: a closed port answers with RST at once
WAKE_POLL_S = 0.25               # how often the interruptible wait checks the flag

# Windows process-creation flags; on non-Windows platforms they stay 0.
_DETACHED_PROCESS = 0x00000008
_CREATE_NEW_PROCESS_GROUP = 0x00000200


def log(msg, path=None):
    """Append a timestamped line to stdout and the watchdog log (best effort)."""
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    try:
        with open(path or LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def resolve_collector(config_path):
    """Locate collector_proxy.py without assuming a drive letter or user name.

    Order: explicit env override -> config.json key -> collector_proxy.py
    NEXT TO THIS FILE. No drive letters, user names, or WorkBuddy install
    assumed: this kit is self-contained and runs on Windows, Linux and macOS.
    """
    from paths import expand_path
    config_dir = os.path.dirname(os.path.abspath(os.path.expanduser(config_path)))
    override = os.environ.get("STRATA_COLLECTOR_PATH")
    if override:
        return expand_path(override, config_dir)
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
        p = cfg.get("collector_script")
        if p:
            return expand_path(p, config_dir)
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return os.path.join(HERE, "collector_proxy.py")


def _bounded(value, fallback):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return fallback
    if not MIN_S <= v <= MAX_S:
        return fallback
    return v


def read_settings(config_path):
    """Read the interval/cooldown fresh every cycle so edits take effect live."""
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
        interval = _bounded(cfg.get("watchdog_interval_s", DEFAULT_INTERVAL_S), DEFAULT_INTERVAL_S)
        cooldown = _bounded(cfg.get("watchdog_relaunch_cooldown_s", DEFAULT_COOLDOWN_S), DEFAULT_COOLDOWN_S)
        return interval, cooldown
    except (OSError, ValueError, TypeError, AttributeError):
        return DEFAULT_INTERVAL_S, DEFAULT_COOLDOWN_S


ENGINE_DEFAULT_PORT = 8787
DEFAULT_ENGINE_GRACE_S = 120.0


def read_engine_settings(config_path):
    """Engine-guard config, read fresh every cycle (hot like the interval).

    Returns (guard, backend, cmd, cwd, grace_s, engine_port). guard=False unless
    config.json says "guard_engine": true — the pre-rev17 default path never
    touches any of this. cmd must be a non-empty list of strings or the guard
    silently stays off for this cycle (a broken key must never stop the proxy
    loop). cwd supports @here/@pkg/~. engine_port comes from the "upstream"
    URL — same trailing-port parse as listen (http://host:port/... forms).
    """
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError, TypeError, AttributeError):
        return False, "", None, "", DEFAULT_ENGINE_GRACE_S, ENGINE_DEFAULT_PORT
    if not isinstance(cfg, dict) or cfg.get("guard_engine") is not True:
        return False, "", None, "", DEFAULT_ENGINE_GRACE_S, ENGINE_DEFAULT_PORT
    backend = str(cfg.get("engine_backend") or "").strip().lower()
    launch = cfg.get("engine_launch")
    cmd = None
    cwd = ""
    if isinstance(launch, dict):
        raw_cmd = launch.get("cmd")
        if (isinstance(raw_cmd, list) and raw_cmd
                and all(isinstance(t, str) and t.strip() for t in raw_cmd)):
            cmd = list(raw_cmd)
        raw_cwd = launch.get("cwd")
        if isinstance(raw_cwd, str) and raw_cwd.strip():
            try:
                from paths import expand_path
                cwd = expand_path(raw_cwd, os.path.dirname(os.path.abspath(config_path)))
            except Exception:
                cwd = ""
    grace = _bounded(cfg.get("engine_grace_s", DEFAULT_ENGINE_GRACE_S), DEFAULT_ENGINE_GRACE_S)
    engine_port = ENGINE_DEFAULT_PORT
    upstream = str(cfg.get("upstream") or "")
    if ":" in upstream:
        tail = upstream.rpartition(":")[2]
        tail = tail.split("/", 1)[0]
        try:
            engine_port = int(tail)
        except (ValueError, TypeError, AttributeError):
            pass
    return (bool(cmd)), backend, cmd, cwd, grace, engine_port


def port_is_up(host, port, timeout=PROBE_TIMEOUT_S):
    """Return True when a raw TCP connect to host:port succeeds.

    Uses socket.connect_ex instead of urllib so HTTP_PROXY / a broken proxy
    cannot make a healthy local port look down (or vice versa).
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return sock.connect_ex((host, port)) == 0
    except OSError:
        return False
    finally:
        try:
            sock.close()
        except OSError:
            pass


def wait_cycle(seconds, flag_path, state, log_fn):
    """Sleep `seconds`, but wake immediately if the relaunch flag is touched."""
    deadline = time.monotonic() + seconds
    while True:
        remain = deadline - time.monotonic()
        if remain <= 0:
            return False
        try:
            mtime = os.path.getmtime(flag_path)
            if mtime != state[0]:
                state[0] = mtime
                log_fn("wake flag touched -> probing now")
                return True
        except OSError:
            pass
        time.sleep(min(WAKE_POLL_S, remain))


def split_cmd(text):
    """Split a command line without eating backslashes in Windows paths.

    shlex.split(posix=True) treats a backslash as an escape and corrupts
    Windows paths that contain them; on Windows use posix=False and strip
    the retained quotes.
    """
    toks = shlex.split(text, posix=(os.name != "nt"))
    out = []
    for tok in toks:
        if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in ('"', "'"):
            tok = tok[1:-1]
        out.append(tok)
    return out


def launch_ledger(args, log_fn):
    """Start collector_proxy.py detached from this process and from any console.

    Production never passes --launch-cmd; the selftest uses it to point at a
    fake service on a temporary port. sys.executable is the interpreter running
    this watchdog, which is correct on every OS and survives Python upgrades.
    """
    cmd = (split_cmd(args.launch_cmd) if args.launch_cmd
           else [sys.executable, resolve_collector(args.config), "--config", args.config])
    log_path = args.log or LOG_PATH
    # The child's console output gets its own file. Sharing the watchdog log
    # meant every client that aborted mid-request made socketserver dump a
    # traceback into it, burying the probe/relaunch lines an operator reads
    # first. Destination: <log dir>/collector-proxy.log.
    child_log = os.path.join(os.path.dirname(log_path) or ".", CHILD_LOG_NAME)
    logf = open(child_log, "a", encoding="utf-8")
    # Windows detaches via creation flags. On POSIX, start a NEW SESSION so the
    # child leaves our process group: a SIGHUP from a closing terminal or a
    # dropped SSH connection can no longer take the ledger down with the
    # launcher. The parameter is POSIX-only, so it is never passed on Windows.
    popen_kwargs = {
        "cwd": HERE,
        "stdin": subprocess.DEVNULL,
        "stdout": logf,
        "stderr": subprocess.STDOUT,
        "close_fds": True,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = _DETACHED_PROCESS | _CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True
    proc = subprocess.Popen(cmd, **popen_kwargs)
    logf.close()   # the child kept its own handle; the parent must not leak one
    log_fn(f"relaunch issued: pid={proc.pid} cmd={cmd!r}")
    return proc


def launch_engine(cwd, cmd, log_fn):
    """Start the engine (Strata/Basalt) detached, same discipline as the proxy.

    Every engine this watchdog starts is its own child; the port probe decides
    whether it is needed. No creation-flag code runs on non-Windows platforms.
    Console output goes to its own file (same separation discipline as
    collector-proxy.log: engine tracebacks must never bury the watchdog log).
    """
    log_path = LOG_PATH
    engine_log = os.path.join(os.path.dirname(log_path) or ".", ENGINE_LOG_NAME)
    logf = open(engine_log, "a", encoding="utf-8")
    popen_kwargs = {
        "cwd": cwd or HERE,
        "stdin": subprocess.DEVNULL,
        "stdout": logf,
        "stderr": subprocess.STDOUT,
        "close_fds": True,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = _DETACHED_PROCESS | _CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True
    proc = subprocess.Popen(cmd, **popen_kwargs)
    logf.close()   # the child kept its own handle; the parent must not leak one
    log_fn(f"engine relaunch issued: pid={proc.pid} cmd={cmd!r}")
    return proc


def parse_args():
    ap = argparse.ArgumentParser(
        description="Token ledger watchdog (Strata/Basalt backends; team port follows config.json listen)")
    ap.add_argument("--config", default=CONFIG_PATH)
    ap.add_argument("--port", type=int, default=None,
                    help="override the team port; default follows config.json listen")
    ap.add_argument("--lock-port", type=int, default=None,
                    help="override the single-instance marker; default = watchdog_lock_port")
    ap.add_argument("--log", default=None)
    ap.add_argument("--lock-wait", type=float, default=0.0,
                    help="seconds to wait for the single-instance marker to free "
                         "up (zero-gap handoff between two watchdogs)")
    ap.add_argument("--launch-cmd", default=None,
                    help="selftest only: override the command used to relaunch")
    ap.add_argument("--cycles", type=int, default=0, help="0 = run forever")
    return ap.parse_args()


def main():
    args = parse_args()
    args.config = os.path.abspath(os.path.expanduser(args.config))
    # Follow config.json `listen` / `watchdog_lock_port` by default, so changing
    # the team port in one place keeps the watchdog probing the right socket.
    # An explicit --port / --lock-port (used by the selftests) always wins.
    # Resolve BEFORE any log line or port_is_up() reads args.port.
    from paths import ports_from_config
    cfg_port, cfg_lock = ports_from_config(args.config, LEDGER_PORT, WATCHDOG_LOCK_PORT)
    if args.port is None:
        args.port = cfg_port
    if args.lock_port is None:
        args.lock_port = cfg_lock
    log_path = args.log or LOG_PATH
    log_fn = lambda m: log(m, log_path)
    flag_path = os.path.join(os.path.dirname(args.config), WAKE_FLAG_NAME)

    # Keep `lock` alive for the whole resident loop. Only one copy may probe.
    # With --lock-wait > 0 a replacement can wait for the current owner to exit
    # and take over without ever leaving 8080 unguarded.
    deadline = time.monotonic() + max(0.0, args.lock_wait)
    lock = None
    while True:
        candidate = socket.socket()
        try:
            candidate.bind((LEDGER_HOST, args.lock_port))
            lock = candidate
            break
        except OSError:
            candidate.close()
            if time.monotonic() >= deadline:
                log_fn("another watchdog already runs, nothing to do")
                return 0
            time.sleep(0.25)

    interval, cooldown = read_settings(args.config)
    guard0, backend0, _, _, grace0, eport0 = read_engine_settings(args.config)
    log_fn(f"watchdog started; pid={os.getpid()}; probe={LEDGER_HOST}:{args.port}; "
           f"interval={interval:g}s (live from config); cooldown={cooldown:g}s; "
           f"python={sys.executable}; lock={args.lock_port}; wake={flag_path}")
    if guard0:
        log_fn(f"engine guard ON: backend={backend0 or 'unlabelled'} "
               f"probe={LEDGER_HOST}:{eport0} (from upstream); grace={grace0:g}s")
    else:
        log_fn("engine guard off (guard_engine not true in config)")
    os.makedirs(os.path.dirname(args.config), exist_ok=True)

    flag_state = [None]
    try:
        flag_state[0] = os.path.getmtime(flag_path)
    except OSError:
        flag_state[0] = 0.0
    last_launch = 0.0
    last_settings = (interval, cooldown)
    # None = never launched by this process: the first probe of each boot must
    # check immediately. time.monotonic() is NOT zero at process start on
    # Windows (fast-boot QPC offsets of hundreds of seconds were observed
    # 2026-11-22), so a 0.0 init silently inherits a fake grace window and
    # can suppress the engine relaunch for up to `grace` seconds after boot.
    last_engine_launch = None
    last_engine_settings = None
    cycle = 0
    while True:
        interval, cooldown = read_settings(args.config)
        if (interval, cooldown) != last_settings:
            log_fn(f"settings reloaded: interval={interval:g}s cooldown={cooldown:g}s")
            last_settings = (interval, cooldown)
        try:
            if port_is_up(LEDGER_HOST, args.port):
                # Healthy: stay silent, otherwise the log fills up every 5 s.
                pass
            else:
                now = time.monotonic()
                if now - last_launch >= cooldown:
                    log_fn(f"DOWN: {LEDGER_HOST}:{args.port} refused connection -> relaunch ledger")
                    launch_ledger(args, log_fn)
                    last_launch = now
                else:
                    log_fn(f"DOWN: {LEDGER_HOST}:{args.port} still down; relaunch in cooldown, skip")
        except Exception:
            log_fn(f"watchdog loop ERROR: {traceback.format_exc()}")
        # ---- engine guard (rev17; default off = nothing below ever runs) ----
        try:
            guard, backend, ecmd, ecwd, grace, eport = read_engine_settings(args.config)
            if guard and ecmd:
                if (guard, backend, eport) != last_engine_settings:
                    log_fn(f"engine guard settings: backend={backend or 'unlabelled'} "
                           f"probe={LEDGER_HOST}:{eport}")
                    last_engine_settings = (guard, backend, eport)
                if not port_is_up(LEDGER_HOST, eport):
                    now = time.monotonic()
                    if last_engine_launch is not None and now - last_engine_launch < grace:
                        left = grace - (now - last_engine_launch)
                        log_fn(f"engine down ({backend or '?'}:{eport}) but in launch grace, "
                               f"{left:g}s left; skip relaunch")
                    elif last_engine_launch is None or now - last_engine_launch >= cooldown:
                        log_fn(f"ENGINE DOWN: {LEDGER_HOST}:{eport} refused connection "
                               f"-> relaunch ({backend or 'unlabelled'})")
                        launch_engine(ecwd, ecmd, log_fn)
                        last_engine_launch = now
                    else:
                        log_fn(f"ENGINE DOWN: {LEDGER_HOST}:{eport} still down; "
                               f"relaunch in cooldown, skip")
        except Exception:
            log_fn(f"engine guard ERROR: {traceback.format_exc()}")
        cycle += 1
        if args.cycles and cycle >= args.cycles:
            log_fn(f"selftest: {cycle} cycles done, exiting")
            return 0
        wait_cycle(interval, flag_path, flag_state, log_fn)


if __name__ == "__main__":
    sys.exit(main())
