#!/usr/bin/env python3
r"""token-ledger · proxy-mode collector: a local pass-through reverse proxy for OpenAI-compatible
(/v1/chat/completions) and Anthropic-compatible (/v1/messages) backends. Every response's
`usage` object is authoritative (the provider counts it, so there is no log-parsing distortion),
and request arrival is the timestamp. Stdlib only.

  python collector_proxy.py --config <out_dir>/config.json

config keys used: out_dir, lock_port, listen ("127.0.0.1:8787"), upstream (https://api...),
upstream_key_env (env var holding the provider key; never stored on disk).

The client changes ONLY its base_url to the listen address; the proxy forwards to `upstream`
unchanged (adding Authorization from upstream_key_env when the client sent none) and writes one
canonical JSONL line per completed request, including the caller's IP (`ip`, plus `fwd` when an
X-Forwarded-For header is present).

RELAY CONTRACT (do not regress):
  1. A forwarder must never change the upstream's response rhythm. SSE responses go out as
     HTTP/1.1 chunks with headers sent immediately and every upstream chunk flushed as it
     arrives, so a long generation never looks like a dead connection to an idle-read-timeout
     gateway. The full body is accumulated only as a private copy for the final usage chunk
     (OpenAI: last data: chunk; Anthropic: message_start / message_delta), so byte-preserving
     relay costs no accounting accuracy.
  2. Non-stream responses still wait for the whole body because their Content-Length must be
     known before the headers go out; the engine itself emits nothing while it generates, so
     no forwarder can make that path incremental without changing the response. This is a
     protocol property, NOT the buffering bug that was fixed on 2026-11-09. The NAS read
     timeout has been raised on the device side to cover this path.
  3. All upstream response headers (Content-Encoding, CORS, ...) are relayed; only hop-by-hop
     and framing headers are dropped. Request headers are relayed the same way, so x-api-key /
     anthropic-version / Accept survive on every endpoint, not just the two chat endpoints.
  4. Once response headers have been sent, NO second HTTP response may be written to the same
     socket. A mid-stream upstream failure closes the connection and records an error instead.

Non-2xx responses are recorded with "error": <status> and zero tokens so failed spend attempts
stay visible. A body larger than 32 MiB stops being accumulated (relay continues untouched)
and the ledger row is marked body_truncated.

Since 2026-11-09 this process ALSO owns the daily-report trigger (formerly scheduler.py): a
daemon thread runs daily_report.run_daily(cfg) once at boot and once per new day, so the ledger
is a single resident process. The standalone scheduler.py is kept for manual use only.

Also since 2026-11-09 it owns the hardware monitor (formerly a separate 127.0.0.1:8089
process). Since 2026-11-16 the monitor is a fully self-owned page: /monitor
(monitor.html + /monitor.js, data from /ext.json) is served here on the SAME
origin as the console, so teammates see every GPU (including TCC cards Task
Manager cannot show), RAM, disks and network adapters at http://<host>:8080/monitor.
GPU cards and waveform history bind by the card's UUID, never by the drifting
nvidia-smi slot index. This process NEVER writes to a web page it does not own:
the old script-injection watcher is removed. /ext.js is kept only as a retired
shim for pages that still carry the old line. Local routes never reach the
upstream and never create ledger rows.
"""
import collections
import gzip
import hashlib
import json
import os
import socket
import sys
import threading
import time
import traceback
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request as urlreq
from urllib import error as urlerr

# The monitor extension lives next to this file. Import failure must never stop
# accounting: the proxy simply keeps forwarding everything to the engine.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import monitor_ext as _monitor_ext
except Exception:
    _monitor_ext = None
from paths import expand_path        # rev11a A-2: strata_config path flattening
                                     # (@here / relative against config_dir);
                                     # paths.py is already a hard runtime
                                     # dependency (load_config below).

CANON_INT = ("prompt", "cached", "new_prompt", "gen")
BODY_ACCUM_CAP = 32 * 1024 * 1024        # stop keeping the private copy past 32 MiB; relay is unaffected
GATE_DEFAULTS = (0, 10.0, 600.0)         # (max_inflight, queue_beat_s, gate_wait_s); 0 = gate off
GATEWAY_VERSION = "rev17k"            # self-reported in /capabilities; bump with each functional change
# rev11a X-2: FOLLOW_DEFAULTS deleted — the follow default (False) is carried by
# `c.get("gate_follow") is True` in _gate_params; the poll-seconds key's consumer
# (the polling thread) is torn out by X-1, so the constant would be dead code.
# The engine-runtime reading cache is retired by rev11a (INTK-0003: the gateway
# only caps the upper bound; it never follows engine runtime values).
_HOP_HEADERS = {
    "host", "content-length", "transfer-encoding", "connection", "keep-alive",
    "upgrade", "trailer", "te", "proxy-authenticate", "proxy-authorization",
}


def client_ip(handler):
    """Caller address for the ledger. IPv4 peers on a dual-stack IPv6 listener
    arrive as ::ffff:a.b.c.d; store the plain IPv4 form so one machine is one label."""
    raw = (handler.client_address or ("", 0))[0]
    return raw[7:] if raw.startswith("::ffff:") else raw


def load_config(path):
    # Portable paths: @here / @pkg / ~ / relative paths are resolved against
    # the config file's own directory, so one config works on any OS.
    from paths import load_config as portable_load_config
    return portable_load_config(path)


class Recorder:
    def __init__(self, out_dir, prefix="requests"):
        self.dir = out_dir
        self.prefix = prefix
        self.lock = threading.Lock()
        self.day = None
        self.f = None

    def write(self, rec):
        day = (rec.get("ts") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))[:10]
        with self.lock:
            if day != self.day:
                if self.f is not None:
                    try:
                        self.f.close()
                    except OSError:
                        pass
                self.f = open(os.path.join(self.dir, f"{self.prefix}-{day}.jsonl"), "a", encoding="utf-8", buffering=1)
                self.day = day
            self.f.write(json.dumps(rec, ensure_ascii=False) + "\n")


