# 网关日报补排队闸拦截三指标（rev13）— 施工票

## 票头（登记区）

- 票 ID：`2026-11-19-ledger-gate-daily-stats`
- 票名：网关日报补排队闸拦截三指标（rev13）
- 票型：功能新增（施工票通道；票种效力＝改动授权（候裁＝H-1 一项，放行＝H-1 随票默认处置生效），不承载终局判定）
- 起草席位／修票权席位：架构席
- 开端读数：ANCHOR＝`f7758646988f3403c6ba01c666238c3b87a21620`（本席当轮实跑 `git -C D:\Projects\strata-ledger-proxy rev-parse HEAD` ＝ 该值，main＝rev12 完工头；`git status --short` ＝ 仅 `?? .scratch/`）
- 决策输入件（唯一口径真源，票面不得重开人类已裁口径）：
  1. **本票效力来源**＝人类 00:19 逐字原件＋B1 登记：`D:\Strata\.workbuddy\collab\input\2026-11-19-0019-gate-daily-stats-verbatim.md`——「网关日报需要补充报告当前拦截入栈次数，拦截请求的最长等待时间和平均等待时间」。主理人备注（非原文，同件在册）＝已路由架构席起草 rev13（三指标＝queued 计数、waited_ms max/mean）；在岗脑仍 rev11a，换脑一次性自动任务排 2026-11-19 03:00。
  2. 被承接件：rev12 票（`D:\Strata\.workbuddy\collab\tickets\rev12-gate-log-ticket.md`——gate-events 三行闭集＋红线六＝本票数据源本体，完工 HEAD＝f775864；其④明示「日报消费 gate-events＝另票后置」，本票即该后置票）；rev10/rev10a/rev11/rev11a（闸本体与跟随链）。全部 append-only 不回改。
