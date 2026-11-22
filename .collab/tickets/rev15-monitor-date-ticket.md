# 监视器汇总行起始时刻补实际年月日期（rev15）— 施工票

## 票头（登记区）

- 票 ID：`2026-11-19-ledger-monitor-date`
- 票名：监视器汇总行起始时刻补实际年月日期（rev15）
- 票型：轻量维护（显示格式，无 API 变更；施工票通道；票种效力＝改动授权；**候裁＝零**）
- 起草席位／修票权席位：架构席
- 开端读数：ANCHOR＝`d54146db0cf970dd3817b486f185b25979636197`（本席当轮实跑 `git -C D:\Projects\strata-ledger-proxy rev-parse HEAD` ＝ 该值，main＝rev14 票 v1 投递头；`git status --short` ＝ ` M monitor.js / M selftest_monitor.py / M tickets/rev14-*.md（本席 v2 修票在途）/ ?? .scratch/`）。**在途面登记（实读 git diff 在册）**：`M monitor.js`＋`M selftest_monitor.py`＝未提交维护改动两族——①「网关闸排队并入顶部状态卡」（人类 2026-11-19 口径直改）；②**汇总行日期改动先行版**：655→657 行 sinceStr 已改 `toLocaleString([], { year:"numeric", month:"2-digit", day:"2-digit", hour:"2-digit", minute:"2-digit" })`（locale 化形态——显示读数随浏览器 locale 变，smoke 不可逐字锁，见 A-1；且无对应断言新增）。**rev15 施工基线＝在途面落 commit 之后**（主理人先行提交），rev15＝在②先行版基础上收严为可锁写死格式＋补断言；票内锚点按在途树轨写死（见②-3）。`M tickets/rev14`＝rev14 v2 修票面（本席），与本票零文件交集。
- 决策输入件（唯一口径真源）：
  1. **本票效力来源**＝人类 11:32 逐字原件＋B1 登记：`D:\Strata\.workbuddy\collab\input\2026-11-19-1132-monitor-date-verbatim.md`（本票实读引用）——「当前的 web 监视器这条汇总很好：自 周二00:21：4,322 个请求 · 读取输入 91,628,949 tokens · 3,895 t/s（复用 287,063,619）· 输出 7,734,630 tokens · 86.7 t/s 但是有个问题，"周二"无法确认是本周二还是上周二，我认为至少应该（实际年月日期）」。主理人路由注记（同件在册）＝指向 monitor 汇总行 `req-totals` 起始时刻显示；诉求＝至少显示实际年月日期；轻量维护级；基线 54/54。
  2. 路由判定件（主理人 INTK-0010 路由令）：monitor 显示面与 rev14（collector_proxy 闸域）、rev13（daily_report 域）领地不相交；一票一问题＝另开 rev15，施工排 rev13 验收闭后按交付面串行纪律（**rev13 已闭**＝完工码头 268b7a8 在册，排程前置满足）。
- 架构席起草实核（本席当轮实跑/实读）：
  - monitor 套基线：`python selftest_monitor.py`＝**54/54 PASS**（ANCHOR 与在途树两次实跑均 54/54＝在途排队改动未动计数）；node v22.22.2 在场（smoke 真跑可判）。
  - 指向代码实核（双轨锚点）：`monitor.js` 汇总行＝ANCHOR 版 655 行 `const sinceStr = new Date(t.since * 1000).toLocaleString([], { weekday: "short", hour: "2-digit", minute: "2-digit" });`＋659 行 `$("req-totals").textContent = \`自 ${sinceStr}：…\``；在途树版＝657/661 行——**在途面已把该行改为 locale 化日期先行版**（`{ year:"numeric", month:"2-digit", day:"2-digit", hour:"2-digit", minute:"2-digit" }`，实读 git diff 在册）。`weekday:` 计数＝ANCHOR 版 **1**／在途树 **0**（被先行版替换所致，非疏漏）。数据源＝`/metrics` 的 `totals.since`（epoch 秒，引擎侧字段，本包只读展示）。
  - smoke 套实核：`selftest_monitor.py` 双 harness 的 `/metrics` stub 均 `totals: {}`（154 行区/604 行区）＝汇总行走 else 支路（空串）＝**现 smoke 无汇总行文本断言**＝本票需补 fixture＋断言（②-3 S-2）。
  - 领地核实：本票可写面（monitor.js/selftest_monitor.py/登记面）∩ rev14 八文件闭集＝`README.md/MANIFEST.md/CHANGELOG.md` 三个登记面（不同节区）＋tickets；∩ rev13 面＝空。monitor_ext.py 零触碰（`since` 来自 /metrics 引擎面，非 ext.json，本票不动数据面）。
