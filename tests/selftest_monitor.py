#!/usr/bin/env python3
r"""Regression selftest for the self-owned monitor page (monitor_ext.py + monitor.html + monitor.js).

Temporary port only (19091). Never touches production 8080 / 8787, never starts
the real proxy, never needs a GPU. Checks:

  * the 18-field nvidia-smi CSV parses into the right keys (uuid, mem_util,
    enc_util, dec_util and the 4 per-card PCIe link fields included)
  * `dmon -s t` tx/rx output parses per index (last full-window sample wins)
  * the page renders ONE PCIe card showing only the LEAD line (big number =
    the current-highest-read card's instant MB/s; two-line sub = fixed
    "当前最高读速" + colour swatch + card name). The standalone legend area
    is gone (no mx-legend__row, cardHtml never requests a legend, legend
    container stays empty). The card carries NO degradation-alarm machinery
    (rev4/rev5 rule: x8 is the normal steady state on this platform, never
    alarm — nothing red anywhere)
  * disks/net subs render via innerHTML (their sub lines embed the 10x3
    mx-sw short-stroke legend HTML); the mx-sw glyph is a 10x3 stroke,
    not an 8x8 square
  * short rows (older drivers) are dropped instead of misaligned
  * a card NAME containing a comma cannot shift columns (csv-based parsing)
  * a missing UUID falls back to the card name, NEVER to the slot index
  * index-swap with stable UUIDs: identity by uuid survives
  * routes: /monitor serves the self-owned FUSED page (metrics grid, state
    badges, ctx gauge, request table, conversation cache), /monitor.js,
    /monitor.css and /monitor-sprite.svg serve our own assets,
    /ext.json / /health answer, unknown paths fall through
  * the page references NO official assets (no web/sprite.svg, app.css,
    components.css); js reads the official localStorage key strata.apikey
  * the injection mechanism (attach/pages/Watcher) is really gone
  * monitor.js binds GPU history by uuid, not by index

  python selftest_monitor.py
"""
import http.client
import importlib.util
import json
import os
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # tests/ -> project root
PORT = 19091
RESULTS = []

# Two fake cards. Realistic nvidia-smi CSV, nounits, 18 columns:
# index,name,driver_model,memory.total,memory.used,util,-temp,power,power.limit,clocks.sm,
# uuid,mem_util,enc_util,dec_util,pcie.gen.cur,pcie.width.cur,pcie.gen.max,pcie.width.max
# (Pro5000 healthy Gen5 x8 of x16; the 4090 row shows a DEGRADED Gen1 x8 of Gen4 x16 —
#  the exact fingerprint of the decode-speed incident.)
CSV_T0 = (
    "0, NVIDIA GeForce RTX 4090, WDDM, 24576, 1200, 55, 61, 300, 450, 2100,"
    " GPU-aaaa1111-0000-0000-0000-0000000000aa, 30, 0, 12, 1, 8, 4, 16\n"
    "1, NVIDIA RTX PRO 5000 72GB, TCC, 73728, 68000, 97, 70, 280, 300, 1800,"
    " GPU-bbbb2222-0000-0000-0000-0000000000bb, 88, 5, 40, 5, 8, 5, 16\n"
)
# Same two cards NEXT cycle: slot numbers SWAPPED, UUIDs unchanged.
CSV_T1 = (
    "0, NVIDIA RTX PRO 5000 72GB, TCC, 73728, 68000, 96, 71, 281, 300, 1800,"
    " GPU-bbbb2222-0000-0000-0000-0000000000bb, 87, 5, 40, 5, 8, 5, 16\n"
    "1, NVIDIA GeForce RTX 4090, WDDM, 24576, 1200, 56, 62, 301, 450, 2100,"
    " GPU-aaaa1111-0000-0000-0000-0000000000aa, 31, 0, 12, 1, 8, 4, 16\n"
)


def rec(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("  " + detail if detail else ""))


