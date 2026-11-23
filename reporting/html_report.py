#!/usr/bin/env python3
r"""token-ledger · HTML report: ONE self-contained static page per anchor day.

  python html_report.py --out-dir DIR [--day YYYY-MM-DD | --all] [--name LABEL]
  python html_report.py --config <out_dir>/config.json [--day D | --all]

Unified page = header (title · meta · 口径 dropdown · history selector) + THREE
same-level query modes as tabs (皮总 ruling 2026-11-05): 按天(单日期选框) /
快捷周期(近7/30/90/180/365天标签) / 起止日期(开始日-结束日日历选单). Picking a mode
reveals its filter control; all stats are then computed in-browser from the shared
usage-data.js sidecar, re-filtered live by the 口径 dropdown.
口径 dropdown appears only when records carry a "key" (proxy mode with API keys);
without keys it is totals only. Every query reports: 总量 + 平均每日(gen AND prompt),
各时段平均(按小时·日均), decode distribution avg/weighted/max/min tok/s, concurrency
(peak, share, per-level split via arrival→finish windows), models, per-key table,
coverage window. usage-report.html always mirrors the newest day.
"""
import glob
import html as H
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gateway"))  # find paths.py (gateway/) however this module is loaded

ESC = H.escape
ALL = "__all__"
QUICK = [7, 30, 90, 180, 365]


def load_all(out):
    by_day = {}
    for p in glob.glob(os.path.join(out, "requests-*.jsonl")):
        fday = os.path.basename(p)[len("requests-"):-len(".jsonl")]
        for line in open(p, encoding="utf-8"):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict):
                by_day.setdefault((r.get("ts") or "")[:10] or fday, []).append(r)
    return by_day


def epoch(ts):
    try:
        return datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S").timestamp()
    except (ValueError, TypeError):
        return None