- 前置票：rev10（gate 卡显示族＝req-totals 同文件同区历史改动）、rev13（完工 268b7a8，排程前置）、rev14（并行票，文件交集仅登记面不同节区）
- 候裁点：**零**（显示格式无真源/执法口径面；「至少」下限解读＝年月日 时:分 全给，见 A-1，属装配细节不上楼）
- Agent 适配度：内部票·适配度不适用
- 修订记录：**v1**（初稿；母本仓除本票文件外零触碰；票未放行、零施工）

### 准入四判据自查（票面自证）

1. **无 API 变更**：`/ext.json`、`/metrics` 转发、`requests-*.jsonl`、`gate-events-*.jsonl` 全零触碰；monitor.js 只改一行显示格式化（纯显示面）。
2. **口径已裁**：「至少实际年月日期」＝11:32 已裁方向；具体格式（分隔符/是否保留星期）＝装配细节票裁 A-1～A-5 决毕，不上楼。
3. **可机械验收**：③节＝命令＋期望读数（静态锁两枚＋smoke 行为读数一枚＋逐套报数＋闭集核验＋单行改动量核验）。
4. **不触真源**：`totals.since` 数据源（引擎 /metrics 面）零触碰；六前置票 append-only；在岗机零触碰。

---

## 票体四字段（自包含）

### ① 目标

监视页「最近请求」汇总行起始时刻从「周X HH:MM」（跨周歧义，人类点名缺陷）改为**实际年月日＋时:分**并**锁死可断言格式**：`自 2026-11-17 00:21：4,322 个请求 · …`（余下数字段零改动）。在途面已含 locale 化先行版（日期已显示但读数随浏览器 locale 变、无断言在册）——rev15 的净改动＝①写死手写 pad 格式化（可逐字锁，A-1）＋②补 fixture＋断言两枚（monitor 套 54→**56**）＋登记面同步。**换脑依赖声明**：monitor.js 属页面资产＝随换脑/刷新部署生效；本票验收全在测试环境，不依赖换脑。

### ② 规格

#### ②-0 红线纪律

- **红线一（单行改动量）**：`monitor.js` 改动＝S-1 一处（sinceStr locale 先行版单行替换为两行写死体）＝`git diff <基线> -- monitor.js` 删除行＝**1**、该文件其余全部零改（含在途两族改动落库后的全部内容）。机检③-4。
- **红线二（数据面零触碰）**：`monitor_ext.py`、`/metrics` 转发链、`/ext.json`、账本/事件文件面零改动；`totals.since` 消费只读语义不变。
- **红线三（其余断言零回归）**：monitor 套既有 54 名零改（只增 2 名）；proxy 45/45（rev14 并行时若已施工＝以并行票落地后实际数为准走其票口径，本票不触 proxy 套）、watchdog 16/0、daily_report 15/15 三套文件零触碰原样通过。
- **红线四（在途排队改动冻结）**：工作区「闸排队并入状态卡」在途面（renderState/pruneStaleGateCard/gate 族断言改名两枚）＝人类口径直改，**本票禁回改禁重排**；rev15 施工基线必含该 commit。

#### ②-1 声明闭集（本票唯一可写仓内面）

