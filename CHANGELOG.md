# 版本改动登记（CHANGELOG）
## rev17j (2026-11-23)
- `SKILL.md` → `INSTALL.md`（git rename）：该文件是给任意操作者（人类或宿主 Agent）的仓根部署工序文档，命名与 Strata 官方 INSTALL.md 对齐；原名易被误解为「依赖 Agent 平台环境的通用 skill 工具」。同时摘除 frontmatter（name/description/agent_created——平台 skill 装载器的标志物，本包不发布为平台 skill）。正文开头加声明：本文件不是 skill 包；运行时对 Agent 平台零依赖（依赖方向刻意单向，不得逆转）。
- `README.md`「Agent 部署入口」节引用同步改名。

## rev17i (2026-11-23)
- GET /capabilities + /v1/capabilities: gateway self-description for NAS compute-pool schedulers, symmetric to the split-gateway facade. Reports gateway version, endpoints, admission gate state (enabled / max_concurrency), engine parallel slots + concurrency_ceiling, live queue, routable flag, engine /health passthrough, and versioned benchmark registry (benchmark-registry.json, template bench-6x256k-v1).
- Concurrency semantics explicit: LLM decode-slot parallelism, NOT comparable to DiT-instance lane counts.
- config.json gained engine_launch_config (disclosure only; gate_follow remains the sole tuning consumer).


倒序登记本包历次改动。详细逐项改动对照表见 `MANIFEST.md` 第二节；本文件只做人读摘要，不重复展开。

---

## 2026-11-22（rev17a）· 引擎看护首查修复：`last_engine_launch` 初始化 0.0 → None（缺陷修复）

- **症状**：重启实机验证时发现——开机后看门狗 27 秒内不拉引擎（日志显示宽限期剩 32.6s 起步），而本看门狗从未拉过引擎，宽限无从谈起。
- **根因**：`last_engine_launch` 初始化 0.0，宽限判定 `now - last_engine_launch < grace` 里 `now = time.monotonic()` 在 Windows 开机早期取值很小（本次实测开机后系统单调钟仅 ~85s），grace=120s 时首查被虚假宽限吞掉。慢开机（monotonic 大）不触发＝潜伏缺陷，快开机必中。
- **修复**：初始化 `None`＝本进程从未拉过引擎，开机首查立即放行；grace 只约束"自己拉过之后"的窗口。语义与注释同步。
- **实证链**：本机 01:32:26 开机→启动目录单入口 VBS 自动拉起看门狗（rev17 单入口自启首次实机通过）→首查被假宽限吞→01:34:26 才拉引擎→90 秒后端 8787 就绪＝期间"本地后端连不上"的直接原因。反代 8080 同理由看门狗 01:33:53 秒补岗，用户侧断连窗口≈开机到看门狗上岗约 1.5 分钟。
- **验证**：`selftest_watchdog.py` 31/31（既有宽限集成断言不回归）。

---

## 2026-11-22（rev17）· 看门狗引擎看护：一快捷方式拉起全套（看门狗→反代＋后端引擎）（功能新增 · 四套全绿）

- **现象/动机**：人类令（逐字要义）：「升级看门狗，同时看守反代和反代沟通的后端，并且当前具体使用 Strata 还是 Basalt 后端，直接在看门狗程序配置，Windows 启动目录里只需要放一个拉起看门狗的快捷方式即可把全套服务拉起来」。此前引擎自启挂在另一条登录自启链上（Strata autostart.bat），与看门狗两条自启并存＝引擎崩了反代空转、自启面双入口。
- **改动**（`ledger_watchdog.py`＋`config.template.json`＋`selftest_watchdog.py`；`collector_proxy.py`/`monitor*` 零触碰）：
  1. 四配置键（每轮热读，改值不重启）：`guard_engine`（缺省 **false**＝行为与 rev16 逐字节一致）、`engine_backend`（"strata"/"basalt"，日志标注＋配置自述）、`engine_launch`（`{cmd: argv 数组, cwd 支持 @here/@pkg/~}`）、`engine_grace_s`（缺省 120s，引擎刚拉起后宽限静默——模型加载期端口本就关着，防重复拉爆显存）。
  2. 引擎探测＝从 `upstream` URL 解析尾端口（与 listen 同法，支持 IPv6 括号形制），raw TCP 与反代同法；纪律沿例：健康端口永不触碰、引擎一律本看门狗 detached 子进程、cooldown＋grace 双限速、看护异常不拖垮反代循环（独立 try）。
  3. 启动日志明示两态：`engine guard ON: backend=… probe=…grace=…`／`engine guard off`；cmd 非法（非列表/空/含非字符串项）＝当轮静默关闸不崩循环。
- **与既有看护划界**：Strata 官方壳自带引擎 restart（tries=3），用 Strata 时 `guard_engine` 保持 false 勿双看护；Basalt 的 serve→engine 看护只兜"serve 壳内引擎"，serve 壳进程本身没人看——Basalt 部署面开 guard。引擎切换/重启仍走人类窗口（`switch_proxy.py` 有会话硬拒绝纪律延伸到引擎＝人类拍板）。
- **selftest**：watchdog 套 **16→31**（看护单测 8＝缺省关/无 cmd 关/四键解析/尾端口含路径与 IPv6/非法 cmd 两项关/坏配置不崩；集成 7＝缺省日志态/热开闸不重启/拉起/日志标注/宽限期抑制二拉（计数=1）/宽限后单次补拉（计数=2）/反代假服务全程存活）。proxy **45/45**、monitor **57/57**、daily_report **15/15** 回归全绿。
- **边界（不粉饰）**：引擎带外启动（人肉 bat）后看门狗不认领其进程所有权，仍按端口探测；grace 期内引擎真死＝最多晚 grace 秒补岗；双看门狗交接窗口内引擎探测短暂空窗（看门狗锁切换既有语义）。

---

## 2026-11-22（本地补丁 · 未推送）· 反代控制台输出独立落 `collector-proxy.log`

- **症状**：客户端请求中途断开时，Python `socketserver` 会往子进程 stderr 打整段 traceback；此前子进程 stdout/stderr 与看门狗自己的日志共用 `ledger-watchdog.log`，把 probe/relaunch 这些运维第一眼要看的行埋掉。
- **改动**：`ledger_watchdog.py` 的 `launch_ledger()` 把子进程输出改到 `<日志目录>/collector-proxy.log`（`CHILD_LOG_NAME` 常量）；`Popen` 后关闭父进程持有的文件句柄，修掉每次重启泄漏一个 fd 的老问题。
- **不动面**：看门狗自身日志、重启判定、端口与锁语义全部不变；子进程仍 `DETACHED_PROCESS`，仍由看门狗单独养活。
- **验证**：`selftest_watchdog.py` 16/16、`bootstrap.py --selftest` 三套全绿。
- **生效时点**：无需停机——新代码在下一次看门狗/反代重启（含重开机）时接管；改动前已在跑的进程仍写旧文件，直到它自己换代。
---

## 2026-11-21（更名）· 仓名/包名 strata-ledger-proxy → token-ledger-proxy（决策者拍板 · 功能代码零触碰）

- **动机**：旧名无 llm/token/usage 任一搜索词，外部发现性最弱；曾议「保留 strata」口径作废。
- **改动面**：GitHub 远程仓改名（旧链接自动重定向）；服务示例三件改名＋VBS 解释器变量 `TOKEN_LEDGER_PYTHON`（旧名 `STRATA_PYTHON` 保留退路）；配置模板/样例 `name` 键；README/SKILL clone 地址与标题（新标题保留 Strata/Basalt 兼容关键词）；argparse 描述、sprite 注释、start.bat 窗口标题（GBK+CRLF 不动）。明细＝MANIFEST 2.27。
- **不动面**：`tickets/` 历史票与 CHANGELOG/MANIFEST 历史节旧名（append-only 证据如实性）；在岗机器本地 `config.json` 与已装旧自启件（行为不变）。

