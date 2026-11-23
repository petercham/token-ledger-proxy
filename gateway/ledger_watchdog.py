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
HERE = os.path.dirname(os.path.abspath(__file__))          # gateway/
PKG_ROOT = os.path.dirname(HERE)                            # 包根＝config/logs/flag 锚
sys.path.insert(0, HERE)              # find paths.py (同目录 gateway/; paths.py lives in this dir)
CONFIG_PATH = os.path.join(PKG_ROOT, "config.json")
LOG_DIR = os.path.join(PKG_ROOT, "logs")           # rev17h: every log file lives under logs/
LOG_PATH = os.path.join(LOG_DIR, "ledger-watchdog.log")
_CRASH_LOG_PATH = os.path.join(os.path.dirname(LOG_PATH), "watchdog-crash.log")
os.makedirs(LOG_DIR, exist_ok=True)
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


# ---- guard_services (rev17c, 2026-11-22): list-driven guards. One entry per
# guarded service; every relaunch goes through that service's OWN launch
# script (the human entry point), never through an inline command the watchdog
# invents itself. config.json:
#   "guard_services": [
#     {"name": "comfyui-full",
#      "port": 20003,
#      "launch": {"cmd": [<shell>, <flag>, "<abs path to its .bat>"],
#                 "cwd": "<its dir>"},
#      "grace_s": 300,          # quiet window after a launch (model loading)
#      "cooldown_s": 10,        # optional; defaults to global cooldown
#      "wait_for": 8787,        # optional port that must be up BEFORE the
#                               # FIRST launch (boot RAM race: never load two
#                               # big models at once)
#      "stabilize_s": 60,       # extra settle time after wait_for came up
#      "wait_timeout_s": 600}   # give up waiting after this long, launch anyway
#   ]
# Entries are parsed fresh every cycle (hot-editable config). A broken entry
# is skipped; a broken list never disturbs the proxy or engine guards. Probes
# use the same raw TCP connect as 8080, so HTTP_PROXY cannot fake a verdict.

DEFAULT_SVC_GRACE_S = 120.0
DEFAULT_SVC_STABILIZE_S = 0.0
DEFAULT_SVC_WAIT_TIMEOUT_S = 600.0
MIN_SVC_S = 0.0
MAX_SVC_S = 3600.0


def _bounded_range(value, fallback, lo, hi):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return fallback
    if not lo <= v <= hi:
        return fallback
    return v


def _validate_guard_item(item, config_dir):
    """Validate ONE guard entry (from config.json or a fetched watchlist).
    Missing/broken pieces drop the single entry, never raise."""
    if not isinstance(item, dict):
        return None
    name = str(item.get("name") or "").strip()
    port = item.get("port")
    launch = item.get("launch")
    if not name or not isinstance(port, int) or not 1 <= port <= 65535:
        return None
    argv = None
    run_cwd = ""
    if isinstance(launch, dict):
        raw_argv = launch.get("cmd")
        if (isinstance(raw_argv, list) and raw_argv
                and all(isinstance(t, str) and t.strip() for t in raw_argv)):
            argv = list(raw_argv)
        raw_run = launch.get("cwd")
        if isinstance(raw_run, str) and raw_run.strip():
            try:
                from paths import expand_path
                run_cwd = expand_path(raw_run, config_dir)
            except Exception:
                run_cwd = ""
    if not argv:
        return None
    cooldown = item.get("cooldown_s")
    wait_for = item.get("wait_for")
    return {
        "name": name,
        "port": port,
        "cmd": argv,
        "cwd": run_cwd,
        "grace_s": _bounded_range(item.get("grace_s", DEFAULT_SVC_GRACE_S),
                                  DEFAULT_SVC_GRACE_S, 1.0, MAX_SVC_S),
        "cooldown_s": (_bounded_range(cooldown, None, 1.0, MAX_SVC_S)
                       if cooldown is not None else None),
        "wait_for": (wait_for if isinstance(wait_for, int)
                     and 1 <= wait_for <= 65535 else None),
        "stabilize_s": _bounded_range(
            item.get("stabilize_s", DEFAULT_SVC_STABILIZE_S),
            DEFAULT_SVC_STABILIZE_S, MIN_SVC_S, MAX_SVC_S),
        "wait_timeout_s": _bounded_range(
            item.get("wait_timeout_s", DEFAULT_SVC_WAIT_TIMEOUT_S),
            DEFAULT_SVC_WAIT_TIMEOUT_S, 1.0, MAX_SVC_S),
        "dep_timeout_action": (item.get("dep_timeout_action")
                               if item.get("dep_timeout_action")
                               in ("hold", "launch") else "hold"),
        "family": (str(item.get("family"))
                   if isinstance(item.get("family"), str) else None),
        "watch_url": (item.get("watch_url")
                      if isinstance(item.get("watch_url"), str) else None),
    }