- 架构席起草实核（本席当轮实跑，读数在册）：
  - 三套回归基线：`python selftest_proxy.py`＝**45/45 PASS**、`grep -c '^PASS  gate:'`＝**23**；`selftest_monitor.py`＝**54/54**；`selftest_watchdog.py`＝**16 passed 0 failed**。
  - `git show b9d2c77:daily_report.py` 与 `git show f775864:daily_report.py` **cmp 字节一致**＝daily_report.py 自 rev11a 起零触碰（rev12 未消费 gate-events，与其④登记吻合）。
  - 在岗数据面实核（`D:\Strata-toolkit\strata-ledger-proxy\data\`）：`requests-2026-11-16.jsonl` 含 `queue_wait_ms` 行＝**0**；`11-17`＝**3**；`11-18`＝**226**；`11-19`＝**31**；`gate-events-*` 文件＝**零枚**（在岗脑 rev11a 不产闸事件→11-18 及以前逐请求闸数据不可恢复，日报需标注缺口口径，禁编造）。
  - 母本仓 `data/` 无既有日报文件；`daily_report.py` 现体＝250 行、四节（总览 83／覆盖窗口 133／按小时分布 148／数据精度说明 158）。
- 前置票：rev10、rev10a、rev11、rev11a、rev12（完工 HEAD＝f775864）
- 候裁点：**H-1 一项**（补充观察列去留——路由件明示「决策者可裁减」＝决策者保留闸，列 H；默认随票生效，见候裁单列）
- Agent 适配度：内部票·适配度不适用
- 修订记录：**v2**（rev13 回流改票：R-1 阻断修一处（③-7 正则收窄·采 (a)）＋QA 黄项 Y-1/Y-2/Y-3/Y-4/Y-8 随票注记，改动面逐条见「修票记录」节；除此之外票面零改动；票未放行、零施工；母本仓除本票文件外零触碰）

### 修票记录（v2·回流改票·修票权＝架构席）

QA 独立审计＝不放行，阻断 R-1 一项＋黄项随票登记。本轮改动面逐条（禁夹带声明：以下之外票面零改动；代码面、在岗机、五前置票零触碰）：

1. **R-1（阻断）·拍板采 (a) 正则收窄**：③-7 幂等零触碰机检正则 `'(skip|force|pending)'`→`'(skip|force=|pending)'`。归因：②-3 G-0 写死代码体含局部量 `forced` 两行（本票 128/130 行面），`force` 子串必命中＝照抄代码体则③-7 恒红（QA 探针读数 2≠0）。不采 (b) 改名的理由：`forced` 改名须同步代码体＋②-4 F-A fixture＋断言文案多面；且 fixture 事件键 `forced` 系 rev12 数据面既有闭集字段名不可改，改名只遮蔽不清除歧义。(a) 后 do_day 的 `force=` 赋值/签名行仍在射程，幂等零触碰判别力保留；②-3 代码体写死纪律保住、零改动。G-0 命名警示处附注在册。
2. **Y-1**：G-1 锚点「141 行 `out.append("")`」修正＝实测 **140 行**（141 行为空行，`hist = {}` 仍 142 行，挂点语义不变）；可施工性判定节锚点同步。
3. **Y-2**：③-1 对 untracked 新文件盲区＝③ 节回执要求补 `git status --short` 空面读数程序（登记入③-1）。
4. **Y-3**：C1 文案补「按生成时刻 config 现值判定，回填历史日时该判定可能失真」诚实标注（与 C2 同族）；②-4 互斥断言 scan 面钉死为判别字面集（两态共有的诚实标注不参与互斥）。
5. **Y-4**：②-4 F-A fixture seq=99 行 JSON 片段补全缺失的开引号。
6. **Y-8**：废弃断言 D 号引用（票内 D 号引用与 ②-4 断言列表序多处错位），**效力以断言名为准**，票内全部引用处改按断言名；②-5 登记面条目改「登-1/登-2/登-3」避免与断言名混淆。

### 准入四判据自查（票面自证）

1. **无 API 变更**：对外 HTTP 面零改动；`/ext.json` 零触碰；`requests-*.jsonl` 与 `gate-events-*.jsonl` 两文件面格式零改动（本票只读不写）；`collector_proxy.py` 本 rev **零改动**（数据源 rev12 已就绪，路由件⑥）。
2. **口径已裁**：三指标定义＝人类 00:19 已裁；「按文件日归属＋如实标注跨日」＝路由件裁定方向；两态（闸开零事件 vs 闸未启用）禁混淆＝路由件已裁；其余（态判别证据、回填口径、文案措辞、节落位、测试形态、gate off 判定证据链）＝装配细节，票裁 A-1～A-8 决毕，不上楼。
3. **可机械验收**：③节全部判据＝命令＋期望读数（闭集核验、diff 删除行＝0 纯增量核验、新测试套逐名读数、三套既有回归逐套报数零触碰、幂等两跑读数、隐私 scan grep）。
4. **不触真源**：五票 append-only 不回改；在岗机 `D:\Strata-toolkit\` 零触碰；引擎侧零触碰；`collector_proxy.py`/requests 账本格式零改动（路由件⑥）。

---

## 票体四字段（自包含）

### ① 目标

日报 `usage-report-YYYY-MM-DD.md` 新增一节 **`## 排队闸拦截统计`**（落位＝「覆盖窗口」之后、「按小时分布」之前），报告三指标：

- **拦截入栈次数**＝当日 `gate-events-<day>.jsonl` 中 `event=="queued"` 行数；
- **最长等待／平均等待**＝当日 `event=="released"` 行 `waited_ms` 的 **max／mean**（单位 ms，展示附人类可读秒）。

补充观察列（H-1）：released 总数、forced 强制放行数、heartbeats 合计——供观察账（攒一周 queue_wait/inflight 数据）用。

四态状态机（②-3 G-0 写死，两态禁混淆）：
- **A 有当日事件文件**→三指标＋补充列数值＋跨日口径标注（含「自前日跨入」计数）；
- **B 无事件文件但当日总账有 `queue_wait_ms` 行**→**回填口径**（从总账 `queue_wait_ms` 派生三指标＋显式标注非逐事件日志、逐事件数据不可恢复）；
- **C1 无文件无佐证且生成时刻 config 静态关闸**→「闸未启用」文案（含「按生成时刻 config 判定、回填历史日时该判定可能失真」诚实标注，与 C2 同族，v2·Y-3），不出闸统计数字；
- **C2 无文件无佐证且生成时刻 config 开闸（含 gate_follow）**→三指标显示 **0／—**＋口径注（按生成时刻 config 判定；回填历史日时该判定可能失真——如实标注，不外推）。

