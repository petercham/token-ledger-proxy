#!/usr/bin/env python3
r"""rev13 · selftest_daily_report.py — fixture-driven regression for the
gate-stats section in daily_report.py. Pure stdlib, no network, no servers.

Each state gets its own throwaway temp box (never touches repo data/):
  F-A  gate-events file present (admitted + queued/released pair + a
       released seq=99 with no same-file queued = cross-day incoming wait)
  F-B  no gate-events file, ledger rows carry queue_wait_ms -> backfill view
  F-C1 no file, no evidence, config max_inflight=0 and no gate_follow
  F-C2 no file, no evidence, config max_inflight=2 (open gate, zero events)

Skeleton fixed by ticket ②-4: tempfile box -> write fixtures -> import
daily_report and call build_report(day, rows, cfg) + do_day(cfg, day)
directly -> rec(name, cond, detail) -> last line "N/N PASS", exit code = failures.
"""
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # tests/ -> project root
sys.path.insert(0, os.path.join(HERE, "reporting"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import daily_report  # noqa: E402

DAY = "2026-01-02"
RESULTS = []


def rec(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    if cond:
        print("PASS  %s" % name)
    else:
        print("FAIL  %s %s" % (name, detail))


def make_box(cfg_extra):
    box = tempfile.mkdtemp(prefix="selftest-daily-report-")
    cfg = {"name": "testbox", "out_dir": box, "max_inflight": 0}
    cfg.update(cfg_extra)
    return box, cfg


def wjsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def ledger_rows():
    return [
        {"ts": f"{DAY} 09:15:00", "key": "none", "fp": "00000000", "model": "m",
         "gen": 100, "prompt": 200, "cached": 0, "gen_ms": 1000, "src": "proxy"},
        {"ts": f"{DAY} 10:30:00", "key": "none", "fp": "00000000", "model": "m",
         "gen": 50, "prompt": 80, "cached": 10, "gen_ms": 500, "src": "proxy"},
    ]


def gate_section_of(text):
    """extract the gate section body for privacy/wording scans (pure scan view)."""
    anchor = text.find("## 按小时分布")
    if anchor == -1:
        anchor = text.find("## 数据精度说明")
    if anchor == -1:
        anchor = len(text)
    start = text.find("## 排队闸拦截统计")
    return text[start:anchor] if start != -1 else ""


def build_text(box, cfg, day=DAY):
    rows = daily_report.load_day(box, day)
    return daily_report.build_report(day, rows, cfg)


# ---------------- F-A: gate-events present ----------------
box_a, cfg_a = make_box({"max_inflight": 2})
wjsonl(os.path.join(box_a, f"requests-{DAY}.jsonl"), ledger_rows())
wjsonl(os.path.join(box_a, f"gate-events-{DAY}.jsonl"), [
    {"ts": f"{DAY} 10:00:00", "event": "admitted", "seq": 0,
     "inflight_at_decision": 1, "limit": 2},
    {"ts": f"{DAY} 10:00:05", "event": "queued", "seq": 1,
     "inflight_at_decision": 2, "limit": 2},
    {"ts": f"{DAY} 10:01:00", "event": "released", "seq": 1,
     "waited_ms": 1500, "heartbeats": 2, "forced": False},
    {"ts": f"{DAY} 11:00:00", "event": "released", "seq": 99,
     "waited_ms": 500, "heartbeats": 0, "forced": True},
])
text_a = build_text(box_a, cfg_a)
sec_a = gate_section_of(text_a)

i_win = text_a.find("## 覆盖窗口")
i_gate = text_a.find("## 排队闸拦截统计")
i_hr = text_a.find("## 按小时分布")
rec("report:gate section present between windows and hours",
    i_win != -1 and i_gate != -1 and i_hr != -1 and i_win < i_gate < i_hr,
    f"idx win={i_win} gate={i_gate} hours={i_hr}")
rec("report:A queued count matches file",
    "拦截入栈（queued） | 1 回" in text_a)
rec("report:A max wait ms and seconds",
    "最长等待（released.max） | 1,500 ms（1.5 s）" in text_a)
rec("report:A mean wait ms and seconds",
    "平均等待（released.mean） | 1,000 ms（1.0 s）" in text_a)
rec("report:A cross-day note counts incoming waits",
    "1 项等待自前日跨入" in text_a)
rec("report:A released forced and heartbeats columns",
    "强制放行 1" in text_a and "心跳合计 2" in text_a)

# ---------------- F-B: backfill from ledger queue_wait_ms ----------------
box_b, cfg_b = make_box({"max_inflight": 2})
rows_b = ledger_rows()
rows_b[0]["queue_wait_ms"] = 100
rows_b[1]["queue_wait_ms"] = 300
rows_b.append({"ts": f"{DAY} 12:00:00", "key": "none", "fp": "00000000",
               "model": "m", "gen": 10, "prompt": 10, "gen_ms": 100,
               "src": "proxy", "queue_wait_ms": 600})
wjsonl(os.path.join(box_b, f"requests-{DAY}.jsonl"), rows_b)
text_b = build_text(box_b, cfg_b)

rec("report:B backfill label present", "回填口径" in text_b)
rec("report:B three metrics from queue_wait_ms",
    "3 回" in text_b and "600 ms（0.6 s）" in text_b
    and "333 ms（0.3 s）" in text_b)

# ---------------- F-C1 / F-C2: no file, no evidence ----------------
box_c1, cfg_c1 = make_box({"max_inflight": 0})   # no gate_follow key
text_c1 = build_text(box_c1, cfg_c1)
sec_c1 = gate_section_of(text_c1)

box_c2, cfg_c2 = make_box({"max_inflight": 2})
text_c2 = build_text(box_c2, cfg_c2)
sec_c2 = gate_section_of(text_c2)

rec("report:C1 gate-off wording",
    "闸未启用" in text_c1 and "拦截入栈" not in text_c1)
rec("report:C2 open-gate zero metrics wording",
    "| 拦截入栈（queued） | 0 |" in text_c2 and "—" in text_c2
    and "闸未启用" not in text_c2)
rec("report:C1 and C2 wordings are mutually exclusive",
    "闸未启用" not in sec_c2
    and "开闸（含 gate_follow 跟随态）但当日无" not in sec_c1
    and "| 拦截入栈（queued） | 0 |" not in sec_c1)

# ---------------- privacy scan over all four states ----------------
PRIVACY_RE = re.compile(r'(fp|key_labels|messages|prompt|route|model)')
bad = [n for n, sec in (("A", sec_a), ("B", gate_section_of(text_b)),
                        ("C1", sec_c1), ("C2", sec_c2))
       if PRIVACY_RE.search(sec)]
rec("report:privacy no per-request fields", not bad, f"hit in {bad}")

# ---------------- idempotency + force rerun (F-A box) ----------------
first = daily_report.do_day(cfg_a, DAY)
second = daily_report.do_day(cfg_a, DAY)
rec("report:idempotent second run skips",
    first is True and second is False, f"first={first} second={second}")
forced_rerun = daily_report.do_day(cfg_a, DAY, force=True)
rec("report:day force rerun rebuilds",
    forced_rerun is True, f"force rerun={forced_rerun}")

# ---------------- existing sections intact (red line one, behavioural) ----------------
order = [text_a.find(h) for h in ("## 总览", "## 覆盖窗口", "## 按小时分布", "## 数据精度说明")]
rec("report:no existing sections altered",
    all(i != -1 for i in order) and order == sorted(order), f"idx={order}")

# ---------------- cleanup + report ----------------
for box in (box_a, box_b, box_c1, box_c2):
    shutil.rmtree(box, ignore_errors=True)

n = len(RESULTS)
passed = sum(1 for _, ok in RESULTS if ok)
print(f"{passed}/{n} PASS")
sys.exit(n - passed)