class Gate:
    """FIFO admission gate for chat requests (rev10). Only ever delays NEW
    entries; in-flight requests are never touched. Every state change holds
    self._cond's lock; on_beat (heartbeat write) is always called OUTSIDE it."""

    def __init__(self):
        self._cond = threading.Condition()
        self._waiters = collections.deque()   # elements: [seq:int, granted:bool]
        self._seq = 0
        self.inflight = 0
        self.queued = 0                       # monotonic counter (never decremented); display truth via _waiters, do not read this field — snapshot's queued key uses len(self._waiters) live value
        self.waited_total = 0                 # ms accumulated across waited requests
        self.beat_total = 0                   # heartbeat frames ever emitted

    def acquire(self, limit, beat_s, wait_s, on_beat=None, on_event=None) -> int:
        """Take a slot; return this request's waited ms (0 = never waited).
        Called only when limit > 0. Never rejects: after wait_s the request
        is forwarded anyway (worst case = today's behaviour).

        rev12: on_event (default None = existing callers unchanged) receives
        one decision line per enrolment — "admitted" on the fast path, then
        "queued" + "released" for waited requests. The decision readings
        (inflight_at_decision) are taken INSIDE the _cond critical section,
        at the very instant the admission decision is made; the event lines
        themselves are emitted OFF-LOCK only (same discipline as on_beat —
        write I/O never runs under the lock). A callback that raises is
        swallowed: a lost event line never blocks the relay nor aborts the
        wait."""
        t0 = time.monotonic()
        deadline = t0 + wait_s
        next_beat = t0 + beat_s
        my = None
        forced = False
        beats = 0
        enq_at = None
        while True:
            outcome = None                    # "granted" / "expired" / None=keep waiting
            beat_now = False
            enqueued_now = False
            fast_admit = False
            adm_at = None
            # Critical section 1 (enrol): first pass only — fast path, or join
            # the queue once. The `my is None` guard preserves the original
            # structure exactly: on a beat-restart pass this section is a
            # no-op and the wait loop resumes in critical section 2.
            with self._cond:
                if my is None:
                    if self.inflight < limit:         # fast path: a free slot
                        adm_at = self.inflight        # rev12: decision reading IN the lock
                        self.inflight += 1
                        fast_admit = True
                    else:
                        my = [self._seq, False]
                        self._seq += 1
                        self._waiters.append(my)
                        self.queued += 1
                        enqueued_now = True
                        enq_at = self.inflight        # rev12: reading at enrolment instant
            if fast_admit:
                if on_event:
                    try:
                        on_event({"event": "admitted", "inflight_at_decision": adm_at})
                    except Exception:
                        pass                          # a lost event line never blocks the relay
                return 0
            # rev10a E-2: one enqueue push OUTSIDE the Condition lock (same
            # off-lock discipline as on_beat), at the instant of enrolment,
            # before the first _cond.wait — so /ext.json gate.queued stops
            # lagging up to queue_beat_s. Fast path never reaches here.
            if enqueued_now:
                _push_gate(self)
                if on_event:
                    try:
                        on_event({"event": "queued", "seq": my[0],
                                  "inflight_at_decision": enq_at})
                    except Exception:
                        pass                          # a lost event line never aborts the wait
            # Critical section 2 (wait): re-enter the lock for the wait loop.
            with self._cond:
                while True:
                    if my[1]:                         # slot handed over by release()
                        outcome = "granted"
                        break
                    if not self._waiters or self._waiters[0] is my:
                        if self.inflight < limit:     # head of queue may take a free slot
                            self._waiters.popleft()
                            self.inflight += 1
                            my[1] = True
                            outcome = "granted"
                            break
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:                # waited gate_wait_s out: forward anyway
                        try:
                            self._waiters.remove(my)
                        except ValueError:
                            pass
                        self.inflight += 1            # deliberate over-run: never reject
                        outcome = "expired"
                        forced = True
                        break
                    timed_out = not self._cond.wait(timeout=min(beat_s, remaining))
                    if not my[1] and timed_out and time.monotonic() >= next_beat:
                        beat_now = True               # heartbeat due: call on_beat off-lock
                        break
            if outcome:
                break
            if beat_now:
                if on_beat:
                    try:
                        on_beat()
                        beats += 1
                    except Exception:
                        pass                          # a lost heartbeat never aborts the wait
                with self._cond:
                    self.beat_total += 1
                _push_gate(self)                      # observation push at beat_total update
                next_beat += beat_s
        waited_ms = int((time.monotonic() - t0) * 1000)
        if waited_ms > 0:
            with self._cond:
                self.waited_total += waited_ms
        if my is not None:                    # this request queued: release event line
            if on_event:
                try:
                    on_event({"event": "released", "seq": my[0], "waited_ms": waited_ms,
                              "heartbeats": beats, "forced": forced})
                except Exception:
                    pass                      # event-log write failure never touches the relay
        return waited_ms

    def release(self):
        """The single finally-exit. A freed slot is handed DIRECTLY to the
        queue head — a fresh arrival may not cut in front of a waiter."""
        with self._cond:
            self.inflight -= 1
            if self._waiters:
                head = self._waiters.popleft()
                head[1] = True
                self.inflight += 1
            self._cond.notify_all()

    def snapshot(self, limit):
        with self._cond:
            return {"inflight": self.inflight, "queued": len(self._waiters),
                    "limit": limit, "waited_total": self.waited_total,
                    "beat_total": self.beat_total}


_last_limit = 0        # the limit of the most recent _gate_params read


def _push_gate(gate):
    """Best-effort observation push: a sampler without data means the field
    is simply absent. Never affects accounting."""
    if _monitor_ext is not None and hasattr(_monitor_ext, "push_gate"):
        try:
            _monitor_ext.push_gate(gate.snapshot(_last_limit))
        except Exception:
            pass


