# 闸 limit 真源闭集：兼容 basalt 启动配置形制＋废除硬编码兜底（rev14）— 施工票

## 票头（登记区）

- 票 ID：`2026-11-19-ledger-gate-limit-truth-source`
- 票名：闸 limit 真源闭集：兼容 basalt 启动配置形制＋废除硬编码兜底（rev14）
- 票型：功能新增＋口径修订（施工票通道；票种效力＝改动授权；**候裁＝零**——原 H-1 已由决策者票前直裁（11:00 件＋11:02 总则件），改按已裁口径着死，见「候裁单列」与修票记录）
- 起草席位／修票权席位：架构席
- 开端读数：**v2 修票轮 ANCHOR＝`d54146db0cf970dd3817b486f185b25979636197`**（本席当轮实跑 `git -C D:\Projects\strata-ledger-proxy rev-parse HEAD` ＝ 该值，main＝rev14 票 v1 投递头；`git status --short` ＝ 仅 `?? .scratch/`＝**rev13 施工已闭**（268b7a8＝rev13 完工码头，日报四态节已入 main）。施工基线＝本 ANCHOR。代码面另证：`git diff f775864 d54146d -- collector_proxy.py selftest_proxy.py monitor_ext.py` 空＝本票三张主改文件在 rev12 完工头→ANCHOR 区间零改动，rev12 完工头锚点全部有效。
- 决策输入件（唯一口径真源，票面不得重开人类已裁口径）：
  1. **本票效力来源**＝人类 10:35 逐字原件＋B1 登记：`D:\Strata\.workbuddy\collab\input\2026-11-19-1035-gate-limit-basalt-verbatim.md`（本票实读引用）——「我认为可以对网关做一下升级，去兼容 basalt 而不是用硬编码兜底并发量！实际终端能承载的并发量真源只能由人类写进 parallel」。主理人路由注记（同件在册）两条诉求＝①解析器兼容 basalt 启动配置形制（basalt config v2 的 parallel 在 model 条目内，非顶层）；②废除「读不到 parallel →退静态 max_inflight 硬编码顶替执法」失败态——**真源闭集＝只认人类写进启动配置的 parallel；网关不许自创、也不许用备用数字顶替真源执法**。
  2. **失败态直裁件（11:00·决策者票前直裁，本票已裁口径着死）**：`D:\Strata\.workbuddy\collab\decisions\rev14-failstate-gate-off-warning-2026-11-19.md`（本票实读引用）——「读不到 parallel 时闸怎么办（关闸告警 vs 拒绝启动）：当然是告警，用户的目的是使用后端，而不是因为网关某项功能的缺陷或者和后端的兼容问题而用不了！网关读 parallel 的目的也只是为了确保用户能用的流畅，而不是让用户没法用！」裁决口径（誊录）＝失败态＝**告警**（拒选「拒绝启动」）；网关自身缺陷/兼容问题不得致用户用不了；闸定位＝为流畅不为阻断。
  3. **阻止 vs 警告总则（11:02·INTK-0009·规则意见类·泛化，与 11:00 件互引）**：`D:\Strata\.workbuddy\collab\decisions\block-vs-warn-principle-2026-11-19.md`（本票实读引用）——「阻止行为只有在实际会对用户造成不可逆或足够严重损失的时候才需要做，否则就不应该用阻止的方式。如果可能给用户带来损失，但是损失不确定具体规模，而且能确定不是严重的损失时，只需要警告！这块 ERROR、WARNING 的软件工程实践应该有非常多的经验足够拿来作为范式吧？」
  4. 被承接件：rev11/rev11a（跟随链与 mtime 守卫缓存形态＝本票改造基座）、rev12（gate-events 三行闭集＋红线六＝本票冻结面，完工 HEAD＝f775864）、rev13（日报闸统计，**已完工入 main＝完工码头 `268b7a8`**；其 C1/C2 态消费 `max_inflight`/`gate_follow` 键在场性＝本票跨票语义面，见④）。全部 append-only 不回改。
  5. 衔接调研件（本票实读引用）：`D:\Strata\.workbuddy\collab\research\basalt-gw-compat-2026-11-19.md`——basalt serve 壳 fork 自 Strata，API/usage 字段逐字兼容；唯 config v2 把 `parallel` 放 model 条目；现解析器读 basalt 文件读不到顶层 parallel＝静默退兜底＝「跟随静默失效」。