---

## 2026-11-19（rev16）· 双后端支持：Basalt 启动配置闸解析＋监视页逐槽状态＋进度条速度表退路（功能新增 · 四套全绿 · 2026-11-21 转正）

- **来源与形态说明（如实登记）**：本 rev 四文件改动发生在运行时部署面（`D:/Strata-toolkit/`）而非本地仓＝部署面裸改窗口实例；2026-11-21 对拍发现后按「仓为基底＋四较新文件覆盖」合回本地仓（备份＝`strata-ledger-proxy-BACKUP-20261121`），commit `542eb74` 曾带 `(wip)` 标记，本节即转正登记，历史 commit 不回改。
- **改动**（`collector_proxy.py`＋`monitor.js`＋`monitor.html`＋`selftest_monitor.py`；`monitor_ext.py`/`daily_report.py` 零触碰）：
  1. `_strata_parallel_parse` 识别 Basalt 启动配置形态：无顶层 `parallel`、值在 `models[].parallel`——Basalt 单显存一轮一脑，在岗条目不可从文件判定，闸取各条目有效值 **max**（闸只卡上限，沿 INTK-0003 裁定）；无有效 parallel 的条目按单发语义贡献 1；两形态皆无＝读失败退 None→静态兜底，绝不猜。
  2. 监视页闸态固定行（人类 2026-11-19 口径）：一行常驻＝最大并发＋各状态实际进程数（basalt `/slots` 带 `state`→「读取 n · 生成 n」；Strata `/slots` 仅 `is_processing`→退「运行 n」不谎报拆态；`/slots` 不可得退 live 聚合单跑语义）＋闸排队＋引擎排队。
  3. 进度条两口径：引擎报 `max_tokens`→完成度（Strata 路）；不报（basalt `live.max_tokens=None` 实测在案）→绿条退速度表，基线 227 tok/s＝本机 basalt 单流满载实测锚点 226.9（压测报告 N=1 在册），条长＝当前 tok/s ÷ 基线每秒实时动。
  4. `fetchSlots()`＝2.5s 超时 abort、带 key、两引擎同路径不同形状（形状归渲染端）；`monitor.html` 增 `state-gate` 锚点行。
- **selftest**：monitor **57/57**（新增闸行三态断言：无 slots／basalt 逐槽／Strata 聚合）；proxy **45/45**、watchdog **16 passed 0 failed**、daily_report **15/15** 回归全绿（2026-11-21 转正时复跑读数）。

---

## 2026-11-19（rev15）· 监视页排队显示改版：独立「等待中」卡撤销、并入顶部模型状态卡＋汇总行日期口径（人类直令 · 四套全绿）

- **现象**：人类 13:45 令（逐字要义）：「等待中卡片根本没有意义……直接放在顶部的模型状态即可！里面不是有个队列吗？只需要区分网关队列还是引擎队列，以及在实际有排队的时候，往标签里面放一个数字即可」。另一令（INTK-0010）：汇总行「自 周二00:21」跨周歧义，「至少应该（实际年月日期）」。
- **改动**（`monitor.js`＋`selftest_monitor.py`＋文档，`monitor_ext.py`/`collector_proxy.py` 零触碰）：
  1. 独立「等待中」卡（rev10 `renderGate`）撤销——`card-gate` 不再产出，旧在岗页缓存残留由每 tick prune 清除。
  2. 顶部模型状态卡承载两队列：排队徽标任一队列 >0 即亮并带数字（`排队 N`，N＝引擎 queued＋网关 gate queued）；标签行按来源区分——「网关队列 N 个在等闸」／「引擎队列 N 个在排队」／双队列并存「排队 N（网关 a · 引擎 b）」。数据源两路本就分置（`/metrics live.queued` vs `/ext.json gate.queued`），口径不混。
  3. 汇总行起始时刻 `{weekday,hour,minute}` → 写死可锁格式 `YYYY-MM-DD HH:MM`（手写 pad，不用 `toLocaleString`——带选项读数随浏览器 locale 变、不可逐字锁，票 A-1）。前后样张：「自 周二00:21：…」→「自 2025-12-17 06:41：…」（票 `2026-11-19-ledger-monitor-date` S-1）。
- **selftest**：monitor 套 gate 段断言反转改版（独立卡永不出现＋状态卡标签承载「网关队列」字样＋归零回退 idle）＋S-2 两枚（静态锁写死两行逐字节＋smoke 行为断言 `^自 \d{4}-\d{2}-\d{2} \d{2}:\d{2}：\d` 不含「周」），**56/56 PASS**；proxy 45/45、watchdog 16/0、daily_report 15/15 回归全绿。红线机检：`monitor.js` 对基线删除行＝1（S-1 单点）、`weekday:` 计数＝0。
- **同日追加（INTK-0011·16:09）**：「网卡合计」独立行撤销（rev8 起老块 `mx-note`，同款低信息量独立块）——每网卡卡已带 ↓/↑ 明细；仅无已连接网卡时留一条状态提示（补 `data-mx-section="net"` 防残留）；`sumDown/sumUp` 死变量清理。monitor 套 56/56 复跑绿。
- **生效时机**：monitor.js/monitor.html 每请求现读磁盘（`_read_asset`）——同步在岗即生效，**不依赖换脑**。

## 2026-11-19（rev13）· 日报补排队闸拦截三指标：`## 排队闸拦截统计` 节四态口径（功能新增 · 四套全绿）

- **现象**：rev12 闸事件日志已落但日报未消费（rev12 票④明示「日报消费 gate-events＝另票后置」）。人类 00:19 令（INTK-0007 逐字）：「网关日报需要补充报告当前拦截入栈次数，拦截请求的最长等待时间和平均等待时间」。
- **改动**：`daily_report.py` 新增 `## 排队闸拦截统计` 节（落位＝「覆盖窗口」后、「按小时分布」前），**纯插入**（diff 对既有行删除/修改＝0，`build_report` 签名不变，幂等/skip/`--day`/`--all`/`--reported` 机制零触碰）。三指标＝拦截入栈次数（当日 `gate-events-<day>.jsonl` 的 `queued` 行数）、最长等待／平均等待（当日 `released` 行 `waited_ms` 的 max/mean，ms 取整展示＋秒括号一位小数）。四态状态机两态禁混淆：A 有当日事件文件→三指标＋补充观察列（released 总数／强制放行数／心跳合计）＋跨日口径标注（「N 项等待自前日跨入」，按文件日归属不做跨文件 join）；B 无事件文件但当日总账有 `queue_wait_ms` 行→**回填口径**（从总账同源字段派生三指标＋显式标注非逐事件日志口径）；C1 无文件无佐证且生成时刻 config 静态关闸→「闸未启用」文案不出数字；C2 无文件无佐证且 config 开闸（含 gate_follow）→三指标 0／—＋口径注。C1/C2 均带「开闸判定按日报生成时刻 config 现值，回填历史日时该判定可能失真」诚实标注。闸统计节只出聚合计数与统计量，不逐请求列出（隐私红线沿 rev12）。新独立测试套 `selftest_daily_report.py`（fixture 驱动、纯标准库、无网络不起服务）15 断言全绿；`bootstrap.py` REQUIRED 加一行。**上线不依赖 rev12 换脑**：四态验收全部测试环境 fixture 化。**在岗 11-18 及以前逐请求闸数据不可恢复**（换脑前的在岗脑不产 gate-events 文件）→该期间日报三指标走**回填口径**（总账 `queue_wait_ms` 同源证据＋降级标注；禁编造≠禁回填），11-16 起该字段行数 0/3/226/31 实测在册。
- **selftest**：新套 `selftest_daily_report.py` **15/15 PASS**；既有三套零触碰原样通过——proxy **45/45**（`grep -c '^PASS  gate:'`＝23 不增不减）、monitor **54/54**、watchdog **16 passed 0 failed**。红线机检：`git diff f775864 -- daily_report.py` 删除行＝**0**（纯增量）；`collector_proxy.py` diff＝0；幂等机制面（`skip|force=|pending`）diff 零命中。MANIFEST 2.24。网页报表/监视页消费 gate-events＝仍另票后置；在岗生效随下次换脑/部署（主理人排窗）。