```
monitor.js
selftest_monitor.py
README.md          (监视页说明段补一句汇总行口径)
MANIFEST.md        (rev15 节)
CHANGELOG.md       (rev15 节·倒序)
tickets/rev15-monitor-date-ticket.md   (本票本体，登记面，不计施工验收面)
```

其余全部不入闭集零触碰（含 `monitor_ext.py`、`collector_proxy.py`、`selftest_proxy.py`、`daily_report.py`、`selftest_daily_report.py`、`ext.js`、`monitor.html`、`monitor.css`、`paths.py`、`config*`、`bootstrap.py`、`docs/**`、`data/**`）。

#### ②-2 禁动面

- `monitor.js` 除 S-1 单点外零改动（红线一机检）；`renderState`/闸排队显示族＋sinceStr locale 先行版以外的一切＝在途改动冻结面（禁回改）。
- `selftest_monitor.py` 既有 54 断言名与断言体零改（只增 S-2 两枚＋stub fixture 一处参数）。
- 引擎侧/在岗 `D:\Strata-toolkit\`：零触碰。六前置票 append-only。

#### ②-3 逐条施工规格（代码体写死，逐字转录）

**S-1 monitor.js 替换（基线＝在途面落库 commit；锚＝在途树 657 行单行，内容锚逐字：`const sinceStr = new Date(t.since * 1000).toLocaleString([], { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });` 替换为两行）**：

```js
      const sd = new Date(t.since * 1000);
      const sinceStr = `${sd.getFullYear()}-${String(sd.getMonth() + 1).padStart(2, "0")}-${String(sd.getDate()).padStart(2, "0")} ${String(sd.getHours()).padStart(2, "0")}:${String(sd.getMinutes()).padStart(2, "0")}`;
```

（661 行 `$("req-totals").textContent = \`自 ${sinceStr}：…\`` 零改动＝数字段口径逐字节不变；局部量名 `sd` 无作用域碰撞——renderRequests 体实读无同名。**改 locale 先行版的理由**＝A-1：`toLocaleString` 带选项的读数随浏览器 locale 变（分隔符/顺序不保证），显示不可逐字锁＝smoke 断言跨机不稳；手写 pad 读数恒定可锁。）

**S-2 selftest_monitor.py 两枚＋fixture 一处**：

1. **fixture**：harness #7（7b 主 smoke，154 行区 stub）的 `/metrics` stub `totals: {}` 改为非空固定样本：

```js
      totals: { requests: 7, since: 1765960860, prompt_tokens: 1200, reused: 300,
                output_tokens: 450, prompt_ms: 400, decode_ms: 900 },
```

（`since=1765960860`＝2025-12-17 06:41 UTC＝本地日随时区，断言只锁结构不锁本地日读数，见断言 1。）

2. **静态锁断言一枚（落 harness 外，js 源 grep 族同法）**：名 `req-totals since line locked to ISO-style date, weekday option gone`，断言＝js 源含 S-1 写死两行逐字节（`b"const sd = new Date(t.since * 1000);"` 与 `b'${sd.getFullYear()}-${String(sd.getMonth() + 1).padStart(2, "0")}'`）＋旧行反例守卫（`b'weekday: "short"' not in js`）。
3. **smoke 行为断言一枚（harness #7 内）**：tick 链跑完后新增一行打印 `TOTALS <els["req-totals"].textContent>`，python 侧回收断言：名 `req-totals line renders real Y-M-D (smoke)`，断言＝该行文本匹配 `^自 \d{4}-\d{2}-\d{2} \d{2}:\d{2}：\d` 且不含 `周`。

#### ②-4 登记面

- **登-1 README.md**：监视页段补一句汇总行口径（起始时刻＝本地实际日期 `YYYY-MM-DD HH:MM`，非星期）。
- **登-2 MANIFEST.md**：rev15 节＝S-1/S-2 摘要；文件数不变。
- **登-3 CHANGELOG.md**：rev15 节（倒序置顶）＝人类 11:32 逐字引用＋前后样张对照（自 周二00:21 → 自 2025-12-17 06:41）。

