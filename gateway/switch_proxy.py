#!/usr/bin/env python3
r"""switch_proxy.py - the ONLY supported way to restart the 8080 ledger proxy.

Mandatory rules (2026-11-09, after the 13:42 outage):

  1. NEVER start collector_proxy.py from here. This tool only STOPS the old
     8080 process; the resident watchdog (ledger_watchdog.py) owns every new
     proxy process. A proxy launched directly from a chat session dies with
     that session; a proxy launched by the watchdog does not.
  2. NEVER restart 8080 while clients have active conversations. `--check` is
     a read-only safety gate. Without --force the switch refuses to run unless
     the endpoint is quiet; a BUSY endpoint is a HARD refusal (force cannot
     override it).

PORTABILITY: no drive letters, user names or absolute project paths are baked
in; everything resolves from __file__ / os.path.expanduser("~"). Port inspection
uses platform-native sources with no third-party packages:
    Windows : netstat -ano -p tcp
    Linux   : /proc/net/tcp, /proc/net/tcp6 (+ /proc/<pid>/fd for LISTEN pids)
    macOS   : lsof -nP -iTCP:<port>   (ships with macOS)
If inspection fails the tool refuses to switch. Runs on Windows / Linux / macOS.

Usage:
  python switch_proxy.py --check     # read-only: report client activity, exit 0/1/2
  python switch_proxy.py             # refuse if busy; otherwise hand off to watchdog
  python switch_proxy.py --force     # allow switching with idle keep-alive sockets

Exit codes for --check: 0 = quiet (safe to switch), 1 = idle keep-alive
(needs --force), 2 = BUSY (do not switch).

Stdlib only. Console output is plain ASCII so it stays readable under chcp 936.
"""
import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))          # gateway/
PKG_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)              # paths.py 同目录
CONFIG_PATH = os.path.join(PKG_ROOT, "config.json")
WAKE_FLAG = os.path.join(PKG_ROOT, "relaunch-now.flag")
PROXY_PORT = 8080
WATCHDOG_LOCK_PORT = 43176
QUIET_WINDOW_S = 300         # a completed request within 5 min = clients are around.
                             # Long generations can run 200-390 s and only write
                             # the ledger when they FINISH, so a short window
                             # would wrongly call a busy endpoint "idle".
RELAUNCH_WAIT_S = 25         # max wait for the watchdog to bring 8080 back
KILL_SIG = getattr(signal, "SIGKILL", 9)     # Windows has no SIGKILL; 9 = TerminateProcess


# ---- Platform-native port inspection ---------------------------------------
def _is_local(addr):
    return addr.startswith("127.") or addr.startswith("[::1]") or addr.startswith("::1")


def _from_netstat(port):
    """Windows: netstat -ano -p tcp gives both ESTABLISHED rows and LISTEN pids."""
    try:
        out = subprocess.run(["netstat", "-ano", "-p", "tcp"],
                             capture_output=True, text=True,
                             errors="replace", timeout=15).stdout
    except Exception as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)
    est, listen = [], []
    for line in out.splitlines():
        p = line.split()
        if len(p) < 5 or p[0].upper() != "TCP":
            continue
        if p[1].endswith(":" + str(port)):
            if p[3].upper() == "ESTABLISHED":
                est.append((p[1], p[2]))
            elif p[3].upper() == "LISTENING":
                try:
                    listen.append(int(p[4]))
                except ValueError:
                    pass
    return (est, listen), None


def _hex_addr(hex_ip):
    """Turn /proc's little-endian IPv4 hex into dotted form (best effort)."""
    try:
        b = bytes.fromhex(hex_ip)
        if len(b) == 4:
            return ".".join(str(x) for x in b[::-1])
    except ValueError:
        pass
    return hex_ip


def _from_proc_net(port):
    """Linux: /proc/net/tcp{,6}. State 01=ESTABLISHED, 0A=LISTEN."""
    est, inodes = [], []
    suffix = ":%04X" % port
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(path, encoding="ascii") as f:
                next(f, None)
                for line in f:
                    p = line.split()
                    if len(p) < 10 or not p[1].upper().endswith(suffix):
                        continue
                    local = p[1].rsplit(":", 1)[0]
                    remote = p[2].rsplit(":", 1)[0]
                    if p[3] == "01":
                        est.append((_hex_addr(local), _hex_addr(remote)))
                    elif p[3] == "0A":
                        inodes.append(p[9])
        except OSError:
            continue
    listen = []
    if inodes:
        wanted = set(inodes)
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            fd_dir = os.path.join("/proc", entry, "fd")
            try:
                for fd in os.listdir(fd_dir):
                    try:
                        target = os.readlink(os.path.join(fd_dir, fd))
                    except OSError:
                        continue
                    if target.startswith("socket:[") and target[8:-1] in wanted:
                        listen.append(int(entry))
                        break
            except OSError:
                continue
    return (est, listen), None


