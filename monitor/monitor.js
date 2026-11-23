/* Token 账本工具 · 自持监控页脚本（/monitor 专用）——官方融合视图完整复刻
 *
 * 完全自持：只依赖本页面自带的 DOM（monitor.html）、本包自有样式
 * （/monitor.css）与图标（/monitor-sprite.svg）。不加载官方页面任何资源，
 * 不依赖官方 DOM / sprite / CSS，零第三方库。
 *
 * 数据两源，各自独立容错（任何一路挂了不影响另一路渲染）：
 *   /ext.json —— 本反代自己的硬件采样（每 GPU/RAM/硬盘/网卡），秒回；
 *   /metrics  —— 反代原样转发引擎的官方指标（live/hardware/history/
 *                requests/totals/conversation_cache/engine），带 Bearer key。
 * 引擎 key 沿用官方页 localStorage 键 "strata.apikey"（官方 app.js 口径，
 * JSON 字符串），团队在官方页配过 key 后本页面免填；401/403 或缺 key 时
 * 页面顶部出现输入框，保存回同一个键。
 *
 * 关键契约（2026-11-16 重构起因，不得回归）：显卡卡片与波形历史一律按 GPU
 * 的 uuid 绑定；nvidia-smi 槽位号 index 会漂，只显示、绝不做身份键。
 *
 * 卡片增删纪律：网格里的每张卡都带 data-mx-section（gpu/disk/net/cpu）；
 * 每个区只清理自己区的卡，绝不跨区误删。固定卡（speed/ram）常驻。
 */
