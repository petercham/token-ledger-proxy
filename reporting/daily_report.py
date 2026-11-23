#!/usr/bin/env python3
r"""token-ledger · daily report generator: read requests-*.jsonl and write one Markdown report
per calendar day in the fixed five-section body (see references/report-format.md), plus a pending
flag so any host agent knows what still owes a verbal report. Idempotent: an existing report is
skipped unless --day. Stdlib only. Runs fine with WorkBuddy/Claude Code offline.

  python daily_report.py --config <out_dir>/config.json            # yesterday + any earlier day without a report
  python daily_report.py --config ... --day 2026-10-14             # one specific day (force)
  python daily_report.py --config ... --all                        # rebuild every day that has data
  python daily_report.py --config ... --reported 2026-10-14,...    # clear days from the pending list
"""
import glob
import json
import os
import statistics
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gateway"))  # find paths.py (gateway/) however this module is loaded


def load_config(path):
    from paths import load_config as portable_load_config
    return portable_load_config(path)


def log(runlog, msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    try:
        with open(runlog, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def load_day(out, day):
    rows = []
    path = os.path.join(out, f"requests-{day}.jsonl")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    for p in glob.glob(os.path.join(out, "requests-*.jsonl")):
        if p == path:
            continue
        for line in open(p, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("ts") and r["ts"][:10] == day:
                rows.append(r)
    return rows


def pct(vals, p):
    if not vals:
        return 0.0
    i = min(len(vals) - 1, int(round(p / 100 * (len(vals) - 1))))
    return vals[i]


def load_gate_day(out_dir, day):
    """rev13: gate-events rows for one calendar day, day-named file only.
    Recorder routes each row to its own ts day, so no cross-file scan is
    needed (unlike load_day, which chases collector backfill rows)."""
    rows = []
    path = os.path.join(out_dir, f"gate-events-{day}.jsonl")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


def gate_section(out_dir, day, req, cfg):
    """rev13: 排队闸拦截统计节（四态：A 有事件文件 / B 总账佐证回填口径 /
    C1 静态关闸 / C2 开闸无事件）。只出聚合量（隐私红线四），禁编造（红线五）。"""
    lines = ["## 排队闸拦截统计\n"]
    ev = load_gate_day(out_dir, day)
    q = [e for e in ev if e.get("event") == "queued"]
    rel = [e for e in ev if e.get("event") == "released"]
    waits = [int(e["waited_ms"]) for e in rel
             if isinstance(e.get("waited_ms"), (int, float))]
    if ev:                                              # A 态
        seqs_q = {e.get("seq") for e in q}
        cross = sum(1 for e in rel if e.get("seq") not in seqs_q)
        lines.append("| 指标 | 数值 |")
        lines.append("|---|---|")
        lines.append(f"| 拦截入栈（queued） | {len(q):,} 回 |")
        if waits:
            mean = sum(waits) / len(waits)
            lines.append(f"| 最长等待（released.max） | {max(waits):,} ms（{max(waits)/1000:.1f} s） |")
            lines.append(f"| 平均等待（released.mean） | {mean:,.0f} ms（{mean/1000:.1f} s） |")
        else:
            lines.append("| 最长等待（released.max） | — |")
            lines.append("| 平均等待（released.mean） | — |")
        forced = sum(1 for e in rel if e.get("forced"))
        beats = sum(int(e.get("heartbeats") or 0) for e in rel)
        lines.append(f"| 放行（released） | {len(rel):,} 回（强制放行 {forced:,}／心跳合计 {beats:,}） |")
        lines.append("\n> 口径：指标按事件文件日归属——`queued` 计入入队日，`released` 计入释放日；"
                     f"本窗口内 {cross:,} 项等待自前日跨入。")
        return lines
    wm = [int(r["queue_wait_ms"]) for r in req
          if isinstance(r.get("queue_wait_ms"), (int, float)) and r.get("queue_wait_ms")]
    if wm:                                              # B 态（回填期）
        mean = sum(wm) / len(wm)
        lines.append("> ⚠️ 当日无 `gate-events` 逐事件日志（rev12 换脑前的在岗脑不产该文件），"
                     "逐事件决策数据不可恢复。以下为总账 `queue_wait_ms` **回填口径**"
                     "（与 released.waited_ms 同源互证，rev12 A-4）——无入队决策读数、无心跳/强发数据。\n")
        lines.append("| 指标 | 数值（回填口径） |")
        lines.append("|---|---|")
        lines.append(f"| 拦截入栈（queue_wait_ms 行数） | {len(wm):,} 回 |")
        lines.append(f"| 最长等待 | {max(wm):,} ms（{max(wm)/1000:.1f} s） |")
        lines.append(f"| 平均等待 | {mean:,.0f} ms（{mean/1000:.1f} s） |")
        return lines
    if int(cfg.get("max_inflight", 0) or 0) <= 0 and cfg.get("gate_follow") is not True:
        lines.append("闸未启用（config 静态 `max_inflight`=0 且无 `gate_follow`）——本日无闸管辖，"
                     "不计闸统计。开闸判定按**日报生成时刻** config 现值，回填历史日时该判定可能失真。")  # C1 态
        return lines
    lines.append("| 指标 | 数值 |")                      # C2 态
    lines.append("|---|---|")
    lines.append("| 拦截入栈（queued） | 0 |")
    lines.append("| 最长等待（released.max） | — |")
    lines.append("| 平均等待（released.mean） | — |")
    lines.append("\n> 口径：开闸（含 gate_follow 跟随态）但当日无 `gate-events` 文件——可能闸开而零拦截，"
                 "也可能事件日志未启用（换脑前）。开闸判定按**日报生成时刻** config 现值，回填历史日时该判定可能失真。")
    return lines


def build_report(day, rows, cfg):
    req = [r for r in rows if not r.get("kind")]
    events = [r for r in rows if r.get("kind")]
    errors = [r for r in req if r.get("error")]
    gen = sum(r.get("gen", 0) for r in req)
    ms = sum(r.get("gen_ms", 0) for r in req)
    tp = sum(r.get("prompt", 0) for r in req)
    tn = sum(r.get("new_prompt", r.get("prompt", 0) - r.get("cached", 0)) for r in req)
    dec = sorted(r["decode_tok_s"] for r in req if r.get("decode_tok_s") and r.get("gen", 0) >= 30)
    tsd = sorted(r["ts"] for r in req if r.get("ts"))
    nots = sum(1 for r in req if not r.get("ts"))
    srcs = sorted({r.get("src", "?") for r in req})

    out = []
    out.append(f"# Token 账本日报（{day}）· {cfg.get('name', 'backend')}\n")
    out.append(f"数据口径：`requests-*.jsonl`（src={'+'.join(srcs)}）；本文件由 daily_report.py 自动生成，"
               "不依赖宿主 Agent 在线。\n")
    out.append("## 总览\n")
    out.append("| 指标 | 数值 |")
    out.append("|---|---|")
    out.append(f"| 请求数 | {len(req):,}（失败 {len(errors):,}） |")
    out.append(f"| 生成 tokens | {gen:,}（累计生成耗时 {ms / 3600000:.2f} h） |")
    if tp:
        reuse = 100 * (1 - tn / tp)
        out.append(f"| prompt tokens | {tp:,}（缓存复用 {reuse:.1f}%，真正新算 {tn:,}） |")
    if dec:
        w = gen / (ms / 1000) if ms else 0
        label = "解码速度（代理往返，含网络）" if "proxy" in srcs else "解码速度"
        out.append(f"| {label} | 加权 **{w:.1f} tok/s**｜中位 {statistics.median(dec):.1f}｜P10 {pct(dec,10):.1f}｜P90 {pct(dec,90):.1f}｜峰值 {max(dec):.1f} |")
    eng = sorted(r["engine_tps"] for r in req if r.get("engine_tps"))
    if eng:
        out.append(f"| 引擎侧解码速度（后端自报） | 中位 {statistics.median(eng):.1f} tok/s｜P10 {pct(eng,10):.1f}｜P90 {pct(eng,90):.1f}｜峰值 {max(eng):.1f} |")
    models = {}
    for r in req:
        if r.get("model"):
            m = models.setdefault(r["model"], [0, 0])
            m[0] += 1
            m[1] += r.get("gen", 0)
    if models:
        out.append("")
        out.append("| 模型 | 请求 | 生成 tok |")
        out.append("|---|---|---|")
        for mm, (n, g) in sorted(models.items(), key=lambda kv: -kv[1][1]):
            out.append(f"| {mm} | {n:,} | {g:,} |")
    keys = {}
    for r in req:
        k = r.get("key")
        if k:
            kk = keys.setdefault(k, [0, 0, 0])
            kk[0] += 1
            kk[1] += r.get("gen", 0)
            kk[2] += r.get("prompt", 0)
    if len(keys) > 1 or (keys and next(iter(keys)) != "none"):
        out.append("")
        out.append("按 API key（SHA-256 前 8 位指纹或 key_labels 人名）：\n")
        out.append("| key | 请求 | 生成 tok | prompt tok |")
        out.append("|---|---|---|---|")
        for kk, (n, g, p) in sorted(keys.items(), key=lambda kv: -kv[1][1]):
            out.append(f"| {kk} | {n:,} | {g:,} | {p:,} |")
    if events:
        kinds = {}
        for e in events:
            kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        out.append("")
        out.append("| 并发/事件 | " + "｜".join(f"{k} {v:,} 次" for k, v in sorted(kinds.items())) + " |")
    out.append("")

    out.append("## 覆盖窗口\n")
    if tsd:
        out.append(f"实测覆盖 **{tsd[0]} → {tsd[-1]}**（{len(tsd):,} 条带时间戳）")
    if nots:
        out.append(f"另有 {nots:,} 条为采集器断线期回填（无时间戳，按 offset 最后写入日归因）")
    if tsd and tsd[0][11:] > "00:00:00":
        out.append(f"\n> ⚠️ 当日 00:00 → {tsd[0][11:]} 无采集记录（服务或采集器当时未运行），该段不可恢复。")
    out.append("")
    out.extend(gate_section(cfg["out_dir"], day, req, cfg))
    out.append("")

    hist = {}
    for r in req:
        if r.get("ts"):
            h = int(r["ts"][11:13])
            hist[h] = hist.get(h, 0) + 1
    if hist:
        out.append("## 按小时分布\n")
        out.append("| 小时 | 请求数 |")
        out.append("|---|---|")
        for h in sorted(hist):
            out.append(f"| {h:02d}:00 | {hist[h]:,} |")
        top = sorted(hist.items(), key=lambda kv: -kv[1])[:3]
        out.append("")
        out.append("最忙时段：" + "｜".join(f"{h:02d} 时 {n:,} 次" for h, n in top))
        out.append("")

    out.append("## 数据精度说明\n")
    if "proxy" in srcs:
        out.append("- proxy 模式的 token 数来自供应商 API 的 `usage` 字段＝**权威计数**（供应商计费同源）。")
        out.append("- 流式（SSE）响应取最后一个携带 usage 的事件；非 2xx 记入失败数、token 记 0。")
    note = cfg.get("profile", {}).get("precision_note") or cfg.get("precision_note")
    if note:
        out.append(f"- {note}")
    out.append("")
    return "\n".join(out)


def flag_pending(out, day):
    p = os.path.join(out, "pending-report.txt")
    try:
        existing = {l.strip() for l in open(p, encoding="utf-8") if l.strip()} if os.path.exists(p) else set()
        if day not in existing:
            with open(p, "a", encoding="utf-8") as f:
                f.write(day + "\n")
    except OSError:
        pass


def do_day(cfg, day, force=False):
    out = cfg["out_dir"]
    runlog = os.path.join(out, "daily-report.log")
    target = os.path.join(out, f"usage-report-{day}.md")
    if os.path.exists(target) and not force:
        log(runlog, f"skip {day}: report already exists")
        return False
    rows = load_day(out, day)
    if not rows:
        log(runlog, f"skip {day}: no records")
        return False
    with open(target, "w", encoding="utf-8") as f:
        f.write(build_report(day, rows, cfg))
    log(runlog, f"wrote usage-report-{day}.md ({len(rows):,} records)")
    flag_pending(out, day)
    return True


def mark_reported(cfg, days):
    out = cfg["out_dir"]
    p = os.path.join(out, "pending-report.txt")
    try:
        existing = [l.strip() for l in open(p, encoding="utf-8") if l.strip()]
    except OSError:
        existing = []
    keep = [d for d in existing if d not in set(days)]
    if keep:
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(keep) + "\n")
    elif os.path.exists(p):
        os.remove(p)
    log(os.path.join(out, "daily-report.log"), f"marked reported: {','.join(days)} (still pending: {','.join(keep) or 'none'})")


def all_days(out):
    return sorted({os.path.basename(p)[len("requests-"):-len(".jsonl")]
                   for p in glob.glob(os.path.join(out, "requests-*.jsonl"))})


def run_daily(cfg):
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    log(os.path.join(cfg["out_dir"], "daily-report.log"), f"scheduled run: reporting {yesterday}")
    do_day(cfg, yesterday)
    for d in all_days(cfg["out_dir"]):
        if d < yesterday:
            do_day(cfg, d)


def main():
    if "--config" not in sys.argv:
        sys.exit("usage: daily_report.py --config <out_dir>/config.json [--day D | --all | --reported D,D]")
    cfg = load_config(sys.argv[sys.argv.index("--config") + 1])
    os.makedirs(cfg["out_dir"], exist_ok=True)
    args = sys.argv[1:]
    if "--reported" in args:
        i = args.index("--reported")
        mark_reported(cfg, args[i + 1].split(","))
        return
    if "--all" in args:
        for d in all_days(cfg["out_dir"]):
            do_day(cfg, d, force=True)
        return
    if "--day" in args:
        i = args.index("--day")
        do_day(cfg, args[i + 1], force=True)
        return
    run_daily(cfg)


if __name__ == "__main__":
    main()