def _from_lsof(port):
    """macOS / BSD: lsof is installed by default."""
    try:
        out = subprocess.run(["lsof", "-nP", "-iTCP:%d" % port],
                             capture_output=True, text=True,
                             errors="replace", timeout=15).stdout
    except Exception as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)
    est, listen = [], []
    for line in out.splitlines()[1:]:
        p = line.split()
        if len(p) < 9:
            continue
        try:
            pid = int(p[1])
        except ValueError:
            continue
        state = line.rsplit("(", 1)[-1].rstrip(")").upper() if "(" in line else ""
        name = p[8]
        local, _, remote = name.partition("->")
        if state == "LISTEN":
            listen.append(pid)
        elif state == "ESTABLISHED":
            est.append((local, remote))
    return (est, listen), None


def port_activity(port):
    """Return ((established_pairs, listening_pids), error) on any OS."""
    if os.name == "nt" or sys.platform.startswith("win"):
        return _from_netstat(port)
    if sys.platform.startswith("linux"):
        return _from_proc_net(port)
    return _from_lsof(port)


def ledger_recent():
    """Return (is_recent, file_age_s, last_ts). A write means a completed request."""
    day = datetime.now().strftime("%Y-%m-%d")
    # The ledger may live outside the package directory (out_dir is portable).
    # Always look where the config says, not next to this script.
    try:
        from paths import load_config as portable_load_config
        out = portable_load_config(CONFIG_PATH).get("out_dir") or PKG_ROOT
    except Exception:
        out = PKG_ROOT
    path = os.path.join(out, "requests-%s.jsonl" % day)
    if not os.path.isfile(path):
        return False, None, None
    age = time.time() - os.path.getmtime(path)
    last_ts = None
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 8192))
            tail = f.read().decode("utf-8", "replace").strip().splitlines()
        if tail:
            last_ts = json.loads(tail[-1]).get("ts")
    except Exception:
        pass
    return age < QUIET_WINDOW_S, age, last_ts


def watchdog_on_duty():
    """True when the single-instance marker is already bound by the watchdog."""
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", WATCHDOG_LOCK_PORT))
        s.close()
        return False                      # nobody holds the marker
    except OSError:
        try:
            s.close()
        except OSError:
            pass
        return True                       # marker held = watchdog running


def port_up(port=None, timeout=0.5):
    # Resolve the default at CALL time, not at import time: main() rebinds the
    # module-level PROXY_PORT from config.json before any probe happens.
    if port is None:
        port = PROXY_PORT
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


def assess():
    """Return a dict describing current client activity."""
    rows, err = port_activity(PROXY_PORT)
    recent, age, last_ts = ledger_recent()
    if err or rows is None:
        return {"state": "UNKNOWN", "err": err, "est": [], "listen": [],
                "recent": recent, "age": age, "last_ts": last_ts}
    est, listen = rows
    if recent:
        state = "BUSY"                    # a request completed within the window
    elif est:
        state = "IDLE"                    # keep-alive sockets, possibly an in-flight long request
    else:
        state = "QUIET"
    return {"state": state, "err": None, "est": est, "listen": listen,
            "recent": recent, "age": age, "last_ts": last_ts}


def report(a):
    print("=== port %d client activity (read-only) ===" % PROXY_PORT)
    print("platform         : %s" % sys.platform)
    print("listening pid(s) : %s" % (a["listen"] or "none"))
    print("ESTABLISHED      : %d" % len(a["est"]))
    remote = [e for e in a["est"] if not _is_local(e[1])]
    print("  from LAN/NAS   : %d" % len(remote))
    if a["age"] is not None:
        print("ledger last write: %s  (%.1f s ago)" % (a["last_ts"] or "?", a["age"]))
    else:
        print("ledger last write: (no ledger file today)")
    print("quiet window     : %d s" % QUIET_WINDOW_S)
    print("watchdog on duty : %s" % ("YES" if watchdog_on_duty() else "NO"))
    print("state            : %s" % a["state"])
    if a["err"]:
        print("port probe error : %s" % a["err"])
    verdict = {
        "QUIET": "OK - no client activity, switching %d is allowed." % PROXY_PORT,
        "IDLE":  "CAUTION - idle connections present; switching needs --force "
                 "(a long request may be in flight, since the ledger only logs on completion).",
        "BUSY":  "REFUSE - clients are actively using %d. Do NOT restart it now." % PROXY_PORT,
        "UNKNOWN": "REFUSE - cannot determine port state.",
    }[a["state"]]
    print("verdict          : %s" % verdict)
    return {"QUIET": 0, "IDLE": 1, "BUSY": 2, "UNKNOWN": 2}[a["state"]]