## 2026-11-18（rev12）· 排队闸拦截事件独立日志：每个入栈请求留「核实在飞＋放行决策」证据，与记账账本严格分离（功能新增 · 三套全绿）

- **现象**：闸按 limit 守住路数时，「拦截真实发生」只在总账请求行 `queue_wait_ms` 字段＋ext.json 瞬时快照里体现，不成事件流——快照回答「此刻有没有人排队」，回答不了「今天拦了几次、拦了谁、等了多久、有没有等死被强发」，更证明不了「每次入栈请求网关都核实过在飞数并做过放行/排队决策」。人类 08:02 令（INTK-0005 逐字）：「如果真实出现了拦截，我希望你能够做成独立的日志」；08:04 补令（续 INTK-0005）：「让我能够确定，你对每次入栈请求都做到了核实在飞进程并决策是否放行，不要和记账日志放在一起」。
- **改动**：新独立事件日志 `data/gate-events-YYYY-MM-DD.jsonl`（Recorder 加 `prefix` 参复用总账同族机制＝按天分文件、append-only、line-buffered、行锁纪律、构造不建文件）。三形态闭集：快路 `admitted` 一行（含临界区内 `inflight_at_decision` 读数＋`limit` 快照）；被拦 `queued`（进闸瞬间，含当次读数）＋`released`（放行/强发，含 `waited_ms`/`heartbeats` 实发帧数/`forced` 强发可辨识）。决策读点写死＝`Gate.acquire` 临界区内取局部量（快路在 `inflight += 1` 前、入队同锁内），发事件一律 off-lock（写盘 I/O 禁入锁）。挂点＝acquire 尾参 `on_event`（默认 None 既有调用零改）＋Handler `_gate_event` 闭包＋`key_identity` 上提复用（同请求值逐位相同）。`main()` 挂 `Handler.gate_rec = Recorder(out, "gate-events")`——闸关 acquire 不跑＝零事件零文件零新字节（缺省零回归红线）。**红线六（补令字面）＝记账/决策分离**：`event/seq/inflight_at_decision/heartbeats/forced` 禁入 `requests-*.jsonl` 键面，总账 rec 字典零新增键（机检 diff `rec[` 加行＝0＋断言内总账 scan）；`queue_wait_ms` 保留不动、双写互证、事件日志＝拦截/决策查证权威源。隐私闭集：三形态字段写死＋禁记请求体内容（可辨识面＝route/model/key/fp 同总账口径）。无新配置键（闸开才有事件，加开关＝加死面）。
- **闸核心冻结（`git diff -w` token 闭集口径）**：`inflight`/`_waiters`/`_seq`/`queued`/`waited_total`/`beat_total`/`_cond.wait|notify`/`release()`/`snapshot()` 全部 token 行零改动（±行＝0）；唯一被允许的语义面触碰＝快路 `return 0` 改「锁内读点→出锁发 admitted→return 0」（返回值/返回条件/快路零等待不变，补令语义所迫）；`acquire` 返回类型仍 `-> int`。防误杀族四断言零改动在场（族面 diff 零行＋逐名 PASS）；既有 41 断言零作废、零删除行。
- **selftest**：proxy 41→**45/45**（只增不减）；新四断言 `gate:gate-events queued line visible while still queued`（排队中 queued 行已在盘＝「进闸即写」行为证＋决策读数 1/1＋分离 scan）／`gate:gate-events forced line on gate_wait_s expiry`（强发态 forced=True/waited≥900/heartbeats=0 非流式实发口径＋行序 queued<released）／`gate:gate-events no file with gate off`（T-1 全程闸关零 gate-events 文件，总账在场作对照）／`gate:gate-events admitted line carries decision reading`（直放留痕 0/1＝「核实到有空位才直放」）；`grep -c '^PASS  gate:'`＝**23**（基线 19＋新 4）；新标记键三枚 KEY_GE1/GE2/GE3 专用（禁复用 KEY_FAST/KEY_WAIT/KEY_3RD——QA 票前审 D-1 撞计数案）。monitor **54/54**、watchdog **16 passed 0 failed** 零触碰原样通过。红线机检：`urlopen`=3、`threading.Thread`=1、Lock=1、Condition=1 逐值不变；`(429|409)`=0；`queue_wait_ms`=1 且 diff ±行=0；冻结 token ±行=0；`rec[` 加行=0。MANIFEST 2.23。监视页/日报消费 gate-events 日志＝另票后置；在岗换脑＝主理人另排安全窗口。

---

## 2026-11-18（rev11a）· 排队闸跟随形态回流：读数源从引擎运行时轮询改为启动配置文件定死值（口径变更回流 · 三套全绿）

- **现象**：rev11 的跟随实现是网关后台线程周期 GET 上游 `/v1/status` 读引擎**运行时**并发（含 `fit_parallel` 显存降级后的真实槽数）。人类 23:13 裁定驳回该口径（INTK-0003 逐字）：「引擎侧自己往下压和网关有什么关系？网关只负责卡住上限，引擎自己爱干什么干什么！」——跟随运行时值＝网关职权越界（卡上限≠跟降级）。
- **根因**：rev11 票裁 R-2 把人类 21:08「看 Strata 实际的启动配置」过度延伸为「读运行时生效值」，把引擎内部降级机制引入网关关注面。本票系定向回流：rev11 按其票面是合格完工（三套全绿），回流＝口径变更非施工质量。
- **改动**：`gate_follow` 开关沿用，新增 `strata_config`（启动配置文件路径，支持 @here/相对），删 `gate_follow_poll_s`。跟随态闸的有效 limit＝该文件顶层 `"parallel"` 定死值（int≥1 取该值不钳制——钳制归引擎；False/None/缺席/bool/非 int/负＝引擎单发语义，闸卡 1）。读法＝模块级缓存＋`(st_mtime_ns, st_size)` 守卫（人类 00:31 续话 INTK-0004：「这个数字启动之后还会变吗？只要 Strata 启动一次没有死掉就不用重读啊！」）：每请求仅一次 `os.stat`（~4µs），守卫命中零 open 零解析，文件保存即自动跟随、无需重启网关。失败态两态同一条（缺文件/路径空/JSON 坏）＝缓存作废＋当请求退 `max_inflight` 静态兜底，不沿旧值、不缓存坏值，文件恢复即自愈。回退链收缩两级（文件读数→静态兜底→0 关闸）。rev11 轮询子系统定向拆尽＝六项 grep 归零（`_follow_loop`/`_engine_status_fetch`/`_engine_reading`/`gate_follow_poll_s`/`global _engine_reading`/main() 线程挂点）——零线程、零 HTTP、零轮询；跟随态对话路径亦零上游 GET（stub 计数 hits=0 行为证）。作废三断言逐名登记（`follow limit tracks engine serving`/`follow last-good on status loss`/`follow poll bypasses gate and records nothing`），新三断言承接行为面（`follow limit from strata_config parallel`＝文件值判别＋mtime 变更生效＋守卫命中恒值／`follow file failure falls back to static`＝缺文件与坏 JSON 两态退静态／`follow on still never polls upstream`＝hits=0）。
- **边界（不粉饰）**：引擎运行时往下压（显存降级/自调）网关不跟——闸仍卡启动配置文件上限，超出引擎能力的并发由引擎自身队列承接（最坏＝无闸现状），这是「网关只负责卡住上限」（23:13 裁定）的设计语义；配置文件中途不可读＝异常配置事故，当请求退兜底、下请求自愈、不沿旧缓存值。README 第九节第 11、12、13 条改写。
- **selftest**：proxy 41→**41/41**（41−作废 3＋新 3）；`grep -c '^PASS  gate:'`＝**19**（rev10/rev10a 10＋防误杀 4＋保留跟随 2＋新增 3）；monitor **54/54**、watchdog **16 passed 0 failed** 不变。红线机检：`urlopen` 回基线 **3**、`v1/status`＝0、`threading.Thread` 回 **1**、`global _engine_reading`＝0、`gate_follow_poll_s`（代码）＝0；无新锁（Lock=1、Condition=1 逐值不变）；新缓存面落位机检（`_strata_parallel_cache`/`_strata_parallel_limit`/`st_mtime_ns`/`global _strata_parallel_cache` 在场，float `st_mtime` 守卫禁语归零）；防误杀族四断言零改动（diff 族面零行＋逐名 PASS）；Gate 类本体零改动。MANIFEST 2.22。在岗 `config.json` 删 `gate_follow_poll_s`＋加 `"strata_config": "D:/Strata/strata-unsloth-ud-iq4_xs.json"`＋换脑＝票后置动作（安全窗口主理人另排）。

