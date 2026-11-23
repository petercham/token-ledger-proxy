#!/usr/bin/env python3
r"""token-ledger · built-in hardware sampler + fully self-owned monitor page.

Runs inside the ledger proxy (one process, one port), so the ledger and the
monitor are ONE thing:

  * RAM / swap / per-physical-disk I/O / per-network-adapter rates (psutil)
  * EVERY GPU in the box, including TCC compute cards that Windows Task
    Manager cannot see (nvidia-smi --query-gpu, one row per GPU)
  * routes /monitor, /monitor.js, /ext.json, /ext.js, /health are answered
    here on the SAME origin as the console

2026-11-16 refactor (this revision): the monitor no longer injects anything
into Strata's official web page. The old `attach()` / `pages()` / `Watcher`
mechanism is deleted outright -- this kit never writes to any page it does not
own. The page is now our own: `/monitor` serves monitor.html, which loads
/monitor.js, which reads /ext.json. No official DOM, sprite, or CSS required.

Why: on the production box a GPU waveform was drawn on the wrong card. The old
page keyed its history by the nvidia-smi `index` while labelling cards by card
name, and that index order drifts on this machine (a scheduled task
disables/re-enables one card at boot; a past incident mapped gpu:0 to the wrong
card and the reported decode rate dropped 210 -> 13.7 tok/s). Slot numbers are
NOT a valid identity on this box. Identity is the GPU UUID / card name. The new
page binds cards and waveform history by UUID; `index` is display-only.

Design rule (unchanged): nothing here may break accounting. Every background
thread wraps its work in try/except, and the HTTP handler only ever reads a
cached snapshot.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MB = 2.0 ** 20

try:
    import psutil
except Exception:                       # a runtime without psutil still answers
    psutil = None

# adapters that are not a physical link
NET_SKIP = ("loopback", "vethernet", "hyper-v", "virtual", "vmware", "virtualbox", "bluetooth",
            "tap-", "tun", "wsl", "npcap", "teredo", "isatap")

# One nvidia-smi call returns every card; TCC cards answer NVML normally even
# though Windows performance counters (Task Manager) cannot see them.
#
# 18 fields, in this order. `uuid` is the STABLE identity of a card; `index`
# is a slot number that can drift and must never be used as a key.
# The last four fields are the PER-CARD PCIe link (current vs max gen/width),
# shown as NEUTRAL information only (user rule, 2026-11-16 rev4): x8 is the
# normal steady state on this platform (7950X gives each card 8 lanes) and
# idle cards downclock to Gen1 on purpose — never raise alarms on these.
# Driver-verified on 621.24: all four query names answer normally (rc=0).
GPU_QUERY = (
    "index,name,driver_model.current,memory.total,memory.used,"
    "utilization.gpu,temperature.gpu,power.draw,power.limit,clocks.sm,"
    "uuid,utilization.memory,utilization.encoder,utilization.decoder,"
    "pcie.link.gen.current,pcie.link.width.current,"
    "pcie.link.gen.max,pcie.link.width.max"
)
GPU_FIELDS = 18
GPU_INTERVAL = 2.0                     # nvidia-smi costs ~150 ms; 2 s is plenty

# ---- gate observation channel (rev10): the proxy pushes snapshots, the
# sampler merges them into /ext.json. No push ever = the "gate" field is
# simply absent (existing frontends and selftests tolerate that). ----
_GATE_LOCK = threading.Lock()
_GATE_STATE = None


def push_gate(state: dict):
    try:
        with _GATE_LOCK:
            global _GATE_STATE
            _GATE_STATE = dict(state)
            _GATE_STATE["_at"] = time.time()
    except Exception:
        pass                           # observation must never break accounting


def get_gate():
    with _GATE_LOCK:
        return _GATE_STATE


class PdhClock:
    r"""Task-Manager-equivalent real-time CPU clock (2026-11-17, user rule).

    Task Manager "Speed" = \Processor Information(_Total)\% Processor
    Performance (PDH rate counter) x base clock (Win32_Processor.MaxClockSpeed).
    The registry ~MHz is NOT it -- on Win11 it sits frozen at the base clock
    (observed: 4500 constant while Task Manager shows 5.0+ GHz).

    Stdlib only: pdh.dll via ctypes. Any failure -> sample() returns None and
    the frontend simply omits the figure. Counter deltas are per collect call,
    so one collect per sampler tick (1 s) matches Task Manager's own window.
    """

    PDH_FMT_DOUBLE = 0x00000200

    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self._ctypes = ctypes
        self._pdh = ctypes.WinDLL("pdh.dll")
        base = 0
        try:  # WMI MaxClockSpeed, the same source Task Manager multiplies with
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_Processor).MaxClockSpeed"],
                capture_output=True, timeout=15, creationflags=0x08000000)
            base = int(float(r.stdout.decode(errors="replace").strip()))
        except Exception:
            base = 0
        if not base:
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                    r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                    base = int(winreg.QueryValueEx(k, "~MHz")[0])
            except OSError:
                base = 0
        if base <= 0:
            raise RuntimeError("no base clock")
        self._base_mhz = base

        class _Value(ctypes.Structure):
            _fields_ = [("dwStatus", ctypes.c_uint32),
                        ("_pad", ctypes.c_uint32),
                        ("value", ctypes.c_double)]

        self._Value = _Value
        self._query = ctypes.c_void_p()
        self._counter = ctypes.c_void_p()
        rc = self._pdh.PdhOpenQueryW(None, 0, ctypes.byref(self._query))
        if rc:
            raise RuntimeError(f"PdhOpenQueryW rc={rc:#x}")
        # English counter path: locale-proof on zh-CN Windows
        rc = self._pdh.PdhAddEnglishCounterW(
            self._query, r"\Processor Information(_Total)\% Processor Performance",
            0, ctypes.byref(self._counter))
        if rc:
            raise RuntimeError(f"PdhAddEnglishCounterW rc={rc:#x}")
        self._pdh.PdhCollectQueryData(self._query)   # prime the rate window

    def sample(self):
        ctypes = self._ctypes
        if self._pdh.PdhCollectQueryData(self._query):
            return None
        v = self._Value()
        rc = self._pdh.PdhGetFormattedCounterValue(
            self._counter, self.PDH_FMT_DOUBLE, None, ctypes.byref(v))
        if rc or v.dwStatus:
            return None                            # busy / no data yet
        return self._base_mhz * v.value / 100.0


def cpu_name() -> str:
    r"""Static CPU model string for the monitor CPU card title (2026-11-17).

    Windows: registry ProcessorNameString (the same source Task Manager shows);
    Linux: first 'model name' line in /proc/cpuinfo. Stdlib only, read once and
    cached by the sampler. Any failure -> "" and the frontend keeps the plain
    'CPU' title -- never invents a name.
    """
    name = ""
    try:
        if os.name == "nt":
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                name = str(winreg.QueryValueEx(k, "ProcessorNameString")[0])
        else:
            with open("/proc/cpuinfo", "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.lower().startswith("model name"):
                        name = line.split(":", 1)[1].strip()
                        break
    except Exception:
        return ""
    name = " ".join(name.split())  # OEM strings carry padding spaces
    return name[:64]


def net_kind(name: str):
    low = name.lower()
    if any(s in low for s in ("wi-fi", "wifi", "wlan", "wireless", "无线")):
        return "wifi"
    if any(s in low for s in ("ethernet", "以太网", "本地连接", "lan")):
        return "wired"
    return None


def _num(raw):
    """nvidia-smi writes 'N/A' / '[Not Supported]' for missing counters."""
    text = str(raw).strip()
    if not text or text.upper() in ("N/A", "[NOT SUPPORTED]", "NAN", "NONE"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _smi_exe() -> str:
    """Locate nvidia-smi without baking in any drive-letter path.

    On Windows the driver installs it under %SystemRoot%/System32. When that
    variable is absent (Linux/macOS, or a stripped environment) we fall back to
    the bare command and let PATH resolve it. Behaviour is unchanged: either
    way a missing executable yields "nvidia-smi".
    """
    root = os.environ.get("SystemRoot") or ""
    if not root:
        return "nvidia-smi"
    found = os.path.join(root, "System32", "nvidia-smi.exe")
    return found if os.path.isfile(found) else "nvidia-smi"


def parse_gpu_csv(text: str) -> list:
    """Turn nvidia-smi CSV output into one dict per GPU. Pure function.

    Parsing is csv-module based (with skipinitialspace) so a card name
    containing a comma stays one field: nvidia-smi separates with ", " and
    quotes fields that contain commas, and a quote only counts as a quote
    when the leading space is skipped. Rows with fewer than GPU_FIELDS
    columns are dropped (a driver too old to answer the last four queries
    must not produce half-empty cards with wrong values in wrong slots).

    Identity contract: `uuid` is the key callers must use. `index` is included
    for display only and is NOT stable across boots / device re-enumeration.
    """
    rows = []
    for parts in csv.reader(io.StringIO(text or ""), skipinitialspace=True):
        parts = [p.strip() for p in parts]
        if len(parts) < GPU_FIELDS:
            continue
        idx = _num(parts[0])
        if idx is None:
            continue
        uuid_val = parts[10]
        # Without a UUID we cannot bind history safely. Fall back to the card
        # name (stable enough on every driver we ship for); never to the index.
        if not uuid_val or uuid_val.upper() in ("N/A", "[NOT SUPPORTED]"):
            uuid_val = "name:" + (parts[1] or "gpu%d" % int(idx))
        total, used = _num(parts[3]), _num(parts[4])
        rows.append({
            "uuid": uuid_val,
            "index": int(idx),
            "name": parts[1],
            "mode": parts[2] if parts[2] and parts[2].upper() != "N/A" else "",
            "mem_total_mib": total,
            "mem_used_mib": used,
            "util": _num(parts[5]),
            "temp": _num(parts[6]),
            "power": _num(parts[7]),
            "power_limit": _num(parts[8]),
            "sm_clock": _num(parts[9]),
            "mem_util": _num(parts[11]),
            "enc_util": _num(parts[12]),
            "dec_util": _num(parts[13]),
            # Per-card PCIe link, current vs capability. _num() tolerates N/A
            # on very old drivers (row shape is still 18 columns because the
            # query itself succeeded).
            "pcie_gen": _num(parts[14]),
            "pcie_width": _num(parts[15]),
            "pcie_gen_max": _num(parts[16]),
            "pcie_width_max": _num(parts[17]),
        })
    return rows


def gpu_sample() -> list:
    """All physical GPUs, one dict each. Never raises: a missing driver just yields []."""
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        r = subprocess.run(
            [_smi_exe(), f"--query-gpu={GPU_QUERY}", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=8, creationflags=flags,
        )
        return parse_gpu_csv(r.stdout or "")
    except Exception:
        return []


# Per-card PCIe throughput (rxpci/txpci MB/s). The 621.24 driver has NO
# `pcie.throughput.tx/rx` query field (rc=2, "not a valid field to query"),
# so we read the same counters via `nvidia-smi dmon -s t`. -c 2 keeps the
# LAST line, which is measured over a full 1 s window (the first line is
# an instant/short-window sample). ~1.4 s wall, runs on the GPU tick inside
# the sampler thread — the proxy and /ext.json serving are never blocked.
# Rows are keyed by enumeration index; we pair them with uuids INSIDE THE
# SAME tick (gpu_sample and dmon enumerate in the same natural order), so
# the cross-time uuid identity contract is untouched.
def parse_dmon_txrx(text: str) -> dict:
    """`dmon -s t` scrolling output -> {gpu_index: (rx_mb_s, tx_mb_s)}.

    Header lines start with '#'. Non-numeric / N/A cells are skipped.
    When the same index appears several times, the LAST sample wins.
    """
    out = {}
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            idx = int(parts[0])
            rx = float(parts[1])
            tx = float(parts[2])
        except ValueError:
            continue  # header remnants, N/A cells, garbage
        out[idx] = (rx, tx)
    return out


def gpu_txrx_sample() -> dict:
    """{gpu_index: (rx_mb_s, tx_mb_s)} via dmon; {} on any failure (e.g. no
    dmon support on this platform/driver — the page then says 不支持)."""
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        r = subprocess.run(
            [_smi_exe(), "dmon", "-s", "t", "-c", "2"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=12, creationflags=flags,
        )
        return parse_dmon_txrx(r.stdout or "")
    except Exception:
        return {}


_DISK_PS = r"""
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
Get-PhysicalDisk | ForEach-Object {
  $p = $_;
  $l = @();
  try {
    $l = @(Get-Partition -DiskNumber ([int]$p.DeviceId) -ErrorAction SilentlyContinue |
           Get-Volume -ErrorAction SilentlyContinue | ForEach-Object { $_.DriveLetter } |
           Where-Object { $_ })
  } catch {}
  [pscustomobject]@{number=$_.DeviceId; model=$_.FriendlyName; bus=$_.BusType;
                    media=[string]$_.MediaType; size=$_.Size; drives=$l}
} | ConvertTo-Json -Compress
"""
MEDIA_BY_CODE = {"HDD": "HDD", "SSD": "SSD", "Unspecified": ""}


def disk_inventory() -> tuple:
    """One-time map: physical disk -> bus type, media, model, mounted letters."""
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        r = subprocess.run(["powershell", "-NoProfile", "-Command", _DISK_PS],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=30, creationflags=flags)
        items = json.loads((r.stdout or "[]").strip() or "[]")
        if isinstance(items, dict):
            items = [items]
        letter_map, out = {}, []
        for d in items:
            drives = [str(x).lower() + ":" for x in (d.get("drives") or []) if x]
            try:
                number = int(d.get("number"))
            except (TypeError, ValueError):
                number = len(out)
            for letter in drives:
                letter_map[letter] = number
            bus = str(d.get("bus") or "").upper()
            media = MEDIA_BY_CODE.get(str(d.get("media") or ""), str(d.get("media") or ""))
            label = " ".join(x for x in (bus, media) if x) or "Disk"
            out.append({"number": number, "label": f"Disk {number} · {label}",
                        "model": str(d.get("model") or ""), "size": int(d.get("size") or 0),
                        "drives": ",".join(x.upper() for x in drives)})
        return out, letter_map
    except Exception:
        return [], {}


class Sampler(threading.Thread):
    """Samples once a second in the background; /ext.json only reads the last result."""

    def __init__(self) -> None:
        super().__init__(daemon=True, name="monitor-ext-sampler")
        self.lock = threading.Lock()
        self.data = {"ok": False, "ts": 0, "error": "still starting", "gpus": []}
        self._prev_net = {}
        self._prev_disk = None
        self._prev_disks = {}
        self._prev_at = None
        self._gpus = []
        self._gpu_at = 0.0
        self._txrx = {}
        self._inv, self._letter_map = [], {}
        self._clock = None                        # PdhClock instance, False = unusable
        self._cpu_name = None                     # static CPU model, read once

    def snapshot(self) -> dict:
        with self.lock:
            return dict(self.data)

    def run(self) -> None:
        # slow one-off inventory lives here, not at import time, so the ledger
        # proxy can start listening immediately
        try:
            self._inv, self._letter_map = disk_inventory()
        except Exception:
            pass
        while True:
            try:
                self._sample()
            except Exception as exc:
                with self.lock:
                    self.data = {"ok": False, "ts": time.time(), "error": repr(exc),
                                 "gpus": self._gpus}
            time.sleep(1.0)

    def _sample(self) -> None:
        now = time.time()
        out = {"ok": psutil is not None, "ts": now}
        if psutil is None:
            out["error"] = "psutil is missing from this Python"
        else:
            vm = psutil.virtual_memory()
            out["ram"] = {"used": vm.total - vm.available, "total": vm.total}
            try:
                sw = psutil.swap_memory()
                out["swap"] = {"used": sw.used, "total": sw.total}
            except (OSError, RuntimeError):
                out["swap"] = {"used": 0, "total": 0}

            # CPU real-time clock, Task-Manager-equivalent (user rule 2026-11-17):
            # on Windows 11 the registry ~MHz value is stuck at the BASE clock
            # (4500 on this box, boost not reflected) -- Task Manager's "Speed"
            # does NOT read it. It multiplies the PDH counter
            # \Processor Information(_Total)\% Processor Performance by the base
            # clock. We read the same counter through PDH via ctypes (stdlib
            # only) once per tick. Any failure -> field missing, frontend omits.
            if os.name == "nt":
                if self._clock is None:
                    try:
                        self._clock = PdhClock()
                    except Exception:
                        self._clock = False
                if self._clock:
                    mhz = self._clock.sample()
                    if mhz:
                        out["cpu_mhz"] = mhz

            # Static CPU model for the card title (both platforms; "" -> omitted)
            if self._cpu_name is None:
                self._cpu_name = cpu_name()
            if self._cpu_name:
                out["cpu_name"] = self._cpu_name

            dt = (now - self._prev_at) if self._prev_at and now > self._prev_at else 0.0
            try:
                disk = psutil.disk_io_counters()
                per_disk = psutil.disk_io_counters(perdisk=True)
            except (OSError, RuntimeError):
                disk, per_disk = None, {}
            if disk is not None:
                if self._prev_disk is not None and dt > 0:
                    out["disk"] = {
                        "read_mb": max(0.0, (disk.read_bytes - self._prev_disk.read_bytes) / dt / MB),
                        "write_mb": max(0.0, (disk.write_bytes - self._prev_disk.write_bytes) / dt / MB),
                    }
                self._prev_disk = disk
            if per_disk:
                by_number, prev_disks = {}, {}
                for key, c in per_disk.items():
                    m = re.match(r"(?i)physicaldrive(\d+)$", key)
                    if m is None:
                        continue
                    number = int(m.group(1))
                    prev = self._prev_disks.get(key)
                    prev_disks[key] = c
                    if prev is None or dt <= 0:
                        continue
                    acc = by_number.setdefault(number, [0.0, 0.0])
                    acc[0] += max(0.0, (c.read_bytes - prev.read_bytes) / dt / MB)
                    acc[1] += max(0.0, (c.write_bytes - prev.write_bytes) / dt / MB)
                self._prev_disks = prev_disks
                inv = {d["number"]: d for d in self._inv}
                for d in self._inv:
                    by_number.setdefault(d["number"], [0.0, 0.0])
                out["disks"] = [
                    {"number": n, "read_mb": r, "write_mb": w,
                     "model": inv.get(n, {}).get("model", ""),
                     "bus": inv.get(n, {}).get("label", f"Disk {n}"),
                     "size": inv.get(n, {}).get("size", 0),
                     "drives": inv.get(n, {}).get("drives", "")}
                    for n, (r, w) in sorted(by_number.items())
                ]
            self._prev_at = now

            try:
                counters = psutil.net_io_counters(pernic=True)
                stats = psutil.net_if_stats()
            except (OSError, RuntimeError):
                counters, stats = {}, {}
            current, rows = {}, []
            for name, c in counters.items():
                if "*" in name or any(s in name.lower() for s in NET_SKIP):
                    continue
                kind = net_kind(name)
                if kind is None:
                    continue
                st = stats.get(name)
                connected = bool(st.isup) if st is not None else True
                current[name] = (now, c.bytes_recv, c.bytes_sent)
                row = {"name": name, "kind": kind, "connected": connected,
                       "down_mb": None, "up_mb": None}
                prev = self._prev_net.get(name)
                if connected and prev is not None and now > prev[0]:
                    span = now - prev[0]
                    row["down_mb"] = max(0.0, (c.bytes_recv - prev[1]) / span / MB)
                    row["up_mb"] = max(0.0, (c.bytes_sent - prev[2]) / span / MB)
                rows.append(row)
            self._prev_net = current
            rows.sort(key=lambda a: (not a["connected"], -((a["down_mb"] or 0) + (a["up_mb"] or 0))))
            out["net"] = rows[:4]

        if now - self._gpu_at >= GPU_INTERVAL:
            self._gpus = gpu_sample()
            # same-tick pairing: dmon rows are keyed by enumeration index,
            # identical natural order to gpu_sample() within one tick.
            try:
                txrx = gpu_txrx_sample()
            except Exception:
                txrx = {}
            self._txrx = txrx
            for g in self._gpus:
                pair = txrx.get(g["index"])
                g["pcie_rx_mb"] = pair[0] if pair else None
                g["pcie_tx_mb"] = pair[1] if pair else None
            out["pcie_txrx_supported"] = bool(txrx)
            self._gpu_at = now
        else:
            # between GPU ticks keep the last throughput pair visible
            for g in self._gpus:
                g.setdefault("pcie_rx_mb", None)
                g.setdefault("pcie_tx_mb", None)
            if "pcie_txrx_supported" not in out:
                out["pcie_txrx_supported"] = bool(getattr(self, "_txrx", None))
        out["gpus"] = self._gpus
        out["gpu_query_fields"] = GPU_FIELDS
        # gate 段（rev10）：proxy 侧 push 过且仍新鲜（30s 内）才出；否则字段整体缺席
        g = get_gate()
        if g is not None and now - g.get("_at", 0) <= 30:
            out["gate"] = {k: g[k] for k in ("inflight", "queued", "limit",
                                             "waited_total", "beat_total") if k in g}
        with self.lock:
            self.data = out


SAMPLER = Sampler()


def start(cfg: dict):
    """Boot the sampler thread. Any failure here must NOT stop the ledger proxy.

    Since 2026-11-16 there is no page watcher: this kit owns its own /monitor
    page and never writes to a page it does not own. `web_root` in the config is
    therefore inert for the monitor (it stays accepted so old configs keep
    loading without errors).
    """
    try:
        SAMPLER.start()
        return SAMPLER
    except Exception:
        return None


def _read_asset(name: str, ctype: str):
    """Serve one file this package owns; a missing file answers empty, never raises."""
    try:
        return (HERE / name).read_bytes(), ctype
    except OSError:
        return b"", ctype


def answer(path: str):
    """Return (body, content-type) for our own routes, or None to fall through.

    NOTE: "/" must NOT be claimed here — on the console port it belongs to the
    engine upstream. Our page lives at "/monitor".
    """
    if path == "/ext.json":
        return json.dumps(SAMPLER.snapshot()).encode("utf-8"), "application/json; charset=utf-8"
    if path == "/monitor":
        return _read_asset("monitor.html", "text/html; charset=utf-8")
    if path == "/monitor.js":
        return _read_asset("monitor.js", "text/javascript; charset=utf-8")
    if path == "/monitor.css":
        return _read_asset("monitor.css", "text/css; charset=utf-8")
    if path == "/monitor-sprite.svg":
        return _read_asset("monitor-sprite.svg", "image/svg+xml")
    if path == "/ext.js":
        # Retired integration shim, kept only so an official page that still
        # carries the old <script src="/ext.js"> line keeps working until that
        # line is removed. New deployments should open /monitor instead.
        return _read_asset("ext.js", "text/javascript; charset=utf-8")
    if path == "/health":
        return b'{"ok":true}', "application/json; charset=utf-8"
    return None