def _strata_parallel_parse(path):
    """rev11a A-1 + rev13 dual-backend: pure parse helper for the ACTIVE
    engine's startup-config file (Strata OR Basalt).

    Called ONLY when the mtime/size guard below goes stale (0-1 times per
    request, 0 in the steady state). Returns the effective gate limit for the
    follow mode, or None when the file cannot be read/parsed at all.

    Strata format (serve/server.py:3588-3602 read-only reference): a top-level
    "parallel" that is an int (not bool) and >= 1 is returned as-is — NO
    PARALLEL_MAX clamping here (clamping is the engine's business, ticket A-4).
    False/None/absent/1/bool/non-int/negative all mean the engine runs
    single-shot, so the gate caps at 1.

    Basalt format (basalt_config.json, rev13 2026-11-19): NO top-level
    "parallel"; the value lives per-model as models[].parallel. Basalt is a
    single-VRAM one-brain-at-a-time router, so which entry is on duty cannot
    be read from the file — the gate takes the MAX across entries that carry a
    valid parallel (gate caps the upper bound, INTK-0003). An entry without a
    valid parallel contributes 1 (its single-shot semantics). A file that has
    neither shape (no top-level int AND no models list) is a read failure ->
    None (never guesses); the caller falls back to static. Any file or JSON
    failure returns None. Zero urlreq, zero threads.
    """
    try:
        with open(path, encoding="utf-8") as f:
            obj = json.load(f)
        if not isinstance(obj, dict):
            return None
        p = obj.get("parallel")
        if isinstance(p, int) and not isinstance(p, bool):
            return p if p >= 1 else 1
        if "parallel" in obj:      # key present but not int (bool/str/None) = Strata single-shot
            return 1
        models = obj.get("models")
        if isinstance(models, list) and models:
            vals = []
            for m in models:
                mp = m.get("parallel") if isinstance(m, dict) else None
                vals.append(mp if isinstance(mp, int) and not isinstance(mp, bool) and mp >= 1 else 1)
            return max(vals)
        return None                # neither engine shape recognised = failure state, no guess
    except Exception:
        return None


_strata_parallel_cache = None   # 模块级：(path:str, guard:(mtime_ns,size), limit:int) | None
                                # 无锁纪律：写＝整体重绑元组（GIL 原子）；多请求线程并发
                                # miss 时允许重复解析（幂等读数，last-write-wins，无撕裂
                                # 读、无正确性问题）——引新锁即违红线四。

def _strata_parallel_limit(c):
    global _strata_parallel_cache   # ← 必须（rev11a B-1 修·rev11 D1 同族坑第二次）：
                                    # 函数体内对 _strata_parallel_cache 的任何赋值使 Python
                                    # 把该名全程判为局部——缺这行则读点 cache = ... 先于
                                    # 赋值执行＝UnboundLocalError，且本函数炸点穿
                                    # _gate_params 穿 do_POST（实码 673 行无外层 try）
                                    # ＝跟随态每请求热路径炸。教训就近登记于此，照抄勿删。
    raw = c.get("strata_config")
    if not raw:
        return None                          # 未配路径：不猜，退静态档
    path = expand_path(raw, c.get("config_dir"))   # @here/相对口径（paths 已依赖）
    try:
        st = os.stat(path)
    except Exception:
        # 抓 Exception 非 OSError（rev11a B-1 顺带修·QA 探针实证）：os.stat 对含 NUL 的
        # 路径串抛 ValueError（非 OSError 族）——统一退静态档，一切读失败不抛穿热路径。
        _strata_parallel_cache = None        # stat 失败＝缓存作废，本请求退静态档
        return None
    guard = (st.st_mtime_ns, st.st_size)
    cache = _strata_parallel_cache
    if cache is not None and cache[0] == path and cache[1] == guard:
        return cache[2]                      # 命中：零 open 零 parse
    v = _strata_parallel_parse(path)
    if v is not None:
        _strata_parallel_cache = (path, guard, v)
    else:
        _strata_parallel_cache = None        # 解析失败＝不缓存坏值，下请求再试
    return v


def _gate_params(cfg_path):
    """Per-request config re-read: changing the thresholds needs no restart."""
    global _last_limit
    try:
        c = load_config(cfg_path)
    except Exception:
        _last_limit = GATE_DEFAULTS[0]
        return GATE_DEFAULTS
    try:
        static_limit = int(c.get("max_inflight", 0))
    except (TypeError, ValueError, AttributeError):
        static_limit = GATE_DEFAULTS[0]
    # rev11a gate-follow (A-2 hook): with the switch on, the effective limit is
    # the FIXED "parallel" value in the Strata startup-config file named by
    # `strata_config` — the gateway only caps that upper bound (INTK-0003:
    # 网关只卡上限，读启动配置定死值；引擎运行时降级网关不跟不问；INTK(00:31):
    # 数字启动一次定死，不每请求重读——mtime 守卫缓存). Two-level fallback:
    # file reading -> static max_inflight -> 0 = gate off. No file-cache
    # last-good tier (rev11's polling last-good is retired; a read failure
    # falls back to static, see _strata_parallel_limit failure states).
    # A-3 (relation of max_inflight): it serves exactly two purposes — the
    # fixed limit when follow is off, AND the fallback when follow is on but
    # the file read fails. On-duty both are filled with the human-ruled
    # parallel count (currently 2).
    # Switch off (default) -> the old fixed-value path, byte-for-byte unchanged.
    # Hot path cost when follow is on: ONE os.stat + tuple compare (~4µs);
    # guard hit = zero open, zero parse; zero upstream calls, zero locks (红线四).
    follow = c.get("gate_follow") is True
    if follow:
        v = _strata_parallel_limit(c)
        limit = v if v is not None else static_limit   # 两级回退：文件读数→静态兜底
    else:
        limit = static_limit
    try:
        beat_s = float(c.get("queue_beat_s", 10))
    except (TypeError, ValueError, AttributeError):
        beat_s = GATE_DEFAULTS[1]
    try:
        wait_s = float(c.get("gate_wait_s", 600))
    except (TypeError, ValueError, AttributeError):
        wait_s = GATE_DEFAULTS[2]
    _last_limit = limit
    return limit, beat_s, wait_s