---

## 2026-11-17（rev11）· 排队闸跟随引擎实际并发：闸阈值从网关自填值改为上游引擎运行时读数（功能改动 · 三套全绿）

- **现象**：rev10 排队闸的上限 `max_inflight` 是人在网关侧另填的一个数，与引擎运行时实际并发是两处口径——引擎 `fit_parallel` 显存降级、`--batch` 引擎自调都会改真实槽数，而网关那个数不会自己动。两处填数＝漂移风险；人类 21:08 裁定口径（INTK-0001 逐字）：「对，所以网关不需要自己创造，就看 Strata 实际的启动配置就好了」。
- **根因**：闸的 limit 来源设计为静态配置，未接引擎运行时读数源（`/v1/status` → `concurrency.serving`＝引擎为「宁愿问也不猜」设计的客户端契约面，已含降级后真值）。
- **改动**：新开关 `gate_follow`（缺省 false＝行为与 rev10a 完全一致）＋`gate_follow_poll_s`（缺省 5s）。置 true 后：后台 daemon 线程（`name="gate-follow"`）周期 GET `{upstream}/v1/status` 读 `concurrency.serving`，缓存于模块级单写元组（唯一写者＝该线程，整体重绑 GIL 原子，读侧无锁）；对话请求每请求重读口径下解引用缓存——limit 自动跟随引擎运行时并发，人不用两处填数。回退链唯一口径：最后成功值（无限期有效）→ 静态 `max_inflight` 兜底（在岗保留人类已裁并发数当兜底）→ 兜底 0＝关闸；**无「临时全通」档**（不违 20:56「按 2slot 守住关卡」裁定）。监视页 limit 展示零改动即动态化（`_last_limit`→`snapshot`→`/ext.json` 链路 rev10 已备）。红线五条全守：无拒绝态；跟随下调不回收在飞（README §九 12）；缺省零回归（既有 32 断言逐字原样＋缺省态对上游零新增 GET——stub 计数 hits=0 为证）；热路径零新增上游同步调用零新增锁（Lock/Condition 计数逐值不变）；读数 GET＝旁路（不经闸、不进账本——闸满窗口内 hits 增长而账本行数增量 0）。**验收重心＝防误杀族（人类 21:18 补令「主要是测试第3路不会被误杀，一定有心跳机制通讯保活」）**：满 2 槽队列的第 3 路流式请求，先收 ≥2 帧带到达时间戳的 `: ping` 心跳（首帧 ≤0.8s、间隔 ≤0.8s），全程单一状态行不断连不 reset，空位后拿到上游真实 SSE（8 帧＋`[DONE]`），账本行 `queue_wait_ms≥400` 无 error；在飞两路速率不受排队者扰动（各自 ≤ 基线+1.0s）；心跳期客户端强断不留幽灵占位（终态 inflight=0 queued=0）；非流式第 3 路静默排队等满 `gate_wait_s` 照样 200 转发。
- **边界（不粉饰）**：跟随生效有一个轮询周期时延；等待中的请求 limit＝进闸时刻快照，新值自下一请求起效；跟随值下调瞬间在飞可超新 limit（闸不放新人，超额由引擎自身队列承接，最坏＝无闸现状）；引擎重启降并发后、新读数落地前可能短暂超放（同上）。README 第九节第 11、12、13 条。
- **selftest**：proxy 32→**41/41**（既有 22 基础＋10 gate 组逐字零改动＋跟随 5＋防误杀 4）；monitor **54/54**、watchdog **16 passed 0 failed** 均同基线。红线机检：`grep -cE '(429|409)'`=0；Lock=1、Condition=1 逐值不变；`urlopen` 3→4（新点＝`_engine_status_fetch` 体内唯一新增）；Gate 类本体 diff 零命中。MANIFEST 2.21。在岗 `config.json` 加 `gate_follow:true`＋换脑属票后置动作（安全窗口主理人另排）。

---

## 2026-11-17（rev10a）· 排队闸 v3 维护小批：入队观测即时可见＋死字段注释＋票面勘误登记（观测时效修复 · 三套全绿）

- **现象**：满位时第二请求入列后、首个 `queue_beat_s` 心跳前，`/ext.json` 的 `gate.queued` 滞后至多一个心跳周期才可见——QA 复攻 C3 探针实测 `queued_seen_in_ext=0`（观测损失根因＝入列与等待内环同处一个 `with self._cond:` 临界区，块内无 push 点，入队后首个 push 落在 10s 心跳）。
- **根因定位**：`Gate.acquire` 入列瞬间不推观测；`_push_gate` 三调用点（acquire 返回后/release 后/心跳计数后）全部晚于入列时刻。属观测时效缺陷，非闸语义缺陷。
- **改动**：E-2＝`Gate.acquire` 拆两段临界区——入列段（快路＋入列＋局部标志）退出锁后、首次 `_cond.wait` 前**锁外** `_push_gate` 恰一次（与 `on_beat` 同纪律：持锁不做 monitor 侧推送）；快路不入列不 push、每 acquire 至多一次入队 push、既有三处调用点内容零改动、`_last_limit` 时序不破坏。E-3＝`Gate.__init__` `self.queued = 0` 就近注释（展示真值走 `_waiters`，勿读此字段；`snapshot` 的 `queued` 键用 `len(self._waiters)` 实时值），语义零改动。T-2＝proxy 自测新增 gate 断言 `gate:queued visible in ext before first beat`（`queue_beat_s=10.0` 不重启调参＋3s 轮询窗口＋`t_seen < 10` 判别，修复前判红、修复后 ≈1–2s 判绿；收尾恢复 cfg）。
- **边界（不粉饰）**：观测时效修复，闸语义零变化——无拒绝态、不触在飞、缺省 `max_inflight=0` 行为不变全部沿 rev10 红线；`queued` 键仅**出现时机**提前，`/ext.json` 键面契约不变。
- **勘误登记（仓外）**：rev10 票 ②-3 S-5 伪码（`_gate_beat` 未置 `responded = True`）与 S-8 声明自相矛盾，落独立登记件 `rev10-gate-v3-erratum.md`（治理族，不在仓内）；81783d5 实现已置位＝必要纠正（QA 判据③ `status_lines=1` 佐证）；rev10 票本体 append-only 不回改。
- **selftest**：proxy 31→**32/32**（既有 15＋9 组逐字零改动＋新 1）；monitor **54/54**、watchdog **16** 均与基线同数。红线机检 `grep -cE '(429|409)' collector_proxy.py` = 0；`_push_gate` 调用点 3→4（新点居两段临界区之间·锁外）。MANIFEST 2.20。在岗换脑属票后置动作（安全窗口主理人另排）。

---

## 2026-11-17（rev10）· 排队闸 v3：网关侧对话请求 FIFO 准入＋SSE 等待心跳（功能改动 · 三套全绿）

