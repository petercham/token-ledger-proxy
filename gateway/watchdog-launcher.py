"""Token Ledger master console entry (rev17c).

ONE watchdog covers everything: the 8080 proxy, the 8787 engine (legacy keys)
and every entry in config.json "guard_services". On the ComfyUI side the ONLY
config entry is the split-gateway facade door (8188). WHO to guard is handed
to the watchdog by the gateway itself: the door carries watch_url and the
gateway publishes its family as self-contained launch-script entries via
GET /watchlist (ticket TK-F-20261123-2). The watchdog probes and relaunches
from that list; instance order inside the list is advisory and stripped.
The only sequencing the watchdog holds is type-level safe boot: LLM family
first, ComfyUI family after (user rulings 2026-11-23, OPS-1123-HOSTSUP rev2).

Window behavior (human request 2026-11-22): boot & manual bat both show the
live watchdog log. If the watchdog is already running (lock 43176 busy), this
window tails the log instead of starting a second copy.
"""
import os
import socket
import sys
import time

ROOT = r"C:\Work\LLM\token-ledger-proxy"
PY = r"C:\Work\LLM\Strata\terminal\python\python.exe"
WD = os.path.join(ROOT, "gateway", "ledger_watchdog.py")
LOG = os.path.join(ROOT, "logs", "ledger-watchdog.log")
LOCK = 43176


def lock_busy(port):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", port))
        return False
    except OSError:
        return True
    finally:
        s.close()


def tail_log():
    print("=== live watchdog log (closing this window does NOT stop it) ===",
          flush=True)
    with open(LOG, "r", encoding="utf-8", errors="replace") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if line:
                print(line, end="", flush=True)
            else:
                time.sleep(0.4)


if __name__ == "__main__":
    if not lock_busy(LOCK):
        print("starting single list-driven watchdog "
              "(proxy 8080 + engine 8787 + guard_services)", flush=True)
        os.chdir(ROOT)
        os.execv(PY, [PY, WD, "--lock-wait", "86400"])
    else:
        tail_log()