def _capabilities_payload(handler):
    """rev17i: GET /capabilities - gateway self-description, symmetric to the
    split-gateway facade's /v1/capabilities (NAS compute-pool scheduler reads
    one request to learn who answers, live concurrency, routability, and the
    measured reference numbers from the versioned benchmark registry).
    Read-only: every probe is best-effort with a 2s budget, never accounting.
    """
    cfg = handler.cfg
    limit, _beat, _wait = _gate_params(handler.cfg_path)
    gate_snap = handler.gate.snapshot(limit) if handler.gate is not None else None
    # engine slot count: the engine's OWN launch config, disclosure only
    # (gate_follow remains the sole tuning consumer of startup params).
    slots = None
    raw_e = cfg.get("engine_launch_config")
    if raw_e:
        slots = _strata_parallel_parse(expand_path(raw_e, cfg.get("config_dir")))
    engine, routable = None, False
    try:
        # ProxyHandler({}): a machine-level HTTP_PROXY must never fake this
        # probe (known 502 forgery trap on this host).
        opener = urlreq.build_opener(urlreq.ProxyHandler({}))
        with opener.open(cfg["upstream"].rstrip("/") + "/health", timeout=2) as r:
            engine = json.loads(r.read().decode("utf-8", "replace"))
            routable = engine.get("status") == "ok" and bool(engine.get("loaded"))
    except Exception:
        pass
    try:
        reg = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "benchmark-registry.json")
        with open(reg, encoding="utf-8-sig") as f:
            bench = json.load(f)
    except Exception as e:
        bench = {"entries": [], "note": "registry unreadable",
                 "error": repr(e),
                 "looked_at": os.path.join(
                     os.path.dirname(os.path.abspath(__file__)),
                     "benchmark-registry.json")}
    return {
        "ok": True,
        "object": "gateway.capabilities",
        "gateway": {
            "kind": "llm-ledger-proxy",
            "version": GATEWAY_VERSION,
            "listen": cfg.get("listen", ""),
            "upstream": cfg.get("upstream"),
            "endpoints": {
                "chat": "/v1/chat/completions", "messages": "/v1/messages",
                "models": "/v1/models", "health": "/health",
                "metrics": "/metrics (needs engine key)",
                "monitor": "/monitor", "ext": "/ext.json",
                "capabilities": "/v1/capabilities",
            },
        },
        "capacity": {
            "admission_gate": {
                "enabled": bool(gate_snap and gate_snap["limit"]),
                "max_concurrency": (gate_snap["limit"]
                                    if gate_snap and gate_snap["limit"] else None),
            },
            "concurrency_model": {
                "kind": "llm_slot_parallelism",
                "unit": "decode-slots",
                "note": "NOT comparable to a video gateway's DiT-instance "
                        "lane count. One resident model on one GPU serves "
                        "several requests SIMULTANEOUSLY, one decode slot "
                        "per request; the hard ceiling is the launch "
                        "config's parallel value (engine_parallel_slots) "
                        "and the admission gate only caps below it as a "
                        "policy. Schedulers must not read slots as "
                        "independent worker instances.",
            },
            "engine_parallel_slots": slots,
            "concurrency_ceiling": (limit if limit else slots),
            "queue": ({"inflight": gate_snap["inflight"], "queued": gate_snap["queued"]}
                      if gate_snap else None),
            "routable": routable,
        },
        "engine_health": engine,
        "benchmarks": bench,
        "server_time": int(time.time()),
    }


def _gateway_status_payload(handler):
    """OPS-1123-GWSTATUS: GET /gateway/status - unified-status/v0 envelope for
    the NAS compute pool. Read-only; every reading is gate-local or config-
    declared, zero upstream I/O. The benchmark-derived speed field has no
    archive in v1 = key absent, never filled 1.0. gpu_bind/vram_gb come only
    from the declared config key machine_profile, absent -> null (no infer)."""
    cfg = handler.cfg
    machine_id = (cfg.get("machine_id") or "").strip() or socket.gethostname()
    # listen port: rpartition like main() (:1102) - IPv6 hosts contain colons
    try:
        vport = int(str(cfg.get("listen", "")).rpartition(":")[2])
    except ValueError:
        vport = None
    limit, _beat, _wait = _gate_params(handler.cfg_path)       # per-request read
    snap = handler.gate.snapshot(limit) if handler.gate is not None else None
    in_flight = snap["inflight"] if snap else 0
    queued = snap["queued"] if snap else 0                     # live queue length, snapshot-issued
    slots = None
    raw_e = cfg.get("engine_launch_config")
    if raw_e:
        slots = _strata_parallel_parse(expand_path(raw_e, cfg.get("config_dir")))
    serving = limit if limit else slots                        # :491 precedent
    available = (serving - in_flight) if serving else None     # no clamp (A-3)
    profile = cfg.get("machine_profile") or {}
    row = {
        "vport": vport,
        "engine": cfg.get("engine_backend") or None,
        "gpu_bind": profile.get("gpu_bind"),
        "vram_gb": profile.get("vram_gb"),
        "available": available,
        "current_tasks": {"in_flight": in_flight, "queued": queued},
        # benchmark speed field: no archive in v1 = whole field absent (A-6/H-3) — key not written
    }
    return {
        "schema": "unified-status/v0",
        "machine_id": machine_id,
        "domain": "llm",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ports": [row],
    }


def key_identity(headers, cfg):
    """Return (tag, fp): fp is the 8-hex SHA-256 prefix of the raw API key
    (or "none"); tag is the human label from key_labels, else fp itself.
    The ledger stores BOTH so a future label/fingerprint collision stays
    auditable and historical rows can still be split.
    """
    raw = headers.get("Authorization") or headers.get("x-api-key") or ""
    raw = raw.strip()
    # RFC 7235 auth-scheme is case-insensitive: "bearer"/"BEARER" must not
    # turn one person's key into a second, unlabelled identity.
    if raw[:7].lower() == "bearer ":
        raw = raw[7:].strip()
    if not raw:
        return ("none", "none")
    fp = hashlib.sha256(raw.encode()).hexdigest()[:8]
    return ((cfg.get("key_labels") or {}).get(fp, fp), fp)