- **现象**：引擎并行模式（本机 parallel=2）准入环节无闸、work-conserving、无 FIFO 序——多请求并发时会话降成龟速（实机：双满每行 ~32 tok/s vs 独行 ~110）。源码核对实锤引擎 `QUEUE_BEAT_S=10` 心跳纯保活非准入闸。
- **根因定位**：缺口在网关补——反代是唯一能看见全部入栈请求的中立层；不给 Strata 源码再背调度器补丁（已 1700+ 行本地补丁）。
- **改动**：`config.json` 三参数（`max_inflight` 缺省 0＝关／`queue_beat_s` 缺省 10／`gate_wait_s` 缺省 600），每对话请求重读＝改值不重启下一请求即效。`max_inflight>0` 时仅 `/v1/chat/completions`、`/v1/messages` 挂闸：在飞达上限→新对话请求进网关 FIFO 队列按序等待（空位**直接移交队首**，新到者不得截胡）；等待超 `queue_beat_s` 的流式请求先收响应头＋`: ping` SSE 注释心跳帧（chunk 帧格式与 `_pump` 一致），槽位一空无缝接引擎真实流；等满 `gate_wait_s` **照样转发**——全程无拒绝态（429 重试风暴事故实证在先，闸门绝不产出上游永远不会产生的东西）、绝不触碰在飞请求（finally 归还是唯一出口）。观测：`/ext.json` 新增 `gate` 段五键（闸未启用＝字段整体缺席）；监视页「等待中」卡仅 `queued>0` 时出现（防与引擎原生 queued 混淆）；账本行等待过才写 `queue_wait_ms`。
- **边界（不粉饰）**：心跳承诺不可撤回——头已上线则同连接容不下第二响应，排队期间上游本身出错（413 超长类）降为流内/流断形态，账本 `error` 如实登记；非流式对话请求排队全程静默（无可发字节），等满照样放行。详见 README 第九节第 9、10 条。
- **selftest**：proxy 22→**31/31**（原 15 组断言逐字零改动＝缺省零回归面＋9 组 `gate:` 断言：判据②~⑧＋gate 段形状＋缺省无 gate 段）；monitor 52→**54/54**（H-1 态甲：node 行为冒烟喂 gate 三态——缺席无卡／queued=2 出卡含「网关等待」文案／回 0 清卡）；watchdog **16** 不变。红线机检 `grep -cE '(429|409)' collector_proxy.py` = 0；三参数缺省全关落模板。
- MANIFEST 2.19。在岗换脑属票后置动作（安全窗口主理人另排；在岗首值 `max_inflight: 1` 不在本票执行）。

---

## 2026-11-17（rev8 后补六）· 边界条改写＋看护声明补核对出处（纯文档，功能代码零改动）

- 第九节第 2 条「非流式长请求仍会静默」改写：该现象是非流式协议本性（接不接本工具都存在），移出本包代价口径；本包定位＝对使用体验零改变、只加细粒度 token 记账。≥600 秒设备读超时建议保留，定性为通用环境建议。
- 第八节「官方引擎壳自带引擎看护」补上游核对出处：官方 tag `v0.2.6` pristine `serve/server.py` 实有 `restart(tries=3)`/`RESTART_RETRY_S=15`/`ENGINE_SILENCE_S=300`（#481/#1317 quick watchdog）＋官方 `test_fatal_recovery.py`/`lifeline.py`。origin/main 领先基线未核（通路 502），如实登记。
- MANIFEST 2.18。

---

## 2026-11-17（rev8 后补五）· 省钱口径进 README + 价表 csv 随包（纯文档/数据，功能代码零改动）

- 皮总点题：本地算力用户最核心的一句话＝「自己用了多少、相比接 API 省了多少钱」。自查发现网页报表的**省钱计算器**（内置 22 款模型牌价折算）在 README 卖点区完全没提，且注释引用的 `api-price-table.csv` 从未随包——002 拿到的悬空指针。
- **`api-price-table.csv` 补入仓**（公开牌价＋各家官方页出处＋峰谷/分档备注，2026-11-05 核验；与在岗 csv cmp 一致）。README 卖点区新增省钱条目（排第二）、第四节加计算器导读段＋真机折算实拍 `docs/savings-calculator.png`（近 30 天账本：最贵一档 $5,600≈¥39,300 vs 最便宜可比 $29≈¥205；口径注释随图）。
- MANIFEST 2.17、文件数 33→35；脱敏实证：csv 全公开牌价、截图裁切区无身份列。

---

## 2026-11-17（rev9）· CPU 卡标题带型号（`ext.cpu_name`）

- **采样端**：`monitor_ext.py` 新增 `cpu_name()`——Windows 走注册表 `ProcessorNameString`（与任务管理器显示同源），Linux 走 `/proc/cpuinfo` 的 `model name`；纯标准库、静态读一次进缓存；多余空格折叠、64 字符截断、任何失败返回空串——**采不到就保持光 "CPU" 标题，绝不编名字**。字段进 `/ext.json` 为 `cpu_name`。
- **前端**：CPU 卡（单插槽与多插槽两分支）标题变 `CPU · 型号`；`ensure` 只在卡片首建时写标题，而 `/ext.json` 可能晚于 `/metrics` 到——label 节点每拍**幂等刷新**补齐。型号过长进 `mx-label-t` 一行省略号口径，不撑卡。
- **selftest** 52/52（新增两条：标题两分支+幂等刷新+裸标题永不复活的反例守卫；采样端源锁〔注册表键/proc 路径/空格折叠/截断〕）；proxy 22/22、watchdog 16/16 不变。node 冒烟 stub 喂含 `<x>` 的型号名走 `esc` 转义链。
- 在岗换脑走 `switch_proxy.py`：第一轮判有 2 条 idle 连接**硬拒绝**未 force（纪律优先于便利）；第二轮在操作会话处工具段、无在飞生成的安全窗 `--force` 切成——1.52 秒回岗、`/ext.json` 出 `cpu_name`（AMD Ryzen 9 7950X 16-Core Processor）、前端实拍确认标题一行不撑。README 硬件区截图同步刷新为带型号版。

---

## 2026-11-17（rev8 后补四）· README 配真机在岗截屏两张（纯文档，功能代码零改动）

- 新增 `docs/monitor-hardware.png` / `docs/monitor-ledger.png`：`/monitor` 页真机在岗实拍（Edge headless 截取后按内容边界裁切），插在第一屏卖点区——上半页逐卡逐盘逐网卡硬件读数，下半页逐请求 token 账＋合计行＋对话缓存卡，配两句读法图注（82% 输入复用 ↔ 解码稳 110+ tok/s；深浅两套主题、按 UUID 绑卡）。
- **坚持实拍不示意图**；脱敏双检（截图前目检＋入仓前复检）：无指纹/姓名/key/IPv6——该机无 key 模式，请求表本就无身份列；MANIFEST 新增 2.15 节并登记文件数 31→33。

---

## 2026-11-17（rev8 后补三）· README 开头重写为价值主张开场（纯文档，功能代码零改动）

- **标题区重写**：问题式定位（谁在用 / 用了多少 / 这台机器扛不扛得住）＋五条卖点——①账按人算、数字取引擎官方字段；②长生成不掐线（逐块转发、首字节约 0.01 秒，含「号称流式实为整包缓冲」这个坑的实机 A/B 实证）；③开箱监控页（异构逐卡、读数与任务管理器同源）；④5 秒自愈＋有人用即拒切换；⑤零依赖主链仅标准库。随后紧跟「代价也先说清楚」段引流第九节，再接「三分钟上手」命令块（clone→init→check→start）。
- **第一节主语通用化**：从「我们内部旧链 vs 本工具」改为「自己写脚本读引擎日志的通用做法 vs 本工具」——外部访客没有我们的旧链，对照对象必须是他们会走的路。
- **两处如实化**：开头引用块里指向内部工具包路径的提醒删除（分叉事实仍登记于 MANIFEST 第三节与 SKILL.md，公开仓不写只有我们可达的路径）；macOS 从「实测跑通」改为「同套启动件＋平台模拟验证」（无 macOS 实机，不混称实测）。
- 第二节往后的实操章节口径一律未动。