改动纪律＝`daily_report.py` **纯插入**（diff 对既有行的删除/修改＝0）；幂等性保持（已有日报 skip、`--day` 强制重跑可回填 gate-events 存在的那些天）；新增独立测试套 `selftest_daily_report.py`（纯标准库、fixture 驱动、无网络、不起服务）断言 A/B/C1/C2 四态＋跨日标注＋回填口径＋幂等＋隐私 scan＋节位共 **≥14 名**。**换脑依赖声明（路由件⑧）**：rev13 上线**不依赖** rev12 换脑完成——A/C1/C2（及 B 用 fixture 总账）验收全部可在测试环境做；生产闸数据产出依赖今晨 03:00 换脑自动任务（票外观察面，不入验收）。完工终态＝③节判据逐条读数达标＋四套回归全绿（既有 proxy 45/45、monitor 54/54、watchdog 16/0 零触碰原样通过＋新套 ≥14/全绿）。

### ② 规格

#### ②-0 红线纪律（一票到底，违一条即整票判红）

- **红线一（既有节口径零改动）**：`daily_report.py` 改动全部为插入，**既有行零修改零删除**（机检③-2：`git diff f775864 -- daily_report.py | grep -c '^-[^-]'` ＝ **0**）。总览/覆盖窗口/按小时分布/数据精度说明四节输出逐字节不变（行为证＝新断言 `report:no existing sections altered` 既有关键行在场断言＋三套回归；v2·Y-8 断言名引用）。
- **红线二（数据源零触碰）**：`collector_proxy.py` 零改动（机检③-4 diff 行＝0）；`requests-*.jsonl`、`gate-events-*.jsonl` 两面只读不改格式；Gate/Recorder/闸核心不在本票域。
- **红线三（缺省零回归）**：既有三套测试文件零触碰原样通过——proxy **45/45**（N 不增不减，新断言全在新文件）、monitor **54/54**、watchdog **16/0**（机检③-5）；静态闸关日报出 C1 文案、不读不建任何闸事件文件（新断言 `report:C1 gate-off wording` 承载；v2·Y-8 断言名引用）。
- **红线四（隐私面）**：闸统计节只输出**聚合计数与统计量**（次数/max/mean/forced 计数/心跳合计），**不逐请求列出**、无 key/fp/route/model 明细、无请求体内容——机检③-6＋新断言 `report:privacy no per-request fields` scan（v2·Y-8 断言名引用）。
- **红线五（禁编造）**：任何态不得输出无证据的数字：A 态数字只来自当日事件文件；B 态只来自当日总账 `queue_wait_ms` 行且带回填标注；C1/C2 只出文案或 0／—。缺数据＝标注缺口，不外推、不回补。

#### ②-1 声明闭集（本票唯一可写仓内面）

```
daily_report.py
selftest_daily_report.py   (新建)
bootstrap.py
README.md
MANIFEST.md
CHANGELOG.md
tickets/rev13-gate-daily-stats-ticket.md   (本票本体，登记面，不计施工验收面)
```

`collector_proxy.py`、`selftest_proxy.py`、`selftest_monitor.py`、`selftest_watchdog.py`、`monitor_ext.py`/`monitor.js`/`monitor.html`/`monitor.css`/`monitor-sprite.svg`/`ext.js`、`html_report.py`、`ledger_watchdog.py`、`switch_proxy.py`、`paths.py`、`config.template.json`、`config-examples/**`、`docs/**`、`data/**`、`legacy/**`、`service-examples/**`：不入闭集零触碰。`config.template.json` 零新键（无开关——闸开才有事件文件，日报按文件证据＋config 现值判态；加键＝加死面，沿 rev12 A-6 同判）。

#### ②-2 禁动面（零触碰清单）