# DOM-stub node smoke harness. The monitor.js source is spliced into the
# /*__SRC__*/ marker at runtime. Any undefined identifier (the SPEED_DECODE
# incident class) or stub-visible TypeError throws -> smoke fails.
_NODE_SMOKE = r"""
"use strict";
const fs = require("fs");
// monitor.js is passed as argv[2]; read verbatim (no splicing: the source
// contains backticks and ${...} which would corrupt an embedded literal).
const src = fs.readFileSync(process.argv[2], "utf-8");

const els = {};
function registerIds(id) { els[id] = makeEl(id); return els[id]; }
function makeEl(id) {
  const _s = new Set();
  const el = {
    id, hidden: false, _html: "", textContent: "", className: "",
    dataset: {}, children: [], style: {},
    classList: {
      toggle(c, force) {
        if (force === true) _s.add(c);
        else if (force === false) _s.delete(c);
        else if (_s.has(c)) _s.delete(c); else _s.add(c);
      },
      add(c) { _s.add(c); }, remove(c) { _s.delete(c); },
      contains(c) { return _s.has(c); },
    },
    set innerHTML(v) { this._html = String(v); },
    get innerHTML() { return this._html; },
    querySelector(sel) { return makeEl(id + sel); },
    querySelectorAll(sel) { return [makeEl(id + sel + "0"), makeEl(id + sel + "1")]; },
    setAttribute() {}, getAttribute() { return null; },
    insertAdjacentHTML(pos, html) {
      this._html += html;
      const re = /id="([^"]+)"/g; let m;
      while ((m = re.exec(html))) if (!document.getElementById(m[1])) registerIds(m[1]);
    },
    remove() {},
  };
  return el;
}
// keep in sync with the id="..." set in monitor.html
const IDS = ["api-key", "apikey-note", "apikey-row", "apikey-row-inner",
  "cc-bars", "cc-card", "cc-facts", "cc-mem-bar", "cc-mem-text", "cc-note",
  "cc-slots-bar", "cc-slots-text", "cc-sum", "ctx-fill", "ctx-pct", "ctx-sub",
  "metrics", "mx-status", "ram-bar", "ram-progress", "ram-text", "req-all",
  "req-body", "req-totals", "req-wrap", "slots-bar", "slots-text",
  "state-badges", "state-bar", "state-detail", "state-gate",
  "state-label", "state-progress",
  "temp-bar", "temp-text", "theme-btn", "theme-icon"];
for (const id of IDS) els[id] = makeEl(id);

global.document = {
  getElementById: (id) => els[id] || null,
  querySelector: () => null,
  querySelectorAll: () => [],
  addEventListener: () => {},
  documentElement: { dataset: {}, setAttribute() {}, getAttribute() { return null; } },
  matchMedia: () => ({ matches: false, addEventListener: () => {} }),
};
global.localStorage = {
  _m: {},
  getItem(k) { return k in this._m ? this._m[k] : null; },
  setItem(k, v) { this._m[k] = String(v); },
  removeItem(k) { delete this._m[k]; },
};
global.window = global;
global.matchMedia = () => ({ matches: false, addEventListener: () => {} });
global.AbortController = class { constructor() { this.signal = {}; } abort() {} };

let metricsCalls = 0;
global.fetch = async (url, opts) => {
  if (String(url).includes("/metrics")) {
    metricsCalls += 1;
    if (metricsCalls === 1) return { status: 401, json: async () => ({}) };
    return {
      ok: true, status: 200,
      json: async () => ({
        engine: { state: "idle", expert_slots: 2, expert_cache_mib: 512, max_context: 131072 },
        live: { state: "idle", prompt_tokens: 0, max_context: 131072 },
        hardware: { cpu: 7, cpu_sockets: [5, 9], gpu_pcie_rx_mb: 12 },
        hardware_static: { cores: 16, threads: 32, cpu_socket_stats: [{ cores: 8, threads: 16 }, { cores: 8, threads: 16 }] },
        history: {}, requests: [], requests_kept: 0,
        totals: { requests: 7, since: 1765960860, prompt_tokens: 1200, reused: 300,
                  output_tokens: 450, prompt_ms: 400, decode_ms: 900 },
        conversation_cache: { enabled: false },
      }),
    };
  }
  return {
    ok: true, status: 200,
    json: async () => ({
      ok: true, ts: Date.now() / 1000,
      gpus: [{ uuid: "GPU-smoke", index: 0, name: "Smoke GPU", mode: "MCDM",
        mem_total_mib: 24576, mem_used_mib: 100, util: 5, temp: 40, power: 30,
        power_limit: 300, sm_clock: 1200, mem_util: 5, enc_util: 0, dec_util: 0,
        pcie_gen: 5, pcie_width: 8, pcie_gen_max: 5, pcie_width_max: 16,
        pcie_rx_mb: 10, pcie_tx_mb: 1 }],
      pcie_txrx_supported: true,
      cpu_name: "Smoke CPU Model <x>", cpu_mhz: 5000,
      ram: { used: 8e9, total: 32e9 }, swap: { used: 0, total: 0 },
      disks: [{ number: 0, read_mb: 1, write_mb: 2, model: "X", bus: "NVMe", size: 1e12, drives: "c:" }],
      net: [{ name: "Ethernet", kind: "wired", connected: true, down_mb: 3, up_mb: 1 }],
    }),
  };
};

const realSetTimeout = setTimeout;
global.__budget = 6;
global.setTimeout = (fn, ms) => {
  if (global.__budget-- <= 0) return 0;
  try { fn(); } catch (e) { console.error("SMOKE FAIL (tick):", (e && e.stack) || e); process.exit(1); }
  return 0;
};

try {
  (0, eval)(src);
  setTimeout(() => {}, 0);
  if (!global.window.__strataLedgerMonitor) throw new Error("IIFE did not execute");
  process.on("uncaughtException", (e) => { console.error("SMOKE FAIL (async):", (e && e.stack) || e); process.exit(1); });
  process.on("unhandledRejection", (e) => { console.error("SMOKE FAIL (rejection):", (e && e.stack) || e); process.exit(1); });
  realSetTimeout(() => {
    if (metricsCalls < 2) { console.error("SMOKE FAIL: metrics 200-branch never exercised (calls=%d)", metricsCalls); process.exit(1); }
    console.log("TOTALS " + JSON.stringify((els["req-totals"] && els["req-totals"].textContent) || ""));
    console.log("SMOKE OK: IIFE + tick + async render chain drained, no ReferenceError");
    process.exit(0);
  }, 300);
} catch (e) {
  console.error("SMOKE FAIL:", (e && e.stack) || e);
  process.exit(1);
}
"""