def read_guard_services(config_path):
    """Parse config.json "guard_services" into validated entries.

    User ruling 2026-11-23 (OPS-1123-HOSTSUP rev2): who to guard is handed
    to the watchdog by the gateways themselves. A door entry may carry
    "watch_url" (loopback http) -- the gateway behind that door publishes
    its family members as self-contained launch-script entries via
    GET /watchlist. "family" names the backend TYPE (e.g. "comfyui"); the
    type-level safe-boot gate (LLM family first, ComfyUI family after) is
    the ONLY sequencing the watchdog holds for guarded services. Entries
    are parsed fresh every cycle; a broken entry is skipped.
    """
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError, TypeError, AttributeError):
        return []
    if not isinstance(cfg, dict):
        return []
    raw = cfg.get("guard_services")
    if not isinstance(raw, list):
        return []
    config_dir = os.path.dirname(os.path.abspath(config_path))
    out = []
    for item in raw:
        ent = _validate_guard_item(item, config_dir)
        if ent:
            out.append(ent)
    return out


WATCHLIST_REFRESH_S = 60.0
_last_watchlist_err = [0.0]


def fetch_watchlist(url, config_dir, log_fn):
    """GET a gateway's watchlist; loopback only, proxy bypassed.

    Instance-level ordering in the response is ADVISORY and stripped here
    (wait_for forced off): scripts are self-contained and hold their own
    single-instance gate, so relaunch order among family members does not
    matter. The family/type gate is applied by the caller from config.
    Returns validated entries, or None on any failure (list unchanged).
    """
    from urllib.request import build_opener, ProxyHandler
    from urllib.parse import urlparse
    u = urlparse(url)
    if u.scheme != "http" or u.hostname not in ("127.0.0.1", "localhost"):
        return None
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(url, timeout=3.0) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except Exception as exc:
        now = time.monotonic()
        if now - _last_watchlist_err[0] >= 120:
            log_fn("watchlist fetch failed (%s): %s" % (url, exc))
            _last_watchlist_err[0] = now
        return None
    if not isinstance(data, dict) or not isinstance(data.get("services"),
                                                    list):
        return None
    out = []
    for item in data["services"]:
        ent = _validate_guard_item(item, config_dir)
        if ent:
            ent["wait_for"] = None
            out.append(ent)
    return out


def read_proxy_launch(config_path):
    """Optional config key "proxy_launch": relaunch the 8080 proxy through a
    script (start-proxy.bat) instead of calling collector_proxy.py directly,
    so the watchdog and a human use the exact same entry point.
    {"cmd": [...], "cwd": "..."}; absent/broken -> None -> classic direct
    launch (byte-identical pre-rev17c default).
    """
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError, TypeError, AttributeError):
        return None
    launch = cfg.get("proxy_launch") if isinstance(cfg, dict) else None
    if isinstance(launch, dict):
        raw_argv = launch.get("cmd")
        if (isinstance(raw_argv, list) and raw_argv
                and all(isinstance(t, str) and t.strip() for t in raw_argv)):
            run_cwd = ""
            raw_run = launch.get("cwd")
            if isinstance(raw_run, str) and raw_run.strip():
                try:
                    from paths import expand_path
                    run_cwd = expand_path(
                        raw_run, os.path.dirname(os.path.abspath(config_path)))
                except Exception:
                    run_cwd = ""
            return {"cmd": list(raw_argv), "cwd": run_cwd}
    return None