- `daily_report.py` 既有行全部禁动（红线一）：`load_config`/`log`/`load_day`/`pct`/`build_report` 各函数体既有行、`build_report(day, rows, cfg)` **签名不变**（闸数据由函数体内自读 `cfg["out_dir"]`，不加参——加参即改行即违红线一）、`flag_pending`/`do_day`/`mark_reported`/`all_days`/`run_daily`/`main` 全部零改动（幂等/skip/`--day`/`--all`/`--reported`/pending 机制原样，路由件⑤回填能力靠既有 `--day` 零改动承载）。
- `collector_proxy.py`：零改动（含 `Recorder`、`Gate`、`_gate_params`、日报线程 `_fire_daily`/`run_daily` 调用面——`run_daily(cfg)` 签名不变即无波及）。
- `selftest_proxy.py`/`selftest_monitor.py`/`selftest_watchdog.py`：零触碰（机检③-5）。
- `html_report.py`：零触碰（网页报表消费闸数据＝另票后置，④登记）。
- 引擎侧任何文件（`D:\Strata\serve\`、启动配置 json）、在岗 `D:\Strata-toolkit\`：零触碰。
- rev10/rev10a/rev11/rev11a/rev12 五票本体＋勘误件：append-only 不回改。

#### ②-3 daily_report.py 逐条施工规格（G＝新增插入；行号＝f775864 实读锚点；代码体写死，全部纯插入）

**命名警示（施工席必读）**：`build_report` 体内局部量 `out`＝输出行 list（现体 79 行）——闸数据目录一律取 `cfg["out_dir"]`，**禁复用 `out` 名**（撞既有行违红线一）。**v2·R-1 附注**：G-0 代码体局部量 `forced` 名保留不改（事件键 `forced`＝rev12 数据面既有闭集字段名）；③-7 幂等机检正则已同步收窄为 `force=`（见③-7 v2 注），施工席**不得**为避正则自行改名——代码体以本节写死体逐字转录为准。

**G-0 helper 两枚（现体 `pct()` 尾 63 行后、`def build_report` 前插入）**：

```python
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
```

**G-1 挂点（现体 140 行 `out.append("")`（覆盖窗口节尾）与 142 行 `hist = {}` 之间插入，两行；v2·Y-1 修正：锚点实测 140 行，141 行为空行，挂点语义不变——插在 140 行之后、141 空行之前或之后均可，以 140 行尾/142 行首为锚）**：

```python
    out.extend(gate_section(cfg["out_dir"], day, req, cfg))
    out.append("")
```

（节位＝「覆盖窗口」后、「按小时分布」前；`req`＝现体 67 行既有过滤产物，B 态复用之，零新过滤行。闸事件不参与任何既有节计算——`rows`/`req`/`events` 口径零触碰。）

#### ②-4 selftest_daily_report.py 逐条施工规格（新建文件，纯标准库，fixture 驱动，无网络、不起服务）

骨架写死：tempfile 建盒→按态写 fixture 文件→`import daily_report` 直调 `build_report(day, rows, cfg)`＋`do_day(cfg, day)`→`rec(name, cond, detail)` 收集→末行打印 `N/N PASS` 并以失败数作退出码。fixture 口径写死：

- **F-A 样例事件文件**（三事件族齐＋跨日）：`gate-events-2026-01-02.jsonl` 写 `{"ts":"2026-01-02 10:00:00","event":"admitted","seq":0,...}`＋queued seq=1 waited 无＋released `{"event":"released","seq":1,"waited_ms":1500,"heartbeats":2,"forced":false}`＋released **seq=99（无本文件 queued＝自前日跨入）** `{"event":"released","seq":99,"waited_ms":500,"heartbeats":0,"forced":true}`（v2·Y-4 补全原片段缺失的开引号与键头）；当日总账 fixture 写 ≥1 条请求行（带 ts）。
- **F-B**：仅总账文件，三行 `queue_wait_ms`＝100/300/600，无 gate-events 文件，config `max_inflight:2`。
- **F-C1**：仅总账（无 queue_wait_ms 行），config `max_inflight:0` 且无 `gate_follow`。
- **F-C2**：仅总账（无 queue_wait_ms 行），config `max_inflight:2`。

断言（名称逐字，全部 `report:` 前缀，**N ≥ 14**。**v2·Y-8 效力声明：断言效力以断言名为准；票内旧 D 号引用全部废弃（v1 中 D 号与列表序多处错位），引用处已改按断言名**）：
- `report:gate section present between windows and hours`＝节标题在场且位于「## 覆盖窗口」之后、「## 按小时分布」之前（index 比较）。
- `report:A queued count matches file`＝A 态输出含 `拦截入栈（queued） | 1 回`。
- `report:A max wait ms and seconds`＝含 `最长等待（released.max） | 1,500 ms（1.5 s）`。
- `report:A mean wait ms and seconds`＝mean＝(1500+500)/2＝1000 → 含 `平均等待（released.mean） | 1,000 ms（1.0 s）`。
- `report:A cross-day note counts incoming waits`＝含 `1 项等待自前日跨入`（seq=99 计数）。
- `report:A released forced and heartbeats columns`＝含 `强制放行 1` 与 `心跳合计 2`（H-1 列，去留随 H-1；H-1 裁撤则此名随之作废＝走回流件改票，不在施工期自删）。
- `report:B backfill label present`＝B 态含 `回填口径` 字面。
- `report:B three metrics from queue_wait_ms`＝含 `3 回`、`600 ms（0.6 s）`、mean 333 → `333 ms（0.3 s）`。
- `report:C1 gate-off wording`＝C1 态含 `闸未启用` 且**不含** `拦截入栈`。
- `report:C2 open-gate zero metrics wording`＝C2 态含 `| 拦截入栈（queued） | 0 |` 与 `—`，且不含 `闸未启用`（两态禁混淆互斥断言）。
- `report:C1 and C2 wordings are mutually exclusive`＝C1 输出无 C2 口径注、C2 输出无 C1 文案（双向 scan）。**v2·Y-3 注（scan 面钉死为判别字面集）**：两态现共有诚实标注字面「按**日报生成时刻** config 现值，回填历史日时该判定可能失真」（同族诚实标注，不参与互斥）。判别字面集＝C1 侧 `闸未启用`（C2 输出须不含）；C2 侧 `开闸（含 gate_follow 跟随态）但当日无` 与表行 `| 拦截入栈（queued） | 0 |`（C1 输出须不含）。
- `report:privacy no per-request fields`＝四态闸统计节文本 scan 无 `"fp"`/`"key"`/`route`/`model` 明细与请求体字段字样（只聚合行）。
- `report:idempotent second run skips`＝A fixture 下 `do_day` 首跑 True、二跑 False（既有 skip 纪律不变）。
- `report:day force rerun rebuilds`＝`--day` 语义（`do_day(force=True)`）对已存在日报仍重写 True（回填历史能力在场）。
- `report:no existing sections altered`＝A 态全文含 `## 总览`/`## 覆盖窗口`/`## 按小时分布`/`## 数据精度说明` 四标题且顺序不变（红线一行为证）。