def load_module():
    spec = importlib.util.spec_from_file_location("monitor_ext",
                                                 os.path.join(HERE, "monitor_ext.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    m = load_module()

    # ---- 1. parser: keys, values, 18 columns ----
    rows = m.parse_gpu_csv(CSV_T0)
    rec("18-field CSV parses into 2 cards", len(rows) == 2, "rows=%d" % len(rows))
    if len(rows) == 2:
        a, b = rows[0], rows[1]
        rec("uuid / index / name / mode correct",
            a["uuid"] == "GPU-aaaa1111-0000-0000-0000-0000000000aa" and a["index"] == 0
            and a["name"] == "NVIDIA GeForce RTX 4090" and a["mode"] == "WDDM"
            and b["mode"] == "TCC", "a=%s b=%s" % (a.get("mode"), b.get("mode")))
        rec("mem/enc/dec util fields present and parsed",
            a["mem_util"] == 30 and a["enc_util"] == 0 and a["dec_util"] == 12
            and b["mem_util"] == 88 and b["dec_util"] == 40,
            "a=%s/%s/%s" % (a["mem_util"], a["enc_util"], a["dec_util"]))
        rec("legacy fields untouched (util/temp/power/clocks/mem)",
            a["util"] == 55 and a["temp"] == 61 and a["power"] == 300
            and a["power_limit"] == 450 and a["sm_clock"] == 2100
            and a["mem_total_mib"] == 24576 and a["mem_used_mib"] == 1200)
        rec("N/A counters become None, not crashes",
            m.parse_gpu_csv(CSV_T0.replace(", 30, 0, 12", ", N/A, N/A, N/A"))[0]["mem_util"] is None)
        rec("4 per-card PCIe link fields parsed (pcie_gen/width + _max)",
            a["pcie_gen"] == 1 and a["pcie_width"] == 8
            and a["pcie_gen_max"] == 4 and a["pcie_width_max"] == 16
            and b["pcie_gen"] == 5 and b["pcie_gen_max"] == 5,
            "a=%s/%s@%s/%s" % (a["pcie_gen"], a["pcie_width"], a["pcie_gen_max"], a["pcie_width_max"]))
        rec("link fields are neutral data (no alarm semantics in the parser)",
            a["pcie_gen"] == 1 and a["pcie_gen_max"] == 4  # idle downclock value, kept as-is
            and b["pcie_gen"] == 5 and b["pcie_gen_max"] == 5)

    # ---- 2. short rows dropped (driver answering fewer columns than GPU_FIELDS) ----
    short = "0, Some GPU, WDDM, 8192, 100, 10, 40, 50, 100, 900\n"
    rec("rows with <18 columns are dropped", m.parse_gpu_csv(short) == [],
        "got=%s" % m.parse_gpu_csv(short))
    # the previous 14-column shape (pre-PCIe era) must also be dropped, not half-filled
    old14 = ("0, Old Shape Card, WDDM, 8192, 100, 10, 40, 50, 100, 900,"
             " GPU-dddd4444-0000-0000-0000-0000000000dd, 5, 1, 2\n")
    rec("14-column rows (missing the 4 PCIe fields) are dropped",
        m.parse_gpu_csv(old14) == [], "got=%s" % m.parse_gpu_csv(old14))

    # ---- 3. comma inside a card name cannot shift columns ----
    # nvidia-smi quotes fields that contain commas; the csv module honours that.
    weird = ('0, "NVIDIA A, B Special Card", TCC, 4096, 10, 5, 30, 40, 500, 600,'
             ' GPU-cccc3333-0000-0000-0000-0000000000cc, 1, 2, 3, 4, 16, 4, 16\n')
    w = m.parse_gpu_csv(weird)
    rec("comma in card name parsed via csv module",
        len(w) == 1 and w[0]["name"] == "NVIDIA A, B Special Card" and w[0]["dec_util"] == 3,
        "rows=%d" % len(w))

    # ---- 4. missing UUID falls back to name, never to index ----
    nouuid = ("0, Solo Card, TCC, 4096, 10, 5, 30, 40, 500, 500,"
              " N/A, 1, 2, 3, N/A, N/A, N/A, N/A\n")
    n0 = m.parse_gpu_csv(nouuid)
    rec("missing UUID falls back to name-based identity",
        len(n0) == 1 and n0[0]["uuid"] == "name:Solo Card",
        "uuid=%s" % (n0[0]["uuid"] if n0 else "none"))

    # ---- 5. index swap with stable uuid: uuid identity survives ----
    r0 = {r["uuid"]: r for r in m.parse_gpu_csv(CSV_T0)}
    r1 = {r["uuid"]: r for r in m.parse_gpu_csv(CSV_T1)}
    rec("index 0/1 swapped but uuid set identical (history cannot cross cards)",
        set(r0) == set(r1)
        and r0["GPU-aaaa1111-0000-0000-0000-0000000000aa"]["index"] == 0
        and r1["GPU-aaaa1111-0000-0000-0000-0000000000aa"]["index"] == 1
        and abs(r0["GPU-bbbb2222-0000-0000-0000-0000000000bb"]["util"]
                - r1["GPU-bbbb2222-0000-0000-0000-0000000000bb"]["util"]) < 2.0)

    # ---- 5b. dmon tx/rx parsing (per-card PCIe throughput, rev4) ----
    dmon = (
        "# gpu  rxpci  txpci \n"
        "# Idx   MB/s   MB/s \n"
        "    0     19     13 \n"
        "    1      0      0 \n"
        "    0   1168      1 \n"
        "    1      0      0 \n"
    )
    d = m.parse_dmon_txrx(dmon)
    rec("dmon -s t parsed: last full-window sample wins per index",
        d == {0: (1168.0, 1.0), 1: (0.0, 0.0)}, "got=%s" % d)
    rec("dmon garbage/N-A lines skipped, empty output -> {}",
        m.parse_dmon_txrx("# gpu\nN/A junk line\n    2   5   6\n") == {2: (5.0, 6.0)}
        and m.parse_dmon_txrx("") == {})

    # ---- 6. injection machinery is gone ----
    rec("attach()/pages()/Watcher removed",
        not hasattr(m, "attach") and not hasattr(m, "pages") and not hasattr(m, "Watcher"))
    # Driver-verified field names (621.24): utilization.encoder / utilization.decoder.
    # The old names encoder.utilization / decoder.utilization make the WHOLE
    # nvidia-smi query fail (rc=2, every card disappears), so assert the exact names.
    rec("GPU_QUERY asks for the 4 new fields (driver-valid names)",
        all(q in m.GPU_QUERY for q in
            ("uuid", "utilization.memory", "utilization.encoder", "utilization.decoder"))
        and "encoder.utilization" not in m.GPU_QUERY
        and "decoder.utilization" not in m.GPU_QUERY)
    rec("GPU_QUERY asks for the 4 PCIe link fields; GPU_FIELDS == 18",
        all(q in m.GPU_QUERY for q in
            ("pcie.link.gen.current", "pcie.link.width.current",
             "pcie.link.gen.max", "pcie.link.width.max"))
        and m.GPU_FIELDS == 18)

    # ---- 7. routes (in-process) ----
    page = m.answer("/monitor")
    rec("/monitor serves our self-owned fused page",
        page is not None and b'id="metrics"' in page[0]
        and b"/monitor.js" in page[0] and b"/monitor.css" in page[0]
        and b"/monitor-sprite.svg" in page[0]
        and b'state-badges' in page[0] and b'ctx-fill' in page[0]
        and b'req-body' in page[0] and b'cc-card' in page[0],
        "len=%s" % (len(page[0]) if page else 0))
    js = m.answer("/monitor.js")
    rec("/monitor.js serves uuid-bound script",
        js is not None and b"uuid" in js[0] and b"hist.gpus" in js[0],
        "len=%s" % (len(js[0]) if js else 0))
    rec("req-totals since line locked to ISO-style date, weekday option gone",
        js is not None
        and b"const sd = new Date(t.since * 1000);" in js[0]
        and b'${sd.getFullYear()}-${String(sd.getMonth() + 1).padStart(2, "0")}' in js[0]
        and b'weekday: "short"' not in js[0],
        "locked-lines=%s weekday-gone=%s" % (
            js is not None and b"const sd = new Date(t.since * 1000);" in js[0],
            js is not None and b'weekday: "short"' not in js[0]))
    css = m.answer("/monitor.css")
    rec("/monitor.css served as text/css with the ported st-* tokens",
        css is not None and "text/css" in css[1]
        and b"--st-accent" in css[0] and b".st-metric__spark" in css[0],
        "len=%s" % (len(css[0]) if css else 0))
    sp = m.answer("/monitor-sprite.svg")
    rec("/monitor-sprite.svg served as svg with the icons we reference",
        sp is not None and "svg" in sp[1]
        and all(("<symbol id=\"i-%s\"" % k).encode() in sp[0]
                for k in ("gauge", "gpu", "memory", "disk", "link", "cpu", "sun", "moon")),
        "len=%s" % (len(sp[0]) if sp else 0))
    rec("page references no official assets (no web/sprite.svg, no app.css)",
        page is not None and b"web/sprite.svg" not in page[0]
        and b"app.css" not in page[0] and b"components.css" not in page[0])
    rec("js reads the official localStorage key for the engine key",
        js is not None and b"strata.apikey" in js[0] and b"/metrics" in js[0])
    rec("js draws ONE PCIe card, lead-line only (rev5): big number = lead card's "
        "instant MB/s, sub = 当前最高读速 + colour swatch + card name",
        js is not None and b"drawMultiSpark" in js[0] and b"SERIES_COLORS" in js[0]
        and b"pcie_rx_mb" in js[0]
        and b"if (!lead || rx > (lead.pcie_rx_mb || 0)) lead = g;" in js[0]  # lead = max pcie_rx_mb this round
        and "当前最高读速".encode() in js[0]                                  # sub line 1 fixed text
        and "sub.innerHTML = `当前最高读速<br>${sw(leadColor)}".encode("utf-8") in js[0]  # sub line 2 = swatch + name
        and b"mx-badge--danger" not in js[0] and b"degraded" not in js[0])
    rec("PCIe standalone legend area removed (no legend rows in js, no legend:true "
        "opt passed, legend container stays empty)",
        js is not None and b"mx-legend__row" not in js[0] and b"legend: true" not in js[0]
        and b'const lg = $(id + "-lg");' in js[0] and b'lg.innerHTML = "";' in js[0])
    rec("disk/net subs render via innerHTML (their lines embed mx-sw legend HTML; "
        "setSub/textContent would show tags literally)",
        # 11-16 sixth-draft: read/write and down/up are now two innerHTML
        # lines under the big number, each led by its own short-stroke glyph.
        js is not None
        and 'sub.innerHTML = `${sw(RW_DOWN)}读 '.encode("utf-8") in js[0]
        and '`<br>${sw(RW_UP)}写 '.encode("utf-8") in js[0]
        and 'subN.innerHTML = `${sw(RW_DOWN)}下行 '.encode("utf-8") in js[0]
        and '`<br>${sw(RW_UP)}上行 '.encode("utf-8") in js[0])
    rec("no degradation alarm machinery anywhere in js/css "
        "(mx-badge--danger / degraded / badgeSlot / mx-bdg all absent)",
        js is not None and b"badgeSlot" not in js[0] and b"mx-bdg" not in js[0]
        and css is not None and b"mx-bdg" not in css[0]
        and b"mx-badge--danger" not in css[0])
    rec("mx-sw legend glyph is a 10x3 short stroke, not an 8x8 square",
        css is not None and b".mx-sw{display:inline-block;width:10px;height:3px" in css[0])
    rec("display-rule baseline (host hotfix, do-not-regress): mode badge rides the "
        "big number, no '% SM', icon via opts.icon",
        js is not None and b'height:20px' in js[0]          # badge in value slot
        and b"% SM" not in js[0]                            # old unit gone
        and b'icon: "gpu"' in js[0]                         # icon path unified
        and b'icon("gpu", "st-icon st-icon--sm")}${label}' not in js[0])  # no icon in label
    # rev7c: GPU card slot number moved BEFORE the name, 1-based like disk cards,
    # muted + tooltip saying the slot number drifts and is not identity.
    rec("display-rule baseline (host hotfix rev7c, do-not-regress): gpu card title "
        "= muted #index+1 (1-based, same style as disk) before the short name; "
        "old 0-based #index form never comes back",
        js is not None
        and ('<span class="muted" title="\u69fd\u4f4d\u53f7\u4f1a\u6f02\uff0c\u4ec5\u4f9b\u5bf9\u7167\uff0c\u4e0d\u4f5c\u4e3a\u8eab\u4efd">#${esc(g.index + 1)}</span> ${esc(shortName)}').encode("utf-8") in js[0]
        and b"${esc(g.index)}" not in js[0])
    # incident regression: a hotfix once referenced undefined SPEED_DECODE /
    # SPEED_PREFILL consts -> ReferenceError killed EVERY readout on the page.
    # The fix is CSS-class based (swc + .mx-sw--decode/--prefill). Never again.
    rec("incident guard: undefined-constant references SPEED_DECODE/SPEED_PREFILL "
        "must never appear in js (ReferenceError killed the whole page once)",
        js is not None and b"SPEED_DECODE" not in js[0] and b"SPEED_PREFILL" not in js[0])
    rec("incident fix in place: swc() helper defined; speed legend uses it; "
        "css carries .mx-sw--decode / .mx-sw--prefill in theme vars",
        js is not None and ('const swc = (cls) => `<i class="mx-sw ${cls}"></i>`;').encode("utf-8") in js[0]
        and b'swc("mx-sw--decode")' in js[0] and b'swc("mx-sw--prefill")' in js[0]
        and css is not None and b".mx-sw--decode{background:var(--st-accent)}" in css[0]
        and b".mx-sw--prefill{background:color-mix(in srgb,var(--st-accent) 65%,black)}" in css[0])
    rec("speed card legend shape (host hotfix): subD/subP innerHTML start with "
        "swc decode/prefill glyphs",
        js is not None
        and b'subD.innerHTML = swc("mx-sw--decode")' in js[0]
        and b'subP.innerHTML = swc("mx-sw--prefill")' in js[0])
    # 11-16 sixth-draft supersedes the &nbsp; big-number shape: the big
    # number is value + <small>MB/s</small> + a code-style spec/kind badge;
    # the 读/下行 markers moved DOWN into the small-text two lines.
    _disk_v6 = ('v.innerHTML = p[0] + `<small>${p[1]}</small>` +').encode("utf-8")
    rec("display-rule baseline (host hotfix rev6, do-not-regress): disk big number "
        "= value + <small>unit</small> + spec badge (bus minus \"Disk N · \" prefix); "
        "title head starts #number+1 (human 1-based)",
        js is not None
        and _disk_v6 in js[0]
        and ('(spec ? ` <span class="st-badge" style="height:20px">${esc(spec)}</span>` : "");').encode("utf-8") in js[0]
        and ('const spec = d.bus ? String(d.bus).replace(/^Disk\\s*\\d+\\s*·\\s*/, "") : "";').encode("utf-8") in js[0]
        and b"const head = [`#${d.number + 1}`];" in js[0]
        # the superseded &nbsp; big-number shapes must never come back
        and ('<small>${p[1]}&nbsp;${sw(RW_DOWN)}读').encode("utf-8") not in js[0]
        and ('${p[1] + "&nbsp;" : ""}${sw(RW_DOWN)}下行').encode("utf-8") not in js[0])
    rec("display-rule baseline (host hotfix rev6b, do-not-regress): wifi adapter is "
        "titled \u65e0\u7ebf\u7f51\u5361 with NO kind badge; wired = real adapter name + "
        "\u6709\u7ebf badge; NET_KIND_LABEL / WLAN gone for good",
        js is not None
        and ('const label = a.kind === "wifi" ? "\u65e0\u7ebf\u7f51\u5361" : esc(a.name);').encode("utf-8") in js[0]
        and ('const badge = a.kind === "wired" ? "\u6709\u7ebf" : "";').encode("utf-8") in js[0]
        and '(badge ? ` <span class="st-badge" style="height:20px">${esc(badge)}</span>` : "");'.encode("utf-8") in js[0]
        and b'cardHtml(id, "net", label, { icon: "link", tone: "info" })' in js[0]
        and b"NET_KIND_LABEL" not in js[0] and b"WLAN" not in js[0])

    rec("cpu card branch shapes locked: single-socket path keeps the old form "
        "+ optional GHz suffix (2026-11-17); "
        "multi-socket branch (hw.cpu_sockets > 1) reuses speed layout + hist.cpuSock buckets",
        js is not None
        # single-socket baseline (this fleet's machines; must not change)
        and b"} else if (hw.cpu != null) {" in js[0]
        and b'v.innerHTML = `${fmt(hw.cpu)}<small>%</small>` +' in js[0]
        # GHz suffix present and gated on cpu_mhz (missing field -> plain % only)
        and b"const mhz = ext && ext.cpu_mhz;" in js[0]
        and b'<small>${fmt(mhz / 1000, 2)}<small> GHz</small></small>' in js[0]
        # the GHz-less old big-number line must never come back verbatim
        and b'v.innerHTML = `${fmt(hw.cpu)}<small>%</small>`;\n' not in js[0]
        # multi-socket branch present and bucketed per socket
        and b"Array.isArray(hw.cpu_sockets) && hw.cpu_sockets.length > 1" in js[0]
        and b"hist.cpuSock" in js[0])
    rec("cpu card title carries static model (ext.cpu_name, both branches) + idempotent "
        "late-ext label refresh; absent field keeps plain 'CPU', never invents a name "
        "(2026-11-17)",
        js is not None
        and 'const cpuLabel = "CPU" + (ext && ext.cpu_name ? ` · ${esc(ext.cpu_name)}` : "");'.encode("utf-8") in js[0]
        and b'setCpuTitle(ensure(host, id, cardHtml(id, "cpu", cpuLabel, { icon: "cpu", tone: "info", speed: true })))' in js[0]
        and b'setCpuTitle(ensure(host, id, cardHtml(id, "cpu", cpuLabel, { icon: "cpu", tone: "info" })))' in js[0]
        and b'lt.innerHTML !== cpuLabel) lt.innerHTML = cpuLabel;' in js[0]
        # bare-title old form must never come back for the cpu card
        and b'cardHtml(id, "cpu", "CPU",' not in js[0])
    rec("cpu_name sampler: stdlib registry (nt) / /proc/cpuinfo (posix), whitespace-collapsed, "
        "64-char cap, empty on any failure -> field omitted",
        getattr(m, "cpu_name", None) is not None
        and b"ProcessorNameString" in open(os.path.join(HERE, "monitor_ext.py"), "rb").read()
        and b'"/proc/cpuinfo"' in open(os.path.join(HERE, "monitor_ext.py"), "rb").read()
        and b'name = " ".join(name.split())' in open(os.path.join(HERE, "monitor_ext.py"), "rb").read()
        and b'return name[:64]' in open(os.path.join(HERE, "monitor_ext.py"), "rb").read())
    rec("cpu legend baseline (host hotfix rev7): multi-socket subs led by cpu1/cpu2 "
        "swatch glyphs + subOf(); single-socket sub gets cpu1 glyph + cores/threads or "
        "\u6574\u673a fallback (old setSub threads line gone)",
        js is not None
        and b'sd1.innerHTML = swc("mx-sw--cpu1") + subOf(0);' in js[0]
        and b'sd2.innerHTML = swc("mx-sw--cpu2") + subOf(n)' in js[0]
        and b'sub1.innerHTML = swc("mx-sw--cpu1") + (st.threads ?' in js[0]
        and "\u6574\u673a".encode("utf-8") in js[0]
        and b'setSub(id + "-s", st.threads' not in js[0])
    rec("cpu legend colours: css .mx-sw--cpu1/--cpu2 keyed to info theme vars; "
        ".st-metric__spark .speed-prefill re-based to currentColor so each card's "
        "right/prefill line auto-matches its own main line (accent vs info tone)",
        css is not None
        and b".mx-sw--cpu1{background:var(--st-info)}" in css[0]
        and b".mx-sw--cpu2{background:color-mix(in srgb,var(--st-info) 65%,black)}" in css[0]
        and b".st-metric__spark .speed-prefill{color:color-mix(in srgb,currentColor 65%,black)}" in css[0])
    rec("sub-line alignment skeleton (host hotfix): cardHtml wraps label text in "
        "mx-label-t (always one line + ellipsis); css locks the wrap rule and the "
        "fixed-height big-number row so subs start at the same offset on every card",
        js is not None
        and b'<span class="st-metric__label">${icon(o.icon || "activity", "st-icon st-icon--sm")}<span class="mx-label-t">${labelHtml}</span></span>' in js[0]
        and css is not None
        and b".mx-label-t{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}" in css[0]
        and b"min-height:var(--st-fs-stat);white-space:nowrap}" in css[0]
        # badge baseline fix (rev7b): the inline-block .st-badge on the baseline
        # used to stretch the big-number line box and push subs down; centring it
        # is the real cure. The short-lived inline-flex variant is banned.
        and b".st-metric__value .st-badge{vertical-align:middle}" in css[0]
        and b"display:inline-flex;align-items:center;gap:0" not in css[0])
    # ---- 7b. node smoke: eval the whole IIFE against a DOM stub. Any
    # undefined identifier (the SPEED_DECODE-class incident: undefined consts
    # -> ReferenceError -> EVERY readout gone, user-confirmed) throws here.
    # node --check cannot catch undefined identifiers; running can.
    # Harness is generated at runtime (kept out of the shipped file count).
    # Skipped (not failed) on boxes without node — it is a dev/CI guard.
    import shutil as _shutil
    import subprocess as _sp
    import tempfile as _tf
    _node = _shutil.which("node")
    if _node:
        with _tf.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as _t:
            _t.write(_NODE_SMOKE)
            _hp = _t.name
        try:
            _r = _sp.run([_node, _hp, os.path.join(HERE, "monitor.js")],
                         capture_output=True, text=True, timeout=30)
            rec("node smoke: monitor.js IIFE + full tick chain run against a DOM "
                "stub, no ReferenceError/TypeError (SPEED_DECODE incident class)",
                _r.returncode == 0 and "SMOKE OK" in (_r.stdout or ""),
                (_r.stderr or _r.stdout or "").strip()[-200:])
            import re as _re
            _tline = ""
            for _ln in (_r.stdout or "").splitlines():
                if _ln.startswith("TOTALS "):
                    _tline = _ln[len("TOTALS "):]
            try:
                _txt = json.loads(_tline)
            except Exception:
                _txt = ""
            rec("req-totals line renders real Y-M-D (smoke)",
                bool(_re.match(r"^自 \d{4}-\d{2}-\d{2} \d{2}:\d{2}：\d", _txt)) and "周" not in _txt,
                "line=%r" % (_txt[:80],))
        finally:
            try:
                os.unlink(_hp)
            except OSError:
                pass
    else:
        rec("node smoke skipped (node not installed on this box)", True)

    # ---- 7c. gate queue merged into state card (2026-11-19 human call): the
    # standalone "等待中" card is retired. ext.gate.queued=2 -> NO card-gate ever
    # (pruned if stale); the state card carries it: label mentions 「网关队列」 + count,
    # engine-queue vs gateway-queue wording distinguished. queued back to 0 ->
    # label returns to idle wording.
    if _node:
        _GATE_SMOKE = r"""
"use strict";
const fs = require("fs");
const src = fs.readFileSync(process.argv[2], "utf-8");
const els = {};
function registerIds(id) { els[id] = makeEl(id); return els[id]; }
function makeEl(id) {
  const _s = new Set();
  const el = {
    id, hidden: false, _html: "", textContent: "", className: "",
    dataset: {}, children: [], style: {}, _removed: false,
    classList: {
      toggle(c, force) {
        if (force === true) _s.add(c);
        else if (force === false) _s.delete(c);
        else if (_s.has(c)) _s.delete(c); else _s.add(c);
      },
      add(c) { _s.add(c); }, remove(c) { _s.delete(c); },
      contains(c) { return _s.has(c); },
    },
    set innerHTML(v) { this._html = String(v); },
    get innerHTML() { return this._html; },
    querySelector(sel) { return makeEl(id + sel); },
    querySelectorAll(sel) { return [makeEl(id + sel + "0"), makeEl(id + sel + "1")]; },
    setAttribute() {}, getAttribute() { return null; },
    insertAdjacentHTML(pos, html) {
      this._html += html;
      const re = /id="([^"]+)"/g; let m;
      const sec = /data-mx-section="([^"]+)"/.exec(html);
      while ((m = re.exec(html))) {
        if (!document.getElementById(m[1])) registerIds(m[1]);
        if (sec) {
          const child = document.getElementById(m[1]);
          if (child && !this.children.includes(child)) {
            child.dataset = child.dataset || {};
            child.dataset.mxSection = sec[1];
            child.remove = () => {
              child._removed = true;
              const i = this.children.indexOf(child);
              if (i >= 0) this.children.splice(i, 1);
            };
            this.children.push(child);
          }
        }
      }
    },
    remove() { this._removed = true; },
  };
  return el;
}
const IDS = ["api-key", "apikey-note", "apikey-row", "apikey-row-inner",
  "cc-bars", "cc-card", "cc-facts", "cc-mem-bar", "cc-mem-text", "cc-note",
  "cc-slots-bar", "cc-slots-text", "cc-sum", "ctx-fill", "ctx-pct", "ctx-sub",
  "metrics", "mx-status", "ram-bar", "ram-progress", "ram-text", "req-all",
  "req-body", "req-totals", "req-wrap", "slots-bar", "slots-text",
  "state-badges", "state-bar", "state-detail", "state-gate",
  "state-label", "state-progress",
  "temp-bar", "temp-text", "theme-btn", "theme-icon"];
for (const id of IDS) els[id] = makeEl(id);

global.document = {
  readyState: "complete",
  getElementById: (id) => (els[id] && !els[id]._removed) ? els[id] : null,
  querySelector: () => null,
  querySelectorAll: () => [],
  addEventListener: () => {},
  documentElement: { dataset: {}, setAttribute() {}, getAttribute() { return null; } },
  matchMedia: () => ({ matches: false, addEventListener: () => {} }),
};
global.localStorage = { _m: {}, getItem(k) { return k in this._m ? this._m[k] : null; },
  setItem(k, v) { this._m[k] = String(v); }, removeItem(k) { delete this._m[k]; } };
global.window = global;
global.matchMedia = () => ({ matches: false, addEventListener: () => {} });
global.AbortController = class { constructor() { this.signal = {}; } abort() {} };

// __gate is swapped between explicit ticks: absent -> queued=2 -> queued=0
global.__gate = undefined;
global.__tick = null;          // captured from monitor.js's own setTimeout(tick, TICK_MS)
global.__slots = undefined;    // /slots fixture: undefined -> 404, else the array
global.fetch = async (url, opts) => {
  if (String(url).includes("/slots")) {
    if (global.__slots === undefined) return { ok: false, status: 404, json: async () => null };
    return { ok: true, status: 200, json: async () => global.__slots };
  }
  if (String(url).includes("/metrics")) {
    return { ok: true, status: 200, json: async () => ({
      engine: { state: "idle", expert_slots: 2, expert_cache_mib: 512, max_context: 131072 },
      live: { state: "idle", prompt_tokens: 0, max_context: 131072 },
      hardware: {}, hardware_static: {}, history: {}, requests: [], requests_kept: 0,
      totals: {}, conversation_cache: { enabled: false } }) };
  }
  const ext = {
    ok: true, ts: Date.now() / 1000, gpus: [], pcie_txrx_supported: false,
    ram: { used: 8e9, total: 32e9 }, swap: { used: 0, total: 0 },
    disks: [], net: [],
  };
  if (global.__gate !== undefined) ext.gate = global.__gate;
  return { ok: true, status: 200, json: async () => ext };
};

// stub setTimeout: capture the scheduled tick, do NOT auto-chain (explicit drive)
const realSetTimeout = setTimeout;
global.setTimeout = (fn) => { global.__tick = fn; return 0; };

const gateCard = () => els["card-gate"] && !els["card-gate"]._removed;

try {
  (0, eval)(src);              // tick #1 starts (gate field absent)
  process.on("uncaughtException", (e) => { console.error("GATE SMOKE FAIL (async):", (e && e.stack) || e); process.exit(1); });
  process.on("unhandledRejection", (e) => { console.error("GATE SMOKE FAIL (rejection):", (e && e.stack) || e); process.exit(1); });
  const settle = () => new Promise((res) => realSetTimeout(res, 80));
  (async () => {
    await settle();                                   // tick #1 rendered with NO gate field
    console.log("G0ABSENT " + (gateCard() ? 0 : 1));
    global.__gate = { inflight: 1, queued: 2, limit: 1, waited_total: 1500, beat_total: 3 };
    await global.__tick();                            // tick #2: gate queued=2 -> state card, NO standalone card
    const shown = gateCard();
    const label = (els["state-label"] && els["state-label"].textContent) || "";
    console.log("G2STATE " + (shown ? 1 : 0) + " LABEL " + JSON.stringify(label));
    global.__gate = { inflight: 1, queued: 0, limit: 1, waited_total: 1500, beat_total: 3 };
    await global.__tick();                            // tick #3: queued back to 0 -> label back to idle
    const label3 = (els["state-label"] && els["state-label"].textContent) || "";
    console.log("G0PRUNED " + (gateCard() ? 0 : 1) + " LABEL3 " + JSON.stringify(label3));
    global.__gate = { inflight: 3, queued: 2, limit: 7, waited_total: 1500, beat_total: 3 };
    await global.__tick();                            // tick #4: fixed one-row gate line, no /slots yet
    const g4 = (els["state-gate"] && els["state-gate"].textContent) || "";
    console.log("G3MN " + JSON.stringify(g4));
    global.__slots = [
      {id:0, is_processing:true, state:"decoding"}, {id:1, is_processing:true, state:"prefill"},
      {id:2, is_processing:true, state:"decoding"}, {id:3, is_processing:false, state:"idle"},
      {id:4, is_processing:false, state:"idle"}, {id:5, is_processing:false, state:"idle"},
      {id:6, is_processing:false, state:"idle"}];
    await global.__tick();                            // tick #5: basalt-shape /slots -> per-state counts
    const g5 = (els["state-gate"] && els["state-gate"].textContent) || "";
    console.log("G4SLOTS " + JSON.stringify(g5));
    global.__slots = [{id:0, is_processing:true}, {id:1, is_processing:false}];
    await global.__tick();                            // tick #6: Strata-shape /slots -> 运行 n
    const g6 = (els["state-gate"] && els["state-gate"].textContent) || "";
    console.log("G5STRATA " + JSON.stringify(g6));
    console.log("GATE SMOKE DONE");
    process.exit(0);
  })().catch((e) => { console.error("GATE SMOKE FAIL:", (e && e.stack) || e); process.exit(1); });
} catch (e) {
  console.error("GATE SMOKE FAIL:", (e && e.stack) || e);
  process.exit(1);
}
"""
        with _tf.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as _t:
            _t.write(_GATE_SMOKE)
            _gp = _t.name
        try:
            _gr = _sp.run([_node, _gp, os.path.join(HERE, "monitor.js")],
                          capture_output=True, text=True, timeout=30)
            _out = _gr.stdout or ""
            _g0 = "G0ABSENT 1" in _out
            _line2 = ""
            for _ln in _out.splitlines():
                if _ln.startswith("G2STATE"):
                    _line2 = _ln
            _nocard = "G2STATE 0" in _out
            _gw = "网关队列" in _line2 and "2" in _line2
            _gp0 = "G0PRUNED 1" in _out
            rec("gate queue: standalone card retired, state card carries it", _g0 and _nocard and _gw and _gp0,
                "absent-hidden=%s no-card-on-queued=%s state-label-carries=%s pruned=%s (%s)"
                % (_g0, _nocard, _gw, _gp0, (_gr.stderr or _out or "").strip()[-120:]))
            rec("gate queue label source-worded", _gw,
                "line=%r" % (_line2[:120],))
            # 2026-11-19 human call: state card shows concurrency m/n (inflight/
            # limit, gateway-side counters) in EVERY state, and per-source queue
            # counts (闸排队 vs 引擎排队) whenever either is non-zero.
            _l4 = _d4 = ""
            for _ln in _out.splitlines():
                if _ln.startswith("G3MN"):
                    _l4 = _ln[5:]
            _mn = "最大并发 7" in _l4 and "闸排队 2" in _l4 and "引擎排队 0" in _l4
            _g5 = ""
            for _ln in _out.splitlines():
                if _ln.startswith("G4SLOTS"):
                    _g5 = _ln[9:]
            _sl = "读取 1 · 生成 2" in _g5 and "闸排队 2" in _g5 and "引擎排队 0" in _g5
            _g6 = ""
            for _ln in _out.splitlines():
                if _ln.startswith("G5STRATA"):
                    _g6 = _ln[10:]
            _st = "运行 1" in _g6
            rec("gate row: limit + per-state running + both queue counts, one line", _mn and _sl and _st,
                "no-slots=%r basalt=%r strata=%r" % (_l4[:120], _g5[:120], _g6[:120]))
        finally:
            try:
                os.unlink(_gp)
            except OSError:
                pass
    else:
        rec("gate-card behaviour smoke skipped (node not installed)", True)

    rec("unknown path falls through to upstream", m.answer("/v1/models") is None)
    rec('"/" is NOT claimed (console belongs to upstream)', m.answer("/") is None)

    # ---- 8. integration: minimal server on temporary port 19091 with fake data ----
    class MiniHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def do_GET(self):
            got = m.answer(self.path.split("?", 1)[0])
            if got is None:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            body, ctype = got
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    # Feed fake data directly; do NOT start the sampler thread (no real GPU calls).
    fake_gpus = m.parse_gpu_csv(CSV_T0)
    for g in fake_gpus:  # what the sampler pairs in on the GPU tick
        g["pcie_rx_mb"] = 1168.0 if g["index"] == 0 else 0.0
        g["pcie_tx_mb"] = 1.0 if g["index"] == 0 else 0.0
    m.SAMPLER.data = {"ok": True, "ts": time.time(), "gpus": fake_gpus,
                      "pcie_txrx_supported": True,
                      "ram": {"used": 8 * 1024 ** 3, "total": 32 * 1024 ** 3},
                      "disks": [{"number": 0, "read_mb": 1.0, "write_mb": 2.0,
                                 "model": "TestDisk", "bus": "NVMe SSD", "size": 10 ** 12,
                                 "drives": "c"}],
                      "net": [{"name": "Ethernet", "kind": "wired", "connected": True,
                               "down_mb": 10.0, "up_mb": 1.0}]}
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), MiniHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    for _ in range(60):
        try:
            s = socket.create_connection(("127.0.0.1", PORT), timeout=0.4)
            s.close()
            break
        except OSError:
            time.sleep(0.1)

    def get(path):
        c = http.client.HTTPConnection("127.0.0.1", PORT, timeout=10)
        c.request("GET", path)
        r = c.getresponse()
        data = r.read()
        c.close()
        return r, data

    r, body = get("/ext.json")
    snap = json.loads(body)
    rec("/ext.json over HTTP: 2 fake GPUs with uuid + 18-field extras",
        r.status == 200 and len(snap.get("gpus", [])) == 2
        and all("uuid" in g and "mem_util" in g and "enc_util" in g and "dec_util" in g
                and "pcie_gen" in g and "pcie_width" in g
                and "pcie_gen_max" in g and "pcie_width_max" in g
                for g in snap["gpus"]))
    r, body = get("/monitor")
    rec("/monitor over HTTP: page has the fused layout blocks (metrics grid, state, ctx, table, cc)",
        r.status == 200
        and all(x in body for x in (b'id="metrics"', b'id="state-badges"', b'id="ctx-fill"',
                                    b'id="req-body"', b'id="cc-card"')))
    r, body = get("/monitor.js")
    rec("/monitor.js over HTTP: served with javascript content-type",
        r.status == 200 and "javascript" in (r.getheader("Content-Type") or ""))
    r, body = get("/monitor.css")
    rec("/monitor.css over HTTP: text/css content-type",
        r.status == 200 and "text/css" in (r.getheader("Content-Type") or ""))
    r, body = get("/monitor-sprite.svg")
    rec("/monitor-sprite.svg over HTTP: svg content-type + non-empty body",
        r.status == 200 and "svg" in (r.getheader("Content-Type") or "") and len(body) > 1000)
    r, body = get("/health")
    rec("/health over HTTP ok", r.status == 200 and json.loads(body).get("ok") is True)
    r, _ = get("/v1/models")
    rec("fall-through returns 404 in the mini server (route not claimed)", r.status == 404)

    # swap indices in the live snapshot, uuids stay: consumer (page) keys by uuid
    for g in m.SAMPLER.data["gpus"]:
        g["index"] = 1 - g["index"]
    r, body = get("/ext.json")
    snap2 = json.loads(body)
    uuids2 = sorted(g["uuid"] for g in snap2["gpus"])
    rec("live snapshot index swap: uuid list unchanged",
        uuids2 == sorted(g["uuid"] for g in fake_gpus))

    srv.shutdown()

    bad = [n for n, ok, _ in RESULTS if not ok]
    print("\n%d/%d PASS" % (len(RESULTS) - len(bad), len(RESULTS)))
    if bad:
        print("FAILED:", ", ".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