def launch_guarded(svc, log_fn):
    """Start one guarded service through its OWN launch script, detached.

    Same discipline as the proxy/engine guards: it is our child, its console
    output goes to guard-<name>.log, and nothing here can block the loop.
    """
    safe = "".join(c if (c.isalnum() or c in "-_.") else "_"
                   for c in svc["name"])
    child_log = os.path.join(os.path.dirname(LOG_PATH) or ".",
                             "guard-%s.log" % safe)
    logf = open(child_log, "a", encoding="utf-8")
    popen_kwargs = {
        "cwd": svc["cwd"] or HERE,
        "stdin": subprocess.DEVNULL,
        "stdout": logf,
        "stderr": subprocess.STDOUT,
        "close_fds": True,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = (_DETACHED_PROCESS
                                         | _CREATE_NEW_PROCESS_GROUP)
    else:
        popen_kwargs["start_new_session"] = True
    proc = subprocess.Popen(svc["cmd"], **popen_kwargs)
    logf.close()
    log_fn("guard[%s] relaunch issued: pid=%d svc=%r"
           % (svc["name"], proc.pid, svc["cmd"]))
    return proc

def child_alive(proc):
    """True while a process WE launched is still running.

    A slow loader (6-slot engine, ComfyUI cold start) keeps its port closed
    for minutes; launching it again because the grace expired is what used
    to put two model copies in RAM at once.
    """
    try:
        return proc is not None and proc.poll() is None
    except Exception:
        return False


def _due(holder, key, now, every):
    slot = "log_" + key
    if now - holder.get(slot, 0.0) >= every:
        holder[slot] = now
        return True
    return False


def guard_cycle(services, states, log_fn, cooldown, now, gens=None):
    """One probe/relaunch pass over all guard_services entries.

    rev17f rules:
      * a child we launched that is still ALIVE but has not opened its port
        yet is never launched twice (the port opens when loading finishes);
      * the RAM steady-state gate is keyed on DEPENDENCY GENERATION, not on
        "first launch". Whenever the watchdog relaunches a dependency (the
        engine on 8787, the proxy on 8080, or another guarded service), that
        port's generation moves forward. A service whose synced generation is
        behind must wait for the dependency to come up AND stay stable for
        stabilize_s before it starts - so "both backends died and were
        restarted together" still gets the ordered, non-competing start and
        ComfyUI only comes up after the LLM backend has reached steady state;
      * a dependency that never comes up HOLDS by default
        (dep_timeout_action=launch opts back into launching anyway).
    """
    if gens is None:
        gens = {}
    for svc in services:
        st = states.setdefault(svc["name"], {"last_launch": None,
                                             "dep_met_at": None,
                                             "waiting_since": None,
                                             "gen_pending": None,
                                             "synced_gen": None,
                                             "proc": None})
        if port_is_up(LEDGER_HOST, svc["port"]):
            st["proc"] = None
            continue
        cd = svc["cooldown_s"] if svc["cooldown_s"] is not None else cooldown
        # ---- dependency-generation gate: RAM race guard ----
        dep_port = svc["wait_for"]
        if dep_port:
            dep_gen = gens.get(dep_port, 0)
            if st["synced_gen"] != dep_gen:
                if dep_gen == 0 and port_is_up(LEDGER_HOST, dep_port):
                    # New watchdog shift, dependency already running: it was
                    # never relaunched THIS shift (gen 0), so the boot ordering
                    # was satisfied by whoever booted it. A fresh shift must
                    # NOT owe a retroactive stabilize window (user ruling
                    # 2026-11-24: LLM backend never restarted, no stabilize
                    # debt). Backdate dep_met_at so the stabilize check below
                    # is already satisfied and we fall straight through to
                    # launch (first patch reset fields but fell into the
                    # dep_met_at branch and still owed the window).
                    st["synced_gen"] = dep_gen
                    st["gen_pending"] = None
                    st["dep_met_at"] = now - svc["stabilize_s"]
                    st["waiting_since"] = None
                elif st["gen_pending"] != dep_gen:
                    st["gen_pending"] = dep_gen
                    st["dep_met_at"] = None
                    st["waiting_since"] = now
                if st["dep_met_at"] is None:
                    if port_is_up(LEDGER_HOST, dep_port):
                        st["dep_met_at"] = now
                        log_fn("guard[%s]: dep %d up (gen %d); stabilize "
                               "%.0fs before launch"
                               % (svc["name"], dep_port, dep_gen,
                                  svc["stabilize_s"]))
                        continue
                    if now - st["waiting_since"] >= svc["wait_timeout_s"]:
                        if svc.get("dep_timeout_action") == "launch":
                            if _due(st, "dep", now, 120):
                                log_fn("guard[%s]: dep %d still down after "
                                       "%.0fs - launching anyway "
                                       "(dep_timeout_action=launch)"
                                       % (svc["name"], dep_port,
                                          svc["wait_timeout_s"]))
                        else:
                            if _due(st, "dep", now, 120):
                                log_fn("guard[%s]: dep %d still down after "
                                       "%.0fs - holding (dependency first, "
                                       "RAM race guard); set "
                                       "dep_timeout_action=launch to override"
                                       % (svc["name"], dep_port,
                                          svc["wait_timeout_s"]))
                            continue
                    else:
                        continue
                elif now - st["dep_met_at"] < svc["stabilize_s"]:
                    continue
                else:
                    st["synced_gen"] = dep_gen
        # ---- never double-launch a child that is still loading ----
        if child_alive(st.get("proc")):
            if _due(st, "alive", now, 60):
                log_fn("guard[%s]: port %d still closed but our child pid=%d "
                       "is alive (loading); skip relaunch"
                       % (svc["name"], svc["port"], st["proc"].pid))
            continue
        if st["last_launch"] is None or now - st["last_launch"] >= cd:
            log_fn("GUARD DOWN: %s:%d (%s) refused connection -> relaunch "
                   "via its launch script"
                   % (LEDGER_HOST, svc["port"], svc["name"]))
            st["proc"] = launch_guarded(svc, log_fn)
            st["last_launch"] = now
            gens[svc["port"]] = gens.get(svc["port"], 0) + 1
        else:
            log_fn("GUARD DOWN: %s:%d (%s) still down; relaunch in cooldown, "
                   "skip" % (LEDGER_HOST, svc["port"], svc["name"]))


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
    if args.launch_cmd:
        cmd = split_cmd(args.launch_cmd)
    else:
        via_script = read_proxy_launch(args.config)
        cmd = (via_script["cmd"] if via_script
               else [sys.executable, resolve_collector(args.config),
                     "--config", args.config])
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


def _install_crash_forensics(log_fn):
    """Never die silently: uncaught exceptions and fatal signals go to the
    watchdog log BEFORE the process exits (silent deaths 2026-11-23/24 were
    undiagnosable — log simply stopped mid-sentence with no traceback)."""
    import faulthandler, sys, threading, traceback
    def _hook(exc_type, exc, tb):
        try:
            log_fn("FATAL uncaught: " + "".join(
                traceback.format_exception(exc_type, exc, tb)).replace(
                    "\n", " | ").strip())
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc, tb)
    sys.excepthook = _hook
    def _thread_hook(args):
        _hook(args.exc_type, args.exc_value, args.exc_traceback)
    if hasattr(threading, "excepthook"):
        threading.excepthook = _thread_hook
    try:
        fh = open(_CRASH_LOG_PATH, "a", encoding="utf-8")
        faulthandler.enable(file=fh)          # segfault / access violation
        faulthandler.register(signal.SIGTERM, file=fh, all_threads=True)
    except Exception:
        pass


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
    services0 = read_guard_services(args.config)
    states = {}
    watch_cache = {}
    config_dir = os.path.dirname(args.config)
    last_guard_names = None
    if services0:
        log_fn("guard_services: " + ", ".join(
            "%s:%d" % (s["name"], s["port"]) for s in services0))
        if read_proxy_launch(args.config):
            log_fn("proxy relaunch route: via its launch script (proxy_launch)")
    os.makedirs(os.path.dirname(args.config), exist_ok=True)

    flag_state = [None]
    try:
        flag_state[0] = os.path.getmtime(flag_path)
    except OSError:
        flag_state[0] = 0.0
    last_launch = 0.0
    last_settings = (interval, cooldown)
    _install_crash_forensics(log_fn)
    last_beat = time.monotonic()
    # None = never launched by this process: the first probe of each boot must
    # check immediately. time.monotonic() is NOT zero at process start on
    # Windows (fast-boot QPC offsets of hundreds of seconds were observed
    # 2026-11-22), so a 0.0 init silently inherits a fake grace window and
    # can suppress the engine relaunch for up to `grace` seconds after boot.
    last_engine_launch = None
    last_engine_proc = None
    engine_alive_log = {}
    last_engine_settings = None
    # port -> how many times the watchdog relaunched whatever
    # serves it. Guarded services must be re-synced after a bump.
    port_gens = {}
    cycle = 0
    while True:
        # Heartbeat: one line every 10 min while healthy. A log gap then
        # localizes the death time of silent watchdog deaths (2026-11-23/24).
        if time.monotonic() - last_beat >= 600:
            last_beat = time.monotonic()
            log_fn("heartbeat ok: probe %d up, guards=%d, cycle=%d"
                   % (args.port, len(states),
                      cycle))
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
                    port_gens[args.port] = port_gens.get(args.port, 0) + 1
                else:
                    log_fn(f"DOWN: {LEDGER_HOST}:{args.port} still down; relaunch in cooldown, skip")
        except Exception:
            log_fn(f"watchdog loop ERROR: {traceback.format_exc()}")
        # ---- engine guard (rev17d; default off = nothing below ever runs) ----
        try:
            guard, backend, ecmd, ecwd, grace, eport = read_engine_settings(args.config)
            if guard and ecmd:
                if (guard, backend, eport) != last_engine_settings:
                    log_fn(f"engine guard settings: backend={backend or 'unlabelled'} "
                           f"probe={LEDGER_HOST}:{eport}")
                    last_engine_settings = (guard, backend, eport)
                if not port_is_up(LEDGER_HOST, eport):
                    now = time.monotonic()
                    if child_alive(last_engine_proc):
                        if _due(engine_alive_log, "engine", now, 60):
                            log_fn(f"engine down ({backend or '?'}:{eport}) but our "
                                   f"child pid={last_engine_proc.pid} is alive and "
                                   f"still loading; skip relaunch")
                    elif last_engine_launch is not None and now - last_engine_launch < grace:
                        left = grace - (now - last_engine_launch)
                        log_fn(f"engine down ({backend or '?'}:{eport}) but in launch "
                               f"grace, {left:g}s left; skip relaunch")
                    elif last_engine_launch is None or now - last_engine_launch >= cooldown:
                        log_fn(f"ENGINE DOWN: {LEDGER_HOST}:{eport} refused connection "
                               f"-> relaunch ({backend or 'unlabelled'})")
                        last_engine_proc = launch_engine(ecwd, ecmd, log_fn)
                        last_engine_launch = now
                        port_gens[eport] = port_gens.get(eport, 0) + 1
                    else:
                        log_fn(f"ENGINE DOWN: {LEDGER_HOST}:{eport} still down; "
                               f"relaunch in cooldown, skip")
        except Exception:
            log_fn(f"engine guard ERROR: {traceback.format_exc()}")
        # ---- guard_services (rev17c): every entry probed and relaunched
        # through its OWN launch script; config read fresh every cycle ----
        try:
            services = read_guard_services(args.config)
            # ---- watchlist hand-off (OPS-1123-HOSTSUP rev2): doors that
            # publish watch_url hand the watchdog THEIR family list.
            noww = time.monotonic()
            try:
                _, _, _, _, _, eport_now = read_engine_settings(args.config)
            except Exception:
                eport_now = eport0
            extra = []
            for door in services:
                url = door.get("watch_url")
                if not url:
                    continue
                cache = watch_cache.setdefault(door["name"],
                                               {"t": 0.0, "list": None})
                if port_is_up(LEDGER_HOST, door["port"]) and (
                        noww - cache["t"] >= WATCHLIST_REFRESH_S
                        or cache["list"] is None):
                    got = fetch_watchlist(url, config_dir, log_fn)
                    if got is not None:
                        cache["t"] = noww
                        cache["list"] = got
                if cache["list"]:
                    for e in cache["list"]:
                        e = dict(e)
                        e.setdefault("family", door.get("family"))
                        extra.append(e)
            services = services + extra
            # ---- type-level safe boot: the ONLY sequencing the watchdog
            # holds for guarded services. A "comfyui"-family entry starts
            # only after the LLM engine (eport) is up and steady; members
            # within the family carry no order at all (self-contained
            # scripts + their own single-instance gates).
            for s in services:
                if s.get("family") == "comfyui" and eport_now:
                    s["wait_for"] = eport_now
                    if s["stabilize_s"] < 60.0:
                        s["stabilize_s"] = 60.0
            names = [(s["name"], s["port"]) for s in services]
            if names != last_guard_names:
                if last_guard_names is not None:
                    log_fn("guard_services reloaded: " + ", ".join(
                        "%s:%d" % (n, p) for n, p in names))
                last_guard_names = names
            if services:
                guard_cycle(services, states, log_fn, cooldown,
                            time.monotonic(), port_gens)
        except Exception:
            log_fn(f"guard_services ERROR: {traceback.format_exc()}")
        cycle += 1
        if args.cycles and cycle >= args.cycles:
            log_fn(f"selftest: {cycle} cycles done, exiting")
            return 0
        wait_cycle(interval, flag_path, flag_state, log_fn)


if __name__ == "__main__":
    sys.exit(main())