def touch_flag():
    """Wake the watchdog so it probes immediately instead of waiting a cycle."""
    with open(WAKE_FLAG, "a", encoding="utf-8") as f:
        f.write("[%s] switch_proxy requested immediate relaunch\n"
                % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    os.utime(WAKE_FLAG, None)


def health():
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        r = op.open("http://127.0.0.1:%d/health" % PROXY_PORT, timeout=5)
        return r.status, r.read(120)
    except Exception as exc:
        return "ERR", str(exc).encode()[:160]


def do_switch(a, force):
    if a["state"] == "BUSY":
        print(("REFUSED: clients are active on %d. This is a hard stop; "
               "--force cannot override it. Wait for a quiet window.") % PROXY_PORT)
        return 2
    if a["state"] == "UNKNOWN":
        print("REFUSED: cannot determine port %d state (%s)." % (PROXY_PORT, a["err"]))
        return 2
    if a["state"] == "IDLE" and not force:
        print("REFUSED: %d idle connection(s) present. Re-check with --check, "
              "or pass --force if you have confirmed no long request is in flight."
              % len(a["est"]))
        return 1
    if not watchdog_on_duty():
        print("REFUSED: watchdog is not on duty (marker %d free). Start "
              "ledger_watchdog.py first - this tool must NEVER launch a proxy itself."
              % WATCHDOG_LOCK_PORT)
        return 2
    if not a["listen"]:
        print("port %d is not listening; the watchdog will bring it up on its next cycle."
              % PROXY_PORT)
        touch_flag()
        return 0

    pid = a["listen"][0]
    print("[1] stopping old port %d pid=%d (no new proxy will be started here)"
          % (PROXY_PORT, pid))
    try:
        os.kill(pid, KILL_SIG)
    except OSError as exc:
        print("    os.kill failed: %s" % exc)
        return 2
    for _ in range(40):
        if not port_up():
            break
        time.sleep(0.1)
    print("[2] port released; waking watchdog")
    touch_flag()

    t0 = time.monotonic()
    ok = False
    for _ in range(int(RELAUNCH_WAIT_S / 0.25)):
        if port_up():
            ok = True
            break
        time.sleep(0.25)
    print("[3] port %d back: %s  (%.2fs)" % (PROXY_PORT, ok, time.monotonic() - t0))
    if not ok:
        print("    !! watchdog did not relaunch. Check ledger-watchdog.log and "
              "marker %d. Do NOT start collector_proxy.py manually." % WATCHDOG_LOCK_PORT)
        return 2

    rows, _ = port_activity(PROXY_PORT)
    print("[4] new listening pid(s): %s" % ((rows[1] if rows else []) or "unknown"))
    status, body = health()
    print("[5] /health -> %s %s" % (status, body))
    print("DONE. The new proxy is a child of the watchdog, not of this session.")
    return 0 if status == 200 else 2


def main():
    global PROXY_PORT, WATCHDOG_LOCK_PORT
    # The team port and the watchdog marker both live in config.json. Rebind the
    # module-level constants here (before assess()/report()/do_switch() read
    # them) so every downstream probe follows `listen` instead of a baked 8080.
    from paths import ports_from_config
    PROXY_PORT, WATCHDOG_LOCK_PORT = ports_from_config(
        CONFIG_PATH, PROXY_PORT, WATCHDOG_LOCK_PORT)
    ap = argparse.ArgumentParser(
        description="Safe port %d proxy switch (watchdog-owned relaunch)" % PROXY_PORT)
    ap.add_argument("--check", action="store_true", help="read-only client-activity report")
    ap.add_argument("--force", action="store_true", help="allow switching with idle sockets")
    args = ap.parse_args()
    a = assess()
    rc = report(a)
    if args.check:
        return rc
    print()
    return do_switch(a, args.force)


if __name__ == "__main__":
    sys.exit(main())