收尾纪律：每态盒用完即弃；不写仓内 `data/`；断言读数并入 RESULTS 逐名打印。

#### ②-5 登记面

- **登-1 README.md**（v2·Y-8：原编号 D-1 废弃，登记面与断言名分流）：日报文件说明段（157 行区 `usage-report-YYYY-MM-DD.md` 条目）补一句闸统计节口径（三指标＋跨日口径＋「闸未启用/开闸零事件」两态措辞）；含字面 `排队闸拦截统计` ≥1。
- **登-2 MANIFEST.md**（v2·Y-8：原编号 D-2 废弃）：第二节 `daily_report.py` 行补 rev13 改动摘要（新增 gate_section 四态口径）；新行登记 `selftest_daily_report.py`。
- **登-3 CHANGELOG.md**（v2·Y-8：原编号 D-3 废弃）：新增 rev13 节（倒序置顶），含人类 00:19 需求字面引用＋四态口径＋「在岗 11-18 及以前逐请求闸数据不可恢复→回填口径」登记。

### ③ 验收标准（全机械可判：命令＋期望读数）

> 母本仓根跑，基线＝`f775864`；回执逐条附命令原文与读数。基线对照（架构席当轮实跑在册）：proxy 45/45（gate 23）、monitor 54/54、watchdog 16/0；`git diff b9d2c77 f775864 -- daily_report.py` 空。

1. **闭集核验**：`git diff --name-only f775864 | grep -vE '^(daily_report\.py|selftest_daily_report\.py|bootstrap\.py|README\.md|MANIFEST\.md|CHANGELOG\.md|tickets/rev13-gate-daily-stats-ticket\.md)$' | wc -l` ＝ **0**。
   - **补盲读数（Y-2·回执必附）**：`git diff --name-only` 对 untracked 新文件为盲区，故回执另附 `git status --short` 原文读数——除已登记面外须空面：允许项仅 `?? tickets/rev13-gate-daily-stats-ticket.md`（本票本体，已在闭集）与临时工作物 `?? .scratch/2026-11-19-ledger-gate-daily-stats/`（完工 commit 前须清零残留，见④）；出现任何其它 `??`／`M`／`D` 行＝闭集外写入，判红。