---

## 2026-11-17（rev8 后补二）· 第十一节改版为「真机踩坑登记」（纯文档，功能代码零改动）

- 原 6 条结论式全部改写为「**症状 → 根因 → 对策**」三段式——排障的人先见到症状、不知道要找什么，结论式不可对照。节名同步改「真机踩坑登记」。
- **新增 4 条**（共 10 条）：②`gaierror 11001` 无限重拉单列成条，附「002 首版在跑先 `git pull`」升级指引；③**引擎区红≠本工具坏**——监视页上半区是浏览器直连引擎 `/metrics`，与反代两条独立链路，先分半页再查引擎进程与 `upstream`；⑨**端口口径全网统一**：门面 `8080`、引擎退环回 `8787`，各机只改数值内的东西，偏离＝全网变更不是本机自由；⑩`listen`+防火墙放行+看门狗重启**三件套同轮**完成，防「端口通但没人守」。
- 不入仓边界同轮裁定：宿主平台行为、本机网络形态、执行沙箱限制、另一产品线档案——与本包无关，一律不入。

---

## 2026-11-17（rev8 后补）· 样例与实测经验入仓（纯文档/样例，功能代码零改动）

- **新增 `config-examples/`**：两份脱敏实例配置——`windows-5090-single-gpu.json`（Windows 单卡终端**在岗实机抄录**，示范 IPv6 双栈门面 + 引擎退环回 + lock 避让改值）与 `ubuntu-pro5000-4090-dual-gpu.json`（Linux 双卡工作站**装配参考**，示范双卡零配置、缺依赖降级、systemd 口径）。机型不是本包配置项（监控按 UUID 动态逐卡发现），样例只示范结构与端口口径；真实地址、指纹、姓名 0 命中。
- **README 新增第十一节「真机实测登记」**：限定与本包功能相关的实测结论 6 条——①IPv6 双栈地址族须在实例化前定类属性（rev8 修）＋改 listen 必重启看门狗（旧脑闪窗定式）；②Win11 注册表 `~MHz` 钉死基准＝废源，实时频率唯一正确源＝PDH × 基准（`PdhClock` 已内置）；③消费卡空闲 ASPM Gen1、负载 Gen5 是链路本态非读数陈旧（饱和拷贝实验实证）；④双卡异构组合无需配置，旧 `ext.js` 槽位分桶有串卡风险已退役；⑤缺 `psutil`/`nvidia-smi` 只降级监控，补装要装进**服务实际使用的那个解释器**；⑥登录环境无交互 PATH，自启件解释器一律绝对路径。
- 第二节第 3 步加样例导读表；`MANIFEST.md` 同步（文件数 29→31、新增 2.12 节）。

## 2026-11-17（rev8）· 000 实测场：双栈监听修复 + CPU/PCIe 卡实时增强 + 改 git 仓分发

全部改动在 000（5090 单卡终端）实测验证后回流。本仓为该包首个 git 分发形态（此前以 zip 传递）。

- **[bug 修] IPv6 双栈监听必炸**：`collector_proxy.py` 的地址族在 `server_bind()` 里才定——但 socketserver 先建 socket 后调 bind，AF_INET 套接字绑 `::` 必 gaierror 11001，看门狗连拉数十次起不来。修法＝地址族在实例化前定为类属性（host 含 `:` → AF_INET6，IP_V6ONLY=0 双栈）。实测：v4+v6 `/health` 双绿、看门狗 5 秒巡检补岗生效。**002 母包需带此修。**
- **CPU 卡大数字后跟实时 GHz（两轮，第一轮被实锤作废）**：第一轮取注册表 `~MHz`——Win11 上它钉死基准频率（实测常年 4500，睿频不进，任务管理器并不读它），4500↔4501 的"吻合"是撞低频瞬间。第二轮＝新增 `PdhClock`（ctypes → pdh.dll，纯标准库无新依赖）：PDH 计数器 `\Processor Information(_Total)\% Processor Performance`（英文计数器路径，中文系统 locale-proof）× `MaxClockSpeed` 基准，与任务管理器"速度"完全同源。实测 5.06–5.15 GHz 跟随负载。任何失败＝字段缺失、前端自动省略，不破账纪律不变。**定式：Windows 实时 CPU 频率唯一正确源＝PDH × 基准频率；注册表 `~MHz` 不可用。**
- **PCIe 线路卡大数字后跟领先卡实际链路 `GenN ×W`**：数据源 nvidia-smi `pcie.link.gen/width.current`（NVML 即时查询，不落注册表）。A/B 饱和拷贝实验验证读数真实：空闲 Gen1×16/SM 195MHz → 9 秒固定内存 H2D 搬运 418.8GiB（≈46GB/s，Gen5 量级，物理上排除虚报）→ 瞬跳 Gen5×16/2902MHz → 停载后 ASPM 延迟降档属链路本态，非读数陈旧。
- **`selftest_monitor.py` 断言对表**：CPU 单插槽大数字断言放宽为「`%` 大数字＋可选 GHz 后缀（门控 `ext.cpu_mhz`）」形态；新增反例守卫＝旧无 GHz 行形态与无门控路径永不复活。当次 **50/50** 全绿；proxy 22/22、watchdog 16/16 不变。
- **分发形态改 git**：仓库只含包体。本机专属件一律不入库（`.gitignore`：`config.json`、`data/`、`*.log`、`relaunch-now.flag`、本机启动 bat）——换机安装走 `python bootstrap.py --init`（template→config，从不覆盖已有配置）。端口口径按 README 缺省：门面 `listen 8080`、引擎环回 `upstream 127.0.0.1:8787`；`lock_port`/`watchdog_lock_port` 按各机在用软件避让自选（000 填 43180/43179 避旧链）。

---

## 2026-11-16（monitor-rev6）· 监视页六稿：磁盘/网卡/CPU 卡形态重构 + 小字基线对齐 + 一起前端事故的收拢

对应 `MANIFEST.md` 2.11 节（明细对照表在该节，此处只收拢叙事）。主理人在生产连续热修前端，本席做「断言对表 + node 冒烟 + 重打 ZIP」收口；功能代码改动均已落生产+母本两边、字节级一致。

- **线上事故与修复（先登记）**：五稿收口后的一版热修引用了未定义常量 `SPEED_DECODE`/`SPEED_PREFILL`，页面 JS 抛 ReferenceError，**所有读数全部消失**（用户线上实锤）。修复为 CSS 类方案（`swc(cls)` 助手 + `.mx-sw--decode/--prefill`）。**新增 node 冒烟守卫**：selftest 内联最小 DOM stub 真跑 monitor.js IIFE + tick 渲染链——`node --check` 抓不到未定义标识符，只有真跑能抓（正是这类事故）；js 中 `SPEED_DECODE`/`SPEED_PREFILL` 永不允许出现（回归断言锁死）。
- **磁盘卡重构**：标题 = `#编号 盘符 型号 · 容量`（编号内部 0 基、显示从 #1 起）；大数字 = 数值 + 单位 + 总线规格代码徽章（去 `Disk N · ` 前缀）；读/写移入小字两行（绿/橙 10×3 短线图例）。
- **网卡卡**：无线网卡标题就叫「无线网卡」且不出徽章；有线网卡标题 = 适配器真名 + 「有线」徽章（中途 `NET_KIND_LABEL`/WLAN 方案已废，断言反向锁死永不复活）；大数字 = 下行数值 + 单位；小字两行 = 下行/上行。
- **CPU 卡图例**：双插槽时左右小字各一条短线对应左右波形色；单插槽也有图例（短线 + 核/线程或「整机」）；波形右线（预填充色）改 `currentColor 65%` 加深——图例颜色恒与所在卡波形色一致。
- **小字基线对齐**：各卡「大数字下面的小字」起始高度统一——`cardHtml` 标题文本包 `mx-label-t`（恒一行 + 超长省略号）、`.st-metric__value` 定高（徽章撑不高行）；徽章撑高行框的真凶用 `.st-metric__value .st-badge{vertical-align:middle}` 修掉（中途 `inline-flex` 方案因间距副作用已撤销并有反例守卫）。
- **GPU 卡序号前置**：标题改为 `#序号 + 卡名`（与磁盘同款、从 1 起），序号带「槽位号会漂，仅供对照，不作为身份」提示；旧「名称在后带 0 基 #index」形态有反例守卫。
- **`selftest_monitor.py`**：断言按以上终态对表（作废旧 `&nbsp;` 大数字、`NET_KIND_LABEL`、单插槽 `setSub`、0 基 `#index` 四组旧锁并转反例守卫），当次 **50/50** 全绿；proxy 22/22、watchdog 16/16 不变。
- **重打包**：`strata-ledger-proxy-2026-11-16.zip` 覆盖重打 **29 文件**，解包实测三套全绿；未启动/停止/重启任何生产进程，8080 未动。