(() => {
  "use strict";
  if (window.__strataLedgerMonitor) return;
  window.__strataLedgerMonitor = true;

  const HISTORY = 180;                 // 1s tick -> 3 minutes of waveform
  const TICK_MS = 1000;
  const SPRITE = "/monitor-sprite.svg";
  const GIB = 1024 ** 3;
  const hist = { ram: [], gpus: {}, disks: {}, diskW: {}, net: {}, netUp: {}, speed: [], prefill: [], cpu: [],
    pcie: {} };

  const $ = (id) => document.getElementById(id);
  const icon = (name, cls = "st-icon") =>
    `<svg class="${cls}" aria-hidden="true"><use href="${SPRITE}#i-${name}"/></svg>`;
  const esc = (s) => String(s).replace(/[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  // 图例短线：走 CSS 类随主题取色（速度卡两线用），带内联色的用 sw()
  const swc = (cls) => `<i class="mx-sw ${cls}"></i>`;
  const fmt = (n, d = 0) => (n == null || Number.isNaN(n) ? "\u2013"
    : Number(n).toLocaleString(undefined, { maximumFractionDigits: d, minimumFractionDigits: d }));
  const kfmt = (n) => (n == null ? "\u2013" : n >= 1000 ? `${fmt(n / 1000, n >= 10000 ? 0 : 1)}k` : fmt(n));
  const ctxfmt = (n) => (n && n % 1024 === 0 ? `${fmt(n / 1024)}K` : kfmt(n));
  const gb = (b, d = 1) => (b == null ? "\u2013" : fmt(b / GIB, d));
  function rateParts(mb) {
    if (mb == null) return ["\u2013", ""];
    if (mb >= 1024) return [(mb / 1024).toFixed(2), "GB/s"];
    return [mb < 10 ? mb.toFixed(1) : String(Math.round(mb)), "MB/s"];
  }
  function gibText(bytes) {
    if (!bytes) return "";
    const gib = bytes / GIB;
    return gib >= 1024 ? (gib / 1024).toFixed(1) + " TB" : Math.round(gib) + " GB";
  }
  function push(arr, v) {
    arr.push(v == null ? 0 : v);
    if (arr.length > HISTORY) arr.shift();
    return arr;
  }
  function since(t) {
    if (!t) return "";
    const s = Math.max(0, Date.now() / 1000 - t);
    return s < 60 ? "刚刚" : s < 3600 ? `${fmt(s / 60)} 分钟前` : `${fmt(s / 3600, 1)} 小时前`;
  }

  // ---------- theme（系统深浅色起步；手动切换存官方页同一个键 strata.theme） ----------
  function themeSet(t, save) {
    document.documentElement.dataset.theme = t;
    const u = $("theme-icon");
    if (u) u.setAttribute("href", `${SPRITE}#i-${t === "dark" ? "sun" : "moon"}`);
    if (save) { try { localStorage.setItem("strata.theme", JSON.stringify(t)); } catch (e) { /* ignore */ } }
  }
  function themeInit() {
    let saved = null;
    try { saved = JSON.parse(localStorage.getItem("strata.theme")); } catch (e) { /* ignore */ }
    if (saved === "dark" || saved === "light") return themeSet(saved, false);
    return themeSet(matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light", false);
  }
  themeInit();
  const themeBtn = $("theme-btn");
  if (themeBtn) themeBtn.onclick = () =>
    themeSet(document.documentElement.dataset.theme === "dark" ? "light" : "dark", true);

  // ---------- API key（与官方页同一个 localStorage 键：strata.apikey） ----------
  let apiKey = "";
  try { const v = localStorage.getItem("strata.apikey"); apiKey = v === null ? "" : JSON.parse(v); } catch (e) { apiKey = ""; }
  let metricsNeedKey = false;
  function keyUi(show, note) {
    const row = $("apikey-row");
    if (!row) return;
    row.hidden = !show;
    if (show) {
      const inp = $("api-key");
      if (inp && document.activeElement !== inp) inp.value = apiKey;
      const n = $("apikey-note");
      if (n) n.textContent = note || "";
    }
  }
  const keyInput = $("api-key");
  if (keyInput) {
    const saveKey = () => {
      apiKey = keyInput.value.trim();
      try { localStorage.setItem("strata.apikey", JSON.stringify(apiKey)); } catch (e) { /* 内存内可用 */ }
    };
    keyInput.oninput = saveKey;
    keyInput.onchange = () => {
      saveKey();
      keyUi(true, apiKey ? "已保存，只存在这台浏览器里" : "留空则读不到引擎指标（硬件卡不受影响）");
    };
  }

  // ---------- metric card skeleton（官方 st-metric 结构逐字复刻） ----------
  function cardHtml(id, section, labelHtml, opts) {
    const o = opts || {};
    const speed = o.speed
      ? `<div class="speed-values">
           <div><span class="st-metric__value" id="${id}-v">\u2013</span><span class="st-metric__sub" id="${id}-s">解码</span></div>
           <div class="speed-prefill"><span class="st-metric__value" id="${id}-pv">\u2013</span><span class="st-metric__sub" id="${id}-ps">预填充</span></div>
         </div>`
      : `<span class="st-metric__value" id="${id}-v">\u2013</span><span class="st-metric__sub" id="${id}-s"></span>`;
    const legend = o.legend ? `<div class="mx-legend" id="${id}-lg"></div>` : "";
    return `<div class="st-card metric-card" id="${id}" data-mx-section="${section}"><div class="st-metric">` +
      `<span class="st-metric__label">${icon(o.icon || "activity", "st-icon st-icon--sm")}<span class="mx-label-t">${labelHtml}</span></span>` +
      speed + legend +
      `<svg class="st-metric__spark" id="${id}-sp" viewBox="0 0 100 32" preserveAspectRatio="none"` +
      (o.tone ? ` data-tone="${o.tone}"` : "") + `>` +
      `<path class="area" fill="currentColor" opacity=".12"/><path class="line" fill="none" stroke="currentColor"` +
      ` stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/>` +
      (o.speed ? `<g id="${id}-sp2" class="speed-prefill"><path class="area" fill="currentColor" opacity=".12"/>` +
        `<path class="line" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"` +
        ` stroke-linecap="round" vector-effect="non-scaling-stroke"/></g>` : "") +
      `</svg></div></div>`;
  }

  // Stable ids get hashed into CSS-safe DOM ids; history lives under the stable id.
  function domId(prefix, stableId) {
    let h = 0;
    for (let i = 0; i < stableId.length; i++) h = (h * 31 + stableId.charCodeAt(i)) >>> 0;
    return prefix + "-" + h.toString(36);
  }

  function sparkPaths(values, max) {
    const v = values.slice(-HISTORY);
    if (v.length < 2) return null;
    const top = Math.max(max || 0, ...v, 1);
    const pts = v.map((x, i) => [(i / (v.length - 1)) * 100, 30 - (x / top) * 26]);
    const d = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(2) + "," + p[1].toFixed(2)).join("");
    return { line: d, area: d + "L100,32L0,32Z" };
  }
  function drawSpark(el, values, max) {
    if (!el) return;
    const line = el.querySelector(".line");
    const area = el.querySelector(".area");
    if (!line || !area) return;
    const p = sparkPaths(values, max);
    if (!p) { line.setAttribute("d", ""); area.setAttribute("d", ""); return; }
    line.setAttribute("d", p.line);
    area.setAttribute("d", p.area);
  }

  // Multi-series sparkline for the PCIe card: one coloured line per GPU.
  // The fixed palette is readable on both themes (mid-saturation hues).
  const SERIES_COLORS = ["#10b981", "#f59e0b", "#3b82f6", "#e0283f", "#8b5cf6", "#06b6d4"];
  function drawMultiSpark(el, series, built) {
    if (!el) return;
    if (!built) {
      // rebuild inner paths (series count changes when cards appear/disappear)
      let svg = `<path class="area" fill="currentColor" opacity=".08"/>`;
      series.forEach((s, i) => {
        svg += `<path class="mline" data-i="${i}" fill="none" stroke="${s.color}" stroke-width="1.6"` +
          ` stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/>`;
      });
      el.innerHTML = svg;
    }
    const area = el.querySelector(".area");
    const lines = el.querySelectorAll(".mline");
    const allMax = Math.max(1, ...series.flatMap((s) => s.values.slice(-HISTORY)));
    series.forEach((s, i) => {
      const p = sparkPaths(s.values, allMax);
      const ln = lines[i];
      if (ln) ln.setAttribute("d", p ? p.line : "");
      if (i === 0 && area) area.setAttribute("d", "");
    });
  }

  // Cards persist across ticks. Sections own their cards via data-mx-section;
  // ensure() adds one, pruneSection() removes only THIS section's stale cards.
  function ensure(host, id, html) {
    let el = document.getElementById(id);
    if (!el) {
      host.insertAdjacentHTML("beforeend", html);
      el = document.getElementById(id);
    }
    return el;
  }
  function pruneSection(host, section, seen) {
    for (const el of Array.from(host.children)) {
      if (el.dataset && el.dataset.mxSection === section && !seen.has(el.id)) el.remove();
    }
  }
  function setSub(id, text) {
    const el = $(id);
    if (el) el.textContent = text;
  }
  function noteOnce(host, noteId, html) {
    if (!$(noteId)) host.insertAdjacentHTML("beforeend", html);
  }

  // ================= model state card（/metrics live，口径照官方 renderMonitor） =================
  function renderState(m, gate, slots) {
    const live = (m && m.live) || {};
    const requests = (m && m.requests) || [];
    const last = requests[0];
    // 两条队列语义不同：engine queued（/metrics live）＝引擎侧排队的请求；
    // gate queued（/ext.json gate 段）＝被网关闸扣在队列里的入栈请求。
    // 排队徽标两队列任一 >0 就亮并带数字；标签行按来源区分口径。
    const engQ = live.queued || 0;
    const gwQ = (gate && gate.queued) || 0;
    const qTotal = engQ + gwQ;
    const on = qTotal > 0 ? "queued" : (live.state || "idle");
    for (const b of document.querySelectorAll("#state-badges .st-badge")) {
      b.classList.toggle("on", b.dataset.s === on || b.dataset.s === live.state);
      if (b.dataset.s === "queued") b.textContent = qTotal > 0 ? `排队 ${fmt(qTotal)}` : "排队";
    }
    const prog = $("state-progress");
    let label = "等待请求", detail = "", pct = 0;
    if (live.state === "reading") {
      label = "读取输入";
      prog.dataset.tone = "info";
      if (live.prompt_total) {
        pct = (100 * live.prompt_read) / live.prompt_total;
        detail = `${fmt(live.prompt_read)} / ${fmt(live.prompt_total)} tokens · ${fmt(pct)}%`;
      } else detail = `${fmt(live.prompt_tokens)} tokens`;
    } else if (live.state === "generating") {
      label = "生成中";
      delete prog.dataset.tone;
      // 进度两口径（2026-11-19 rev13）：引擎报了 max_tokens → 完成度（Strata 路）；
      // 没报（basalt live.max_tokens=None 实测在案）→ 绿条退为速度表：
      // 基线 227 tok/s ＝ 本机 basalt 单流满载实测锚点 226.9（压测报告
      // N=1 在册，2026-11-19），条长＝当前 tok_s/基线，随每秒刷新实时动。
      if (live.max_tokens) {
        pct = Math.min(100, (100 * live.generated) / live.max_tokens);
      } else if (live.tok_s != null) {
        pct = Math.min(100, (100 * live.tok_s) / 227);
      }
      detail = `${fmt(live.generated)} tokens · ${fmt(live.tok_s, 1)} tok/s`;
    } else if (live.state === "unloaded") {
      label = "未加载";
      delete prog.dataset.tone;
      detail = "加载会把它拉回来，发条消息也会。";
    } else {
      delete prog.dataset.tone;
      if (last) detail = `上一次：${fmt(last.output_tokens)} tokens${last.decode_tok_s ? ` · ${fmt(last.decode_tok_s, 1)} tok/s` : ""}`;
      if (gwQ > 0 && engQ > 0) label = `排队 ${fmt(qTotal)}（网关 ${fmt(gwQ)} · 引擎 ${fmt(engQ)}）`;
      else if (gwQ > 0) label = `网关队列 ${fmt(gwQ)} 个在等闸`;
      else if (engQ > 0) label = `引擎队列 ${fmt(engQ)} 个在排队`;
    }
    // 闸态固定行＝一行左侧常驻（2026-11-19 human call）：最大允许并发、
    // 各状态实际进程数（按 /slots 逐槽聚合）、闸排队、引擎排队。
    // basalt 每槽有 state（idle/prefill/decoding）；Strata 每槽只有
    // is_processing（bool）→ 退为"运行 n"不拆态。数据源 /slots 经网关透传。
    const gateEl = $("state-gate");
    if (gateEl) {
      const lim = gate ? fmt(gate.limit) : "—";
      let busySeg = "在跑 —";
      if (Array.isArray(slots) && slots.length) {
        const hasState = slots.some((s) => typeof s.state === "string");
        if (hasState) {
          const pre = slots.filter((s) => s.state === "prefill").length;
          const dec = slots.filter((s) => s.state === "decoding").length;
          busySeg = `读取 ${fmt(pre)} · 生成 ${fmt(dec)}`;
        } else {
          busySeg = `运行 ${fmt(slots.filter((s) => s.is_processing).length)}`;
        }
      } else if (m && m.live && m.live.state) {
        // /slots 不可得时退聚合口径：live 汇总（单跑语义，不谎报多槽）
        const st = m.live.state;
        busySeg = (st === "reading" || st === "generating") ? "运行 1" : "运行 0";
      }
      gateEl.textContent = `最大并发 ${lim} · ${busySeg} · 闸排队 ${gate ? fmt(gwQ) : "—"} · 引擎排队 ${fmt(engQ)}`;
    }
    $("state-label").textContent = label;
    $("state-detail").textContent = detail;
    $("state-bar").style.width = `${pct}%`;
  }

  // ================= Speed card（/metrics；固定卡，常驻） =================
  function renderSpeed(m) {
    const host = $("metrics");
    if (!host) return;
    const live = (m && m.live) || {}, totals = (m && m.totals) || null;
    const requests = (m && m.requests) || [];
    const last = requests[0];
    const id = "card-speed";
    ensure(host, id, cardHtml(id, "fixed", "速度", { icon: "gauge", speed: true }));
    const avgDecode = totals && totals.decode_ms > 0 && totals.output_tokens > 0
      ? totals.output_tokens / (totals.decode_ms / 1000) : null;
    const readTokens = totals ? (totals.prompt_tokens || 0) - (totals.reused || 0) : 0;
    const avgPrefill = totals && totals.prompt_ms > 0 && readTokens > 0
      ? readTokens / (totals.prompt_ms / 1000) : null;
    const speed = live.state === "generating" ? live.tok_s
      : avgDecode != null ? avgDecode : last ? last.decode_tok_s : null;
    const prefill = live.state !== "idle" ? live.prefill_tok_s_mean
      : avgPrefill != null ? avgPrefill
      : last && last.prompt_ms > 0 ? Math.max(0, (last.prompt_tokens || 0) - (last.reused || 0)) / (last.prompt_ms / 1000) : null;
    const v = $(id + "-v");
    if (v) v.innerHTML = speed == null ? "\u2013" : `${fmt(speed, 1)}<small>t/s</small>`;
    // 波形两线颜色：主线=accent，预填充线=accent 混黑 65%（见 .speed-prefill）——图例走 CSS 类，随主题取色
    const subD = $(id + "-s");
    if (subD) subD.innerHTML = swc("mx-sw--decode") + (live.state === "generating" ? "解码 · 当前" : avgDecode != null ? "解码 · 本次运行均值" : last ? "解码 · 上一次请求" : "解码");
    const pv = $(id + "-pv");
    if (pv) pv.innerHTML = prefill == null ? "\u2013" : `${fmt(prefill)}<small>t/s</small>`;
    const subP = $(id + "-ps");
    if (subP) subP.innerHTML = swc("mx-sw--prefill") + (live.state === "reading" ? "预填充 · 当前" : live.state === "generating" ? "预填充 · 本次请求" : avgPrefill != null ? "预填充 · 本次运行均值" : last ? "预填充 · 上一次请求" : "预填充");
    // 波形优先用引擎侧 history（与官方页同源同曲线），没有就本地攒
    const h = (m && m.history) || {};
    const sp = $(id + "-sp");
    if (sp) {
      const speedSeries = Array.isArray(h.tok_s) && h.tok_s.length ? h.tok_s : push(hist.speed, speed);
      drawSpark(sp, speedSeries);
      const g2 = $(id + "-sp2");
      if (g2) drawSpark(g2, Array.isArray(h.prefill_tok_s_mean) && h.prefill_tok_s_mean.length ? h.prefill_tok_s_mean : push(hist.prefill, prefill));
    }
  }

  // CPU 卡：/metrics hardware.cpu 有就画、没有就移除（ext.json 采不到 CPU）。
  // 多插槽 CPU（hardware.cpu_sockets 为 >1 的数组时）：同一张卡、版式同速度卡——
  // 左右各一组贴边读数（左=第一插槽，右=末插槽），波形两线一插槽一条，不开第二张卡。
  function renderCpu(m, ext) {
    const host = $("metrics");
    if (!host) return;
    const hw = (m && m.hardware) || {};
    const st = (m && m.hardware_static) || {};
    const seen = new Set();
    const socks = Array.isArray(hw.cpu_sockets) && hw.cpu_sockets.length > 1 ? hw.cpu_sockets : null;
    // 标题 = CPU · 型号（/ext.json cpu_name，静态读一次；采不到就保持光 "CPU"，不编名字）。
    // ensure 只在卡片首建时写标题，ext.json 可能晚于 /metrics 到——label 节点每拍幂等刷新。
    const cpuLabel = "CPU" + (ext && ext.cpu_name ? ` · ${esc(ext.cpu_name)}` : "");
    const setCpuTitle = (el) => {
      const lt = el && el.querySelector ? el.querySelector(".mx-label-t") : null;
      if (lt && lt.innerHTML !== cpuLabel) lt.innerHTML = cpuLabel;
    };
    if (socks) {
      const id = "card-cpu";
      seen.add(id);
      setCpuTitle(ensure(host, id, cardHtml(id, "cpu", cpuLabel, { icon: "cpu", tone: "info", speed: true })));
      const n = socks.length - 1;
      const v1 = $(id + "-v"), v2 = $(id + "-pv");
      if (v1) v1.innerHTML = `${fmt(socks[0])}<small>%</small>`;
      if (v2) v2.innerHTML = `${fmt(socks[n])}<small>%</small>`;
      const sstats = Array.isArray(st.cpu_socket_stats) ? st.cpu_socket_stats : [];
      const subOf = (i) => {
        const s = sstats[i] || {};
        return `CPU ${i + 1}` + (s.cores ? ` · ${s.cores} 核${s.threads ? " / " + s.threads + " 线程" : ""}` : "");
      };
      // 图例短线与左右两条波形同色：左线=accent 主色，右线=accent 加深（.speed-prefill）
      const sd1 = $(id + "-s"), sd2 = $(id + "-ps");
      if (sd1) sd1.innerHTML = swc("mx-sw--cpu1") + subOf(0);
      if (sd2) sd2.innerHTML = swc("mx-sw--cpu2") + subOf(n) + (socks.length > 2 ? ` （共 ${socks.length} 插槽，显示首末）` : "");
      // 波形：历史按插槽分桶（引擎 history 若给 cpu_sockets 数组的数组则优先）
      const h = (m && m.history) || {};
      const hs = Array.isArray(h.cpu_sockets) ? h.cpu_sockets : null;
      if (!hist.cpuSock) hist.cpuSock = {};
      const sp = $(id + "-sp");
      if (sp) {
        drawSpark(sp, hs && hs[0] && hs[0].length ? hs[0] : push(hist.cpuSock[0] || (hist.cpuSock[0] = []), socks[0]), 100);
        const g2 = $(id + "-sp2");
        if (g2) drawSpark(g2, hs && hs[n] && hs[n].length ? hs[n] : push(hist.cpuSock[n] || (hist.cpuSock[n] = []), socks[n]), 100);
      }
    } else if (hw.cpu != null) {
      const id = "card-cpu";
      seen.add(id);
      setCpuTitle(ensure(host, id, cardHtml(id, "cpu", cpuLabel, { icon: "cpu", tone: "info" })));
      const v = $(id + "-v");
      // 大数字后跟实时主频（/ext.json cpu_mhz＝PDH % Processor Performance × 基准频率，
      // 与任务管理器"速度"同源；注册表 ~MHz 在 Win11 钉死基准，已废，2026-11-17）
      if (v) {
        const mhz = ext && ext.cpu_mhz;
        v.innerHTML = `${fmt(hw.cpu)}<small>%</small>` +
          (mhz ? ` <small>${fmt(mhz / 1000, 2)}<small> GHz</small></small>` : "");
      }
      // 单插槽也要图例：短线=波形主色，后跟规格文字
      const sub1 = $(id + "-s");
      if (sub1) sub1.innerHTML = swc("mx-sw--cpu1") + (st.threads ? `${st.cores ? st.cores + " 核 · " : ""}${st.threads} 线程` : "整机");
      const h = (m && m.history) || {};
      const sp = $(id + "-sp");
      if (sp) drawSpark(sp, Array.isArray(h.cpu) && h.cpu.length ? h.cpu : push(hist.cpu, hw.cpu), 100);
    }
    pruneSection(host, "cpu", seen);
  }

  // ================= PCIe 卡：每卡一条实时线路波形（11-16 四稿修订） =================
  // 数据主源 /ext.json：每卡 pcie_rx_mb/pcie_tx_mb（nvidia-smi dmon -s t，
  // 与 gpu_sample 同 tick 按枚举序配对 uuid）；链路 Gen/宽度进图例，
  // 纯文字、不告警——本机 ×8 是稳态正常值（7950X 平台双卡各 8 lane）。
  // 引擎 /metrics 的 gpu_pcie_rx_mb 只描述引擎所用那张卡，作为额外的
  // 「引擎侧实测」一条并入同一张图，与每卡线互补。
  function renderPcie(ext, m) {
    const host = $("metrics");
    if (!host) return;
    const hw = (m && m.hardware) || {};
    const id = "card-pcie";
    ensure(host, id, cardHtml(id, "fixed", "PCIe 线路", { icon: "link", tone: "info" }));
    const gpus = (ext && ext.gpus) || [];
    const supported = ext ? ext.pcie_txrx_supported : null;

    // 历史仍按 uuid 每卡分桶（身份契约不变），但图上只画“当前读速最快”的那一条。
    gpus.forEach((g) => {
      const uid = g.uuid || "name:" + (g.name || "gpu" + g.index);
      push(hist.pcie[uid] || (hist.pcie[uid] = []), g.pcie_rx_mb);
    });
    const seen = new Set(gpus.map((g) => g.uuid || "name:" + (g.name || "gpu" + g.index)));
    for (const uid of Object.keys(hist.pcie)) {
      if (!seen.has(uid)) delete hist.pcie[uid];
    }

    // 领先者 = 本轮读速最大的卡（并列取序前）
    let lead = null;
    for (const g of gpus) {
      const rx = g.pcie_rx_mb || 0;
      if (!lead || rx > (lead.pcie_rx_mb || 0)) lead = g;
    }
    const leadUid = lead ? (lead.uuid || "name:" + (lead.name || "gpu" + lead.index)) : null;
    const leadColor = lead ? SERIES_COLORS[Math.max(0, gpus.indexOf(lead)) % SERIES_COLORS.length]
      : SERIES_COLORS[0];

    const v = $(id + "-v");
    if (v) {
      const rx = lead ? (lead.pcie_rx_mb || 0) : 0;
      // 大数字后跟该领先线路的实际链路：Gen几 ×几（nvidia-smi 每卡上报，
      // 实测链路而非额定上限；上限在图例小字里对照）
      const link = lead && lead.pcie_gen != null && lead.pcie_width != null
        ? ` <small>Gen${parseInt(lead.pcie_gen, 10)} ×${parseInt(lead.pcie_width, 10)}</small>` : "";
      v.innerHTML = supported === false || !lead ? "\u2013"
        : `${fmt(rx, rx < 10 ? 1 : 0)}<small> MB/s</small>` + link;
    }
    // 小字固定两行：第一行=固定文案"当前最高读速"；第二行=图例色块+显卡名。
    // 大数字本身就是该领先线路的即时速度，不再重复写数值/卡名。
    const sub = $(id + "-s");
    if (sub) {
      if (supported === false) sub.textContent = "这台机器的 nvidia-smi 不支持每卡 PCIe 吞吐采样（dmon -s t 无输出）";
      else if (!lead) sub.textContent = "暂无显卡数据";
      else sub.innerHTML = `当前最高读速<br>${sw(leadColor)}${esc(String(lead.name || "").replace(/^NVIDIA\s+/i, ""))}`;
    }

    // 单曲线：领先卡的历史波形（卡切换时曲线换色，历史仍各归各卡）
    const sp = $(id + "-sp");
    const series = leadUid ? [{ uid: leadUid, color: leadColor, values: hist.pcie[leadUid] || [] }] : [];
    const built = !!sp && sp.querySelectorAll(".mline").length === series.length;
    if (sp) sp.style.color = series.length ? series[0].color : "";
    drawMultiSpark(sp, series, built);
    if (sp) { const ln = sp.querySelector(".mline"); if (ln) ln.setAttribute("stroke", leadColor); }

    // 图例区已并入小字第二行，卡片不再单独列图例
    const lg = $(id + "-lg");
    if (lg) lg.innerHTML = "";
  }
  // ================= GPU cards（/ext.json，按 uuid 绑定，index 仅展示） =================
  function renderGpus(data) {
    const host = $("metrics");
    if (!host) return;
    const gpus = data.gpus || [];
    const seen = new Set();
    for (const g of gpus) {
      const uid = g.uuid || "name:" + (g.name || "gpu" + g.index);
      const id = domId("gpu", uid);
      seen.add(id);
      const shortName = String(g.name || ("GPU " + g.index)).replace(/^NVIDIA\s+/i, "");
      // 序号在名称前（与磁盘卡 #N 同款）；编号从 1 起，槽位号会漂仅作对照、不作为身份
      const label = `<span class="muted" title="槽位号会漂，仅供对照，不作为身份">#${esc(g.index + 1)}</span> ${esc(shortName)}`;
      // 图标走 cardHtml 的 opts.icon（与其他卡同一路径）；label 里不再自带图标，
      // 否则骨架的默认图标 + 自带图标 = 双图标，视觉上显卡图标偏右
      ensure(host, id, cardHtml(id, "gpu", label, { icon: "gpu" }));
      // 大数字后缀：保留 % 单位，去掉 "SM"；运行模式沿用原徽章样式观感
      const v = $(id + "-v");
      if (v) v.innerHTML = `${fmt(g.util)}<small>%</small>` +
        (g.mode ? ` <span class="st-badge" style="height:20px">${esc(g.mode)}</span>` : "");
      const parts = [];
      if (g.mem_used_mib != null && g.mem_total_mib)
        parts.push(`${(g.mem_used_mib / 1024).toFixed(1)} / ${(g.mem_total_mib / 1024).toFixed(0)} GB 显存`);
      if (g.mem_util != null) parts.push("显存利用率 " + fmt(g.mem_util) + "%");
      if (g.enc_util != null) parts.push("编码 " + fmt(g.enc_util) + "%");
      if (g.dec_util != null) parts.push("解码 " + fmt(g.dec_util) + "%");
      if (g.temp != null) parts.push(fmt(g.temp) + "°C");
      if (g.power != null) parts.push(fmt(g.power) + (g.power_limit ? "/" + fmt(g.power_limit) : "") + " W");
      if (g.sm_clock != null) parts.push(fmt(g.sm_clock) + " MHz");
      // 每卡 PCIe 链路：中性信息（用户口径 11-16 四稿修订：本机 ×8 就是
      // 稳态正常值，不做任何告警标记）。空闲时链路自动降代显示 Gen1 也属正常。
      if (g.pcie_gen != null)
        parts.push(`PCIe Gen${g.pcie_gen} ×${fmt(g.pcie_width)}`);
      setSub(id + "-s", parts.join(" · "));
      drawSpark($(id + "-sp"), push(hist.gpus[uid] || (hist.gpus[uid] = []), g.util), 100);
    }
    pruneSection(host, "gpu", seen);
    // uuid 消失：一并清掉波形历史，重新插卡不串历史
    for (const uid of Object.keys(hist.gpus)) {
      if (!gpus.some((g) => (g.uuid || "name:" + (g.name || "gpu" + g.index)) === uid)) delete hist.gpus[uid];
    }
    if (!gpus.length) {
      noteOnce(host, "gpu-note", '<p class="muted" id="gpu-note" style="grid-column:1/-1">没有显卡数据（这台机器没有 nvidia-smi 或驱动未装；记账不受影响）</p>');
    } else if ($("gpu-note")) $("gpu-note").remove();
  }

  // ================= RAM card（/ext.json，含 swap；固定卡） =================
  function renderRam(data) {
    const host = $("metrics");
    if (!host) return;
    if (data.ram) {
      const id = "card-ram";
      ensure(host, id, cardHtml(id, "fixed", "系统内存", { icon: "memory" }));
      const v = $(id + "-v");
      if (v) v.innerHTML = `${(data.ram.used / GIB).toFixed(1)}<small>GB</small>`;
      const parts = ["共 " + (data.ram.total / GIB).toFixed(1) + " GB"];
      if (data.swap && data.swap.total)
        parts.push("交换 " + (data.swap.used / GIB).toFixed(1) + " / " + (data.swap.total / GIB).toFixed(1) + " GB");
      setSub(id + "-s", parts.join(" · "));
      drawSpark($(id + "-sp"), push(hist.ram, data.ram.used), data.ram.total);
      if ($("ram-note")) $("ram-note").remove();
    } else {
      const el = document.getElementById("card-ram");
      if (el) el.remove();
      noteOnce(host, "ram-note", '<p class="muted" id="ram-note" style="grid-column:1/-1">没有内存数据（这台机器的 Python 没装 psutil；记账不受影响）</p>');
    }
  }

  // ================= 网关排队闸：已并入顶部模型状态卡（2026-11-19 人类口径） =================
  // 独立「等待中」卡信息量过低，撤销。两条队列（网关闸 gate.queued / 引擎
  // live.queued）的计数与来源区分都在 renderState 的排队徽标＋标签行承载。
  // 旧版在岗页缓存里的 card-gate 残留由下面 prune 清除。
  function pruneStaleGateCard() {
    pruneSection($("metrics"), "gate", new Set());
  }

  // ================= 每物理硬盘卡（/ext.json；读=绿 写=橙，波形双色） =================
  const RW_DOWN = "#10b981";   // 读 / 下行
  const RW_UP = "#f59e0b";     // 写 / 上行
  const sw = (c) => `<i class="mx-sw" style="background:${c}"></i>`;
  function drawDualSpark(el, aVals, bVals, ca, cb) {
    const built = !!el && el.querySelectorAll(".mline").length === 2;
    drawMultiSpark(el, [
      { uid: "a", color: ca, values: aVals },
      { uid: "b", color: cb, values: bVals },
    ], built);
  }
  function renderDisks(data) {
    const host = $("metrics");
    if (!host) return;
    const disks = data.disks || [];
    const seen = new Set();
    for (const d of disks) {
      const id = domId("disk", "disk" + d.number);
      seen.add(id);
      // 标题行 = 编号 + 盘符 + 型号 + 容量（如 #1 C: HS-SSD-CC700 2048G · 1.9 TB）
      const head = [`#${d.number + 1}`];
      if (d.drives) head.push(String(d.drives).split(",").map((x) => x.trim().toUpperCase()).join(" "));
      if (d.model) head.push(d.model.length > 24 ? d.model.slice(0, 23) + "…" : d.model);
      const size = gibText(d.size);
      const title = head.join(" ") + (size ? " · " + size : "");
      ensure(host, id, cardHtml(id, "disk", esc(title), { icon: "disk", tone: "info" }));
      // 大数字后跟规格徽章（NVMe SSD 等），代码样式包装，同显卡运行模式徽章
      const spec = d.bus ? String(d.bus).replace(/^Disk\s*\d+\s*·\s*/, "") : "";
      const v = $(id + "-v");
      if (v) {
        const p = rateParts(d.read_mb);
        v.innerHTML = p[0] + `<small>${p[1]}</small>` +
          (spec ? ` <span class="st-badge" style="height:20px">${esc(spec)}</span>` : "");
      }
      // 读/写两行都放到大数字下面（各带短线图例）
      const sub = $(id + "-s");
      if (sub) sub.innerHTML = `${sw(RW_DOWN)}读 ${rateParts(d.read_mb).join(" ")}` +
        `<br>${sw(RW_UP)}写 ${rateParts(d.write_mb).join(" ")}`;
      const hr = hist.disks[d.number] || (hist.disks[d.number] = []);
      const hw_ = hist.diskW[d.number] || (hist.diskW[d.number] = []);
      drawDualSpark($(id + "-sp"), push(hr, d.read_mb), push(hw_, d.write_mb), RW_DOWN, RW_UP);
    }
    pruneSection(host, "disk", seen);
  }

  // ================= 每已连接网卡卡 + 底部合计行（/ext.json；下行=绿 上行=橙） =================
  function renderNet(data) {
    const host = $("metrics");
    if (!host) return;
    const adapters = (data.net || []).filter((a) => a.connected);
    const seen = new Set();
    for (const a of adapters) {
      const id = domId("net", a.name);
      seen.add(id);
      // 标题行：无线网卡就叫"无线网卡"；有线用适配器真名。规格徽章只保留"有线"，无线不出徽章
      const label = a.kind === "wifi" ? "无线网卡" : esc(a.name);
      ensure(host, id, cardHtml(id, "net", label, { icon: "link", tone: "info" }));
      const badge = a.kind === "wired" ? "有线" : "";
      const v = $(id + "-v");
      if (v) {
        const p = rateParts(a.down_mb);
        v.innerHTML = p[0] + `<small>${p[1]}</small>` +
          (badge ? ` <span class="st-badge" style="height:20px">${esc(badge)}</span>` : "");
      }
      // 下行/上行两行都放到大数字下面（各带短线图例）
      const subN = $(id + "-s");
      if (subN) subN.innerHTML = `${sw(RW_DOWN)}下行 ${a.down_mb != null ? rateParts(a.down_mb).join(" ") : "\u2013"}` +
        `<br>${sw(RW_UP)}上行 ${a.up_mb != null ? rateParts(a.up_mb).join(" ") : "\u2013"}`;
      const hd = hist.net[a.name] || (hist.net[a.name] = []);
      const hu = hist.netUp[a.name] || (hist.netUp[a.name] = []);
      drawDualSpark($(id + "-sp"), push(hd, a.down_mb), push(hu, a.up_mb), RW_DOWN, RW_UP);
    }
    pruneSection(host, "net", seen);
    // 「网卡合计」独立行撤销（2026-11-19 人类口径：独立低信息量块不留，
    // 每网卡卡已带下行/上行明细）；只在没有任何已连接网卡数据时留一条状态提示。
    const nx = $("mx-note");
    if (nx) nx.remove();
    if (!adapters.length) {
      host.insertAdjacentHTML("beforeend",
        '<div id="mx-note" data-mx-section="net" class="muted">网卡 · 没有已连接的网卡数据（psutil 缺失或都未连接）</div>');
    }
  }

  // ================= Context fill 环表 + 三条进度（/metrics 与 /ext.json 混用） =================
  function renderCtx(m, ext) {
    const eng = (m && m.engine) || {}, live = (m && m.live) || {};
    const requests = (m && m.requests) || [];
    const last = requests[0];
    const ctx = eng.max_context || 0;
    let used = 0;
    if (live.state && live.state !== "idle") used = (live.prompt_tokens || 0) + (live.generated || 0);
    else if (last) used = (last.prompt_tokens || 0) + (last.output_tokens || 0);
    const frac = ctx ? Math.min(1, used / ctx) : 0;
    const fill = $("ctx-fill");
    if (fill) {
      fill.setAttribute("stroke-dasharray", `${(235.6 * frac).toFixed(1)} 314.2`);
      fill.style.opacity = 235.6 * frac >= 3 ? "1" : "0";   // 近零弧线只剩圆头，隐藏
    }
    $("ctx-pct").textContent = `${Math.round(frac * 100)}%`;
    $("ctx-sub").textContent = ctx ? `${kfmt(used)} / ${ctxfmt(ctx)}` : "\u2013";
    // Experts in VRAM：引擎侧口径（官方同源）
    const hw = (m && m.hardware) || {};
    const cacheBytes = (eng.expert_cache_mib || 0) * 1048576;
    $("slots-text").textContent = eng.expert_slots ? `${fmt(eng.expert_slots)} · ${gb(cacheBytes)} GB` : "\u2013";
    $("slots-bar").style.width = hw.gpu_mem_total ? `${Math.min(100, (100 * cacheBytes) / hw.gpu_mem_total)}%` : "0%";
    // System RAM：优先 /ext.json（本反代秒级采样），退 /metrics
    const ram = ext && ext.ram ? ext.ram : (hw.ram_total ? { used: hw.ram_used, total: hw.ram_total } : null);
    $("ram-text").textContent = ram && ram.total ? `${gb(ram.used)} / ${gb(ram.total, 0)} GB` : "\u2013";
    const ramPct = ram && ram.total ? (100 * ram.used) / ram.total : 0;
    $("ram-bar").style.width = `${ramPct}%`;
    const ramProg = $("ram-progress");
    if (ramPct > 92) ramProg.dataset.tone = "danger"; else delete ramProg.dataset.tone;
    // GPU temperature：/ext.json 最热一张卡，退 /metrics
    let temp = hw.gpu_temp == null ? null : hw.gpu_temp;
    if (ext && Array.isArray(ext.gpus) && ext.gpus.length) {
      const ts = ext.gpus.map((g) => g.temp).filter((x) => x != null);
      if (ts.length) temp = Math.max(...ts);
    }
    $("temp-text").textContent = temp == null ? "\u2013" : `${fmt(temp)} °C`;
    $("temp-bar").style.width = temp == null ? "0%" : `${Math.min(100, temp)}%`;
  }

  // ================= Recent requests 表 + totals（/metrics，9 列照官方） =================
  let reqShowAll = false;
  function renderRequests(m) {
    const requests = (m && m.requests) || [];
    const kept = m && m.requests_kept != null ? m.requests_kept : requests.length;
    const body = $("req-body");
    if (!requests.length) {
      body.innerHTML = '<tr><td colspan="9" class="muted">还没有请求</td></tr>';
    } else {
      const badge = { stop: ["", "完成"], length: ["", "触顶"], cancel: ["st-badge--queued", "已停止"],
                      disconnect: ["st-badge--queued", "已断开"], error: ["st-badge--error", "错误"],
                      timeout: ["st-badge--queued", "超时"] };
      body.innerHTML = requests.slice(0, reqShowAll ? requests.length : 12).map((r) => {
        const [cls, text] = badge[r.finish] || ["", r.finish || "\u2013"];
        const t = new Date(r.time * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
        const hit = r.hit_rate == null ? "\u2013" : `${(r.hit_rate * 100).toFixed(1)}%` +
          (r.pcie_share ? ` <span class="muted" title="经 PCIe 读取或别的卡算的专家占比">+${(r.pcie_share * 100).toFixed(1)}% PCIe</span>` : "");
        const fresh = r.prompt_tokens == null ? null : Math.max(0, r.prompt_tokens - (r.reused || 0));
        const prefillRate = fresh > 0 && r.prompt_ms > 0 ? fresh / (r.prompt_ms / 1000) : null;
        return `<tr><td>${esc(t)}</td><td><span class="st-badge ${cls}">${esc(text)}</span></td>` +
          `<td class="num">${fmt(r.prompt_tokens)}</td><td class="num">${fmt(r.reused)}</td>` +
          `<td class="num">${fmt(r.output_tokens)}</td><td class="num">${fmt(prefillRate)}</td>` +
          `<td class="num">${fmt(r.decode_tok_s, 1)}</td><td class="num">${hit}</td>` +
          `<td class="num">${fmt(r.duration_s, 1)} s</td></tr>`;
      }).join("");
    }
    const all = $("req-all");
    if (all) {
      all.hidden = kept <= 12;
      all.textContent = reqShowAll ? "只看最近" : `全部（${kept}）`;
    }
    $("req-wrap").classList.toggle("all", reqShowAll);
    const t = m && m.totals;
    if (t && t.requests) {
      const sd = new Date(t.since * 1000);
      const sinceStr = `${sd.getFullYear()}-${String(sd.getMonth() + 1).padStart(2, "0")}-${String(sd.getDate()).padStart(2, "0")} ${String(sd.getHours()).padStart(2, "0")}:${String(sd.getMinutes()).padStart(2, "0")}`;
      const read = (t.prompt_tokens || 0) - (t.reused || 0);
      const pSpeed = t.prompt_ms > 0 && read > 0 ? ` · ${fmt(read / (t.prompt_ms / 1000))} t/s` : "";
      const oSpeed = t.decode_ms > 0 && t.output_tokens > 0 ? ` · ${fmt(t.output_tokens / (t.decode_ms / 1000), 1)} t/s` : "";
      $("req-totals").textContent = `自 ${sinceStr}：${fmt(t.requests)} 个请求 · 读取输入 ${fmt(read)} tokens${pSpeed}（复用 ${fmt(t.reused)}）· 输出 ${fmt(t.output_tokens)} tokens${oSpeed}`;
    } else $("req-totals").textContent = "";
  }
  const reqAllBtn = $("req-all");
  if (reqAllBtn) reqAllBtn.onclick = () => { reqShowAll = !reqShowAll; };

  // ================= Conversation cache（/metrics） =================
  function renderConvCache(c) {
    const card = $("cc-card");
    card.hidden = !c;
    if (!c) return;
    const pct = (a, b) => (b ? `${Math.min(100, (100 * a) / b)}%` : "0%");
    $("cc-bars").hidden = !c.enabled;
    if (c.enabled) {
      $("cc-slots-text").textContent = `${fmt(c.parked)} / ${fmt(c.slots)}`;
      $("cc-slots-bar").style.width = pct(c.parked, c.slots);
      const budget = (c.budget_mib || 0) * 1048576;
      $("cc-mem-text").textContent = `${gb(c.bytes)} / ${gb(budget)} GB`;
      $("cc-mem-bar").style.width = pct(c.bytes, budget);
    }
    $("cc-sum").textContent = c.requests ? `${fmt(c.requests_reused)} / ${fmt(c.requests)} 个请求复用了部分输入` : "";
    const share = c.prompt_tokens ? `（占全部输入 token 的 ${fmt((100 * c.reused_tokens) / c.prompt_tokens)}%）` : "";
    const event = c.last_event ? `${c.last_event === "parked" ? "驻留" : "恢复"} ${fmt(c.last_tokens)} tokens · ${since(c.last_at)}` : null;
    const rows = [
      ["上一次请求", c.last_prompt != null ? `复用 ${fmt(c.last_reused || 0)} / ${fmt(c.last_prompt)} 输入 tokens` : null],
      ["开服以来复用", c.requests ? `${fmt(c.reused_tokens)} tokens${share}` : null],
      ["驻留 / 恢复", c.enabled ? `${fmt(c.parks)} / ${fmt(c.restores)}${c.evictions ? ` · 逐出 ${fmt(c.evictions)}` : ""}` : null],
      ["最近切换", c.enabled ? event : null],
    ];
    $("cc-facts").innerHTML = rows.filter((r) => r[1] != null && r[1] !== "").map(
      ([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("");
    $("cc-note").textContent = c.enabled
      ? "接着驻留对话的请求直接取回状态而不是重读；槽位或内存满了先逐出最旧的。"
      : "引擎保留上一次对话的状态，追问只读新内容。要多对话并行，在运行配置里加 --conversation-cache-mib。";
  }

  // ================= main loop：两个源并发、各自容错 =================
  async function fetchExt() {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2500);
    try {
      const r = await fetch("/ext.json", { cache: "no-store", signal: controller.signal });
      if (!r.ok) throw new Error("HTTP " + r.status);
      return await r.json();
    } finally { clearTimeout(timer); }
  }
  async function fetchSlots() {
    // 每槽状态：basalt GET /slots（带 state）、Strata GET /slots（只有
    // is_processing）。两引擎同路径不同形状，本函数只管取，形状归渲染端。
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2500);
    try {
      const headers = {};
      if (apiKey) headers.Authorization = "Bearer " + apiKey;
      const r = await fetch("/slots", { cache: "no-store", signal: controller.signal, headers });
      if (!r.ok) return null;
      const d = await r.json();
      return Array.isArray(d) ? d : null;
    } catch { return null; }
    finally { clearTimeout(timer); }
  }
  async function fetchMetrics() {    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 3500);
    try {
      const headers = {};
      if (apiKey) headers.Authorization = "Bearer " + apiKey;
      const r = await fetch(reqShowAll ? "/metrics?requests=all" : "/metrics",
                            { cache: "no-store", signal: controller.signal, headers });
      if (r.status === 401 || r.status === 403) {
        metricsNeedKey = true;
        keyUi(true, apiKey ? "key 不被引擎接受（401/403），请核对" : "引擎需要 API key 才能读 /metrics");
        return null;
      }
      if (!r.ok) throw new Error("HTTP " + r.status);
      metricsNeedKey = false;
      keyUi(false, "");
      return await r.json();
    } finally { clearTimeout(timer); }
  }

  async function tick() {
    if (!$("metrics")) { setTimeout(tick, TICK_MS); return; }
    let ext = null, met = null, slots = null, extErr = null, metErr = null, renderErr = null;
    await Promise.all([
      fetchExt().then((d) => { ext = d; }, (e) => { extErr = e; }),
      fetchMetrics().then((d) => { met = d; }, (e) => { metErr = e; }),
      fetchSlots().then((d) => { slots = d; }),
    ]);

    // 卡片区顺序照旧融合视图：速度 → 每显卡 → PCIe → CPU → 系统内存 → 硬盘 → 网卡。
    // ensure() 在卡片第一次出现时按调用顺序插进网格，所以这里先渲染谁、谁就在前。
    // 渲染段整体 try/catch（2026-11-19）：任何一处 render 抛错只坏本拍并显式
    // 报状态行，绝不吞掉尾部 setTimeout——一处异形数据不再冻结全页图表。
    try {
    if (met) {
      renderState(met, ext && ext.gate, slots);
      renderSpeed(met);
    }
    if (ext) {
      renderGpus(ext);
    } else {
      // /ext.json 断了：只清本区卡，引擎侧卡不受牵连
      const host = $("metrics");
      pruneSection(host, "gpu", new Set());
      pruneSection(host, "disk", new Set());
      pruneSection(host, "net", new Set());
      pruneSection(host, "gate", new Set());
      const ramEl = document.getElementById("card-ram");
      if (ramEl) ramEl.remove();
    }
    // PCIe 卡每 tick 必画：主源是 /ext.json 每卡吞吐，/metrics 只贡献
    // 「引擎侧实测」一条；两边任一在就有内容。
    if (met || ext) renderPcie(ext, met);
    if (met) {
      renderCpu(met, ext);
    }
    if (ext) {
      renderRam(ext);
      pruneStaleGateCard();
      renderDisks(ext);
      renderNet(ext);
    }
    if (met) {
      renderCtx(met, ext);
      renderRequests(met);
      renderConvCache(met.conversation_cache);
    }
    } catch (e) {
      renderErr = e;                   // 状态行显式报渲染异常，不冒充连接断
      if (window.console && console.error) console.error("monitor render error:", e);
    }

    const st = $("mx-status");
    if (st) {
      if (renderErr) { st.textContent = "本拍渲染异常（图表可能缺一条）：" + (renderErr.message || renderErr); st.className = "bad"; }
      else if (extErr && metErr) { st.textContent = "连不上 /ext.json 与 /metrics（服务没在跑或网络断了）"; st.className = "bad"; }
      else if (extErr) { st.textContent = "硬件采样断了（/ext.json 连不上）；引擎指标正常"; st.className = "bad"; }
      else if (metricsNeedKey) { st.textContent = "引擎指标需要 API key（顶部输入框填入即可）；硬件卡正常"; st.className = "bad"; }
      else if (metErr) { st.textContent = "引擎 /metrics 连不上（引擎没起或反代没转发）；硬件卡正常"; st.className = "bad"; }
      else {
        const g = ext && ext.gpus ? ext.gpus.length : 0;
        st.textContent = `正常 · 显卡 ${g} 张 · 每秒刷新${met ? "" : "（仅硬件）"}`;
        st.className = "";
      }
    }
    setTimeout(tick, TICK_MS);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", tick);
  else tick();
})();