def key_tag(headers, cfg):
    """Backward-compatible wrapper: just the display tag."""
    return key_identity(headers, cfg)[0]


def usage_from_openai(obj):
    u = obj.get("usage") or {}
    details = u.get("prompt_tokens_details") or {}
    return {"prompt": u.get("prompt_tokens", 0), "cached": details.get("cached_tokens", 0),
            "gen": u.get("completion_tokens", 0), "model": obj.get("model", "")}


def usage_from_anthropic(obj):
    u = obj.get("usage") or {}
    return {"prompt": u.get("input_tokens", 0), "cached": u.get("cache_read_input_tokens", 0),
            "gen": u.get("output_tokens", 0), "model": obj.get("model", "")}


def usage_from_sse(body, kind):
    """Scan an SSE body and MERGE every usage it carries. Anthropic splits usage across two
    events (message_start: input+cache, message_delta: output); OpenAI streams usage only in
    the final chunk. A nonzero field from any event wins over a zero from another."""
    out = {"prompt": 0, "cached": 0, "gen": 0, "model": ""}
    for raw in body.split(b"\n"):
        line = raw.strip()
        if not line.startswith(b"data:"):
            continue
        payload = line[5:].strip()
        if not payload or payload == b"[DONE]":
            continue
        try:
            obj = json.loads(payload)
        except ValueError:
            continue
        if not isinstance(obj, dict):
            continue
        if kind == "anthropic":
            src = (obj.get("usage") or (obj.get("message") or {}).get("usage")) or {}
            got = {"prompt": src.get("input_tokens", 0), "cached": src.get("cache_read_input_tokens", 0),
                   "gen": src.get("output_tokens", 0), "model": obj.get("model", "") or (obj.get("message") or {}).get("model", "")}
        else:
            got = usage_from_openai(obj)
        for k in ("prompt", "cached", "gen"):
            if got.get(k):
                out[k] = got[k]
        if got.get("model"):
            out["model"] = got["model"]
        met = obj.get("metrics")          # vLLM --enable-per-request-metrics (engine-side timing)
        if isinstance(met, dict):
            if met.get("tokens_per_second"):
                out["engine_tps"] = met["tokens_per_second"]
            if met.get("generation_time_ms"):
                out["engine_gen_ms"] = met["generation_time_ms"]
    return out