def day_view_row(rows):
    """Compact per-day aggregates consumed by the in-browser query engine.
    Layout: [req, err, gen, gen_ms, prompt, cached, dec_n, dec_sum, dec_min, dec_max,
             hist([[bucket,count]..]), hreq[24], hgen[24], ivs([start_s,dur_s]..),
             models([[name,req,gen]..]), t0(first ts), t1(last ts), kb({key:[req,gen,prompt]})]"""
    req = [r for r in rows if not r.get("kind")]
    hreq = [0] * 24
    hgen = [0] * 24
    hist = {}
    ivs = []
    models = {}
    kb = {}
    dec_n = dec_sum = 0
    dec_min = dec_max = None
    gen = ms = tp = cached = err = 0
    t0 = t1 = None
    for r in req:
        if r.get("error"):
            err += 1
        g = r.get("gen", 0)
        gen += g
        ms += r.get("gen_ms", 0)
        p = r.get("prompt", 0)
        tp += p
        cached += r.get("cached", 0)
        if r.get("model"):
            m = models.setdefault(r["model"], [0, 0])
            m[0] += 1
            m[1] += g
        k = r.get("key")
        if k and k != "none":
            kk = kb.setdefault(k, [0, 0, 0])
            kk[0] += 1
            kk[1] += g
            kk[2] += p
        if r.get("ts"):
            if t0 is None or r["ts"] < t0:
                t0 = r["ts"]
            if t1 is None or r["ts"] > t1:
                t1 = r["ts"]
            h = int(r["ts"][11:13])
            hreq[h] += 1
            hgen[h] += g
            if r.get("gen_ms"):
                e0 = epoch(r["ts"])
                if e0 is not None:
                    ivs.append(round(e0))
                    ivs.append(round(r["gen_ms"] / 1000.0, 1))
        d = r.get("decode_tok_s")
        if d and g >= 30:
            dec_n += 1
            dec_sum += d
            dec_min = d if dec_min is None or d < dec_min else dec_min
            dec_max = d if dec_max is None or d > dec_max else dec_max
            b = int(d // 20) * 20
            hist[b] = hist.get(b, 0) + 1
    return [len(req), err, gen, ms, tp, cached, dec_n, round(dec_sum, 1),
            dec_min, dec_max, sorted(hist.items()), hreq, hgen, ivs,
            [[m, c, g] for m, (c, g) in sorted(models.items(), key=lambda kv: -kv[1][1])],
            t0, t1, kb]


def write_sidecar(out, by_day, days):
    allrows = [r for d in days for r in by_day[d]]
    keys = sorted({r["key"] for r in allrows if r.get("key") and r["key"] != "none"})
    views = {"__all__": {d: day_view_row(by_day[d]) for d in days}}
    for k in keys:
        v = {d: day_view_row([r for r in by_day[d] if r.get("key") == k])
             for d in days if any(r.get("key") == k for r in by_day[d])}
        views[k] = v
    data = {"days": days, "views": views}
    with open(os.path.join(out, "usage-data.js"), "w", encoding="utf-8") as f:
        f.write("window.TL_DATA=" + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";")
    return os.path.getsize(os.path.join(out, "usage-data.js"))


CSS = """
/* Design tokens — light-first, GitHub Primer / Adminator inspired:
   white cards on a blue-grey canvas, one royal-blue accent, soft tints for active states,
   ordered chart hues (blue family + one teal + one amber) instead of rainbow. */
:root{
  --bg:#f4f6fa; --panel:#ffffff; --panel2:#f6f8fb;
  --ink:#1f2328; --dim:#59636e; --faint:#8c959f; --line:#dfe4ec; --line2:#eceff4;
  --accent:#2563eb; --accent-deep:#1d4ed8; --accent-soft:#eff5ff; --accent-ink:#ffffff;
  --c-1:#2563eb; --c-2:#7aa7f5; --c-3:#0d9488; --c-4:#d97706;
  --warn-bg:#fff8e6; --warn-line:#f3d9a4; --warn-ink:#8a6116;
  --shadow:0 1px 2px rgba(20,30,55,.04),0 4px 14px -6px rgba(20,30,55,.08);
  --radius:12px;
}
/* dark only via manual toggle (data-theme), never forced by system preference */
[data-theme=dark]{
  --bg:#0d1117; --panel:#161b22; --panel2:#1c2129;
  --ink:#e6edf3; --dim:#9aa4b0; --faint:#6e7a87; --line:#2d333b; --line2:#22272e;
  --accent:#4c8dff; --accent-deep:#6ba3ff; --accent-soft:#17294a; --accent-ink:#ffffff;
  --c-1:#4c8dff; --c-2:#79abff; --c-3:#2dd4bf; --c-4:#f0a35e;
  --warn-bg:#302513; --warn-line:#54451f; --warn-ink:#e5c789;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 6px 20px -8px rgba(0,0,0,.5);
}
*{box-sizing:border-box}
body{font-family:"Segoe UI","Microsoft YaHei",system-ui,-apple-system,sans-serif;margin:0;
  background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased;font-size:14px;line-height:1.55}
.wrap{max-width:840px;margin:30px auto 44px;padding:0 20px}
.brand{border-bottom:1px solid var(--line);padding-bottom:14px;margin-bottom:4px}
.brow{display:flex;align-items:baseline;gap:12px}
h1{font-size:21px;font-weight:700;letter-spacing:.3px;margin:0}
h1::before{content:"";display:inline-block;width:9px;height:9px;border-radius:2px;background:var(--accent);margin-right:10px;vertical-align:2px}
.sub{color:var(--faint);font-size:12.5px}
.thtog{margin-left:auto;flex:none}
html[data-theme=dark]{color-scheme:dark}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(172px,1fr));gap:12px;margin:18px 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:15px 17px;box-shadow:var(--shadow);position:relative;overflow:hidden}
.kpi::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--c-1);opacity:.75}
.kpi:nth-child(2)::before{background:var(--c-3)} .kpi:nth-child(3)::before{background:var(--c-2)} .kpi:nth-child(4)::before{background:var(--c-4)}
.kpi .v{font-size:23px;font-weight:700;letter-spacing:-.3px;font-variant-numeric:tabular-nums}
.kpi .l{font-size:12px;color:var(--dim);margin-top:3px;font-weight:600}
.kpi .s{font-size:11px;color:var(--faint);margin-top:3px;font-variant-numeric:tabular-nums}
.sec{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:20px 22px;margin:16px 0;box-shadow:var(--shadow)}
.sec h2{font-size:14px;margin:0 0 4px;font-weight:700;letter-spacing:.3px}
.sec h2 .muted{font-weight:400}
.sec>.cards{margin-top:14px}
.h3{font-size:12px;margin:22px 0 8px;color:var(--dim);font-weight:700;letter-spacing:.4px;display:flex;align-items:center;gap:8px}
.h3::after{content:"";flex:1;height:1px;background:var(--line2)}
table{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line2);font-variant-numeric:tabular-nums}
th{color:var(--faint);font-weight:600;font-size:11.5px;letter-spacing:.4px;text-transform:uppercase}
tr:hover td{background:var(--panel2)}
.muted{color:var(--faint);font-size:13px}
.warn{background:var(--warn-bg);border:1px solid var(--warn-line);color:var(--warn-ink);border-radius:10px;padding:9px 13px;font-size:13px;margin-top:8px}
.nav{display:flex;gap:10px;align-items:center;margin:12px 0;flex-wrap:wrap}
.nav select{padding:7px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--ink);font-size:13px}
.nav a{font-size:13px;color:var(--accent)}
/* segmented control (Linear/Stripe style) instead of loose pills */
.tabs{display:inline-flex;gap:2px;background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:3px;box-shadow:var(--shadow)}
.tabrow{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:16px 0 8px;position:sticky;top:0;z-index:5;background:linear-gradient(180deg,var(--bg) 70%,transparent);padding:4px 0}
.kv-l{font-size:12px}
.kv-s{padding:6px 10px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--ink);font-size:12.5px;max-width:240px}
.tab{padding:7px 18px;border-radius:8px;border:0;background:transparent;color:var(--dim);font-size:13px;font-weight:600;cursor:pointer;user-select:none;transition:all .13s}
.tab:hover{color:var(--ink)}
.tab.on{background:var(--panel);color:var(--accent);box-shadow:0 1px 3px rgba(20,30,55,.12)}
.ctl{display:flex;gap:10px;align-items:center;flex-wrap:nowrap;background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:12px 16px;margin:10px 0 4px;box-shadow:var(--shadow)}
.ctl input[type=date]{padding:7px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--ink);font-size:13px}
:root{color-scheme:light}
.chip{padding:6px 15px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--dim);font-size:12.5px;font-weight:600;cursor:pointer;user-select:none;transition:all .13s}
.chip:hover{border-color:var(--accent);color:var(--accent)}
.chip.on{background:var(--accent-soft);color:var(--accent-deep);border-color:var(--accent)}
.calc-btn{margin-left:auto;flex-shrink:0;align-self:flex-start}
.sel{display:flex;gap:10px;align-items:center;flex-wrap:wrap;flex:1;min-width:0}
footer{color:var(--faint);font-size:12px;margin:28px 0 0;text-align:center;letter-spacing:.3px}
svg text{fill:var(--faint)}
"""

JS = """<script>
var TLK='__all__',MODE='day',QK=7,lastAgg=null;
function fmt(n){return (Math.round(n*10)/10).toLocaleString('zh-CN',{maximumFractionDigits:1})}
function fmti(n){return Math.round(n).toLocaleString('zh-CN')}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')}
function bars(items,color,dec){var mx=0;items.forEach(function(it){if(it[1]>mx)mx=it[1]});
if(!mx)return '<div class="muted">无数据</div>';
var W=640,TOP=18,Hh=118,bw=(W-40)/items.length,s='<svg viewBox="0 0 '+W+' '+(Hh+26)+'" width="100%" font-family="inherit">';
items.forEach(function(it,i){var h=(Hh-TOP-6)*it[1]/mx,x=20+i*bw;
s+='<rect x="'+x.toFixed(1)+'" y="'+(Hh-h).toFixed(1)+'" width="'+Math.max(1,bw-2).toFixed(1)+'" height="'+h.toFixed(1)+'" rx="2" style="fill:'+(color||'var(--c-1)')+';opacity:.88"><title>'+it[0]+': '+(dec?fmt(it[1]):fmti(it[1]))+'</title></rect>';
if(items.length<=24||i%Math.max(1,Math.floor(items.length/12))===0)s+='<text x="'+(x+bw/2).toFixed(1)+'" y="'+(Hh+16)+'" font-size="10" text-anchor="middle">'+it[0]+'</text>'});
s+='<text x="20" y="12" font-size="10">峰值 '+(dec?fmt(mx):fmti(mx))+'</text></svg>';return s}
function kpiC(v,l,s2){return '<div class="kpi"><div class="v">'+v+'</div><div class="l">'+l+'</div>'+(s2?'<div class=s>'+s2+'</div>':'')+'</div>'}
function anchorD(){return window.TL_ANCHOR||(window.TL_DATA&&TL_DATA.days[TL_DATA.days.length-1])||''}
function addDays(iso,n){var t=new Date(iso+'T12:00:00');t.setDate(t.getDate()+n);var m=t.getMonth()+1,d=t.getDate();
return t.getFullYear()+'-'+(m<10?'0':'')+m+'-'+(d<10?'0':'')+d}
function collect(days){var D=(TL_DATA.views||{})[TLK]||{},a={n:0,req:0,err:0,gen:0,ms:0,pr:0,ca:0,dn:0,dsum:0,dmin:null,dmax:null,
hist:{},hreq:[],hgen:[],ivs:[],models:{},kb:{},t0:null,t1:null,daily:[]};
for(var h=0;h<24;h++){a.hreq.push(0);a.hgen.push(0)}
days.forEach(function(d){var p=D[d];if(!p)return;a.n++;
a.req+=p[0];a.err+=p[1];a.gen+=p[2];a.ms+=p[3];a.pr+=p[4];a.ca+=p[5];a.dn+=p[6];a.dsum+=p[7];
if(p[8]!=null&&(a.dmin==null||p[8]<a.dmin))a.dmin=p[8];
if(p[9]!=null&&(a.dmax==null||p[9]>a.dmax))a.dmax=p[9];
(p[10]||[]).forEach(function(hc){a.hist[hc[0]]=(a.hist[hc[0]]||0)+hc[1]});
for(var h=0;h<24;h++){a.hreq[h]+=p[11][h];a.hgen[h]+=p[12][h]}
a.ivs=a.ivs.concat(p[13]||[]);
(p[14]||[]).forEach(function(m){var e=a.models[m[0]];if(e){e[1]+=m[1];e[2]+=m[2]}else a.models[m[0]]=[m[0],m[1],m[2]]});
var kb=p[17];if(kb)for(var k in kb){var v=a.kb[k];if(v){v[1]+=kb[k][0];v[2]+=kb[k][1];v[3]+=kb[k][2]}else a.kb[k]=[k,kb[k][0],kb[k][1],kb[k][2]]}
if(p[15]&&(a.t0===null||p[15]<a.t0))a.t0=p[15];
if(p[16]&&(a.t1===null||p[16]>a.t1))a.t1=p[16];
a.daily.push([d.slice(5),p[2],p[0]])});
return a}
function concHtml(a){var ev=[];for(var i=0;i<a.ivs.length;i+=2){var t=a.ivs[i],d=a.ivs[i+1];if(d>0){ev.push([t,1]);ev.push([t+d,-1])}}
if(!ev.length)return '<div class="muted">无带时长（gen_ms）记录，无法估算并发</div>';
ev.sort(function(x,y){return x[0]-y[0]||x[1]-y[1]});
var lvl=0,prev=null,ta={},peak=0,i2=0;
while(i2<ev.length){var t2=ev[i2][0];if(prev!==null&&lvl>0&&t2>prev)ta[lvl]=(ta[lvl]||0)+(t2-prev);
while(i2<ev.length&&ev[i2][0]===t2){lvl+=ev[i2][1];i2++}if(lvl>peak)peak=lvl;prev=t2}
var tot=0,par=0,ks=Object.keys(ta).map(Number);ks.forEach(function(k){tot+=ta[k];if(k>=2)par+=ta[k]});
if(!tot)return '<div class="muted">无并发数据</div>';
ks.sort(function(x,y){return x-y});
return '<div class="cards">'+kpiC(peak+' 路','最高并发')+kpiC((100*par/tot).toFixed(1)+'%','并发时间占比','活跃总时长 '+fmt(tot/3600)+' h')
+kpiC(fmt(par/3600)+' h','并行时长','串行 '+fmt((ta[1]||0)/3600)+' h')+'</div>'
+'<h2 class="h3">各并发度时长占比</h2>'+bars(ks.map(function(k){return [k+'路',ta[k]]}),'var(--c-4)',false)
+'<table><tr><th>并发度</th><th>时长</th><th>占活跃时间</th></tr>'
+ks.map(function(k){return '<tr><td>'+k+' 路</td><td>'+(ta[k]/3600).toFixed(2)+' h</td><td>'+(100*ta[k]/tot).toFixed(1)+'%</td></tr>'}).join('')+'</table>'}
function render(a,title,span){if(!a.n)return '<div class="muted">'+esc(span)+' 区间内无记录</div>';
var nd=a.n,tn=a.pr?100*a.ca/a.pr:0,w=a.ms?a.gen/(a.ms/1000):0;
var one=(nd===1);
var cards='<div class="cards">'+kpiC(fmti(a.req),'请求数',(one?'':'日均 '+fmti(a.req/nd)+'｜')+'失败 '+fmti(a.err))
+kpiC(w.toFixed(1),'解码 tok/s（加权）',(a.dmin!=null?'最高 '+fmt(a.dmax)+'｜最低 '+fmt(a.dmin):''))
+kpiC(fmti(a.gen),'生成 tokens',(one?'':'平均每日 '+fmti(a.gen/nd)+' tok｜日均 '+(a.ms/3600000/nd).toFixed(1)+' h<br>')+'生成耗时 '+fmt(a.ms/3600000)+' h')
+kpiC(fmti(a.pr),'prompt tokens',(one?'':'平均每日 '+fmti(a.pr/nd)+' tok<br>')+'新算 '+fmti(a.pr-a.ca)+'｜复用 '+tn.toFixed(1)+'%')+'</div>';
var dg=a.daily.map(function(x){return [x[0],x[1]]}),dr=a.daily.map(function(x){return [x[0],x[2]]});
var hg=[],hr=[];for(var h=0;h<24;h++){var lab=('0'+h).slice(-2);hg.push([lab,a.hgen[h]/nd]);hr.push([lab,a.hreq[h]/nd])}
var dsec='<div class="muted">无数据</div>';
if(a.dn){var bks=Object.keys(a.hist).map(Number).sort(function(x,y){return x-y});
dsec='<div class="cards">'+kpiC(fmt(a.dsum/a.dn),'平均 tok/s')+kpiC(w.toFixed(1),'加权 tok/s','总生成 tok ÷ 总生成时长')
+kpiC(fmt(a.dmax),'最高 tok/s')+kpiC(fmt(a.dmin),'最低 tok/s')+'</div><h2 class="h3">分布直方图</h2>'
+bars(bks.map(function(b){return [String(b),a.hist[b]]}),'var(--c-3)',false)}
var mm=Object.keys(a.models).map(function(k){return a.models[k]}).sort(function(x,y){return y[2]-x[2]});
var msec=mm.length?'<h2 class="h3">模型</h2><table><tr><th>模型</th><th>请求</th><th>生成 tok</th></tr>'
+mm.map(function(m){return '<tr><td>'+esc(m[0])+'</td><td>'+fmti(m[1])+'</td><td>'+fmti(m[2])+'</td></tr>'}).join('')+'</table>':'';
var kbr=TLK==='__all__'?Object.keys(a.kb).map(function(k){return a.kb[k]}).sort(function(x,y){return y[2]-x[2]}):[];
var ksec=kbr.length?'<h2 class="h3">按 API key</h2><table><tr><th>key</th><th>请求</th><th>生成 tok</th><th>prompt tok</th></tr>'
+kbr.map(function(e){return '<tr><td>'+esc(e[0])+'</td><td>'+fmti(e[1])+'</td><td>'+fmti(e[2])+'</td><td>'+fmti(e[3])+'</td></tr>'}).join('')+'</table>':'';
var cov='';
if(a.t0)cov='<div class="muted">实测覆盖 <b>'+esc(a.t0)+' → '+esc(a.t1)+'</b></div>'
+(one&&a.t0.slice(11)>'00:05:00'?'<div class="warn">⚠️ 当日 00:00 → '+esc(a.t0.slice(11))+' 无采集记录（服务或采集器未运行），该段不可恢复。</div>':'');
var bodyHtml=cards
+'<h2 class="h3">每日生成 tokens</h2>'+bars(dg,'var(--c-2)',false)
+'<h2 class="h3">每日请求数</h2>'+bars(dr,null,false)
+'<h2 class="h3">各时段平均用量（按小时·日均）· 生成 tokens</h2>'+bars(hg,'var(--c-2)',true)
+'<h2 class="h3">各时段平均用量（按小时·日均）· 请求数</h2>'+bars(hr,null,true)
+'<h2 class="h3">解码速度（tok/s，仅 gen≥30 的请求）</h2>'+dsec
+'<h2 class="h3">并发（按请求到达→生成结束窗口估算）</h2>'+concHtml(a)
+msec+ksec+'<h2 class="h3">覆盖窗口</h2>'+(cov||'<div class="muted">无带时间戳记录</div>');
return '<div class="sec"><h2>'+esc(title)+'<span class="muted">　'+esc(span)+'｜有数据日 '+a.n+' 天</span></h2>'+bodyHtml+'</div>'}
function selDays(){var D=TL_DATA.days;
if(MODE==='day'){var v=document.getElementById('tl-day').value;return v?[v]:[]}
if(MODE==='quick'){var an=addDays(anchorD(),-1),s=addDays(an,-(QK-1));return D.filter(function(d){return d>=s&&d<=an})}
var a=document.getElementById('tl-from').value,b=document.getElementById('tl-to').value;
if(!a||!b)return [];if(a>b){var t=a;a=b;b=t}
return D.filter(function(d){return d>=a&&d<=b})}
function go(){var o=document.getElementById('out');if(!o)return;
if(!window.TL_DATA){o.innerHTML='<div class="warn">缺少同目录 usage-data.js（生成 HTML 时自动写出），无法计算。</div>';return}
var days=selDays();
if(!days.length){o.innerHTML='<div class="muted">未选择日期或所选区间内无记录</div>';lastAgg=null;calcGo();return}
var a=collect(days),title,span;lastAgg=a;
if(MODE==='day'){var dv=document.getElementById('tl-day').value;title='按天 · '+dv;span=dv;
if(TL_DATA.days.indexOf(dv)<0){o.innerHTML='<div class="muted">'+dv+' 无采集记录</div>';lastAgg=null;calcGo();return}}
else if(MODE==='quick'){var an=addDays(anchorD(),-1),st=addDays(an,-(QK-1));title='近'+QK+'天';span=st+' → '+an+'（不含当天，按实际有统计区间计）'}
else{var x=document.getElementById('tl-from').value,y=document.getElementById('tl-to').value;if(x>y){var t2=x;x=y;y=t2}
title='起止日期';span=x+' → '+y}
o.innerHTML=render(a,title,span);calcGo()}
function tm(m){MODE=m;CALC=false;
['day','quick','custom'].forEach(function(x){document.getElementById('tab-m-'+x).classList.toggle('on',x===m)});
calcUI();go()}
function qk(n){QK=n;
document.querySelectorAll('.chip[data-q]').forEach(function(e){e.classList.toggle('on',e.getAttribute('data-q')===String(n))});go()}
function kv(v){TLK=v;go()}
function th(){var h=document.documentElement,n=h.getAttribute('data-theme')==='dark'?'light':'dark';
if(n==='dark')h.setAttribute('data-theme','dark');else h.removeAttribute('data-theme');
try{localStorage.setItem('tl-theme',n)}catch(e){}thBtn(n)}
function thBtn(n){var b=document.getElementById('th-btn');if(b)b.textContent=(n==='dark'?'☀ 浅色':'深色 ◐')}
/* 省钱计算器：价表=各厂商公开 API 牌价（USD/1M tok），抓取于 2026-11-04，见 data-defs/api-price-table.csv。
   计费口径：prompt 中缓存命中部分按各家 cache-hit 价、新算部分按 cache-miss 价、生成 tok 按输出价；
   汇率 ¥7.1/$。各家分词器不同，按本地计数折算有 ±20% 偏差。 */
/* 排序＝厂商按各家最高输入价从高到低、同厂商模型聚拢且内部按输入价降序（与 data-defs/api-price-table.csv 一致） */
var TLP=[["OpenAI","GPT-6 Astra",10,1,50],["OpenAI","GPT-5.6 Terra",2,0.2,12],["OpenAI","GPT-6 Sol",2,0.2,10],["Anthropic","Claude Fable 5",10,1,50],["Anthropic","Claude Opus 5.5",4,0.2,20],["Anthropic","Claude Sonnet 5.5",2,0.1,10],["Anthropic","Claude Haiku 5.5",0.1,0.01,0.5],["Moonshot","Kimi K3",2.82,0.28,14.08],["Moonshot","Kimi K3.1 Pro",1.83,0.18,9.58],["Google","Gemini 4 Argon",2,0.1,10],["Google","Gemini 3.8 Flash",0.75,0.075,3.75],["xAI","Grok 4.7",2,0.5,6],["阿里云","Qwen3.8-Max",1.69,1.69,5.07],["阿里云","Qwen3.8-Flash",0.11,0.11,0.38],["DeepSeek","V4-Pro",1.32,0.044,3.96],["DeepSeek","V4.1-Flash",0.3,0.006,1.2],["智谱","GLM-5.3",1.13,0.28,3.94],["智谱","GLM-5.3-Flash",0.11,0.03,0.39],["小米","MiMo-V2.6-Pro",0.435,0.0036,0.87],["小米","MiMo-V2.6-Flash",0.14,0.0028,0.28],["MiniMax","MiniMax-M3",0.3,0.06,1.18],["MiniMax","MiniMax-M3.1-Flash",0.15,0.015,0.6]];
var CALC=false;
function calcUI(){document.querySelectorAll('.calc-btn').forEach(function(e){e.textContent=CALC?'关闭计算器':'省钱计算器';e.classList.toggle('on',CALC)});
['day','quick','custom'].forEach(function(x){var c=document.getElementById('ctl-'+x);if(!c)return;
c.style.display=(x===MODE?'':'none');var sel=c.querySelector('.sel');if(sel)sel.style.display=CALC?'none':''});
var o=document.getElementById('out');if(o)o.style.display=CALC?'none':''}
function calc(){CALC=!CALC;calcUI();calcGo()}
function calcGo(){var o=document.getElementById('calc');if(!o)return;
if(!CALC){o.style.display='none';o.innerHTML='';return}
o.style.display='';
if(!window.TL_DATA||!lastAgg){o.innerHTML='<div class="warn">缺少查询数据，无法折算。</div>';return}
var a=lastAgg,miss=(a.pr-a.ca)/1e6,hit=a.ca/1e6,out=a.gen/1e6;
var rows=TLP.map(function(p){return[p[0],p[1],miss*p[2]+hit*p[3]+out*p[4]]});
var costs=rows.map(function(r){return r[2]});
var best=Math.min.apply(null,costs),bestName=rows[costs.indexOf(best)][1];
var mx=Math.max.apply(null,costs);
var lastV='',lastI=-2;
o.innerHTML='<div class="sec"><h2>省钱计算器<span class="muted">　按当前查询的 token 量折算各家 API 牌价（假设同等缓存命中结构）</span></h2>'
+'<table><tr><th>厂商</th><th>模型</th><th>USD</th><th>≈¥</th><th>相对最贵</th></tr>'
+rows.map(function(r,i){var vc=r[0]===lastV?'':r[0];lastV=r[0];
var sep=(i===lastI+1&&i>0)?' style="border-top:2px solid var(--line)"':'';lastI=i;
return '<tr'+sep+'><td>'+esc(vc)+'</td><td>'+esc(r[1])+'</td><td>'+r[2].toLocaleString('zh-CN',{maximumFractionDigits:2})+'</td><td>'+(r[2]*7.1).toLocaleString('zh-CN',{maximumFractionDigits:0})+'</td><td>'+(100*r[2]/mx).toFixed(1)+'%</td></tr>'}).join('')+'</table>'
+'<div class="muted">排序＝按各家牌价从高到低，同厂商模型聚拢。口径：prompt 新算 '+fmti(a.pr-a.ca)+' tok 按各家 cache-miss 价、KV 命中 '+fmti(a.ca)+' tok 按 cache-hit 价、生成 '+fmti(a.gen)+' tok 按输出价。汇率 7.1。牌价 2026-11-05 逐家官方页核验（data-defs/api-price-table.csv 含出处与峰谷/分档备注）；各家分词器差异 ±20%；阿里云未公布缓存命中价，按其输入价计（偏保守）。按当前用量折算最便宜 <b>'+esc(bestName)+'</b> ≈ ¥'+(best*7.1).toFixed(0)+'。</div></div>'}
function today(){var dd=document.getElementById('tl-day');if(dd)dd.value=anchorD();go()}
(function init(){var an=anchorD();
var dd=document.getElementById('tl-day');if(dd){dd.value=an;dd.min=TL_DATA?TL_DATA.days[0]:an;dd.max=an}
var f=document.getElementById('tl-from'),t=document.getElementById('tl-to');
if(f&&window.TL_DATA){f.min=t.min=TL_DATA.days[0];f.max=t.max=an;f.value=TL_DATA.days[0];t.value=an}
var tn='light';try{tn=localStorage.getItem('tl-theme')||'light'}catch(e){}
if(tn==='dark')document.documentElement.setAttribute('data-theme','dark');thBtn(tn);
tm('day')})();
</script>"""


def unified_body(day, by_day, name="", keys_cfg=None):
    """Header + three same-level query-mode tabs (口径 dropdown appended to the tabs row,
    driven by BOTH ledger keys and configured keys from out_dir/config.json key_labels);
    each tab reveals its own filter control (date box / quick chips / date range)."""
    days = [d for d in sorted(by_day) if d <= day]
    allrows = [r for d in days for r in by_day[d]]
    keys = sorted({r["key"] for r in allrows if r.get("key") and r["key"] != "none"} |
                  set(keys_cfg or []))

    header = ('<div class="brand"><div class="brow"><h1>Token 账本</h1>'
              '<span class="chip thtog" id="th-btn" onclick="th()"></span></div>'
              f'<div class="sub">{ESC(name)} · 数据截至 {day} · 页面刷新于 {datetime.now().strftime("%Y-%m-%d %H:%M")}</div></div>')
    # 口径下拉恒显示，默认「总量」；有 key 被启用（账本记录带 key 或 config.json key_labels 配了 key）才追加可选项
    opts = f'<option value="{ALL}" selected>总量</option>' + "".join(
        f'<option value="{ESC(k)}">{ESC(k)}</option>' for k in keys)
    key_sel = (f'<label class="muted kv-l">口径</label>'
               f'<select class="kv-s" id="tl-kv" onchange="kv(this.value)">{opts}</select>')

    tabs = (f'<span class="tab on" id="tab-m-day" onclick="tm(\'day\')">按天</span>'
            f'<span class="tab" id="tab-m-quick" onclick="tm(\'quick\')">快捷周期</span>'
            f'<span class="tab" id="tab-m-custom" onclick="tm(\'custom\')">起止日期</span>')
    lo = days[0] if days else day
    calc_btn = '<span class="chip calc-btn" onclick="calc()">省钱计算器</span>'
    ctl_day = (f'<div class="ctl" id="ctl-day"><span class="sel">'
               f'<label class="muted">日期</label>'
               f'<input type="date" id="tl-day" min="{lo}" max="{day}" value="{day}" onchange="go()">'
               f'<span class="chip" onclick="today()">今天</span></span>{calc_btn}</div>')
    chips = "".join(f'<span class="chip{" on" if n == 7 else ""}" data-q="{n}" onclick="qk({n})">近{n}天</span>'
                    for n in QUICK)
    ctl_quick = f'<div class="ctl" id="ctl-quick" style="display:none"><span class="sel">{chips}<span class="muted">不含当天，从昨天往回算</span></span>{calc_btn}</div>'
    ctl_custom = (f'<div class="ctl" id="ctl-custom" style="display:none"><span class="sel">'
                  f'<input type="date" id="tl-from" min="{lo}" max="{day}" value="{lo}" onchange="go()">'
                  f'<span class="muted">→</span>'
                  f'<input type="date" id="tl-to" min="{lo}" max="{day}" value="{day}" onchange="go()">'
                  f'<span class="muted">起止含当日</span></span>{calc_btn}</div>')
    return (header + f'<div class="tabrow"><div class="tabs">{tabs}</div>{key_sel}</div>'
            + ctl_day + ctl_quick + ctl_custom + '<div id="calc" style="display:none"></div><div id="out"></div>')


def page(title, name, body, cur=""):
    """Single live page — no per-day snapshot files and no top history selector any more:
    history is queried in-page (按天 date box covers every day; 快捷周期 anchors to latest)."""
    anchor = f'<script>window.TL_ANCHOR="{cur}";</script>' if cur else ""
    pretheme = '<script>try{if(localStorage.getItem("tl-theme")==="dark")document.documentElement.setAttribute("data-theme","dark")}catch(e){}</script>'
    return (f'<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
            f'<title>{ESC(title)} · {ESC(name)}</title><style>{CSS}</style>{pretheme}</head>'
            f'<body><div class="wrap">{body}'
            f'<footer>token-ledger · html_report.py · 由 html_report.py 生成 · 手动重跑可刷新（不随日报自动刷新）</footer>'
            f'</div><script src="usage-data.js"></script>{anchor}{JS}</body></html>')


def main():
    args = sys.argv[1:]
    cfg_path_hint = None
    if "--config" in args:
        from paths import load_config as portable_load_config
        cfg = portable_load_config(args[args.index("--config") + 1])
        out, name = cfg["out_dir"], cfg.get("name", "backend")
        cfg_path_hint = cfg.get("config_path")
    elif "--out-dir" in args:
        out = args[args.index("--out-dir") + 1]
        name = args[args.index("--name") + 1] if "--name" in args else "backend"
    else:
        sys.exit("usage: html_report.py --out-dir DIR [--name LABEL]  (--day/--all accepted, ignored)")
    by_day = load_all(out)
    days = sorted(by_day)
    if not days:
        sys.exit("no requests-*.jsonl records found")
    nd = days[-1]
    # 配置单里的 key（config.json → key_labels 的值），让下拉在账本还没截到该 key 记录时也可预选
    keys_cfg = []
    cfg_path = cfg_path_hint or os.path.join(out, "config.json")
    if os.path.exists(cfg_path):
        try:
            _cfg = json.load(open(cfg_path, encoding="utf-8"))
            keys_cfg = list((_cfg.get("key_labels") or {}).values())
        except Exception:
            pass
    sz = write_sidecar(out, by_day, days)
    with open(os.path.join(out, "usage-report.html"), "w", encoding="utf-8") as f:
        f.write(page(f"Token 账本 {nd}", name, unified_body(nd, by_day, name, keys_cfg), nd))
    print(f"wrote usage-report.html (anchor {nd} · {len(days)} days · sidecar {sz // 1024} KiB)")
    # retired artefacts: per-day snapshot pages and the old summary page
    removed = 0
    for p in glob.glob(os.path.join(out, "usage-report-*.html")):
        os.remove(p)
        removed += 1
    legacy = os.path.join(out, "usage-summary.html")
    if os.path.exists(legacy):
        os.remove(legacy)
        removed += 1
    if removed:
        print(f"removed {removed} retired snapshot pages")


if __name__ == "__main__":
    main()