### ③ 验收标准（全机械可判）

> 母本仓根跑，基线＝在途排队改动落库后的 commit（回执须附其哈希；票 ANCHOR＝d54146d）；回执逐条附命令原文与读数。

1. **闭集核验**：`git diff --name-only <基线> | grep -vE '^(monitor\.js|selftest_monitor\.py|README\.md|MANIFEST\.md|CHANGELOG\.md|tickets/rev15-monitor-date-ticket\.md)$' | wc -l` ＝ **0**；`git status --short` 空面（除本票本体与 `.scratch/2026-11-19-ledger-monitor-date/`）。
2. **monitor 套逐套报数**：`python selftest_monitor.py` 退出码 0 且 **56/56**；S-2 两枚断言名逐名 PASS（回执贴原始输出，含 `TOTALS` 行原文）。
3. **weekday 归零**：`grep -c 'weekday:' monitor.js` ＝ **0**。
4. **单行改动量（红线一）**：`git diff <基线> -- monitor.js | grep -c '^-[^-]'` ＝ **1**；`git diff <基线> -- monitor.js | grep -c '^+'` ≤ **3**（diff 头 `+++` 行＋两行新码）。
5. **其余三套零触碰原样通过（红线三）**：`git diff --name-only <基线> | grep -cE '(collector_proxy|selftest_proxy|daily_report|monitor_ext|selftest_watchdog)'` ＝ **0**；`selftest_watchdog.py` 16/0、`selftest_daily_report.py` 15/15 照跑照绿（proxy 套读数随并行 rev14 票口径登记，不属本票判据）。
6. **数据面零触碰（红线二）**：`git diff <基线> -- monitor_ext.py | wc -l` ＝ **0**。

### ④ 边界约束

- **票间关系**：rev13 已闭（268b7a8）＝排程前置满足；rev14 并行——文件交集＝README/MANIFEST/CHANGELOG 不同节区＋tickets，无代码交集；merge 序＝后合者 rebase 登记面（主理人程序）。在途「闸排队并入状态卡」维护改动＝先落库再开本票施工分支。
- **同源纪律**：`totals.since`＝引擎 /metrics 字段，本包只读展示；若引擎改该字段语义＝另票。人类样张中的数字段（请求数/tokens/t/s）口径本票零触碰。
- **施工面纪律**：开分支/工作树；临时工作物只落仓根 `.scratch/2026-11-19-ledger-monitor-date/`，完工 commit 前清零；禁仓外临时路径。
- **交付与 commit 纪律**：单一工程师席新鲜实例、票间串行、同席禁多实例；完工 commit 前回执先行，落 `D:\Strata\.workbuddy\collab\receipts\2026-11-19-ledger-monitor-date-receipt.md`：开端 HEAD＋写入清单＋③六条读数（含 TOTALS 行样张）＋`.scratch/` 自查。
- **票放行**＝主理人程序确认；候裁＝零，无前置表态项。

## 租约段（票内·经架构签注由 B2 lease-issuer 实例化）

- path_globs：`monitor.js`、`selftest_monitor.py`、`README.md`、`MANIFEST.md`、`CHANGELOG.md`、`tickets/rev15-monitor-date-ticket.md`
- deny_globs：`monitor_ext.py`、`collector_proxy.py`、`selftest_proxy.py`、`daily_report.py`、`selftest_daily_report.py`、`selftest_watchdog.py`、`bootstrap.py`、`monitor.html`、`monitor.css`、`monitor-sprite.svg`、`ext.js`、`html_report.py`、`ledger_watchdog.py`、`switch_proxy.py`、`paths.py`、`config.json`、`config.template.json`、`config-examples/**`、`docs/**`、`data/**`、`legacy/**`、`service-examples/**`、`.scratch/**`、`D:\Strata-toolkit\**`、`D:\Strata\**`
- 灰度判据（票内声明字段·decision-pack 读取）：monitor 套 **56/56** 退出码 0＋③-3 weekday＝0＋③-4 删除行＝1＋TOTALS 行为结构匹配——测试环境判据，不依赖换脑。
- 席位 ID／票 ID／哈希：由状态机签发，非人工填写

