/* Strata Monitor extension — the web replacement for Task Manager.
 *
 * Served by the ledger proxy itself (same origin, no extra port). Card order:
 * Speed, one card per physical GPU (including TCC compute cards Windows cannot
 * see), CPU, System RAM, one card per physical disk, one card per connected
 * network adapter. The official single-GPU "GPU load"/"VRAM" and aggregate
 * "Disk read" cards are hidden once the per-device cards exist; the official
 * temp / power / PCIe cards stay, since they carry engine-specific detail.
 *
 * All numbers come from /ext.json on this same host. The one <script> line in
 * index.html is same-origin too, so a teammate opening http://<host>:8080/#monitor
 * gets exactly the same view as somebody sitting at the machine.
 */
(() => {
  "use strict";
  if (window.__strataMonitorExt) return;
  window.__strataMonitorExt = true;

  // Data origin. Served by the ledger proxy itself (same origin) this is "". Loaded from another origin —
  // Strata's own console on :8787 has no /ext.json — document.currentScript points at the proxy, so the
  // sampler is read cross-origin (the proxy sends Access-Control-Allow-Origin: *).
  const API = (() => {
    try {
      const s = document.currentScript;
      if (s && s.src) {
        const u = new URL(s.src, location.href);
        if (u.protocol === "http:" || u.protocol === "https:") return u.origin;
      }
    } catch (e) { /* keep same-origin */ }
    return "";
  })();
  const GIB = 1024 ** 3;
  const HISTORY = 180;
  const hist = { ram: [], disks: {}, net: {}, gpus: {} };

  const CSS = `
  #mx-note { font-size: var(--st-fs-xs, 11px); color: var(--st-ink-muted, #6b7280);
             padding: 2px 4px; grid-column: 1 / -1; }
  `;

  const $ = (id) => document.getElementById(id);

  function addStyle() {
    if ($("mx-style")) return;
    const style = document.createElement("style");
    style.id = "mx-style";
    style.textContent = CSS;
    document.head.appendChild(style);
  }

  function hideCard(id) {
    const value = $(id);
    const card = value && value.closest(".metric-card");
    if (card && card.style.display !== "none") card.style.display = "none";
  }

  // the official cards only describe GPU 0; the per-GPU cards below replace them.
  // temp/power are already printed (with the power limit) on every GPU card, so
  // keeping them would show GPU 0 twice. Speed / PCIe / CPU stay: they carry the
  // engine-side detail that the hardware sampler does not have.
  function hideOfficialSingles() {
    hideCard("mv-gpu");
    hideCard("mv-vram");
    hideCard("mv-temp");
    hideCard("mv-power");
    hideCard("mv-disk");
  }

  function cardShell(id, iconId, label) {
    return `<div class="st-card metric-card" id="${id}"><div class="st-metric">
      <span class="st-metric__label"><svg class="st-icon st-icon--sm"><use href="web/sprite.svg#${iconId}"/></svg>${label}</span>
      <span class="st-metric__value" id="${id}-v">–</span>
      <span class="st-metric__sub" id="${id}-s"></span>
      <svg class="st-metric__spark" id="${id}-sp" viewBox="0 0 100 32" preserveAspectRatio="none">
        <path class="area" fill="currentColor" opacity=".12"/><path class="line" fill="none" stroke="currentColor"
          stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/></svg>
    </div></div>`;
  }

  function ensureCard(id, iconId, label, afterEl) {
    let el = $(id);
    if (!el) {
      const wrap = document.createElement("div");
      wrap.innerHTML = cardShell(id, iconId, label);
      el = wrap.firstElementChild;
      if (afterEl && afterEl.parentNode) afterEl.parentNode.insertBefore(el, afterEl.nextSibling);
      else $("metrics").appendChild(el);
    }
    return el;
  }

  function ramCard() {
    const cpu = $("mv-cpu");
    const cpuCard = cpu && cpu.closest(".metric-card");
    if (!cpuCard) return null;
    return ensureCard("mx-card-ram", "i-memory", "System RAM", cpuCard);
  }

  function drawSpark(id, values, max) {
    const svg = $(id);
    if (!svg) return;
    const line = svg.querySelector(".line");
    const area = svg.querySelector(".area");
    const v = values.map((x) => (x == null ? 0 : x));
    if (v.length < 2) {
      line.setAttribute("d", "");
      area.setAttribute("d", "");
      return;
    }
    const top = Math.max(max || 0, ...v, 1);
    const points = v.map((x, i) => [(i / (v.length - 1)) * 100, 30 - (x / top) * 26]);
    const d = points.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(2)},${p[1].toFixed(2)}`).join("");
    line.setAttribute("d", d);
    area.setAttribute("d", `${d}L100,32L0,32Z`);
  }

  function rateParts(mb) {
    if (mb == null) return ["–", ""];
    if (mb >= 1024) return [(mb / 1024).toFixed(2), "GB/s"];
    return [mb < 10 ? mb.toFixed(1) : String(Math.round(mb)), "MB/s"];
  }

  function gibText(bytes) {
    if (!bytes) return "";
    const gib = bytes / GIB;
    return gib >= 1024 ? `${(gib / 1024).toFixed(1)} TB` : `${Math.round(gib)} GB`;
  }

  function setSub(id, text) {
    const el = $(`${id}-s`);
    if (el) el.textContent = text;
  }

  function offline(reason) {
    const ramV = $("mx-card-ram-v");
    if (ramV) ramV.textContent = "–";
    setSub("mx-card-ram", reason);
    for (const el of Array.from(document.querySelectorAll(".metric-card[data-mx-gpu]"))) {
      const v = $(`${el.id}-v`);
      if (v) v.textContent = "–";
      setSub(el.id, reason);
    }
  }

  function renderGpus(data) {
    const host = $("metrics");
    if (!host) return;
    const gpus = data.gpus || [];
    const seen = new Set();
    let after = ($("mv-speed") && $("mv-speed").closest(".metric-card")) || null;
    for (const g of gpus) {
      const id = `mx-gpu-${g.index}`;
      seen.add(id);
      const shortName = String(g.name || `GPU ${g.index}`).replace(/^NVIDIA\s+/i, "");
      const label = `GPU ${g.index} · ${shortName.length > 18 ? `${shortName.slice(0, 17)}…` : shortName}`;
      const card = ensureCard(id, "i-gpu", label, after);
      card.dataset.mxGpu = "1";
      after = card;
      const v = $(`${id}-v`);
      if (v) v.innerHTML = g.util == null ? "–" : `${Math.round(g.util)}<small>%</small>`;
      const parts = [];
      if (g.mem_used_mib != null && g.mem_total_mib) {
        parts.push(`${(g.mem_used_mib / 1024).toFixed(1)} / ${(g.mem_total_mib / 1024).toFixed(0)} GB`);
      }
      if (g.temp != null) parts.push(`${Math.round(g.temp)}°C`);
      if (g.power != null) {
        parts.push(`${Math.round(g.power)}${g.power_limit ? `/${Math.round(g.power_limit)}` : ""} W`);
      }
      if (g.mode) parts.push(g.mode);                    // TCC / WDDM
      if (g.sm_clock != null) parts.push(`${Math.round(g.sm_clock)} MHz`);
      setSub(id, parts.join(" · "));
      const h = hist.gpus[g.index] || (hist.gpus[g.index] = []);
      h.push(g.util);
      if (h.length > HISTORY) h.shift();
      drawSpark(`${id}-sp`, h, 100);
    }
    for (const el of Array.from(host.querySelectorAll(".metric-card[data-mx-gpu]"))) {
      if (!seen.has(el.id)) el.remove();
    }
    if (!gpus.length) {
      let note = $("mx-gpu-note");
      if (!note) {
        note = document.createElement("div");
        note.id = "mx-gpu-note";
        note.textContent = "GPU · nvidia-smi unavailable, no card reported";
        host.appendChild(note);
      }
    }
  }

  function renderRam(data) {
    const card = ramCard();
    if (!card) return;
    const ramV = $("mx-card-ram-v");
    if (ramV && data.ram) {
      ramV.innerHTML = `${(data.ram.used / GIB).toFixed(1)}<small>GB</small>`;
    }
    let sub = data.ram ? `of ${(data.ram.total / GIB).toFixed(1)} GB` : "";
    if (data.swap && data.swap.total) {
      sub += ` · swap ${(data.swap.used / GIB).toFixed(1)} / ${(data.swap.total / GIB).toFixed(1)} GB`;
    }
    setSub("mx-card-ram", sub);
    if (data.ram) {
      hist.ram.push(data.ram.used);
      if (hist.ram.length > HISTORY) hist.ram.shift();
      drawSpark("mx-card-ram-sp", hist.ram, data.ram.total);
    }
  }

  function renderDisks(data) {
    const host = $("metrics");
    if (!host) return;
    const disks = data.disks || [];
    const seen = new Set();
    let after = $("mx-card-ram") || ($("mv-cpu") && $("mv-cpu").closest(".metric-card"));
    for (const d of disks) {
      const id = `mx-disk-${d.number}`;
      seen.add(id);
      const label = d.bus || `Disk ${d.number}`;
      const card = ensureCard(id, "i-disk", label, after);
      after = card;
      const v = $(`${id}-v`);
      if (v) {
        const [num, unit] = rateParts(d.read_mb);
        v.innerHTML = `${num}<small>${unit}</small>`;
      }
      const parts = [`↑ ${rateParts(d.write_mb).join(" ")}`];
      if (d.model) parts.push(d.model.length > 24 ? `${d.model.slice(0, 23)}…` : d.model);
      const size = gibText(d.size);
      if (size) parts.push(size);
      if (d.drives) parts.push(d.drives);
      setSub(id, parts.join(" · "));
      const h = hist.disks[d.number] || (hist.disks[d.number] = []);
      h.push(d.read_mb);
      if (h.length > HISTORY) h.shift();
      drawSpark(`${id}-sp`, h, 0);
    }
    for (const el of Array.from(host.querySelectorAll(".metric-card"))) {
      if (el.id && el.id.startsWith("mx-disk-") && !seen.has(el.id)) el.remove();
    }
  }

  function netId(a) {
    return `mx-net-${String(a.name).replace(/[^a-zA-Z0-9_-]/g, "_")}`;
  }

  function renderNet(data) {
    const host = $("metrics");
    if (!host) return;
    const adapters = (data.net || []).filter((a) => a.connected);
    const seen = new Set();
    let after = $("mx-card-net-last");
    const diskCards = host.querySelectorAll(".metric-card[id^='mx-disk-']");
    if (diskCards.length) after = diskCards[diskCards.length - 1];
    else if ($("mx-card-ram")) after = $("mx-card-ram");
    else if ($("mv-cpu")) after = $("mv-cpu").closest(".metric-card");

    let sumDown = 0, sumUp = 0;
    for (const a of adapters) {
      const id = netId(a);
      seen.add(id);
      const label = a.kind === "wifi" ? "Wi-Fi" : (a.kind === "wired" ? "Wired" : a.name);
      const card = ensureCard(id, "i-link", label, after);
      card.dataset.mxNet = "1";
      after = card;
      const v = $(`${id}-v`);
      if (v) {
        const [num, unit] = rateParts(a.down_mb);
        v.innerHTML = unit ? `${num}<small>${unit}</small>` : num;
      }
      setSub(id, a.up_mb != null ? `↑ ${rateParts(a.up_mb).join(" ")}${a.name !== label ? ` · ${a.name}` : ""}` : "");
      const h = hist.net[a.name] || (hist.net[a.name] = []);
      h.push(a.down_mb);
      if (h.length > HISTORY) h.shift();
      drawSpark(`${id}-sp`, h, 0);
      sumDown += a.down_mb || 0;
      sumUp += a.up_mb || 0;
    }
    for (const el of Array.from(host.querySelectorAll(".metric-card"))) {
      if (el.dataset && el.dataset.mxNet && !seen.has(el.id)) el.remove();
    }
    let note = $("mx-note");
    if (!note) {
      note = document.createElement("div");
      note.id = "mx-note";
      host.appendChild(note);
    }
    note.textContent = adapters.length
      ? `network total · ↓ ${rateParts(sumDown).join(" ")} · ↑ ${rateParts(sumUp).join(" ")}`
      : "network · no connected adapter";
  }

  function render(data) {
    if (!data || !data.ok) {
      offline(data && data.error ? data.error : "collector not running");
      return;
    }
    renderGpus(data);
    renderRam(data);
    renderDisks(data);
    renderNet(data);
  }

  async function tick() {
    const host = $("metrics");
    if (!host) {
      setTimeout(tick, 1000);
      return;
    }
    if (!ramCard()) {
      setTimeout(tick, 1000);
      return;
    }
    hideOfficialSingles();
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 2500);
      const response = await fetch(`${API}/ext.json`, {cache: "no-store", signal: controller.signal});
      clearTimeout(timer);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      render(await response.json());
    } catch (e) {
      offline("collector not running");
    }
    setTimeout(tick, 1000);
  }

  function init() {
    addStyle();
    hideOfficialSingles();
    tick();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