---

## 2026-11-16（monitor-rev5）· 监视页五稿收口：PCIe 卡单卡化对齐 selftest + 重打 ZIP

对应 `MANIFEST.md` 2.11 节。摘要：

- **前端终态登记（主理人热修已落两边，本轮未改功能代码）**：PCIe 线路卡简化为单卡单线——大数字 = 本轮读速最快那张卡的即时 MB/s；小字固定两行（「当前最高读速」+ 同色短线图例与显卡名）；独立图例区删除。磁盘/网卡卡小字走 `innerHTML`（内嵌 10×3 `mx-sw` 短线图例）。零告警纪律与显示基线不变。
- **`selftest_monitor.py` 对齐**：作废「每卡图例行 `mx-legend__row` 存在」断言；PCIe 卡断言改锁五稿终态（lead 选择逻辑关键串、「当前最高读速」固定文案、小字 `innerHTML` 图例+卡名）；新增独立图例区缺席、disks/net `innerHTML`、`.mx-sw` 10×3 短线三组断言；「告警缺席」断言加强（js+css 同时断言四类告警元素全缺席）、「显示基线」断言原样保留。当次 **39/39 全绿**。
- **文档同步**：README 第六节 PCIe 卡描述改为五稿终态；MANIFEST 新增 2.11 节并更新修订口径与文件表。
- **重打包**：`strata-ledger-proxy-2026-11-16.zip` 覆盖旧 27 文件版（旧版漏打 `monitor.css`/`monitor-sprite.svg`），按包内全量重打 **29 文件**，打包后 `zipfile` 核对。
- **母本↔生产**：核心件逐文件 `cmp` 字节级一致；未启动 / 停止 / 重启任何生产进程，8080 未动。

---

## 2026-11-16（monitor-standalone）· 监控页重构：自持独立页，按卡的唯一身份绑卡

对应 `MANIFEST.md` 2.8 节。摘要：

- **彻底弃用官方页面注入**：删掉整套「往 Strata 控制台页面塞脚本」的机制（`attach/pages/Watcher`）。本工具从此不写任何它不拥有的页面；配置里的 `web_root` 字段弃用（留着不报错，可删）。
- **自带监控页**：打开 `http://<主机>:<端口>/monitor` 即完整监控页（`monitor.html` + `monitor.js`，数据走同源 `/ext.json`），卡片布局大数字+副行+波形，零第三方依赖，深浅色跟随系统。
- **修根因**：旧注入页把显卡波形按 nvidia-smi 槽位号存历史，而槽位号会漂（本机实证：A 卡波形画到 B 卡卡片上）。新页一律按显卡唯一身份（UUID）绑定卡片与波形历史，槽位号只在标题展示；极老驱动没有 UUID 时退卡名，绝不退槽位。
- **数据接口只增不改**：`/ext.json` 的 GPU 行新增 `uuid`、显存/编码/解码利用率四个字段（nvidia-smi 查询 10 列 → 14 列）；旧注入页过渡期照常渲染。`/ext.js` 仅为过渡兼容保留，官方页恢复原状后即可退役。
- **新增第三套回归 `selftest_monitor.py`**（本轮 21/21 通过；含「槽位 0/1 互换、唯一身份不变→历史不串卡」用例）。`bootstrap.py --selftest` 现跑三套。
- **记账主链零改动**：`collector_proxy.py` 只改了文档注释和一行启动提示；转发契约、记账、看门狗、切换纪律全部未动。
- **同日工程复核后补修（11-16 二稿）**：①`GPU_QUERY` 编解码字段改驱动实证可用的 `utilization.encoder/utilization.decoder`（旧名 `encoder.utilization/decoder.utilization` 在 621.24 驱动下整条 nvidia-smi 查询 rc=2 失败、所有显卡消失——真 bug，真机复验新名 rc=0 双卡 14 列全解析）；②更正 11-12 段不存在的 `archive/` 回滚件说法；③README/SKILL/MANIFEST 补看门狗划界：本包 `ledger_watchdog.py` 只守护本包记账反代，与 Strata 官方引擎壳（`terminal/serve/server.py`）自带的引擎进程看护无关、不碰不依赖；④`ext.js` 本轮跨源 API 解析改动补登记进 MANIFEST 2.8；⑤`bootstrap.py` 自测口径「两套」改「三套」；⑥README 补旧注入页过渡期仍按槽位分桶可能串卡的提示、补 /monitor 自身故障的退回路径。
- **同日三稿：`/monitor` 升级为官方监视页完整复刻 + 硬件卡融合视图**（用户拍板终极形态，对应 `MANIFEST.md` 2.9 节）：视觉与之前寄宿官方页的形态一致，但页面、样式、图标、数据、渲染 100% 本包自有文件——新增 `monitor.css`（官方 st-* 令牌/组件/布局逐条移植，深浅色两套）与 `monitor-sprite.svg`（12 个图标 symbol 逐字拷自官方 sprite）；`monitor.html`/`monitor.js` 重写为融合视图（模型状态卡、Speed 双曲线、每 GPU 卡按 UUID 绑定、CPU、System RAM 含 swap、每物理盘、每已连接网卡+合计、Context fill 环表+三条进度、Recent requests 9 列+totals、Conversation cache）；每秒并发 fetch `/ext.json` 与 `/metrics`（反代原样转发引擎）两源独立容错；引擎 key 读写官方同键 `localStorage["strata.apikey"]`，401 时页面小输入框补填存回同键；页脚自报账本工具自持页面。`monitor_ext.py` 唯一 py 改动 = 加 `/monitor.css` 与 `/monitor-sprite.svg` 两条静态路由（上线需按切换纪律重启一次窗口，时机主理人定）；`bootstrap.py --check` 必需文件 13→15 项；三套回归扩断言后按当次实际输出全绿。GPU 采样/14 列契约、记账主链、看门狗、切换纪律、`ext.js` shim 未动；官方 `terminal/serve/web/` 未写一字。
- **同日四稿（含用户口径修订）：每卡 PCIe 链路字段（GPU 查询 14→18 列）+ 每卡多色实时线路波形**（对应 `MANIFEST.md` 2.10 节）：`/ext.json` 的 GPU 行新增 `pcie_gen / pcie_width / pcie_gen_max / pcie_width_max` 四个链路字段（621.24 驱动真机实证 rc=0）与每卡吞吐 `pcie_rx_mb / pcie_tx_mb`（该驱动无 `pcie.throughput.*` 查询字段，rc=2 实证；改走 `nvidia-smi dmon -s t` 同 tick 按枚举序配对 uuid）。监视页顶部 PCIe 卡升级为**每 GPU 一条彩色实时波形**，图例每卡一行「卡名 · Gen5 ×8 · 360 MB/s」，另并入引擎侧实测一条；GPU 卡副行加中性 `PCIe Gen5 ×8` 文字。**不做任何退化告警/红标**——用户口径：本机 ×8 就是稳态正常值（7950X 双卡各 8 lane），空闲降代显示 Gen1 也属正常；首版做过的退化徽章机制已全部移除并有回归断言防复活。旧 14 列形态整行丢弃规则保留。生产上线需要 8080 按切换纪律重启一次窗口。
- **生产待办（本包不代做）**：官方页面从 `index.html.orig` 恢复（README 6.1 给了命令）；8080 按切换纪律（先 `switch_proxy.py --check`）重启一次生效。本轮未启动 / 停止 / 重启 / 连接 / 占用任何生产服务端口。

