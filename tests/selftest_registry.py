#!/usr/bin/env python3
r"""Schema/regression selftest for benchmark-registry.json (OPS-1123-LOADSWEEP-T1).

No network, no servers, no production ports touched. R-5 imports the real
collector_proxy module (import-safe: main() sits under the __main__ guard) and
calls _capabilities_payload() with a stub handler whose upstream points at a
provably closed loopback port, so the engine probe dies inside its own
try/except within the 2s budget. Never needs a GPU or the Strata engine.

  python tests/selftest_registry.py

It locks: the file parses (R-1); the v2 top-level contract is present without
losing any old top-level key (R-2); every entry honours the row-family schema
(layer enum, template_id/model_pack/engine_version non-empty strings, scalars
exactly the three closed slots, null-or-nonnegative values, null implies a
non-empty scalars_note) (R-3); the two pre-T1 rows keep every original key and
value byte-for-byte as pinned constants and migrated as map rows with all
scalars null (R-4); and /capabilities keeps its response shape with
payload["benchmarks"] byte-equal to the registry on disk (R-5).
"""
import json
import os
import socket
import sys
import tempfile
from types import SimpleNamespace

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # tests/ -> project root
REGISTRY = os.path.join(HERE, "benchmark-registry.json")
SCALAR_SLOTS = {"saturation_knee", "steady_tok_s_per_lane_at_knee", "prefill_tok_s"}
LAYER_ENUM = {"anchor", "map", "calibration"}
SCHEMA_VERSION_TICKET = 2          # H-1 ruling: integer 2 (ticket S-1 / R-2)
RESULTS = []


def rec(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("  " + detail if detail else ""))


# ---- R-4 pinned constants: every pre-T1 key/value, verbatim from the ----
# ---- f352023/a6b9f97 baseline (ticket S-3; byte-freeze red line)      ----
ROW_2026_11_22 = {
    "template": "bench-6x256k-v1",
    "hardware": "RTX PRO 5000 72GB / 1344GB-s / 64GB RAM",
    "model": "qwen3.8-flash-next-iq3_s",
    "engine": "basalt 0.5.5+00c3209b",
    "measured_at": "2026-11-22",
    "decode_agg_tps": 135.2,
    "decode_slot_median_tps": 68.2,
    "prefill_agg_tps": 2730,
    "single_route_decode_tps": 204.3,
    "source": "logs/bench_prod_6.log (basalt-fork ops)",
    "status": "user-accepted baseline",
}
ROW_2026_11_23 = {
    "template": "bench-6x256k-v1",
    "hardware": "RTX PRO 5000 72GB / 1344GB-s / 64GB RAM",
    "model": "qwen3.8-flash-next-iq3_s",
    "engine": "basalt 0.5.5+00c3209b (post-upgrade run, all 6 routes ran to max_tokens)",
    "measured_at": "2026-11-23",
    "decode_agg_tps": 141.6,
    "decode_slot_median_tps": 51.6,
    "prefill_agg_tps": 2702,
    "note": "slot median not comparable to the 11-22 baseline: every route filled "
            "16384 tokens here vs early-stop before; agg/prefill are the comparable figures",
    "source": "logs/bench_6slot_new_exe_20261123.log",
    "status": "regression pass, kept as second reference point",
}