2. **纯增量核验（红线一）**：`git diff f775864 -- daily_report.py | grep -c '^-[^-]'` ＝ **0**（删除/修改既有行＝0）；`git diff --numstat f775864 -- daily_report.py` 删除列＝**0**。
3. **新测试套**：`python selftest_daily_report.py` 退出码 **0**、末行 **N/N PASS 且 N ≥ 14**；②-4 全部断言名逐名 PASS（回执贴全输出）。
4. **数据源零改动（红线二）**：`git diff f775864 -- collector_proxy.py | wc -l` ＝ **0**；`git diff f775864 -- selftest_proxy.py | wc -l` ＝ **0**。
5. **三套既有回归逐套报数（红线三）**：`python selftest_proxy.py` 退出码 0 且 **45/45**、`grep -c '^PASS  gate:'` ＝ **23**（不增不减）；`selftest_monitor.py` **54/54**；`selftest_watchdog.py` **16 passed 0 failed**；`git diff --name-only f775864 | grep -cE 'selftest_(proxy|monitor|watchdog)\.py'` ＝ **0**。
6. **隐私面（红线四）**：`python - <<'EOF'` 跑 F-A fixture 出节后 `grep -cE '(fp|key_labels|messages|prompt)' <节文本>` ＝ **0**（或等效：`report:privacy no per-request fields` 断言 PASS＋回执贴节全文，人工可核只有聚合行；v2·Y-8 断言名引用）。
7. **幂等与回填（路由件⑤）**：fixture 盒内连跑两次 `do_day` 读数 True→False；`--day` 强制路径仍重写（`report:idempotent second run skips`／`report:day force rerun rebuilds` 断言承载；v2·Y-8 断言名引用）；`git diff f775864 -- daily_report.py | grep -cE '^[-+].*(skip|force=|pending)'` ＝ **0**（幂等机制行零触碰）。**v2 注（R-1）**：正则已由 `force` 收窄为 `force=`——do_day 的 force 赋值/参数行（`force=True` 等）仍在射程；②-3 G-0 写死代码体的局部量 `forced` 行不再误命中（QA 探针实证旧正则恒红＝2≠0）。
8. **bootstrap 登记**：`grep -c 'selftest_daily_report.py' bootstrap.py` ≥ **1**（新测试文件入 REQUIRED 清单；只增一行，bootstrap 其余零改）。
9. **登记面**：`grep -c '排队闸拦截统计' README.md` ≥1；CHANGELOG rev13 节含 `00:19` 字面 ≥1＋`回填口径` ≥1；MANIFEST 含 `selftest_daily_report` ≥1。

### ④ 边界约束

- **票间关系**：前置＝rev12（数据源本体）；本票＝rev12 票④预留的「日报消费」后置票。**上线不依赖换脑**（路由件⑧）：本票完工即可合母本仓；在岗生效＝随下次换脑/部署（主理人排窗，不入本票验收）。**后置另票**：网页报表 `html_report.py` 消费 gate-events、监视页闸统计、观察账攒周报表＝均不在本票。在岗实跑观察（换脑后 gate-events 出现→日报 A 态实见）＝票外面。
- **同源与引用纪律**：口径真源＝00:19 逐字件；三指标定义不得走样（「拦截入栈次数」≠released 数、「平均等待」≠queue_wait_ms 与总账 gen_ms 混算）；跨日归属＝文件日＋标注，禁改成按 queued 日回配（那需要跨文件 join＋seq 全局性假设，路由件未裁、YAGNI）；工程师席不得据票外记忆补设计，疑义走回流件。
- **施工面纪律**：母本仓开分支/工作树，基线＝`f775864`；临时工作物只落仓根 `.scratch/2026-11-19-ledger-gate-daily-stats/`，完工 commit 前自查 `.scratch/` 零残留；禁磁盘根裸路径/宿主 Temp/仓外自建目录。
- **交付与 commit 纪律**：单一工程师席新鲜实例、票间串行、同席禁多实例；完工 commit 前回执先行，落 `D:\Strata\.workbuddy\collab\receipts\2026-11-19-ledger-gate-daily-stats-receipt.md`：开端 HEAD＋写入清单＋③逐条读数（含②-4 全断言原始输出＋四态节全文样张）＋`.scratch/` 自查。
- **票放行**＝主理人程序确认（H-1 默认处置随放行生效）。

## 租约段（票内·经架构签注由 B2 lease-issuer 实例化）

- path_globs：`daily_report.py`、`selftest_daily_report.py`、`bootstrap.py`、`README.md`、`MANIFEST.md`、`CHANGELOG.md`、`tickets/rev13-gate-daily-stats-ticket.md`
- deny_globs：`collector_proxy.py`、`selftest_proxy.py`、`selftest_monitor.py`、`selftest_watchdog.py`、`monitor_ext.py`、`monitor.js`、`monitor.html`、`monitor.css`、`monitor-sprite.svg`、`ext.js`、`html_report.py`、`ledger_watchdog.py`、`switch_proxy.py`、`paths.py`、`config.template.json`、`config.json`、`config-examples/**`、`docs/**`、`data/**`、`legacy/**`、`service-examples/**`、`.scratch/**`、`D:\Strata-toolkit\**`、`D:\Strata\**`
- 灰度判据（票内声明字段·decision-pack 读取）：四套回归退出码全 0＋③-2 删除行＝0＋新套 N≥14 全绿；三态 fixture（A/C1/C2）逐名 PASS——测试环境判据，不依赖在岗换脑。
- 席位 ID／票 ID／哈希：由状态机签发，非人工填写