---

## 2026-11-12（startup-example-fix）· 修正 Windows 自启示例 / 终版重打包

对应 `MANIFEST.md` 2.7 节。摘要：

- **修掉一个会静默失败的坑**：`service-examples/Strata ledger watchdog.vbs` 原注释让人「把 VBS 放进启动夹」，但脚本按自身目录找 `ledger_watchdog.py`；复制过去后目录变成启动夹，看门狗根本起不来且不报错。改为 **VBS 留在包目录、启动夹只放快捷方式**（快捷方式启动时脚本解析到的仍是自己的真实路径，所在目录不变）。
- **解释器可指定**：新增 `STRATA_PYTHON` 环境变量覆盖（Python 不在 PATH 时指向 `python.exe` 全路径），不再经额外的命令处理器中转、直接运行解释器；用 `Chr(34)` 拼引号避免转义出错；`--lock-wait 86400` 与纯 ASCII + CRLF 保持不变。
- **文档同步**：`README.md` 第二节表格与说明、第九节第 7 条，`SKILL.md` 第 6 步表格与说明，全部改成「启动夹放快捷方式」并写清原因与 `STRATA_PYTHON`。
- **重打包**：`strata-ledger-proxy-2026-11-12.zip` 覆盖为终版（24 文件）。回滚件即 dist 下现存的 `strata-ledger-proxy-2026-11-12.zip` 与更早的 `strata-ledger-proxy-2026-11-11.zip`（当时另存于 `archive/` 的说法不实，2026-11-16 已更正——该文件从未存在）。
- **未动任何运行主链**：包内 `.py` / 配置模板 / `start.bat` / `start.sh` 一字未改；未启动或停止任何生产进程。

---
## 2026-11-12（watchdog-align）· 看门狗对齐 / 自启接管 / 重打包

对应 `MANIFEST.md` 2.6 节。摘要：

- **生产看门狗对齐**：`usage/ledger_watchdog.py` 新增自包含 `ports_from_config()`（不 `import paths`）、`--port` / `--lock-port` 默认跟随 `config.json`、`launch_ledger()` 的 POSIX 分支加 `start_new_session=True`；`resolve_collector()` 默认路径与 `--lock-wait` 候补锁循环未动。
- **开机自启接管**：两个 Windows 启动夹 VBS 追加 `--lock-wait 86400`，登录副本改为热备候补、旧看门狗退出后零缝隙接管；注释改纯 ASCII、CRLF（清掉 P3-5）。
- **回归自测**：`usage/selftest_watchdog.py` 新增端口解析 / 显式参数优先 / 候补接管用例，原有回归用例逐字保留，按当次实际用例数报出；`bootstrap.py --selftest` 两套回归全绿。
- **文档与工程化**：`bootstrap.py` 加 `sys.path` 兜底（P3-2）；`README.md` 补畸形 `Bearer ` 边界（P3-1）与 VBS 候补说明；`MANIFEST.md` 清掉写死用例数（P3-4）、文件总数口径改 24；新增本记录。
- **重打包**：`strata-ledger-proxy-2026-11-12.zip`（24 文件），保留 11-09 / 11-11 两个旧 ZIP。
- **生产进程状态（如实）**：生产 `8080` 已于 2026-11-12 20:19 切换到 11-11 归因修复版并实证生效；**看门狗磁盘代码已对齐但进程待主理人交接**。本轮只改磁盘文件，未启动 / 停止 / 重启 / 连接 / 占用任何生产服务端口。

---

## 2026-11-12（docs-r2）· 文档层重构

- 新增 `SKILL.md`：宿主 Agent 的部署工序入口（模式判定表、前置自检、必问人类拍板项、编号工序、验收判据、运维与故障、边界与债、每日投递工序）。
- 新增 `CHANGELOG.md`：本文件。
- `README.md`：顶部插入「Agent 部署入口」短小节（指引宿主 Agent 直接按 `SKILL.md` 执行；README 其余内容一字未动）。
- `MANIFEST.md`：文件清单登记两个新文件；改动登记新增 2.5 docs-r2 小节；发行版本修订日期更新为 2026-11-12。

**本次未改任何 `.py` / `.bat` / `.sh` / 配置模板，契约不变量全部未动。**

---

## 2026-11-11（rev）· 按 key 归因修复轮

对应 `MANIFEST.md` 2.4 节。摘要：

- `collector_proxy.py`：新增 `key_identity()`——先 `strip()` 再按 RFC 7235 大小写不敏感剥 `Bearer ` 前缀，`Bearer` / `bearer` / `BEARER` 归一；账本每行新增 `fp` 字段（原始 8 位指纹永久留存，便于事后拆分合并、追查撞码）。
- `selftest_proxy.py`：新增归因用例（大小写归合同 `key`+`fp`、`x-api-key` 记录合法 `fp`、全量账本行 `fp` 格式校验），用例数按当次实际输出报出。
- `bootstrap.py --check`：新增 `key_labels` 纯读取校验（键须 8 位小写 hex、值须非空、同姓名合并仅 warn、空配置 warn）；`lock_port == watchdog_lock_port` 改为不合格。
- `README.md`：第三节补三个坑（裸 key 不带 `Bearer `、空 `key_labels` 看似撞车、同姓名合并不可从历史拆开）；第九节新增「8 位指纹可能撞码、不做自动检测」边界。
- `daily_report.py` / `html_report.py`：已核查未改（按 `key` 分组，`fp` 不影响出表）。
- 回归自测：两套均按当次实际用例数报出且全绿。
- 生产母本同步改磁盘但**未重启任何进程**（磁盘代码已更新 ≠ 进程已生效）。

---

## 2026-11-09（v1）· 首版发行

给另一台机器（代号 5090）替换旧「旁路边读引擎日志」账本链的独立工具包。首发内容：

- **反代逐块流式修复**：响应头立即发出、每个上游数据块到达即 `flush()`（首字节约 0.01 秒）；源母本的 `resp.read()` 整包缓冲会原样复现 502，本包版本已修正。
- **按 key 指纹归人**：SHA-256 前 8 位十六进制指纹映射姓名，配置不存原始 key，`python collector_proxy.py --fp <key>` 算指纹。
- **看门狗**：5 秒巡检、掉了自动补岗、配置热更新、立即补岗标记、脱离会话拉起服务。
- **切换纪律**：`switch_proxy.py` 唯一切换入口，有客户端会话硬拒绝且 `--force` 不覆盖，判忙窗口 5 分钟。
- **两套回归自测**：`selftest_proxy.py`（假上游 + 临时端口）+ `selftest_watchdog.py`，不碰正式服务。
- **三平台启动件**：Windows 启动夹 VBS / Linux systemd（`Restart=always`）/ macOS launchd（`KeepAlive`）。
- **legacy 兼容件**：旧读日志采集器 + 排程（可选，主链不依赖）。
- 交付前修复轮（同日）：路径相对化（`@here`/`@pkg`/`~`）、端口自动跟随（`ports_from_config`）、脱会话子进程（`start_new_session`）、去硬编码、指纹/姓名脱敏、日报与网页报表口径如实化——逐项见 `MANIFEST.md` 2.1–2.3 节。
