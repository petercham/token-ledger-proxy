"""ComfyUI watchdog - keeps the 20003 ComfyUI instance alive.

Parallel companion to ledger_watchdog.py. That one guards the 8080 proxy and
the 8787 LLM engine; this one guards ComfyUI on 20003. Both are launched by
the same startup bat. ComfyUI's own start_comfyui.bat already holds marker
43174 and pins the RTX 4090, so relaunching here can never start a second copy.

Lock 43180 = this watchdog's own single-instance marker (distinct from the
engine watchdog 43176 and from service_guard's 43174/43175/43177).

Boot-time RAM race guard:
  Basalt loads ~26GB of weights and pins a large RAM arena at boot. That
  machine has a hard 16GB ram-reserve guard and once died silently when RAM
  ran low during load. ComfyUI initializing torch/CUDA grabs a few more GB.
  Starting both at once makes them fight over system RAM (VRAM is not the
  issue - they use different GPUs). So before the FIRST ComfyUI launch this
  watchdog waits for the 8787 engine to be listening, then gives it a short
  stabilization window. The wait is skipped when ComfyUI is already up, and
  has a timeout fallback so a broken engine can never block ComfyUI forever.
"""
import os
import socket
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "comfy-watchdog.log")
CHILD_LOG = os.path.join(HERE, "comfy-child.log")
HOST = "127.0.0.1"
PORT = 20003
LOCK = 43180
INTERVAL_S = 5.0
COOLDOWN_S = 10.0          # min gap between two relaunch attempts
GRACE_S = 300.0            # ComfyUI loads models slowly; stay quiet this long
PROBE_TIMEOUT_S = 0.5
ENGINE_PORT = 8787             # Basalt LLM engine - must load before ComfyUI at boot
ENGINE_WAIT_TIMEOUT_S = 600.0  # max wait for engine at boot before fallback launch
ENGINE_STABILIZE_S = 60.0      # settle after engine is up (CUDA graph / pinned RAM)
COMFY_BAT = r"C:\Work\ComfyUI-aki-v3.2\start_comfyui.bat"
COMFY_DIR = r"C:\Work\ComfyUI-aki-v3.2"
_DETACHED = 0x00000008
_NEW_GROUP = 0x00000200


def log(msg):
    line = "[%s] %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def port_up(host, port, timeout=PROBE_TIMEOUT_S):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def wait_for_engine_ready():
    """At boot, let Basalt finish loading weights before ComfyUI starts.

    Both compete for system RAM, not VRAM (different GPUs). Basalt has a hard
    16GB ram-reserve guard and once exited silently when RAM ran low mid-load.
    Returns True if the engine came up, False on timeout fallback.
    """
    deadline = time.monotonic() + ENGINE_WAIT_TIMEOUT_S
    log("boot RAM guard: waiting for LLM engine on %d (max %.0fs) before ComfyUI"
        % (ENGINE_PORT, ENGINE_WAIT_TIMEOUT_S))
    while time.monotonic() < deadline:
        if port_up(HOST, ENGINE_PORT, 1.0):
            log("LLM engine on %d is ready; settling %.0fs before ComfyUI"
                % (ENGINE_PORT, ENGINE_STABILIZE_S))
            time.sleep(ENGINE_STABILIZE_S)
            return True
        time.sleep(INTERVAL_S)
    log("engine not up after %.0fs; launching ComfyUI anyway (fallback)"
        % ENGINE_WAIT_TIMEOUT_S)
    return False


def launch_comfy():
    """Start ComfyUI via its own bat (holds marker 43174, pins RTX 4090)."""
    logf = open(CHILD_LOG, "a", encoding="utf-8")
    kwargs = {"cwd": COMFY_DIR, "stdin": subprocess.DEVNULL,
              "stdout": logf, "stderr": subprocess.STDOUT, "close_fds": True}
    if os.name == "nt":
        kwargs["creationflags"] = _DETACHED | _NEW_GROUP
    try:
        proc = subprocess.Popen(
            [r"C:\Windows\System32\cmd.exe", "/c", COMFY_BAT], **kwargs)
        log("comfy relaunch issued: pid=%d" % proc.pid)
    finally:
        logf.close()


def main():
    # single-instance lock: only one comfy watchdog runs
    lock_sock = socket.socket()
    try:
        lock_sock.bind((HOST, LOCK))
    except OSError:
        log("another comfy watchdog already holds lock %d, nothing to do" % LOCK)
        return 0
    log("comfy watchdog started; probe=%s:%d; grace=%.0fs; bat=%s"
        % (HOST, PORT, GRACE_S, COMFY_BAT))

    # Boot-time RAM race guard: only needed when ComfyUI is not already up.
    if not port_up(HOST, PORT):
        wait_for_engine_ready()

    last_launch = None
    while True:
        try:
            if not port_up(HOST, PORT):
                now = time.monotonic()
                if last_launch is not None and now - last_launch < GRACE_S:
                    left = GRACE_S - (now - last_launch)
                    log("comfy down but in load grace, %.0fs left; skip" % left)
                elif last_launch is None or now - last_launch >= COOLDOWN_S:
                    log("COMFY DOWN: %s:%d refused -> relaunch" % (HOST, PORT))
                    launch_comfy()
                    last_launch = now
                else:
                    log("COMFY DOWN still; in cooldown, skip")
        except Exception:
            import traceback
            log("comfy watchdog ERROR: " + traceback.format_exc())
        time.sleep(INTERVAL_S)


if __name__ == "__main__":
    sys.exit(main())