def main():
    # ---------- R-1: file parses ----------
    obj = None
    try:
        with open(REGISTRY, encoding="utf-8-sig") as f:
            obj = json.load(f)
        rec("R-1:registry-json-parses", isinstance(obj, dict),
            "top-level keys: %s" % ",".join(obj))
    except Exception as e:
        rec("R-1:registry-json-parses", False, repr(e))

    # ---------- R-2: top-level contract present, old top keys kept ----------
    if obj is not None:
        ok = (obj.get("object") == "gateway.benchmark_registry"
              and "schema_version" in obj and obj["schema_version"] == SCHEMA_VERSION_TICKET
              and isinstance(obj.get("contract_note"), str) and obj["contract_note"].strip() != ""
              and "template_note" in obj and "entries" in obj)
        rec("R-2:top-level-contract", ok,
            "object=%r schema_version=%r contract_note_len=%d template_note=%s entries=%s"
            % (obj.get("object"), obj.get("schema_version"),
               len(obj.get("contract_note") or ""),
               "present" if "template_note" in obj else "MISSING",
               "present" if "entries" in obj else "MISSING"))
    else:
        rec("R-2:top-level-contract", False, "registry unparsed")

    # ---------- R-3: per-entry row-family schema ----------
    entries = (obj or {}).get("entries")
    if isinstance(entries, list) and entries:
        bad = []
        for i, row in enumerate(entries):
            why = None
            if not isinstance(row, dict):
                why = "entry not an object"
            elif row.get("layer") not in LAYER_ENUM:
                why = "layer=%r not in enum" % (row.get("layer"),)
            else:
                for k in ("template_id", "model_pack", "engine_version"):
                    if not (isinstance(row.get(k), str) and row[k].strip() != ""):
                        why = "%s not a non-empty string: %r" % (k, row.get(k))
                        break
                sc = row.get("scalars")
                if why is None:
                    if not isinstance(sc, dict) or set(sc) != SCALAR_SLOTS:
                        why = "scalars keys != closed 3-slot set: %r" % (
                            sorted(sc) if isinstance(sc, dict) else sc,)
                    else:
                        for sk, sv in sc.items():
                            if not (sv is None or (isinstance(sv, (int, float))
                                                   and not isinstance(sv, bool) and sv >= 0)):
                                why = "scalars.%s=%r not null/non-negative number" % (sk, sv)
                                break
                        if why is None and any(v is None for v in sc.values()):
                            note = row.get("scalars_note")
                            if not (isinstance(note, str) and note.strip() != ""):
                                why = "a null scalar but scalars_note empty/missing"
            if why:
                bad.append("#%d(%s@%s): %s" % (i, row.get("template") if isinstance(row, dict) else "?",
                                               row.get("measured_at") if isinstance(row, dict) else "?", why))
        rec("R-3:entry-row-schema", not bad, "; ".join(bad) if bad else
            "%d entries validated" % len(entries))
    else:
        rec("R-3:entry-row-schema", False, "entries missing or empty")

    # ---------- R-4: pre-T1 rows byte-frozen + migrated as map rows ----------
    def find_row(by):
        for row in (entries or []):
            if isinstance(row, dict) and row.get("template") == by["template"] \
                    and row.get("measured_at") == by["measured_at"]:
                return row
        return None

    for label, pinned in (("2026-11-22", ROW_2026_11_22), ("2026-11-23", ROW_2026_11_23)):
        row = find_row(pinned)
        if row is None:
            rec("R-4:frozen-row-%s" % label, False, "row not found by template+measured_at")
            continue
        diffs = [k for k, v in pinned.items() if k not in row or row[k] != v]
        migrated = (row.get("layer") == "map"
                    and isinstance(row.get("scalars"), dict)
                    and all(row["scalars"].get(s) is None for s in SCALAR_SLOTS))
        rec("R-4:frozen-row-%s" % label, not diffs and migrated,
            ("old-key diffs: %s; " % diffs if diffs else "") +
            ("layer=%r map+migrated" % row.get("layer") if not migrated else "map row, scalars null"))

    # ---------- R-5: /capabilities payload shape + passthrough lock ----------
    # Import-safe real module (main() under __main__ guard); stub handler has
    # exactly the three attributes _capabilities_payload touches: cfg, cfg_path, gate.
    try:
        sys.path.insert(0, HERE)
        import collector_proxy

        # a provably closed loopback port: bind(0) then release before use
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        dead_port = s.getsockname()[1]
        s.close()

        tmp = tempfile.mkdtemp(prefix="selftest_registry_")
        try:
            cfg_path = os.path.join(tmp, "config.json")
            cfg = {"upstream": "http://127.0.0.1:%d" % dead_port,
                   "listen": "127.0.0.1:0", "config_dir": tmp,
                   "max_inflight": 0}     # gate off; no engine_launch_config -> slots None
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f)
            stub = SimpleNamespace(cfg=cfg, cfg_path=cfg_path, gate=None)
            payload = collector_proxy._capabilities_payload(stub)

            need = ["ok", "object", "gateway", "capacity",
                    "engine_health", "benchmarks", "server_time"]
            missing = [k for k in need if k not in payload]
            with open(REGISTRY, encoding="utf-8-sig") as f:
                on_disk = json.load(f)
            passthrough = payload.get("benchmarks") == on_disk
            count_ok = (isinstance(payload.get("benchmarks"), dict)
                        and isinstance(payload["benchmarks"].get("entries"), list)
                        and len(payload["benchmarks"]["entries"]) == len(on_disk.get("entries", [])))
            rec("R-5:capabilities-shape-and-passthrough",
                not missing and passthrough and count_ok,
                "missing=%s benchmarks==on-disk-registry:%s entries:%s/%s"
                % (missing or "none", passthrough,
                   len(payload.get("benchmarks", {}).get("entries", [])),
                   len(on_disk.get("entries", []))))
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
    except Exception as e:
        rec("R-5:capabilities-shape-and-passthrough", False, repr(e))

    bad = [n for n, okv, _ in RESULTS if not okv]
    print("\n%d/%d PASS" % (len(RESULTS) - len(bad), len(RESULTS)))
    if bad:
        print("FAILED:", ", ".join(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