class Handler(BaseHTTPRequestHandler):
    # HTTP/1.1 is required for Transfer-Encoding: chunked, which is how SSE is
    # relayed without buffering. Every non-chunked branch sends an exact
    # Content-Length, so keep-alive framing stays well-formed.
    protocol_version = "HTTP/1.1"
    recorder = None
    gate_rec = None          # rev12: dedicated gate-interception event log (lazy file)
    cfg = None
    gate = None
    cfg_path = None

    def log_message(self, *a):            # silence default stderr logging
        pass

    # ---- shared relay helpers -------------------------------------------------

    @staticmethod
    def _clean_headers(source, skip=()):
        """Drop hop-by-hop / framing headers; normalize key spelling so later
        lookups such as headers['Authorization'] behave predictably."""
        out = {}
        for k, v in source.items():
            lk = k.lower()
            if lk in _HOP_HEADERS or lk in skip:
                continue
            out["-".join(p.capitalize() for p in k.split("-"))] = v
        return out

    def _forward_headers(self):
        """All client headers except hop-by-hop ones. Never send an empty
        Authorization when the client sent none: some engines reject an empty
        credential even in no-key mode."""
        h = self._clean_headers(self.headers)
        if not any(k.lower() == "content-type" for k in h):
            h["Content-Type"] = "application/json"
        return h

    def _read_body(self):
        """Honor both Content-Length and chunked request bodies. A client that
        sends TE: chunked used to be read as zero bytes, silently losing the
        whole request and desynchronizing keep-alive."""
        te = (self.headers.get("Transfer-Encoding") or "").lower()
        if "chunked" in te:
            parts = []
            while True:
                line = self.rfile.readline(65536)
                if not line:
                    break
                try:
                    size = int(line.split(b";", 1)[0].strip(), 16)
                except ValueError:
                    break
                if size == 0:
                    while True:                      # consume trailers up to the blank line
                        t = self.rfile.readline(65536)
                        if not t or t in (b"\r\n", b"\n"):
                            break
                    break
                buf = b""
                while len(buf) < size:
                    piece = self.rfile.read(size - len(buf))
                    if not piece:
                        break
                    buf += piece
                parts.append(buf)
                self.rfile.read(2)                   # trailing CRLF
            return b"".join(parts)
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except (TypeError, ValueError):
            n = 0
        return self.rfile.read(n) if n > 0 else b""

    def _send_fixed(self, status, source, data, extra=None):
        """Send a complete response with an exact Content-Length, relaying
        upstream headers (Content-Encoding, CORS, ...) verbatim."""
        self.send_response(status)
        sent = set()
        for k, v in self._clean_headers(source).items():
            self.send_header(k, v)
            sent.add(k.lower())
        if "content-type" not in sent:
            self.send_header("Content-Type", "application/json")
        for k, v in (extra or {}).items():
            if v and k.lower() not in sent:
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _start_chunked(self, status, source):
        """Send response headers IMMEDIATELY, before any body byte exists."""
        self.send_response(status)
        sent = set()
        for k, v in self._clean_headers(source, skip={"cache-control"}).items():
            self.send_header(k, v)
            sent.add(k.lower())
        if "content-type" not in sent:
            self.send_header("Content-Type", "application/json")
        if "cache-control" not in sent:
            self.send_header("Cache-Control", "no-cache, no-transform")
        if "x-accel-buffering" not in sent:
            self.send_header("X-Accel-Buffering", "no")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

    def _start_gate_chunked(self):
        """Send SSE response headers on behalf of the gate while the request
        still queues (rev10 heartbeat promise). Same header shape as
        _start_chunked, but there is no upstream response to relay headers
        from yet. RELAY CONTRACT §4: once these headers are out, NO second
        HTTP response may follow on this socket."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

    def _write_gate_hb(self):
        """One SSE comment frame (`: ping`) in the SAME chunk framing _pump
        uses. Parsers ignore comment lines by design."""
        hb = b": ping\n\n"
        try:
            self.wfile.write(("%x\r\n" % len(hb)).encode("ascii") + hb + b"\r\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            # client hung up mid-heartbeat; the slot stays held until the
            # upstream relay finishes (returned by the finally, not here)
            self.close_connection = True

    def _pump(self, resp, keep_body):
        """Relay every upstream chunk as it arrives. Returns
        (private_body_copy, client_still_connected, body_truncated).
        If the client disconnects we keep draining upstream so the final usage
        chunk is still accounted for."""
        parts, total, truncated, client_ok = [], 0, False, True
        while True:
            chunk = resp.read1(65536)
            if not chunk:
                break
            if keep_body and not truncated:
                if total + len(chunk) <= BODY_ACCUM_CAP:
                    parts.append(chunk)
                    total += len(chunk)
                else:
                    truncated = True
                    parts = []
            if client_ok:
                try:
                    frame = ("%x\r\n" % len(chunk)).encode("ascii") + chunk + b"\r\n"
                    self.wfile.write(frame)
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    client_ok = False
                    self.close_connection = True
        if client_ok:
            try:
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
            except OSError:
                client_ok = False
                self.close_connection = True
        body = b"".join(parts) if (keep_body and not truncated) else b""
        return body, client_ok, truncated

    # ---- endpoints ------------------------------------------------------------

    def _pass_post(self, body):           # non-chat endpoints (stop/unload/images/...): relay, no ledger row
        req = urlreq.Request(self.cfg["upstream"].rstrip("/") + self.path, data=body,
                             headers=self._forward_headers(), method="POST")
        responded = False
        try:
            with urlreq.urlopen(req, timeout=1800) as resp:
                ctype = resp.headers.get("Content-Type", "application/json")
                if "event-stream" in ctype.lower() and hasattr(resp, "read1"):
                    self._start_chunked(resp.status, resp.headers)
                    responded = True
                    self._pump(resp, False)
                else:
                    data = resp.read()
                    responded = True
                    self._send_fixed(resp.status, resp.headers, data)
        except urlerr.HTTPError as e:
            try:
                data = e.read() or b""
            except Exception:
                data = b""
            if not responded:
                self._send_fixed(e.code, e.headers, data)
            else:
                self.close_connection = True
        except Exception as e:
            if responded:
                self.close_connection = True     # never append a 2nd HTTP response to a live stream
                return
            data = json.dumps({"error": {"message": f"{type(e).__name__}: {e}"}}).encode()
            self._send_fixed(502, {}, data)

    def do_POST(self):
        cfg = self.cfg
        path = self.path.split("?", 1)[0]
        body = self._read_body()
        if path not in ("/v1/chat/completions", "/v1/messages"):
            return self._pass_post(body)
        kind = "anthropic" if path.startswith("/v1/messages") else "openai"
        t0 = time.monotonic()
        req_obj = {}
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):         # a JSON array/string must not crash .get() below
                req_obj = parsed
        except (ValueError, TypeError):
            pass
        up = cfg["upstream"].rstrip("/") + self.path
        headers = self._forward_headers()
        key = os.environ.get(cfg.get("upstream_key_env", ""), "")
        auth = self.headers.get("Authorization")
        if auth:
            headers["Authorization"] = auth
        elif key and kind == "openai":
            headers["Authorization"] = f"Bearer {key}"
        elif key and kind == "anthropic":
            headers["x-api-key"] = key
        if kind == "anthropic":
            headers.setdefault("Anthropic-Version", self.headers.get("anthropic-version", "2023-06-01"))
        # vLLM/SGLang/Ollama do NOT emit usage on a stream unless the client asks for it
        # (stream_options.include_usage). Without this the whole request is recorded as 0 tokens,
        # silently. Anthropic always reports usage in message_start/message_delta, so it needs nothing.
        if cfg.get("force_include_usage") and kind == "openai" and req_obj.get("stream") is True:
            opts = req_obj.get("stream_options")
            opts = dict(opts) if isinstance(opts, dict) else {}
            opts["include_usage"] = True
            req_obj = dict(req_obj)
            req_obj["stream_options"] = opts
            body = json.dumps(req_obj).encode()
        # ---- rev10 queue gate: only ever delays THIS entry point; the request
        # content is untouched, in-flight requests are never reclaimed.
        limit, beat_s, wait_s = _gate_params(self.cfg_path)
        gate_on = limit > 0
        tag, fp = key_identity(self.headers, cfg)   # rev12: hoisted — the gate-event
        #  lines reuse it (same values as the ledger row); key_identity was already
        #  computed once per chat request below, hoisting costs zero extra per request.
        gate_headers_sent = False          # 闸已替客户端发过响应头？
        responded = False                  # once headers are out, no second response is allowed
        truncated = False
        waited_ms = 0
        is_stream_req = req_obj.get("stream") is True
        if gate_on:
            def _gate_beat():              # 仅 SSE 请求有字节可发；非流式＝静默排队（无可发字节）
                nonlocal gate_headers_sent, responded
                if is_stream_req:
                    if not gate_headers_sent:
                        self._start_gate_chunked()
                        gate_headers_sent = True
                        responded = True   # headers are on the wire: RELAY CONTRACT §4 applies
                    self._write_gate_hb()
            def _gate_event(ev):           # rev12: dedicated gate-interception log
                if self.gate_rec is None:
                    return
                ev = dict(ev)
                ev["ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ev["route"] = path
                ev["model"] = req_obj.get("model", "")
                ev["key"] = tag
                ev["fp"] = fp
                ev["limit"] = limit
                ev["stream"] = is_stream_req
                try:
                    self.gate_rec.write(ev)
                except Exception:
                    pass                   # 磁盘异常禁穿热路径（红线四）
            waited_ms = self.gate.acquire(limit, beat_s, wait_s,
                                          _gate_beat if is_stream_req else None,
                                          _gate_event)
            _push_gate(self.gate)
        try:
            req = urlreq.Request(up, data=body, headers=headers, method="POST")
            rec = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "src": "proxy",
                   "model": req_obj.get("model", ""), "key": tag, "fp": fp,
                   "ip": client_ip(self)}
            fwd = self.headers.get("X-Forwarded-For")
            if fwd:
                rec["fwd"] = fwd.split(",", 1)[0].strip()
            try:
                with urlreq.urlopen(req, timeout=1800) as resp:
                    ctype = resp.headers.get("Content-Type", "application/json")
                    is_sse = (("event-stream" in ctype.lower()
                               or req_obj.get("stream") is True)
                              and hasattr(resp, "read1"))
                    if is_sse and gate_headers_sent:
                        # heartbeat headers are already on the wire — never send
                        # headers twice; the real stream joins the open chunk stream
                        responded = True
                        data, client_ok, truncated = self._pump(resp, True)
                    elif is_sse:
                        self._start_chunked(resp.status, resp.headers)
                        responded = True
                        data, client_ok, truncated = self._pump(resp, True)
                    elif gate_headers_sent:
                        # client claimed stream but upstream answered non-stream:
                        # fixed body re-framed into the open chunk stream (bytes kept)
                        responded = True
                        data, client_ok, truncated = self._pump(resp, True)
                    else:
                        data = resp.read()
                        responded = True
                        self._send_fixed(resp.status, resp.headers, data)
                    if resp.status == 200:
                        # Relay bytes stay untouched; only the private accounting copy
                        # is decompressed. A gzip upstream must not silently record 0 tokens.
                        parse_body = data
                        if "gzip" in (resp.headers.get("Content-Encoding") or "").lower():
                            try:
                                parse_body = gzip.decompress(data)
                            except (OSError, ValueError):
                                pass
                        if "event-stream" in ctype.lower() or parse_body.lstrip().startswith(b"event:"):
                            got = usage_from_sse(parse_body, kind)
                        else:
                            got = {}
                            try:
                                obj = json.loads(parse_body)
                                if isinstance(obj, dict):
                                    got = usage_from_anthropic(obj) if kind == "anthropic" else usage_from_openai(obj)
                                    met = obj.get("metrics")
                                    if isinstance(met, dict):
                                        got["engine_tps"] = met.get("tokens_per_second")
                                        got["engine_gen_ms"] = met.get("generation_time_ms")
                            except ValueError:
                                pass
                        for k in ("prompt", "cached", "gen"):
                            rec[k] = got.get(k, 0)
                        for k in ("engine_tps", "engine_gen_ms"):   # vLLM --enable-per-request-metrics
                            if got.get(k):
                                rec[k] = got[k]
                        if got.get("model"):
                            rec["model"] = got["model"]
                    else:
                        rec["error"] = resp.status
            except urlerr.HTTPError as e:
                rec["error"] = e.code
                if responded:
                    self.close_connection = True
                else:
                    try:
                        data = e.read() or b""
                    except Exception:
                        data = b""
                    self._send_fixed(e.code, e.headers, data)
            except Exception as e:            # record the failure, then surface a 502 if nothing was sent yet
                rec["error"] = f"{type(e).__name__}: {e}"[:120]
                if responded:
                    self.close_connection = True
                else:
                    data = json.dumps({"error": {"message": rec["error"]}}).encode()
                    self._send_fixed(502, {}, data)
            if truncated:
                rec["body_truncated"] = True
            rec["gen_ms"] = int((time.monotonic() - t0) * 1000)
            if waited_ms > 0:                 # only requests that actually waited carry this
                rec["queue_wait_ms"] = waited_ms
            rec["new_prompt"] = rec.get("prompt", 0) - rec.get("cached", 0)
            if rec.get("gen") and rec["gen_ms"]:
                rec["decode_tok_s"] = round(rec["gen"] / (rec["gen_ms"] / 1000), 1)
            for k in CANON_INT:
                rec.setdefault(k, 0)
            self.recorder.write(rec)
        finally:
            if gate_on:
                self.gate.release()           # the single slot-return exit (红线二: in-flight never reclaimed before here)
                _push_gate(self.gate)

    def do_GET(self):                     # pass-through: /v1/models, console pages, /metrics, ...
        # Local monitor routes are answered here and never forwarded. "/" is NOT
        # one of them: on 8080 it is the Strata console itself.
        if self.path.split("?", 1)[0] in ("/capabilities", "/v1/capabilities"):
            try:
                body = json.dumps(_capabilities_payload(self)).encode("utf-8")
            except Exception as e:
                body = json.dumps({"ok": False, "error": repr(e)}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        if self.path.split("?", 1)[0] == "/gateway/status":
            try:
                body = json.dumps(_gateway_status_payload(self)).encode("utf-8")
            except Exception as e:
                body = json.dumps({"ok": False, "error": repr(e)}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        local = None
        if _monitor_ext is not None:
            try:
                local = _monitor_ext.answer(self.path.split("?", 1)[0])
            except Exception:
                local = None
        if local is not None:
            body, ctype = local
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        cfg = self.cfg
        req = urlreq.Request(cfg["upstream"].rstrip("/") + self.path, method="GET",
                             headers=self._forward_headers())
        # forward the browser's credentials so engine-served pages (/metrics, #monitor) keep working
        auth = self.headers.get("Authorization")
        if not auth:
            auth = os.environ.get(cfg.get("upstream_key_env", ""), "")
            if auth:
                auth = f"Bearer {auth}"
        if auth:
            req.add_header("Authorization", auth)
        responded = False
        try:
            with urlreq.urlopen(req, timeout=30) as resp:
                data = resp.read()
                responded = True
                self._send_fixed(resp.status, resp.headers, data)
        except urlerr.HTTPError as e:      # pass real status through (401 etc.), don't mask as 502
            try:
                data = e.read() or b""
            except Exception:
                data = b""
            responded = True
            self._send_fixed(e.code, e.headers, data)
        except Exception:
            if responded:
                # Headers are already on the wire (client dropped mid-write):
                # appending a 502 would corrupt the stream. Close instead.
                self.close_connection = True
                return
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()


def _append_line(path, line):
    """Append one UTF-8 line to a log file; never propagate IO errors to the caller."""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _fire_daily(daily_report, cfg, runlog, why):
    """Run the idempotent daily report once and log the outcome.

    Log format is byte-for-byte compatible with the legacy scheduler.py so any
    existing consumer of daily-report.log keeps working. A failing fire is
    recorded and swallowed, so it can never take the HTTP server down.
    """
    try:
        daily_report.run_daily(cfg)
        _append_line(runlog, f"[{datetime.now():%Y-%m-%d %H:%M:%S}] scheduler fired ({why})")
    except Exception:
        _append_line(runlog, f"[{datetime.now():%Y-%m-%d %H:%M:%S}] scheduler ERROR: {traceback.format_exc()}")


def _report_scheduler_loop(cfg, out_dir):
    """Daemon-thread body replacing the legacy resident scheduler.py process.

    Fires one immediate "boot check" catch-up on start, then wakes about every
    20 s and fires again after crossing into a new calendar day at/after
    report_hour:report_minute. daily_report.run_daily(cfg) is idempotent, so a
    manually started legacy scheduler.py cannot produce duplicate reports and no
    extra lock port (lock_port + 1) is claimed here. Any exception is logged and
    swallowed so neither this thread nor the HTTP server can die from a bad fire.
    """
    rh = int(cfg.get("report_hour", 0))
    rm = int(cfg.get("report_minute", 0))
    runlog = os.path.join(out_dir, "daily-report.log")
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    boot_done = False
    today = datetime.now().strftime("%Y-%m-%d")
    while True:
        try:
            import daily_report  # cached after the first pass; lives next to this file
            now = datetime.now()
            if not boot_done:
                _fire_daily(daily_report, cfg, runlog, "boot check")
                boot_done = True
                today = now.strftime("%Y-%m-%d")
            else:
                day = now.strftime("%Y-%m-%d")
                if day != today and (now.hour, now.minute) >= (rh, rm):
                    _fire_daily(daily_report, cfg, runlog, f"new day {day}")
                    today = day
        except Exception:
            _append_line(runlog,
                         f"[{datetime.now():%Y-%m-%d %H:%M:%S}] scheduler loop ERROR: {traceback.format_exc()}")
        time.sleep(20)


def main():
    if "--fp" in sys.argv:                      # print the 8-hex label for a key (fills key_labels)
        print(hashlib.sha256(sys.argv[sys.argv.index("--fp") + 1].encode()).hexdigest()[:8])
        return
    if "--config" not in sys.argv:
        sys.exit("usage: collector_proxy.py --config <out_dir>/config.json")
    cfg = load_config(sys.argv[sys.argv.index("--config") + 1])
    out = cfg["out_dir"]
    os.makedirs(out, exist_ok=True)
    lock = socket.socket()
    try:
        lock.bind(("127.0.0.1", int(cfg.get("lock_port", 43177))))
    except OSError:
        print("[proxy] another proxy already runs, nothing to do")
        return
    listen = cfg.get("listen", "127.0.0.1:8787")
    # rsplit, not partition: an IPv6 listen host like "::" or "2408::1" contains colons
    host, _, port = listen.rpartition(":")
    host = host or "0.0.0.0"
    Handler.cfg = cfg
    Handler.gate = Gate()
    Handler.cfg_path = sys.argv[sys.argv.index("--config") + 1]
    Handler.recorder = Recorder(out)
    # rev12: dedicated gate-interception event log. Recorder opens NO file at
    # construction (first write does) — gate-off means zero writes, hence zero
    # files, zero new bytes on disk (缺省零回归红线).
    Handler.gate_rec = Recorder(out, "gate-events")

    class _Server(ThreadingHTTPServer):
        # Default backlog is 5; at 11:18 the engine alone had 5 in-flight
        # requests, so a burst could make the OS queue/refuse team connections.
        request_queue_size = 128
        # BUGFIX (2026-11-16, 000 deploy): socketserver creates the socket in
        # __init__ BEFORE server_bind() runs, so flipping address_family inside
        # server_bind() is too late — the socket was already AF_INET and
        # bind(('::', port)) dies with gaierror 11001. Pick the family as a
        # class attribute BEFORE instantiation instead.
        # "::" or "::1" -> AF_INET6; the default dual-stack socket then accepts
        # IPv4 too, so one listener serves both families (user runs IPv4+IPv6).
        address_family = socket.AF_INET6 if ":" in host else socket.AF_INET
        def server_bind(self):
            if self.address_family == socket.AF_INET6:
                try:
                    self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                except OSError:
                    pass
            super().server_bind()

    srv = _Server((host, int(port)), Handler)
    _append_line(os.path.join(out, "ledger-service.log"),
                 f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ledger service started; "
                 f"listen={listen}; upstream={cfg['upstream']}; pid={os.getpid()}; "
                 "daily report merged into this process (daemon thread)")
    # Daily trigger now lives here (formerly the separate scheduler.py process).
    # daemon=True: it never blocks serve_forever() nor interpreter shutdown.
    reporter = threading.Thread(target=_report_scheduler_loop, args=(cfg, out),
                                name="ledger-daily-report", daemon=True)
    reporter.start()
    # rev11a X-1: the gate-follow daemon thread and its hook are removed —
    # follow mode now reads the Strata startup-config file inside the
    # per-request _gate_params path (mtime-guarded cache), zero threads.
    # Hardware monitor (formerly a separate 8089 process) is two more daemon
    # threads in this same process. A failure here cannot stop the ledger.
    monitor_on = False
    if _monitor_ext is not None:
        try:
            monitor_on = _monitor_ext.start(cfg) is not None
        except Exception:
            monitor_on = False
    print(f"[proxy] {listen} -> {cfg['upstream']}  records in {out}")
    print("[proxy] daily report scheduler merged in daemon thread (single resident process)")
    print(f"[proxy] hardware monitor merged: {'on (open /monitor; /ext.json feeds it)' if monitor_on else 'unavailable'}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