## 票裁已决（A-1～A-8·起草席决；推翻走回流件）

- **A-1｜跨日归属＝按文件日，不做跨文件 join**。理由：Recorder 按 ts 路由（`Recorder.write` 现体 118 行），released 天然落释放日文件；跨日回配需读前日文件＋依赖 `_seq` 日切连续性假设（`Gate._seq` 跨日不重置＝内存态，日界处无对账锚），扩面违 YAGNI 且路由件明裁「按文件日归属＋如实标注」。`cross` 计数口径＝当日 released 行 seq ∉ 当日 queued 行 seq 集＝「自前日跨入」下界估计（同日 seq 复用碰撞不存在——`_seq` 进程内单调）；如实标注为「窗口内 N 项等待自前日跨入」。
- **A-2｜闸关 vs 开闸零事件两态判别证据＝当日文件证据 → 当日总账 queue_wait_ms 佐证 → 生成时刻 config 现值，三级顺序**。理由：`_gate_params` 的跟随链（读引擎启动配置）在 collector 域，日报复制之＝违红线二＋真源二处；config 静态两键（`max_inflight`/`gate_follow`）是日报可达的最强证据，判别力＝C1（静态关闸，确证「闸未启用」）vs C2（config 开闸/跟随态，只能出 0/—＋失真标注）。C2 文案明写「按生成时刻 config 判定，回填历史日可能失真」＝诚实边界，不假称知道当刻闸态。
- **A-3｜B 态回填口径＝保留**。理由：路由件「11-18 及以前逐请求闸数据不可恢复（禁编造）＋标注缺口」——但总账 `queue_wait_ms`（rev10 既存、在岗 11-18 有 226 行）恰是同量回填源（rev12 A-4 明示双写互证关系）。禁编造≠禁回填：**回填＝有同源字段证据＋显式标注非权威事件日志口径**；编造＝无证据外推。无 B 态则 11-18 日报三指标只能空着，观察账断档。回填口径只出三指标不出补充列（无 heartbeats/forced 数据可回填）。
- **A-4｜节落位＝「覆盖窗口」后、「按小时分布」前**。理由：闸统计属「当天发生了什么」叙事族，与覆盖窗口同源时间轴；插总览内＝动既有大表风险面；置末精度说明后＝统计节被说明压底。纯插入两行（G-1），零既有行触碰。
- **A-5｜补充列形态＝一行三列合并（放行 N 回（强制放行 f／心跳 b））**。理由：H-1 若裁撤＝删一行，改动面最小；观察账需要 released 分母才能算 forced 率/心跳率，与三指标同表可比。承载断言 `report:A released forced and heartbeats columns` 随 H-1 联动（见候裁单列；v2·Y-8 断言名引用）。
- **A-6｜新测试套独立成文件 `selftest_daily_report.py`，不入 selftest_proxy**。理由：proxy 套＝真 stub 服务＋网络＋计时（重、有 flake 面），日报套＝纯函数＋fixture（秒级、无端口）；混入违「闸关零回归」既有 45 断言冻结面（红线三要求 proxy 套 N 不减不增）。新文件入 bootstrap REQUIRED（③-8），与既有四套同族。
- **A-7｜`--day` 回填能力＝零新代码，靠既有 force 路径**。理由：路由件⑤「`--day` 强制重跑可回填历史」——现体 `do_day(force=True)` 已满足（184-186 行 skip 仅非 force 生效），本票只需断言承载（`report:idempotent second run skips`／`report:day force rerun rebuilds`；v2·Y-8 断言名引用），零实现面。幂等三态（skip/重写/pending）零触碰＝③-7 机检。
- **A-8｜统计口径细节写死**：mean＝`sum(waits)/len(waits)`（released 行等权，非按请求加权——被拦请求一次 released）；单位 ms 取整展示＋秒括号一位小数；`waited_ms` 非数值行跳过＋`heartbeats` 缺省按 0（对 rev12 闭集是冗余防御，对损坏行不炸日报）；`admitted` 行不参与三指标（它不是拦截）但**文件在场即 A 态证据**（闸开零拦截日＝有 admitted 行无 queued/released → 拦截 0／max—／mean—，恰是「闸开但零事件→0/—」的正确读数路径之一）。