- 架构席起草实核（v1 在册＋v2 补充，全部当轮实跑/实读）：
  - 四套回归基线（母本仓根 ANCHOR 实跑）：`python selftest_proxy.py`＝**45/45 PASS**、`grep -c '^PASS  gate:'`＝**23**；`selftest_monitor.py`＝**54/54**；`selftest_watchdog.py`＝**16 passed 0 failed**；`selftest_daily_report.py`（rev13 已完工）＝**15/15**。
  - 现闸跟随实现（ANCHOR 实读锚点）：`collector_proxy.py`（1041 行）`GATE_DEFAULTS` 83 行／`_last_limit` 279 行／`_strata_parallel_parse` 292 行／`_strata_parallel_cache` 318 行／`_strata_parallel_limit` 323 行／`_gate_params` 353 行（**383 行失败态＝`limit = v if v is not None else static_limit`＝本票废除对象**）；`_append_line` 904 行；`_push_gate` 282-289 行；do_POST 闸挂点 710-747 行（747 `_push_gate`＝闸开请求完成即推）；`Handler.gate = Gate()` 985 行。
  - **告警可观测面实核（v2 新增）**：`monitor_ext.py` `/health` 路由 617-618 行＝本地应答（ext 数据面）；ext 白名单摘键 561-564 行；`push_gate`/`get_gate` 75-95 行（`_GATE_LOCK`＋30s 新鲜度窗）；`_push_gate` 调用面＝仅 gate_on 路径（747/843）＋排队路径（201/246）——**失败态 limit 0＝gate_on False＝gate 段整体缺席**＝「无顶替数字」的天然读数，失败态在场证据须另挂点（A-9 裁定）。
  - basalt 形制实核（只读源 `D:\Strata\.scratch\basalt-src`，serve/config.py 实读）：config v2 顶层闭集键＝`version/server/engine/models`（151-164 行 `read_config`：**意外顶层键直接拒**＝两键并存文件中顶层 `parallel` 在 basalt 侧非法）；`parallel` ∈ MODEL_OPTIONS 26 行；顶层 `engine` 段可被 model 条目继承（89-90/196-203 行）；缺省＝1（527-528 行 help）；`PARALLEL_MAX=8`（21 行，钳制属引擎业务沿 rev11a A-4）；`models` 必须非空 dict 列表（178-179 行）。
  - 在岗实配（只读）：`D:\Strata-toolkit\strata-ledger-proxy\config.json` 现值 `max_inflight:2, gate_follow:true, strata_config:"D:\\Strata\\strata-unsloth-ud-iq4_xs.json"`；该启动配置文件顶层 `"parallel": 2`（Strata 形制实存）。母本仓 `config.json` 无三键（untracked，在岗另配）。
  - 解析器候选体实跑（v2 重写版·真源闭集收严）：本席 scratch 盒 `D:\Projects\strata-ledger-proxy\.scratch\rev14-gate-limit-truth-source\`（`region.py`＋`probe.py`）＝**20 态 fixture 全过**（Strata 顶层 2/缺键/null/true/0/字符串、basalt 条目/两键并存×2/条目 max/engine 继承/engine 独占/无键/engine 坏值、空 models、models 非列表、条目非 dict、顶层 list、坏 JSON、缺文件）；G-1/G-2 区哈希（AST 四段重拼·规范化 CRLF·去尾空行·sha256 前 8）＝**`79de29b6`**。
  - 告警分级体实跑（v2 新增）：scratch 盒 `g4.py`＝行为断言全过（首条 WARNING 恰 1 枚／第 10 枚升 ERROR 恰 1 枚／恢复写 re-engaged 一行清零／ambiguous 只 WARNING 不升 ERROR）；G-4 区哈希（AST 五段重拼，同规范）＝**`24456011`**。票内 ③-5/③-6 探针逐字对拍。
- 前置票：rev10、rev10a、rev11、rev11a、rev12（完工 HEAD＝f775864）、rev13（完工码头＝268b7a8）
- 候裁点：**零**（原 H-1＝失败态语义，已由决策者 11:00 票前直裁＋11:02 总则收口，票面改为已裁口径着死；登记见「候裁单列」节）
- Agent 适配度：内部票·适配度不适用
- 修订记录：**v2**（rev14 回流改票·决策者直裁落地轮：原 H-1 三选项候裁面作废→失败态按「告警不执法」着死；新增 INTK-0009 设计原则段；解析器真源闭集收严（缺键/坏值不再卡 1＝退真源缺席）；可观测面重设（limit_src 入 gate 段＋告警分级落 ledger-service.log＋gate-events **不加**第四事件类型·显式裁定 A-10）；四态 fixture 验收配套；改动面逐条见「修票记录」。票 v1 已投递（d54146d 在册），v2 覆盖同路径；除此之外母本仓零触碰，票未放行、零施工）

### 修票记录（v2·决策者直裁落地·修票权＝架构席）

主理人补充令两条（11:00 直裁件＋11:02 总则件）落票，改动面逐条（禁夹带声明：以下之外票面零改动；代码面、在岗机、六前置票零触碰）：

1. **候裁清空**：v1「H-1 三选项候裁（甲/乙/丙）」整节作废重写＝失败态按已裁口径着死（告警不执法）；**「拒绝启动/fail-closed」形态禁入票面任何位置**（v1 乙选项及其利害叙述全部撤除，不作折中保留——按补充令 1）；v1 丙（last-good）同步撤除（11:00 件既裁不执法，无残余面可留）。
2. **新增「设计原则（INTK-0009）」段**：阻止门槛与警告覆盖带＋ERROR/WARNING 范式（决策者明示拿来即用）。
3. **解析器语义收严（G-1/G-2 重写·哈希换 `79de29b6`）**：v1 把「键存在但坏值」与「键缺席」判成「卡 1」——那是**网关自创缺省**，与真源闭集冲突（11:00 直裁把失败态语义定死为告警不执法后，「卡 1」成了伪装成执法的数字顶替：卡 1＝只有 1 路能用，恰是「让用户没法用」）。v2＝键缺席/坏值＝`(None, "absent")`＝真源缺席态入告警不执法；仅「文件可读且形制对」才与「不可读」分两态（登记 A-9）；两键并存新增 `src="ambiguous"` 读数（执法走条目侧 max＋WARNING，登记 A-4）。
4. **可观测面重设**：告警＝ledger-service.log 分级行（首告 WARNING／连续 10 枚升 ERROR 一次／恢复写 re-engaged＋清零，G-4 写死体；两态均只告警不阻止）＋ext.json gate 段 `limit_src` 键（G-5/G-6）＋**limit_src 闭集×告警分级互查一致表**（G-5 后新增，令文②落点；闭集实数＝七值＋static，令文「六值」系 v1 旧称回指，票内校正）；**gate-events 不加第四事件类型**＝显式裁定 A-10（rev12 三行闭集不回改；rev13 日报 queued/released 计数零干扰）。
5. **四态 fixture 验收配套**（补充令 4/验收要求）：文件缺失（unreadable）/JSON 坏（unreadable）/键缺失（absent）/两键并存（ambiguous）四态各自断言＝**请求直通＋告警读数在场＋分级读数正确＋limit 读数非数字顶替**（前三态 gate 段缺席或 limit 0 读数＋日志 WARNING；第四态 limit＝条目 max）。
6. **断言计数重排**：N 45→**49**、gate 23→**27**（2 改名＋2 扩判＋4 新增，逐名在册）。
7. **禁动面补条**（补充令 4）：排队闸「入队等待＋心跳＋超时放行」＝背压＋延迟非终局阻止，不在总则禁面内，本票零改动（防误伤条款，见②-0 红线六）。

### 设计原则（INTK-0009·阻止 vs 警告总则·票面登记）

- **阻止门槛**：仅当行为实际会对用户造成**不可逆**或**足够严重**损失时才允许阻止。本 rev 射程内（启动配置读不到/形制不认识/键坏）无此类损失——后果带宽＝并发上限失去网关侧兜护、由引擎槽位承接，可恢复、非严重 → **全链无阻止形态，只告警**（fail-closed 已禁入票面）。
- **警告覆盖带**：损失规模不确定但可确定非严重 → 只警告。
- **范式来源**：ERROR/WARNING 严重度分级（logging 惯例）拿来即用——本票落法：状态翻转首告＝WARNING；持续不可用（连续失败样本到 `FOLLOW_FAIL_ERROR_AT=10`）升 ERROR 一次＝升读数不升形态（**仍只告警不阻止**）；恢复写一行 re-engaged 清零。

### 准入四判据自查（票面自证）

1. **无 API 变更**：对外 HTTP 面零改动；`/ext.json` gate 段增一枚 `limit_src` 键（既有 24 号断言用 `>=` 子集判定不炸、monitor.js 只消费 queued/limit＝零波及）；`requests-*.jsonl` 与 `gate-events-*.jsonl` 两文件面格式**零改动**（GEV_FIELDS 闭集不回改，A-10）。
2. **口径已裁**：真源闭集＝人类写进启动配置的 parallel（10:35）；basalt 形制兼容（10:35）；硬编码兜底废除（10:35）；**失败态＝告警不执法（11:00 直裁）**；**阻止仅限不可逆/足够严重损失、本 rev 全链无阻止形态（11:02 总则）**——候裁清零；其余（形制判别规则、多条目聚合、继承读点、告警落点与分级档位、ext 字段名、max_inflight 键去留、测试形态）＝装配细节，票裁 A-1～A-10 决毕，不上楼。
3. **可机械验收**：③节全部判据＝命令＋期望读数（闭集核验、两枚写死代码体哈希探针、四套逐套报数（proxy 49/49·gate 27）、四态 fixture 断言读数、告警分级 grep 计数、ext limit_src 读数、结构计数不变面、429/409 零计数＝无阻止形态守卫）。
4. **不触真源**：六票 append-only 不回改；在岗机 `D:\Strata-toolkit\` 零触碰；引擎侧配置与 `D:\Strata\strata-unsloth-ud-iq4_xs.json` 零触碰；`daily_report.py`/`selftest_daily_report.py` 零触碰（rev13 领地）；requests 记账账本格式零触碰。

---

## 票体四字段（自包含）

### ① 目标

闸 limit 跟随器（`_strata_parallel_parse`/`_strata_parallel_limit`，rev11a 形态）两改：

1. **解析器兼容两类启动配置形制**：Strata 形制（顶层 `parallel`）与 basalt config v2 形制（`parallel` 在 `models` 条目内，顶层 `engine` 段可继承）。形制判别＝纯结构判别（②-3 G-2 写死），**禁按文件名猜**。真源闭集收严＝只有「人类写进 parallel 的有效整数」才是真源；键缺席/坏值＝真源缺席态（不是网关缺省 1），与文件不可读同走告警不执法通道（读数分档，A-9）。
2. **废除硬编码兜底失败态（10:35 已裁）＋失败态＝告警不执法（11:00 直裁着死）**：现失败态「退 config.json 写死的 `max_inflight` 顶替执法」整条废除；读不到真源时**任何网关侧数字不得顶替**，闸停执法（limit 0＝网关既有缺省态，语义零发明）、请求直通，同时**显式告警**（分级日志＋ext 读数，G-4/G-5/G-6），文件恢复即自愈。无任何阻止形态（11:02 总则，红线六）。

配套：limit 来源可观测（ext.json gate 段 `limit_src` 键，七值闭集）；`max_inflight` 键语义重新登记（不再被跟随态消费，保留为**非跟随模式**静态上限，A-6）；README/MANIFEST/CHANGELOG/config.template.json 同步登记。

**换脑依赖声明（沿 rev13 例）**：rev14 上线**不依赖**换脑完成——全部验收在测试环境可判；在岗生效依赖换脑（现岗 rev11a 脑；rev12/rev13 换脑链由主理人排窗，rev14 随其后，不入本票验收）。完工终态＝③节判据逐条读数达标＋四套回归全绿（proxy **49/49**（gate **27**）、monitor 54/54、watchdog 16/0、daily_report 15/15）。

### ② 规格

#### ②-0 红线纪律（一票到底，违一条即整票判红）

- **红线一（真源闭集·10:35 字面）**：跟随态的有效 limit **只**能来自 `strata_config` 所指文件的 parallel（顶层／models 条目／engine 段三读点之一）；失败态**禁任何网关侧数字顶替执法**（`max_inflight`、字面常量、缓存旧值、自创缺省一律禁）。机检＝③-3＋失败态断言族行为读数。
- **红线二（rev12 冻结面）**：`Gate` 类 token 闭集沿 rev12 ③-8 全套零改动（`git diff -w` 口径）；`GEV_FIELDS`/`GEV_SEP_KEYS` 两常量与 gate-events 事件行字段/事件类型闭集**零增减（三行闭集不加第四事件类型，A-10）**；`queue_wait_ms` 写点零改动；总账 rec 字典零新增键。机检③-4。
- **红线三（缺省零回归）**：`gate_follow` 缺省 false＝非跟随路径逐字节不变（`limit = static_limit` 原语义保留）；闸关（limit 0）行为与 ANCHOR 一致（零 gate-events 文件、ext 无 gate 段）。既有 selftest_proxy 45 断言：非跟随 21 名零改；跟随组改名 2＋扩判 2；新断言只增（gate 23→**27**、N 45→**49**）。monitor 54/54、watchdog 16/0、daily_report 15/15 三文件零触碰原样通过（机检③-2）。
- **红线四（热路径纪律）**：每对话请求仍＝一次 `os.stat`＋元组比较，守卫命中零 open 零 parse；**禁每请求重读解析**；零新增上游调用（`urlopen` 仍＝3）、零新增锁、零新增线程；告警去抖与 streak 计数用无锁 int（A-7：良性竞争＝告警行±1，永不入执法判据）。`global _strata_parallel_cache` 声明坑（rev11 D1/rev11a B-1 同族两犯史）＝写死体在场，③-5/③-6 哈希探针覆盖。机检③-7。
- **红线五（禁动面互不侵犯）**：`daily_report.py`/`selftest_daily_report.py` 零触碰（rev13 领地）；rev10/rev10a/rev11/rev11a/rev12/rev13 六票本体＋勘误件 append-only 不回改。
- **红线六（无阻止形态·11:02 总则着死·防误伤双钉）**：本票新增面**禁引入任何拒绝/阻断形态**——无 429/409、无拒启、无断连、无队列前置拦截（机检③-8：`grep -cE '(429|409)'`＝0 沿例）。**反向防误伤**：既有排队闸「入队等待＋心跳保活＋超时放行」＝背压＋延迟形态、超时终会放行＝**非终局阻止，不在总则禁面内**，本票对其零改动（`Gate.acquire`/心跳/超时链＝rev10~rev12 领地，禁动）。

#### ②-1 声明闭集（本票唯一可写仓内面）

```
collector_proxy.py
selftest_proxy.py
monitor_ext.py            (仅白名单一行，G-6)
config.template.json      (comment 口径整改＋零新键)
README.md
MANIFEST.md
CHANGELOG.md
tickets/rev14-gate-limit-truth-source-ticket.md   (本票本体，登记面，不计施工验收面)
```

`daily_report.py`、`selftest_daily_report.py`、`selftest_monitor.py`、`selftest_watchdog.py`、`bootstrap.py`（无新测试文件）、`monitor.js`/`monitor.html`/`monitor.css`/`monitor-sprite.svg`/`ext.js`、`html_report.py`、`ledger_watchdog.py`、`switch_proxy.py`、`paths.py`、`config.json`、`config-examples/**`、`docs/**`、`data/**`、`legacy/**`、`service-examples/**`：不入闭集零触碰。`config.template.json` **零新键**（三键键名不动、comment 口径改写）。

#### ②-2 禁动面（零触碰清单）

- `daily_report.py`／`selftest_daily_report.py`：**零触碰**（rev13 领地；rev14 完工 commit 不得含这两文件 diff，机检③-1）。
- `collector_proxy.py` 内非本票域面零改动：`Recorder`、`Gate` 类全体（红线二 token 闭集）、do_POST 闸挂点 710-747 行区（含 `_gate_beat`/`_gate_event` 闭包）、`key_identity`、日报线程、`_append_line` 本体、main() 挂点注释。
- `requests-*.jsonl` 键面、`gate-events-*.jsonl` 字段面与三事件类型闭集：零改动（红线二＋A-10）。
- 引擎侧任何文件（`D:\Strata\serve\`、`D:\Strata\strata-unsloth-ud-iq4_xs.json`）、在岗 `D:\Strata-toolkit\`：零触碰。
- 六前置票本体＋勘误件：append-only 不回改。

#### ②-3 collector_proxy.py 逐条施工规格（行号＝ANCHOR 实读锚点；G-1/G-2/G-4 代码体写死，逐字转录）

**G-1 常量区（现 83 行 `GATE_DEFAULTS` 行后、84 行 rev11a X-2 注释前插入）**：

```python
FOLLOW_FAIL_ERROR_AT = 10    # rev14: 连续告警样本 WARNING→ERROR 升档点（INTK-0009 分级范式）
```

**G-2＋G-3 写死替换体（现体 292-350 行区＝`_strata_parallel_parse` 定义至 `_strata_parallel_limit` 尾 `return v` 全段替换；AST 四段对拍区＝`_parallel_value`＋`_strata_parallel_parse`＋`_strata_parallel_cache` 赋值＋`_strata_parallel_limit`，sha8＝`79de29b6`）**：

```python
def _parallel_value(p):
    """rev14 A-1: one written parallel value -> gate limit. Validity rule is the
    rev11a one, semantics unchanged: an int (not bool) >= 1 is taken as-is;
    bool/non-int/<1 = not a written parallel (truth source absent). None/absent
    handled by the callers as "absent" (INTK-0008: the truth source is only what
    a human wrote into parallel - a gateway-side default is not the truth).
    NO PARALLEL_MAX clamping here (clamping is the engine's business, rev11a A-4;
    basalt's own clamp is 1..8, serve/config.py parallel_count - not ours).
    """
    if isinstance(p, int) and not isinstance(p, bool) and p >= 1:
        return p
    return None


def _strata_parallel_parse(path):
    """rev14 (INTK-0008): parse one engine startup-config file, BOTH forms.
    Form is discriminated by JSON structure only, NEVER by file name:
    "models" key holding a list -> basalt config v2 reader; else Strata reader.

    Returns (limit, src) / (None, src) / None. src is a closed set:
    "top" / "entry" / "engine" / "ambiguous" / "absent". Plain None = file or
    JSON unreadable. (None, "absent") = readable file of a legal form carrying
    NO written parallel: the truth source is absent, caller enters the
    warn-only state (INTK-0008 + INTK-0009: no stand-in number, no blocking).

    Two-key files (top-level "parallel" AND a "models" list) are basalt form:
    top-level "parallel" is NOT a legal basalt v2 key (serve/config.py
    read_config rejects unexpected top-level keys) and is NOT read; src comes
    back "ambiguous" so the warn channel can name it (A-4).

    basalt reader: models must be a non-empty list of dicts (else None); each
    entry takes its own "parallel", else the top-level "engine" section's.
    Gate limit = MAX across written entries (ticket A-2). Never raises,
    zero urlreq, zero threads.
    """
    try:
        with open(path, encoding="utf-8") as f:
            obj = json.load(f)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    entries = obj.get("models")
    if isinstance(entries, list):
        if not entries or not all(isinstance(e, dict) for e in entries):
            return None
        shared = obj.get("engine")
        shared = shared.get("parallel") if isinstance(shared, dict) else None
        best, src = None, "absent"
        for ent in entries:
            if "parallel" in ent:
                v, s = _parallel_value(ent["parallel"]), "entry"
            elif shared is not None:
                v, s = _parallel_value(shared), "engine"
            else:
                continue
            if v is None:
                continue
            if best is None or v > best:
                best, src = v, s
        if best is None:
            return None, "absent"
        if "parallel" in obj:
            return best, "ambiguous"
        return best, src
    p = obj.get("parallel")
    if p is None:
        return None, "absent"
    v = _parallel_value(p)
    return (v, "top") if v is not None else (None, "absent")


_strata_parallel_cache = None   # 模块级：(path:str, guard:(mtime_ns,size), (limit,src)) | None
                                # 无锁纪律：写＝整体重绑元组（GIL 原子）；多请求线程并发
                                # miss 时允许重复解析（幂等读数，last-write-wins，无撕裂
                                # 读、无正确性问题）——引新锁即违红线四。

def _strata_parallel_limit(c):
    global _strata_parallel_cache   # ← 必须（rev11a B-1 修·rev11 D1 同族坑第二次）：
                                    # 函数体内对 _strata_parallel_cache 的任何赋值使 Python
                                    # 把该名全程判为局部——缺这行则读点 cache = ... 先于
                                    # 赋值执行＝UnboundLocalError，且本函数炸点穿
                                    # _gate_params 穿 do_POST（实码 673 行无外层 try）
                                    # ＝跟随态每请求热路径炸。教训就近登记于此，照抄勿删。
    raw = c.get("strata_config")
    if not raw:
        return None                          # 未配路径：无真源，报失败态（调用侧告警不执法）
    path = expand_path(raw, c.get("config_dir"))   # @here/相对口径（paths 已依赖）
    try:
        st = os.stat(path)
    except Exception:
        # 抓 Exception 非 OSError（rev11a B-1 顺带修·QA 探针实证）：os.stat 对含 NUL 的
        # 路径串抛 ValueError（非 OSError 族）——统一报失败态，一切读失败不抛穿热路径。
        _strata_parallel_cache = None        # stat 失败＝缓存作废，本请求入失败态
        return None
    guard = (st.st_mtime_ns, st.st_size)
    cache = _strata_parallel_cache
    if cache is not None and cache[0] == path and cache[1] == guard:
        return cache[2]                      # 命中：零 open 零 parse
    v = _strata_parallel_parse(path)
    if v is not None:
        _strata_parallel_cache = (path, guard, v)   # 含 (None,"absent")：合法形制无真源＝
    else:                                          # 守卫内可缓存（改文件必动 mtime＝自愈）；
        _strata_parallel_cache = None              # 不可读/坏 JSON 不缓存（中途保存可自愈）
    return v
```

（返回值升格 `(limit, src)`，limit 可为 None＝真源缺席；`None`＝不可读。absent 元组可入缓存、不可读不缓存——两态自愈性不同，A-9。）

**G-4 告警面（模块级新增，落位＝现 279 行 `_last_limit = 0` 之后；AST 五段对拍区＝`FOLLOW_FAIL_ERROR_AT`/`_FOLLOW_WARN_SRC`/`_follow_warn_streak`/`_follow_warn_src` 四赋值＋`_follow_warn_gate` 函数，sha8＝`24456011`）**：

```python
_FOLLOW_WARN_SRC = ("follow_fail", "absent", "ambiguous")   # 告警态 src 闭集（前两者不执法；ambiguous＝执法＋警告）

_follow_warn_streak = 0      # 连续告警态样本数（无锁 int，A-7：良性竞争＝告警行±1，永不入执法判据）
_follow_warn_src = ""        # 上一请求的 src（src 翻转即再告一条 WARNING）


def _follow_warn_gate(out_dir, src, limit):
    """rev14（11:00 直裁＋INTK-0009）：真源不可得＝只告警、不执法、不阻止。
    落点＝ledger-service.log 分级行＋ext.json gate 段 limit_src（G-5 push 点）。
    首条 WARNING；streak==FOLLOW_FAIL_ERROR_AT 升档 ERROR 一次（仅执法失败族，
    ambiguous 不升——它在执法）；恢复写一行 re-engaged 并清零。成功稳态零日志行。"""
    global _follow_warn_streak, _follow_warn_src
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if src not in _FOLLOW_WARN_SRC:
        if _follow_warn_streak:
            _follow_warn_streak, _follow_warn_src = 0, ""
            if out_dir:
                _append_line(os.path.join(out_dir, "ledger-service.log"),
                             "[%s] gate follow re-engaged: limit=%s src=%s" % (ts, limit, src))
        return
    _follow_warn_streak += 1
    if src != _follow_warn_src:
        _follow_warn_src = src
        reason = {"ambiguous": "two-key file: top-level parallel ignored, entries enforced (A-4)",
                  "absent": "startup-config readable but carries no written parallel",
                  "follow_fail": "startup-config unreadable (missing/broken/wrong form)"}[src]
        effect = ("enforcing entries' max=%s" % limit) if src == "ambiguous" \
            else "gate NOT enforcing, no stand-in number"
        if out_dir:
            _append_line(os.path.join(out_dir, "ledger-service.log"),
                         "[%s] WARNING gate follow [%s]: %s — %s (INTK-0008/0009: warn, never block)"
                         % (ts, src, reason, effect))
    if _follow_warn_streak == FOLLOW_FAIL_ERROR_AT and src != "ambiguous" and out_dir:
        _append_line(os.path.join(out_dir, "ledger-service.log"),
                     "[%s] ERROR gate follow [%s]: truth source still unavailable for %d chat "
                     "requests — gate still NOT enforcing (escalation is reading-only, no blocking, INTK-0009)"
                     % (ts, src, _follow_warn_streak))
```

**G-5 `_gate_params` 失败态改体（现体 353-395 行函数体内三处）**：

1. 现 355 行改 `global _last_limit, _last_limit_src`；现 359 行 except 分支 `_last_limit = GATE_DEFAULTS[0]` 后插 `_last_limit_src = "config_fail"`。
2. 现 380-385 行（`follow = ...` 至 `limit = static_limit`）替换为（**已裁口径着死＝11:00 告警不执法，无选项面**）：

```python
    follow = c.get("gate_follow") is True
    if follow:
        v = _strata_parallel_limit(c)
        if v is None:
            limit, src = 0, "follow_fail"          # 不可读：闸停执法（网关既有缺省态）
        elif v[0] is None:
            limit, src = 0, "absent"               # 可读无形制内真源：闸停执法
        else:
            limit, src = v                          # (limit, src) 元组直解
        _follow_warn_gate(c.get("out_dir"), src, limit)
    else:
        limit, src = static_limit, "static"
    _last_limit, _last_limit_src = limit, src
```

3. 现 365-379 行注释块内 A-3 段（`max_inflight` 两用途口径）改写：跟随态失败不再退静态（告警不执法已裁）；`max_inflight` 仅剩非跟随模式一用途（A-6）。注释改动不入红线二 token 面。

（`limit 0`＝`gate_on False`＝acquire 不被调用＝零 gate-events 行＋ext gate 段缺席＝「无顶替数字」的天然可查读数；**不新增任何拒绝路径**，请求走非闸直通支路＝红线六。）

**limit_src 闭集与告警分级互查一致（修票 v2·补充令②钉死）**：src 闭集全貌＝**七值**（`top/entry/engine/ambiguous/absent/follow_fail/config_fail`）＋非跟随态 `static`＝ext 读数面共八值（主理人令文「六值」按 v1 旧称回指，v2 收严后实数为七＋1，如实校正于此）。互查映射写死（日志分级字面 ↔ src 值，两面对账只准出下表组合）：

| limit_src | 执法 | 日志分级 | ext gate 段 |
|---|---|---|---|
| `top`/`entry`/`engine` | limit＝读值 | 无（稳态零行）或 re-engaged 一行 | 在（limit＋limit_src 一致） |
| `ambiguous` | 条目侧 max | WARNING（永不升 ERROR） | 在（limit＝条目 max） |
| `absent` | 0 不执法 | WARNING→持续 ERROR | 缺席（limit 0） |
| `follow_fail` | 0 不执法 | WARNING→持续 ERROR | 缺席（limit 0） |
| `config_fail` | GATE_DEFAULTS 0 | 无（config 面既有语义沿例，不入本告警族） | 缺席 |
| `static`（非跟随） | max_inflight | 无 | 在 |

机检＝③-9 逐名 detail 读数＋③-5/③-6 写死体哈希（映射内化于 G-4 写死体，改动即红）。

**G-6 可观测面（两处小改）**：

1. collector_proxy 现 279 行后（G-4 块内已含 `_follow_warn_src` 等）补一行 `_last_limit_src = ""   # rev14: 最近 limit 来源，闭集 top/entry/engine/ambiguous/absent/follow_fail/config_fail/static`。
2. `_push_gate`（现 282-289 行）快照行替换为：

```python
        snap = gate.snapshot(_last_limit)
        snap["limit_src"] = _last_limit_src
        _monitor_ext.push_gate(snap)
```

3. `monitor_ext.py` 白名单（现 563-564 行摘键 tuple）追加 `"limit_src"`（六键）。除该行外 monitor_ext.py 零触碰。

（`Gate.snapshot` 本体零改；limit_src 在 push 侧附加。**gate-events 不加第四事件类型**＝A-10，告警证据面＝日志分级行＋ext limit_src＋gate-events 缺口三件套。）

#### ②-4 selftest_proxy.py 逐条施工规格（45 名面：21 名零改、2 改名、2 扩判、4 新增；期望 N=49、gate=27）

**改名两名（跟随失败态族——已裁「告警不执法」口径）**：

- K-1（现 1185-1227 行）「gate:follow boot fallback to static max_inflight」→ **`gate:follow source unreadable gates off with warning`**。工序骨架复用（pin_slot＋第二请求判别）：follow ON、`strata_config` 指不存在路径、`max_inflight:1`——**期望反转**：第 2 请求 0.65s 内**完成**（200 直通，非排队）；ext 无 gate 段（limit 0＝acquire 不触发）；`<测试 out_dir>/ledger-service.log` 含 `WARNING gate follow [follow_fail]` 恰 1 枚。detail 含状态/日志计数/ext 缺席三读数。
- A-4ff（现 1299-1348 行）「gate:follow file failure falls back to static」→ **`gate:follow broken json gates off then self-heals`**。第一步坏 JSON（`{broken`）：直通＋WARNING `[follow_fail]` 在场；收尾**新增自愈步**：`strata_config` 重指可读文件（`{"parallel":2}`）→第 3 请求组恢复执法（ext gate 段回归、`limit==2`、`limit_src=="top"`、日志 `gate follow re-engaged` ≥1 枚、streak 清零后再坏一次会再告）。

**扩判两名（名不变）**：

- A-4「gate:follow limit from strata_config parallel」（现 1229-1297 行）：断言式增 conjunct `g_sc1.get("limit_src") == "top"`（工序零改）。
- 24 号「gate:ext.json gate section shape」（现 1134-1140 行）：断言式增 conjunct `g.get("limit_src") == "static"`（该阶段非跟随）。

**新增四名（落位＝跟随组 A-5 断言（现 1350-1360 行）之前；组内 cfg 自恢复纪律沿例）**：

- `gate:follow basalt entry parallel followed`：basalt 形制 fixture `{"version":2,"models":[{"model":"m1","parallel":2}]}`，`max_inflight:1`（判别：旧形态读不到顶层→退 1→第 2 排队；新形态 limit 2→第 2 直通）；ext `limit==2`＋`limit_src=="entry"`。
- `gate:follow two-key file enforces entries with ambiguous warning`（两键并存歧义态）：fixture 顶层 `"parallel":5`＋`models:[{"model":"m1","parallel":1}]`——执法走条目侧 max＝**1**（第 2 请求 0.65s 仍排队＝顶层 5 被无视判据）；ext `limit==1`＋`limit_src=="ambiguous"`；日志 `WARNING gate follow [ambiguous]` ≥1；且该态**不出现** ERROR（红线六分级钉）。
- `gate:follow key absent gates off no stand-in number`（键缺失态）：fixture `{"port":8000}`（可读、形制合法、无 parallel），`max_inflight:2`——**不执法**（第 2 请求直通）、ext 无 gate 段（**limit 读数缺席＝非数字顶替**判据）、日志 `WARNING gate follow [absent]` 恰 1；判据含「max_inflight 2 未生效」行为证（若退 2＝不排队＝同判据巧合？**反钉**：pin_slot 占 1 路后第 2 请求在 0.65s 内完成＝不执法确证——退 2 时亦完成，故补 ext 缺席为判别主证：退 2＝gate 段会出现。诚实登记：本断言 ext 缺席读数即判别点）。
- `gate:follow warning escalates to error at streak 10`（分级档位）：失败态（缺文件）下连发 10 个对话请求（非流式 json，stub 快回）→日志计数 `WARNING gate follow [follow_fail]`＝恰 **1**（首告去抖）＋`ERROR gate follow [follow_fail]`＝恰 **1**（streak==10 升档恰一次）＋10 请求全 200 直通（**告警不阻止**行为证）。detail 贴两计数＋状态列表。

**四态 fixture 对照（补充令 4 要求）**：文件缺失＝K-1 改名族；JSON 坏＝A-4ff 改名族；键缺失＝新增 absent 名；两键并存＝新增 ambiguous 名。四态各自断言面＝请求直通（或条目侧执法）＋告警读数在场＋分级读数正确＋limit 非数字顶替——全数在册。

收尾纪律：每断言 cfg 自恢复（rev10a 沿例）；不写仓内 `data/`；A-5「follow on still never polls upstream」**零改动**（hits 零判据自动纳入新增名）。

#### ②-5 登记面

- **登-1 README.md**：第八节「闸卡启动配置上限（rev11a 改形）」段改写＝两类形制口径（Strata 顶层／basalt v2 条目＋engine 继承）＋「读不到／键缺失＝**告警不执法**（11:00 直裁）＋分级日志＋自愈」＋`limit_src` 可观测口径＋两键并存口径；第九节第 13 条回退次序改写＝max_inflight 档作废（两级再收零级：跟随态无回退档）。含字面 `basalt` ≥1、`真源` ≥1、`告警` ≥1。
- **登-2 MANIFEST.md**：新增 rev14 节（倒序）＝G-1~G-6 逐面摘要＋GEV_FIELDS 三行闭集零改登记＋`max_inflight` 语义重登记（A-6）＋INTK-0009 设计原则引用；文件数不变。
- **登-3 CHANGELOG.md**：新增 rev14 节（倒序置顶）＝人类 10:35 需求字面引用＋失败态前后行为对照（退静态执法→告警不执法）＋11:00/11:02 两裁决引用。
- **登-4 config.template.json comment**：跟随段——「`strata_config` 读不到…退回 max_inflight 兜底（建议与人类已裁并发数同值）」句**删除**，改为「读不到／键缺失＝闸停执法＋ledger-service.log 分级告警（WARNING→持续 ERROR）＋文件恢复自愈（INTK-0008/0009＋人类 2026-11-19 11:00 裁语：告警不阻断）；两类启动配置形制自动判别；两键并存走条目侧并告 ambiguous」；`max_inflight` 说明补「仅非跟随模式生效」。JSON 键面零增删。

### ③ 验收标准（全机械可判：命令＋期望读数）

> 母本仓根跑，基线＝`d54146d`；回执逐条附命令原文与读数。基线对照（架构席 ANCHOR 实跑在册）：proxy 45/45（gate 23）、monitor 54/54、watchdog 16/0、daily_report 15/15。

1. **闭集核验**：`git diff --name-only d54146d | grep -vE '^(collector_proxy\.py|selftest_proxy\.py|monitor_ext\.py|config\.template\.json|README\.md|MANIFEST\.md|CHANGELOG\.md|tickets/rev14-gate-limit-truth-source-ticket\.md)$' | wc -l` ＝ **0**。补盲读数：回执附 `git status --short` 原文——允许项仅本票本体与临时工作物 `?? .scratch/2026-11-19-ledger-gate-limit-truth-source/`（完工 commit 前清零）；出现 `daily_report.py`/`selftest_daily_report.py`/`bootstrap.py` 任何行＝侵 rev13 领地，判红。
2. **四套回归逐套报数（红线三）**：`python selftest_proxy.py` 退出码 0 且 **49/49**、`grep -c '^PASS  gate:'` ＝ **27**；`selftest_monitor.py` **54/54**；`selftest_watchdog.py` **16 passed 0 failed**；`selftest_daily_report.py` **15/15**；`git diff --name-only d54146d | grep -cE 'selftest_(monitor|watchdog|daily_report)\.py'` ＝ **0**。
3. **兜底废除（红线一·结构面）**：`git diff d54146d -- collector_proxy.py | grep -c '^-.*else static_limit'` ≥ **1**；`git diff d54146d -- collector_proxy.py | grep -cE '^\+.*(else static_limit|\? static_limit)'` ＝ **0**；`grep -c 'follow_fail' collector_proxy.py` ≥ **3**。
4. **rev12 冻结面（红线二）**：`git diff -w d54146d -- collector_proxy.py | grep -cE '^[-+].*(self\.inflight <|self\.inflight \+=|self\.inflight -=|self\._waiters\.append|self\._waiters\.popleft|self\._waiters\.remove|self\._seq \+=|self\.queued \+=|self\.waited_total|self\.beat_total \+=|self\._cond\.wait|self\._cond\.notify)'` ＝ **0**；`git diff d54146d -- selftest_proxy.py | grep -cE '^[-+].*GEV_(FIELDS|SEP_KEYS) ='` ＝ **0**；`git diff d54146d -- collector_proxy.py | grep -cE '^[-+].*queue_wait_ms'` ＝ **0**；`git diff d54146d -- collector_proxy.py | grep -cE '^\+.*"(queued|released|admitted)"'` ＝ **0**（gate-events 三事件类型闭集未扩，A-10）。
5. **写死体甲对拍（G-2/G-3·常规工序升格）**：母本仓根跑

   ```bash
   python - <<'EOF'
   import ast, hashlib, sys
   src = open("collector_proxy.py", "rb").read().replace(b"\r\n", b"\n")
   tree = ast.parse(src)
   want = {"_parallel_value", "_strata_parallel_parse", "_strata_parallel_limit"}
   parts = []
   for node in tree.body:
       name = getattr(node, "name", None)
       seg = None
       if isinstance(node, ast.FunctionDef) and name in want:
           seg = ast.get_source_segment(src.decode("utf-8"), node)
       elif isinstance(node, ast.Assign):
           t = node.targets[0]
           if isinstance(t, ast.Name) and t.id == "_strata_parallel_cache":
               seg = ast.get_source_segment(src.decode("utf-8"), node)
       if seg:
           parts.append(seg)
   body = "\n\n".join(parts).rstrip("\n") + "\n"
   b = body.encode("utf-8")
   print("G23 bytes", len(b), "sha8", hashlib.sha256(b).hexdigest()[:8])
   sys.exit(0 if hashlib.sha256(b).hexdigest().startswith("79de29b6") else 1)
   EOF
   ```

   退出码 **0**、sha8＝**`79de29b6`**（起草实跑在册，scratch 件 `region.py` 可对拍）。
6. **写死体乙对拍（G-1/G-4 告警面）**：同法对拍五段（`FOLLOW_FAIL_ERROR_AT`/`_FOLLOW_WARN_SRC`/`_follow_warn_streak`/`_follow_warn_src` 四赋值按源码序＋`_follow_warn_gate` 函数），期望 sha8＝**`24456011`**、bytes＝**2197**（起草实跑在册，scratch 件 `g4.py` 可对拍；`_append_line` 本体不在对拍区＝既有函数复用）。global 声明坑自查：`grep -c 'global _strata_parallel_cache' collector_proxy.py`＝**1**；`grep -c 'global _follow_warn_streak, _follow_warn_src' collector_proxy.py`＝**1**；`grep -c 'global _last_limit, _last_limit_src' collector_proxy.py`＝**1**。
7. **热路径结构计数不变（红线四）**：`grep -c 'urlopen' collector_proxy.py`＝**3**；`grep -c 'threading.Thread'`＝**1**；`grep -cE 'threading\.(Lock|RLock|Semaphore)\('`＝**1**；`grep -c 'threading.Condition()'`＝**1**；`grep -c 'os\.stat(' collector_proxy.py`＝**1**；行为证＝A-5 hits=0 断言零改动 PASS。
8. **无阻止形态（红线六·11:02 总则机检）**：`grep -cE '(429|409)' collector_proxy.py`＝**0**；`git diff d54146d -- collector_proxy.py | grep -cE '^\+.*(send_error|close_connection|Connection.*close)'`＝**0**（新增面无任何拒绝/断连形态）。
9. **四态告警读数（已裁口径行为面）**：回执贴②-4 四新增名＋两改名族逐名 detail 原文；逐名期望＝absent/ambiguous/fail 三族 `limit_src` 读数＋日志分级计数（WARNING 恰 1／ERROR 恰 1／re-engaged ≥1）＋直通状态读数＋ext gate 段缺席或 limit 非顶替读数，全部在册。
10. **登记面**：`grep -c 'basalt' README.md` ≥1；`grep -c '真源' README.md` ≥1；CHANGELOG rev14 节含 `10:35` 字面 ≥1＋`11:00` ≥1；`git diff d54146d -- config.template.json | grep -cE '^\+  "'`＝**0**（零新键）＋`git diff d54146d -- config.template.json | grep -c '"max_inflight"'`＝**0**（键行零改）。

### ④ 边界约束

- **票间关系（互不侵犯·红线五）**：rev13 已完工（码头 268b7a8）＝本票基线在其之上；rev14 禁动面含 rev13 两文件。**跨票语义登记**：rev13 日报 C1 态判别读 `max_inflight`/`gate_follow` 键在场性（`max_inflight<=0 且 gate_follow is not True`）——rev14 后两键键名与在场性不变，C1/C2 判别零波及，rev13 无需改票。rev13 日报 queued 计数口径消费 gate-events `event=="queued"`——本票不加第四事件类型（A-10）＝rev13 计数零干扰（补充令 3 核对项，登记为验据入③-4）。
- **上线/生效两态（换脑依赖声明）**：完工＝合母本仓即「上线」（不依赖换脑）；在岗生效＝随换脑部署（现岗 rev11a 脑；换脑窗主理人另排，票外面不入验收）。**在岗 config 零改键即安全**：在岗 `gate_follow:true`＋Strata 顶层 `parallel:2` 实存＝新脑首请求走「top 读数 2」＝与现岗执法一致；仅启动配置不可读时进入新失败态（告警不执法＝换脑窗内引擎配置事故不炸服务、不断接入，恰是 11:00 裁语语义）。
- **同源与引用纪律**：口径真源＝10:35 件＋11:00 件＋11:02 总则件；「真源闭集」不得走样（三读点全在人类手写的启动配置文件内；网关 config.json 的 `max_inflight` 不是真源）。basalt 形制按 v0.4.0 config v2 实测，形制漂移（v3）＝另票，不预答。工程师席不得据票外记忆补设计，疑义走回流件。
- **施工面纪律**：母本仓开分支/工作树，基线＝`d54146d`；临时工作物只落仓根 `.scratch/2026-11-19-ledger-gate-limit-truth-source/`，完工 commit 前自查零残留；禁磁盘根裸路径/宿主 Temp/仓外自建目录。
- **交付与 commit 纪律**：单一工程师席新鲜实例、票间串行、同席禁多实例；完工 commit 前回执先行，落 `D:\Strata\.workbuddy\collab\receipts\2026-11-19-ledger-gate-limit-truth-source-receipt.md`：开端 HEAD＋写入清单＋③十条逐条读数（含③-5/③-6 探针原始输出＋②-4 六名断言 detail 全文＋分级日志样张）＋`.scratch/` 自查。
- **票放行**＝主理人程序确认；**候裁＝零，放行无前置表态项**（失败态已着死）。

## 租约段（票内·经架构签注由 B2 lease-issuer 实例化）

- path_globs：`collector_proxy.py`、`selftest_proxy.py`、`monitor_ext.py`、`config.template.json`、`README.md`、`MANIFEST.md`、`CHANGELOG.md`、`tickets/rev14-gate-limit-truth-source-ticket.md`
- deny_globs：`daily_report.py`、`selftest_daily_report.py`、`selftest_monitor.py`、`selftest_watchdog.py`、`bootstrap.py`、`monitor.js`、`monitor.html`、`monitor.css`、`monitor-sprite.svg`、`ext.js`、`html_report.py`、`ledger_watchdog.py`、`switch_proxy.py`、`paths.py`、`config.json`、`config-examples/**`、`docs/**`、`data/**`、`legacy/**`、`service-examples/**`、`.scratch/**`、`D:\Strata-toolkit\**`、`D:\Strata\**`
- 灰度判据（票内声明字段·decision-pack 读取）：四套回归退出码全 0＋proxy **49/49（gate 27）**＋③-3 兜底废除两读数（≥1／＝0）＋③-5 sha8＝`79de29b6`＋③-6 sha8＝`24456011`＋③-8 无阻止形态两读数＝0＋四态告警断言逐名 PASS——测试环境判据，不依赖在岗换脑。
- 席位 ID／票 ID／哈希：由状态机签发，非人工填写

## 票裁已决（A-1～A-10·起草席决；推翻走回流件）

- **A-1｜形制判别＝纯结构判别写死**：顶层 dict 且 `models` 持 list→basalt 读路径；否则 Strata 读路径。路由件①「禁按文件名猜」落点；判据取 basalt 自身强制面（read_config 顶层闭集键拒意外键）＝判别力有源可引。
- **A-2｜basalt 多条目聚合＝MAX across entries**：多 model 各起进程可能用不同 parallel，闸卡「任一进程可同时接的上限」取 max（min＝误杀高并发条目；首条目＝「首条目未写键」配置误杀——防误杀族既有重心）。max 仍是人类写入诸值之一，不违真源闭集。多值时 limit_src 只出胜者源名（ambiguous 标记另族），逐条目对账＝排障增强 YAGNI。
- **A-3｜engine 段继承读点写死；**「缺省 1」撤除**：条目缺 parallel 继承顶层 engine 段（basalt 实证）；两处皆无＝**真源缺席**（v1 曾按两引擎「缺省 1」语义卡 1——v2 收严：「缺省 1」是**引擎**的缺省，不是人类写进 parallel 的真源；网关拿引擎缺省当执法数字＝网关侧数字顶替的变体，与 11:00 直裁后「卡 1＝只有 1 路能用」的实际伤害不相称，故走告警不执法通道。人类要写 parallel 时写；不写＝不执法＋日志点名 absent）。
- **A-4｜两键并存＝basalt 形制、条目侧执法＋`src="ambiguous"` 告警**：顶层 `parallel` 在 basalt v2 非法（read_config 拒），不读＝不给非法键发执法权；并存是「文件曾手工混改」信号＝WARNING 级告警可查（不升 ERROR＝它在执法）；歧义裁定写死＋测试名钉死（顶层 5 被无视）。
- **A-5｜解析器返回 `(limit, src)` 升格**：src 七值闭集 `top/entry/engine/ambiguous/absent/follow_fail/config_fail`＋非跟随 `static`；全链 `_last_limit_src`→`_push_gate`→monitor_ext 白名单→ext。gate-events **不加字段**（A-10）。
- **A-6｜`max_inflight` 保留＋语义收窄＝「非跟随模式静态上限」**：非跟随模式仍有合法用户（缺省零回归）；rev13 C1 判别消费键在场性（④）；废除的是跟随失败态对它的消费。
- **A-7｜告警去抖/streak 用无锁 int**：GIL 原子赋值，良性竞争＝告警行±1；计数永不入执法判据；引锁违红线四。告警落 `ledger-service.log`（main 启动行同文件同族；禁 stdout-only——在岗 stdout 被 watchdog 重定向，排障面落数据目录一处可查）。
- **A-8｜改判断言改名不沿用**：旧名含「fallback to static」，已裁语义反转（不执法非退静态）——名与效力相反＝清单说谎（rev13 Y-8 纪律反向应用）。计数 23→27＝2 改名＋4 新增，逐名在册。
- **A-9｜absent 与 unreadable 两态分档（同源不同读点）**：同为「告警不执法」，但缓存与告警文案分两态——unreadable（缺文件/坏 JSON/形制不对）不缓存（中途保存自愈友好）＋`follow_fail` 文案；absent（可读合法无键）可入守卫缓存（改文件必动 mtime＝自愈仍成立）＋`absent` 文案。四态 fixture 各自可指认（补充令 4 的「各自断言」落点）。
- **A-10｜gate-events 不加第四事件类型（显式裁定·补充令 3）**：告警证据面＝日志分级行＋ext `limit_src`＋gate-events **缺口**三件套（失败态 limit 0＝acquire 不调用＝零事件行——缺口本身＝「未执法」的天然读数，与日志行交叉可证）。加第四事件类型＝破 rev12 三行闭集＋污染 rev13 日报 queued/released 计数口径（补充令 3 红线核对项）＋失败态每请求一行刷屏面（闸关无 acquire 挂点，要加须另开写点＝违红线二/四）。**裁＝不加**；rev13 消费面零同步动作（③-4 机检钉死）。
- **A-11｜absent 态不卡 1 的利害诚实登记（供回流质询）**：引擎无 parallel＝引擎自身单发（1 路），网关不执法＝第 2 路进引擎由引擎侧排队——与「卡 1」的差别＝谁执法（引擎 vs 网关）、数字来源（引擎缺省 vs 无）。v1 曾采卡 1（沿 rev11a「缺席＝单发语义卡 1」旧口径）；11:00 直裁把闸定位钉为「为流畅不为阻断」后，卡 1 属无真源数字执法（伪装度低于 max_inflight，仍是数字）＝收严入告警不执法。此条登记改判痕迹，防「rev11a 口径被静默改掉」误读＝**显式改判，非疏漏**；rev11a 票本体不回改（append-only），CHANGELOG rev14 节登记前后对照（登-3）。

## 候裁单列（H-x）

- **候裁＝零**（v1 的 H-1 已消解）：原 H-1「真源不可得时闸怎么办」＝决策者 11:00 票前直裁（`D:\Strata\.workbuddy\collab\decisions\rev14-failstate-gate-off-warning-2026-11-19.md`：告警，拒选拒绝启动）＋11:02 总则收口（`block-vs-warn-principle-2026-11-19.md`：阻止仅限不可逆/足够严重损失；ERROR/WARNING 分级范式拿来即用）。**起草席 v1 立场「甲」（不执法＝limit 0 既有语义＋显式告警＋自愈）＝与两裁语语义一致，现登记为已裁口径**——票面据此着死：失败态＝不执法＋分级告警＋自愈；**拒绝启动/last-good 两形态＝裁决禁面**（v1 乙/丙选项叙述全部撤除，无折中残留；改判痕迹居修票记录与 A-11）。放行无前置表态项。真冲突核：无——两裁决件覆盖原冲突面；残余（basalt v3 形制漂移、`/v1/responses` 端点扩面）＝④另票，不上楼。

## 健康账登记（回流素材）

1. **「两键同值」遮蔽失败态语义（沿用 v1，供 sops 立账，本票不代立）**：在岗 `max_inflight:2` 与启动配置 `parallel:2` 同值，兜底路径生产从未显形——兜底与真源常年同值＝死面假活，负样本判据（改兜底值看执法是否变化）供同类巡检。
2. **「卡 1 也是数字」（本票 v2 新增素材）**：真源闭集收严时，「引擎缺省值」与「网关硬编码」同样不是人类当时写入的真源——「无兜底」审计要连「沿引擎缺省」档一起查（A-11 改判痕迹可引）。
3. **裁决先于票到达的流程素材**：本票 H 项在起草期间被决策者票前直裁＝候裁面「呈上去前已被裁」的新时序；修票轮把裁决件入真源链＋撤选项叙述的动作（修票记录①）供 SOP 裁决插队场景引用。

## 可施工性判定（架构席自评）

- 全部挂点在 `d54146d` 实测存在：`collector_proxy.py` 1041 行——`GATE_DEFAULTS` 83／`_last_limit` 279／`_push_gate` 282／`_strata_parallel_parse` 292／`_strata_parallel_cache` 318／`_strata_parallel_limit` 323／`_gate_params` 353（383 兜底行＝废除对象）／do_POST 710-747／`_append_line` 904／`Handler.gate` 985；`monitor_ext.py` 白名单 563-564；selftest_proxy 跟随组 1176-1362（K-1 1224／A-4 1290／A-4ff 1342／A-5 1357／24 号 1137）。
- 两枚写死体已实跑：G-2/G-3 区（`region.py`＋`probe.py` 20 态全过·sha8 `79de29b6`）；G-1/G-4 区（`g4.py` 行为断言全过·sha8 `24456011`）——③-5/③-6 探针与票内写死体同源可对拍。基线四套读数在册（45/45·gate 23／54/54／16/0／15/15）。
- 判别力自评：③-3 对「兜底暗渡」判红；③-5/③-6 哈希对「写死体走样/global 声明丢」判红；`gate:follow two-key file enforces entries with ambiguous warning` 对「读点顺序错」判红；`gate:follow basalt entry parallel followed` 对「basalt 形制不识别」判红（旧形态必红＝真判别非重言）；`gate:follow key absent gates off no stand-in number` 对「缺键退数字（含退 1）」判红；`gate:follow warning escalates to error at streak 10` 对「分级档位失效」判红；K-1/A-4ff 改名族对「失败态回退到执法」判红；③-7 对「热路径加料」判红；③-8 对「引入阻止形态」判红；③-4 对「rev12 冻结面破口／事件类型扩面」判红；③-1 补盲读数对「侵 rev13 领地」判红。
- 未实跑面（留施工/QA）：G-5 挂接体与②-4 六名断言体的首跑（锚点为实码行号＋语义等价推演）；`absent` 断言的 ext 缺席判别主证在并发时序下的稳定性（sampler 新鲜度窗 30s 内无 push＝字段缺席＝机理在册，施工首跑复核）；在岗失败态告警实见（换脑后票外）。判定＝**可施工**（无候裁阻塞、无前置表态项）。

—— 架构席 · rev14 v2（决策者直裁落地轮） · 开端 HEAD 实测 `d54146db0cf970dd3817b486f185b25979636197`（git -C D:\Projects\strata-ledger-proxy rev-parse HEAD）· 2026-11-19 · 起草实核与两枚写死体探针件居仓根 `.scratch/rev14-gate-limit-truth-source/`＋治理族 `D:\Strata\.workbuddy\collab\`（本票文件本体落仓根 `tickets/`，路由件指定）