## 票裁已决（A-1～A-5·起草席决；推翻走回流件）

- **A-1｜格式＝`YYYY-MM-DD HH:MM`（本地时区），弃星期**：手写 pad 格式化，不用 `toLocaleString` 带选项——后者读数随浏览器 locale 变（月日顺序/分隔符不定），显示不可锁＝smoke 断言无法逐字钉、跨机不可对拍；人类要「实际年月日期」，ISO 序无歧义且可断言。星期信息弃（日期全给后星期冗余，人类原话只点名日期缺失——「至少」下限取全给）。
- **A-2｜只改显示行，不触数据**：`totals.since` 语义/来源零动；不做「跨周累计」之类口径改动（人类未提，YAGNI）。
- **A-3｜断言双保险＝静态锁＋smoke 行为**：静态锁防「改回 weekday／写死体走样」；smoke 断言防「格式化炸页」（ReferenceError/TypeError 类，沿 SPEED_DECODE 事故史——纯 grep 给不了行为证）。fixture since 用固定 epoch，断言锁**结构**（四位数年-月-日 时:分）不锁本地日读数（时区无关性＝断言跨机稳定）。
- **A-4｜harness #7 stub 加 totals 样本的副作用面登记**：totals 非空后 speed 卡/均值计算首次进 smoke 路径＝runnability 覆盖**扩大**（利好）；风险＝若该路径现有炸点会新红——属真缺陷暴露非本票引入，施工若红＝按缺陷回流，不放宽断言。
- **A-5｜在途两族改动先落库＝本票基线；S-1 内容锚逐字写死**：施工分支基线＝在途面 commit（回执附其哈希）；S-1 以 locale 先行版整行为内容锚（逐字在②-3），行号（657）仅辅助——防基线漂移坑。若主理人选择把 locale 先行版**不**入库直接丢弃（回到 ANCHOR 版），S-1 锚改 ANCHOR 版 weekday 旧行逐字、其余施工体不变——两轨皆可装配，回执注明实际轨。

## 候裁单列（H-x）

- **无。** 真冲突核：显示格式无真源/执法/安全口径面；「至少」下限＝全给日期（A-1）属装配；其余无对立未收敛面。

## 健康账登记（回流素材）

1. **locale 化格式化＝不可锁显示（素材）**：monitor 页其余 `toLocaleString` 用法（星期/百分比）未受本票点名但同族不可断言——若后续 monitor 断言族再扩，「显示逐字锁」与「locale 化 API」的张力需统一裁（本票以手写 pad 样例先行，供引用）。

## 可施工性判定（架构席自评）

- 挂点双轨实读在册（ANCHOR 655/659；在途树 657/661；内容锚逐字在②-3）；harness stub 锚点 154 行区实读；`sd` 无碰撞实读；node 在场（smoke 真跑可判）。
- 判别力自评：③-3/静态锁对「改回星期」判红；smoke 断言对「格式化炸/格式走样」判红；③-4 对「顺手改他行」判红；③-1/③-6 对「越领地」判红。
- 未实跑面（留施工/QA）：S-2 fixture 注入后 harness #7 全链首跑（A-4 副作用面）。判定＝**可施工**，无阻塞点。

—— 架构席 · rev15 v1 · 开端 HEAD 实测 `d54146db0cf970dd3817b486f185b25979636197`（git -C D:\Projects\strata-ledger-proxy rev-parse HEAD）· 2026-11-19 · 起草实核居治理族 `D:\Strata\.workbuddy\collab\`（本票文件本体落仓根 `tickets/`）