## 候裁单列（H-x·起草席不自行拍）

- **H-1｜补充观察列去留**（released 总数、forced 强制放行数、heartbeats 合计，落位见 A-5）——路由件明示「补充列（决策者可裁减）」＝决策者保留闸，列 H。默认处置＝**保留**（观察账攒一周 queue_wait/inflight 数据需要 released 分母与 forced 计数；数据已全在 released 行，零采集成本）。若决策者裁撤＝删 A-5 行＋断言 `report:A released forced and heartbeats columns` 作废，走回流件改票一处，不伤三指标本体（v2·Y-8 断言名引用）。真冲突核：三指标本体＝00:19 已裁不入 H；跨日标注/B 态回填/两态文案＝改真源口径类才列 H，然路由件已明裁方向（②③⑧条）＝无对立未收敛，不列；残余（在岗换脑时点、html 报表消费）归④后置，不上楼。

## 健康账登记（回流素材）

1. **缺口口径先于功能可见（供 sops 立账，本票不代立）**：rev12 事件日志闭链但换脑未执行＝数据面空转两天；本票验收被迫三态 fixture 化（A 态用造数据）——「代码就绪≠数据在场」两态需在 SOP 换脑环节立可见状态（换脑完成回执），否则日报类需求天然带 B 态尾巴。
2. **回填口径与权威口径的边界话术（素材）**：B 态＝同源字段＋显式降级标注；红线五「禁编造」的可操作定义＝有无同源证据＋有无标注，本票 A-3 落判据，供后续同类「历史数据缺日志但账本有影子字段」案复用。

## 可施工性判定（架构席自评）

- 全部挂点在 `f775864` 实测存在：`daily_report.py` 250 行实读锚点——`pct()` 尾 63／`build_report` 定义 66／`req` 过滤 67／`out = []` 79／覆盖窗口节尾 `out.append("")` **140**（v2·Y-1 实测修正，141 为空行）／`hist = {}` 142／`do_day` 幂等 184-186／`--day` force 242-245；`Recorder.write` ts 路由 118 行（跨日归属证据）；bootstrap REQUIRED 30-36 行。
- 基线实跑读数在册：proxy 45/45（gate 23）、monitor 54/54、watchdog 16/0；`daily_report.py` rev11a 起零触碰（cmp 实证）；在岗四日 `queue_wait_ms` 行计数 0/3/226/31、gate-events 零枚（B/C 态现实分布证据）。
- 判别力自评（v2·Y-8：断言引用改按名，旧 D 号引用废弃）：③-2 对「顺手改既有节」判红；`report:gate section present between windows and hours`／`report:no existing sections altered` 对「节位错／既有序被打乱」判红；`report:A queued count matches file`／`report:A max wait ms and seconds`／`report:A mean wait ms and seconds`／`report:B three metrics from queue_wait_ms` 对「指标算错（max/mean/计数）」判红；`report:A cross-day note counts incoming waits` 对「跨日标注缺失或计数错」判红；`report:C1 gate-off wording`／`report:C2 open-gate zero metrics wording`／`report:C1 and C2 wordings are mutually exclusive` 对「两态文案混淆」判红（互斥双向 scan）；`report:privacy no per-request fields` 对「逐请求明细泄露」判红；`report:idempotent second run skips`／`report:day force rerun rebuilds` 对「幂等破坏／回填能力丢」判红；`report:A released forced and heartbeats columns` 对「补充列缺失」判红；③-4 对「动 collector」判红；③-5 对「改既有测试套凑数」判红；③-1 补盲读数（Y-2）对「untracked 新文件绕闭集」判红。
- 未实跑面（留施工/QA）：②-3 写死代码体的正式转录预跑与②-4 断言体首跑（本票锚点为实码行号＋语义等价推演）；在岗实跑 A 态实见（④后置）。判定＝**可施工**，无阻塞点；候裁仅 H-1 一项且不阻塞装配。

—— 架构席 · rev13 v2（回流改票轮） · 开端 HEAD 实测 `f7758646988f3403c6ba01c666238c3b87a21620`（git -C D:\Projects\strata-ledger-proxy rev-parse HEAD）· 2026-11-19 · 起草实核居治理族 `D:\Strata\.workbuddy\collab\`（本票文件本体落仓根 `tickets/`，路由件指定）
