#!/usr/bin/env python3
"""OPS-1123-GWSTATUS · selftest for GET /gateway/status (unified-status/v0).

Import-direct stub suite (LOADSWEEP-T1 A-6 precedent): `import collector_proxy`
starts nothing (main() is guarded at :1160, module level has no side effects),
so this suite touches zero ports, zero threads, zero ledger, zero monitor, zero
registry and zero config.json. Each case builds its own throwaway config file
inside .scratch/OPS-1123-GWSTATUS/ plus a stub handler (SimpleNamespace with
cfg / cfg_path / gate) and calls cp._gateway_status_payload directly.

GS-1 envelope five-field lock · GS-2 ports row closed-set (no-archive form)
GS-3 machine_id source lock · GS-4 available synthesis lock ·
GS-5 machine_profile + engine_backend declared form
"""
import json
import os
import re
import shutil
import socket
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import collector_proxy as cp          # noqa: E402  (import-safe: see docstring)

RESULTS = []

SCRATCH = os.path.join(ROOT, ".scratch", "OPS-1123-GWSTATUS")
_counter = [0]


def rec(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("  " + detail if detail else ""))


def stub(cfg_dict, extra_files=None):
    """Throwaway config file + stub handler (cfg / cfg_path / gate).

    The dict is written verbatim to .scratch/ and handler.cfg is the SAME file
    re-read through cp.load_config — exactly what main() does in production —
    so config_dir/config_path bookkeeping keys and path normalisation match
    the live handler byte-for-byte, and the per-request _gate_params re-read
    sees the same values.
    extra_files: {name: obj} written next to the config, name returned for use
    as e.g. engine_launch_config.
    """
    _counter[0] += 1
    d = os.path.join(SCRATCH, "gs%02d" % _counter[0])
    os.makedirs(d, exist_ok=True)
    for name, obj in (extra_files or {}).items():
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            json.dump(obj, f)
    cp_path = os.path.join(d, "config.json")
    with open(cp_path, "w", encoding="utf-8") as f:
        json.dump(cfg_dict, f)
    return SimpleNamespace(cfg=cp.load_config(cp_path), cfg_path=cp_path, gate=None)


def main():
    if os.path.isdir(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH, exist_ok=True)

    # ---------------- GS-1 envelope 五字段锁（gate off，无申报键） ----------------
    h = stub({"listen": "127.0.0.1:18181"})
    p = cp._gateway_status_payload(h)
    rec("GS-1: envelope keys == {schema, machine_id, domain, generated_at, ports}",
        set(p.keys()) == {"schema", "machine_id", "domain", "generated_at", "ports"},
        "got=%s" % sorted(p.keys()))
    rec("GS-1: schema/domain/machine_id/generated_at/ports one row",
        p.get("schema") == "unified-status/v0"
        and p.get("domain") == "llm"
        and isinstance(p.get("machine_id"), str) and p["machine_id"] != ""
        and re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", p.get("generated_at") or "")
        and isinstance(p.get("ports"), list) and len(p["ports"]) == 1,
        "schema=%s domain=%s mid=%r gen=%r ports=%d" % (
            p.get("schema"), p.get("domain"), p.get("machine_id"),
            p.get("generated_at"), len(p.get("ports") or [])))

    # ---------------- GS-2 ports 行闭集锁（无档案形态） ----------------
    row = p["ports"][0]
    rec("GS-2: row keys == {vport, engine, gpu_bind, vram_gb, available, current_tasks}",
        set(row.keys()) == {"vport", "engine", "gpu_bind", "vram_gb", "available", "current_tasks"},
        "got=%s" % sorted(row.keys()))
    rec("GS-2: speed_bias key ABSENT (no archive = field absent, not null)",
        "speed_bias" not in row)
    rec("GS-2: current_tasks keys == {in_flight, queued}",
        isinstance(row.get("current_tasks"), dict)
        and set(row["current_tasks"].keys()) == {"in_flight", "queued"},
        "got=%s" % sorted((row.get("current_tasks") or {}).keys()))
    rec("GS-2: gate off + no launch config -> available None, counters 0, vport from listen",
        row.get("available") is None
        and row["current_tasks"]["in_flight"] == 0
        and row["current_tasks"]["queued"] == 0
        and row.get("vport") == 18181
        and row.get("engine") is None
        and row.get("gpu_bind") is None
        and row.get("vram_gb") is None,
        "row=%s" % row)

    # ---------------- GS-3 machine_id 来源锁（A-4 两段） ----------------
    p = cp._gateway_status_payload(stub({"listen": "127.0.0.1:1", "machine_id": "nas-box-7"}))
    rec("GS-3: declared machine_id wins",
        p.get("machine_id") == "nas-box-7", "got=%r" % p.get("machine_id"))
    for label, cfg in (("empty string", {"listen": "127.0.0.1:1", "machine_id": ""}),
                       ("blank string", {"listen": "127.0.0.1:1", "machine_id": "   "}),
                       ("absent", {"listen": "127.0.0.1:1"})):
        p = cp._gateway_status_payload(stub(cfg))
        rec("GS-3: machine_id %s -> socket.gethostname()" % label,
            p.get("machine_id") == socket.gethostname(),
            "got=%r want=%r" % (p.get("machine_id"), socket.gethostname()))

    # ---------------- GS-4 available 合成式锁（available = serving - inflight） ----------------
    g = cp.Gate()
    g.inflight = 1                      # test-process local object, no threads: direct set is legal
    h = stub({"listen": "127.0.0.1:1", "max_inflight": 2})
    h.gate = g
    row = cp._gateway_status_payload(h)["ports"][0]
    rec("GS-4: limit 2, inflight 1 -> available 1",
        row.get("available") == 1, "got=%r" % row.get("available"))
    g.inflight = 3                      # forced over-run state (:228 semantics)
    row = cp._gateway_status_payload(h)["ports"][0]
    rec("GS-4: inflight 3 over-run -> available -1 (no clamp)",
        row.get("available") == -1, "got=%r" % row.get("available"))
    g._waiters.append([0, False])       # one live waiter
    row = cp._gateway_status_payload(h)["ports"][0]
    rec("GS-4: live waiter -> current_tasks.queued == 1",
        row["current_tasks"]["queued"] == 1, "got=%r" % row["current_tasks"])

    # serving 退路：闸关（limit 0）＋引擎启动配置在场 -> serving = 引擎槽位（:491 先例）
    g2 = cp.Gate()
    g2.inflight = 1
    h = stub({"listen": "127.0.0.1:1", "max_inflight": 0,
              "engine_launch_config": "engine.json"},
             extra_files={"engine.json": {"models": [{"parallel": 4}]}})
    h.gate = g2
    row = cp._gateway_status_payload(h)["ports"][0]
    rec("GS-4: gate off + engine slots 4 -> available 3",
        row.get("available") == 3, "got=%r" % row.get("available"))
    # 两源皆不可得（闸关＋启动配置读不到）-> available null 缺位弃权
    h = stub({"listen": "127.0.0.1:1", "max_inflight": 0,
              "engine_launch_config": "missing.json"},
             extra_files={})
    h.gate = cp.Gate()
    row = cp._gateway_status_payload(h)["ports"][0]
    rec("GS-4: no limit + no readable launch config -> available None",
        row.get("available") is None, "got=%r" % row.get("available"))

    # ---------------- GS-5 machine_profile + engine_backend 在场形态 ----------------
    h = stub({"listen": "127.0.0.1:1",
              "machine_profile": {"gpu_bind": "GPU-abc123", "vram_gb": 72},
              "engine_backend": "basalt"})
    row = cp._gateway_status_payload(h)["ports"][0]
    rec("GS-5: declared gpu_bind/vram_gb/engine pass through verbatim",
        row.get("gpu_bind") == "GPU-abc123" and row.get("vram_gb") == 72
        and row.get("engine") == "basalt", "row=%s" % row)
    rec("GS-5: declared row keys stay the closed set; speed_bias still ABSENT",
        set(row.keys()) == {"vport", "engine", "gpu_bind", "vram_gb", "available", "current_tasks"}
        and "speed_bias" not in row,
        "got=%s" % sorted(row.keys()))
    # 申报半截：machine_profile 在场但子键缺位 -> 该键 null（H-2＝A-5 在场但 null）
    h = stub({"listen": "127.0.0.1:1", "machine_profile": {"vram_gb": 72}})
    row = cp._gateway_status_payload(h)["ports"][0]
    rec("GS-5: machine_profile without gpu_bind -> gpu_bind None (present but null)",
        "gpu_bind" in row and row["gpu_bind"] is None and row.get("vram_gb") == 72,
        "row=%s" % row)

    shutil.rmtree(SCRATCH, ignore_errors=True)

    bad = [n for n, ok, _ in RESULTS if not ok]
    print("\n%d/%d PASS" % (len(RESULTS) - len(bad), len(RESULTS)))
    if bad:
        print("FAILED:", ", ".join(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
