# GATEWAY-HANDOFF-20261123 网关面统一交接件（Basalt 会话 → 网关会话）

性质：交接文档（用户持转）。网关仓是否立案、票型、落位由网关会话自定；本会话对网关仓零写。
内容＝上篇（调优顾问调研移交）＋下篇（压测归网关工单稿）。两篇同源同日，合并交付。

────────────────────────────────────────
上篇 · 调优顾问面移交：调研实缺结论＋实测能力＋经验案例
────────────────────────────────────────
来源：Basalt 会话 2026-11-23（用户令：写交接件移交，网关侧自行立案实施工单）
本件是交接文档，不是工单：网关仓是否立案、如何立案、写到哪里，由网关会话自己决定。

【一、调研实缺结论（已查证，可直接采信）】

1. Strata 有真正的自动调优器但形态重：terminal/strata_cli/tune_commands.py +
   strata_control/autotune.py（`strata tune auto`）。机制＝从用户当前配置出发、
   单旋钮交错轮测、只收超噪声增益（>=+3% 且 >2x漂移 且 >2xA/A），存预设开机自动应用；
   支持 --goal room / --leave-ram PERCENT 这类资源约束目标。
   调优知识在 tune_knobs.py（候选表＝数据行，来源官方内部 TUNING-SPEC.md，不交付用户）。
   代价＝搜索式：quick 约 20min、thorough 最长 2h，每候选真起引擎。
2. Basalt 只给建议不改配置：官方 basalt-probe（docs/probe.md）测机器速率后对
   --pool-workers / --adapt-* / --prefill-cpu-share / --expert-profile-save 打印建议值，
   原文 "It is manual: it changes and saves nothing"。
   002 机运行区已有现成 exe：C:\Work\LLM\Basalt\runtime\basalt-v0.5.0-windows-x64\bin\basalt-probe.exe
   （尚未用过，网关侧可直接调）。
   docs/community.md 的 basalt-bench --community 是基准提交仪式（统一预设、一行一机），
   是采集端不是调优器。
3. 两边都没有"按资源预算反推配置"的 skill/用户文档——这正是网关面的差异化空档：
   网关已天然看得见资源水位、并发形态、基准注册表（benchmark-registry.json），
   适合做"环境画像＋分布标定＋经验库查询"层；搜索/验证仍交引擎侧官方工具，勿重造 tuner。

【二、可直接移交的实测能力与经验（拿来即用）】
A. 专家驻留覆盖线探针：C:\Work\Projects\basalt-fork\ops\expert_coverage.py
读 /metrics 的 experts_map.routed（640 槽抽样，0.5s 轮询累计）→ 直接算覆盖线，
不重启引擎、无需搜索轮次。实测标定（qwen3.8-flash-next IQ3_S，Strata 分层）：

- 每专家 约 2.1 MiB；全驻 约 51.3 GiB（RAM 仅 0.3 GiB，"every expert is resident"）。
- 90% 路由覆盖＝前 28.3% 专家 约 14.6 GiB；99%＝前 47.5% 约 24.5 GiB。
- 覆盖线单位是"专家数/显存"，不等于上下文长度；"80K+ 才回文件层"这种说法要把
  token 换算成路由专家覆盖才成立。
- 价值定位：腾显存换模型时的现成刻度（已留存 Basalt/Strata 双方 .workbuddy 记忆）。
B. ram-reserve-mib 口径（已裁定落地）：官方默认 2048（docs/running.md，含 2GiB 后置垫层）；
   16384 是护栏误伤时代遗产、4096 是无立案搬迁值，均废弃。生产档 iq3_s-6slot-strata-copy.json
   已改 2048（备份 .bak-ram2048），待下次引擎重启生效。
C. prefill-cpu-share 实测（002 机）：默认 0.6=5624 tok/s vs 设 0=5758 tok/s（+2.4% 噪声内）
   -> 不改，生产档无此项。冷 prefill 探针 ops/prefill_probe.py；语料须滤 DSML/<tool_calls> 否则 500。
D. 基准锚点已在网关侧：benchmark-registry.json（模板 bench-6x256k-v1：
   6 路合计 135.2 / 每路中位 68.2 / 单路 204.3 / prefill 2730；A/B 必须冷启动或先热身）。
E. 环境坑（防止重演）：本机 HTTP 探测必须 ProxyHandler({})（环境代理伪造 502）；
   等引擎就绪盯 engine.log 的 "session is up"（run_prod.log 无此标记），加载约 1 分钟。
F. 概念判据（调优顾问话术标准）：分层驻留不等于量化——量化改表示（付质量），分层改位置
   （付尾延迟、质量零损失），两杠杆正交可叠加；"默认值不等于可选范围"；一次报错不等于一条禁令。

【三、建议挖的用户价值点（方向，不 prescribe 实现）】

1. /capabilities 已有骨架 -> 扩 "advice" 或独立 /tuning 只读接口：按当前资源水位＋
   已登记 bench 返回"建议档位"（驻留覆盖线、slot 数、ram-reserve），只建议不改配置
   （对齐 Basalt probe 的 manual 哲学，改配置留给用户/官方 tuner）。
2. 经验知识库落仓：把 A-F 做成结构化档案（yaml/json：适用条件＋实测值＋出处），
   未来 Strata/Basalt 社区案例可持续并入——网关成为跨后端的唯一经验索引。
3. 环境画像采集（只读、低频）：GPU 显存/RAM 水位、引擎版本、已加载 pack ->
   与经验条目匹配（"这台机跑这个 pack，90% 线要 14.6 GiB，你还有 X GiB 空闲"）。
4. 勿重造 tune auto：Strata 搜索式 tuner 由 Strata Terminal 承担；网关只做
   "该不该调、往哪个方向调、预算是多少"的决策层。

【四、验收要点（供网关侧立案参考）】

- 经验档案入仓且每条含出处与适用条件；
- 接口扩展不破既有消费端（NAS 算力池）；
- 引用 002 实测数字处注明机型（PRO 5000 72GB / 64GB RAM / 1,344 GB/s）与模板 ID。

【五、边界】

- Basalt 会话零网关改动；探针原件在 basalt-fork\ops\，需要副本由网关侧自取（只读）。
- 引擎重启/换 exe 属 Basalt 运行面待办（引擎升级窗口），不属本件。

【增补（2026-11-23 19:2x，用户裁定：bench 归终端、压测归网关）】

1. 槽数与档长不是常数：6 槽×256K 仅是 002 机 IQ3_S 的当前实测点，不可硬编码。
   槽数=f(显存-驻留预算,KV池,档长)，档长=f(模型rope上限,KV每token成本,分层水位)。
2. 最终形态三分：
   - 终端/引擎面＝标准化 bench（官方 basalt-bench/probe，确定性回归＋对外口径）＋测量原语
     （/metrics、/tokenize、本面 ops 探针样件）；
   - 网关面＝容量压测的**参数决策与编排**：按节点档案（机型/显存/RAM/模型 pack）
     自选槽数与档长候选→跑扫描→导出三标量（饱和拐点、拐点处每路稳态 tok/s、prefill tok/s）
     →写 registry→据此定接纳阈值；换模型/换机/升级＝网关重扫，终端零改动；
   - registry＝汇聚点：map 行族存"扫描序列＋三标量"（非单点值），anchor 行存官方锚
     （入池资格＋漂移报警用），calibration 行存覆盖线快照。
3. 样件：ops/bench_slots.py（并发分段计时/槽隔离/防缓存互吃）＋ops/expert_coverage.py
   ＋ops/sweep_*.sh 的**方法学**随本件移交，参数化/编排形态由网关面自行设计。
   方法学要点：每请求独立 session-id；语料不同偏移防前缀缓存互吃；
   prefill/decode 分段计时不混聚合；A/B 冷启动或双方同热身。
4. 三标量跨机可比的前提＝同模型同 pack 同夹具；异构 pack 节点间不直接比标量绝对值，
   比"相对各自档案的达标度"（NAS 侧设计注意项）。

────────────────────────────────────────
下篇 · 压测归网关：容量压测参数决策与编排（工单稿）
────────────────────────────────────────
来源：Basalt 会话 2026-11-23（用户裁定："bench 归终端，压测归网关"）。
性质：交接工单稿。是否立案、票型、落位由网关会话自定；本会话零网关写。
关联：本件上篇（调优顾问移交，含 19:2x 裁定增补节）。

【一、裁定与动机】
槽数与档长不是模板常数：

- 槽数 = f(显存 − 专家驻留预算, KV 池容量, 档长)；
- 档长 = f(模型 rope 上限, KV 每 token 成本, RAM/SSD 分层水位)。
  现状 6 槽×256K 仅是 002 机 IQ3_S 的实测点。换 pack / 换机型须重扫。
  决策放网关的理由：网关是唯一同时看见池内全部节点资源与请求形态的位置。

【二、建议领办的四段】
T1 registry 契约扩展（先行、可独立开工）

- map 行族改存"扫描序列＋三导出标量"，不存单点：
  标量①饱和拐点（边际收益跌破阈值的并发度）→接纳上限；
  标量②拐点处每路稳态 tok/s →排队体验承诺；
  标量③prefill tok/s →长提示排队时长预估；
- 行加 layer(anchor|map|calibration)、template_id、model_pack、engine_version；
- anchor 行族收官方 basalt-bench 社区口径行（入池资格＋升级漂移报警）；
  calibration 行族收覆盖线快照（来源见上篇二.A）。
- 向后兼容：既有两条 bench-6x256k-v1 迁移为 map 行（标量缺测则置 null＋注明）。
T2 节点档案＋扫描参数决策器
- 按 /capabilities（engine_parallel_slots、concurrency_model）＋引擎 pack 元数据＋
  calibration 行（驻留 GiB/覆盖线）推算候选槽数×档长组合；
- 决策输出＝扫描计划（例：该 pack 支持 256K→扫 1/2/4/6；48G 机型→上限 2×128K）；
- 触发点＝节点入池、引擎升级、pack 更换、calibration 位移>2pp。
T3 压测编排器（调用终端原语，零引擎侵入）
- 经 /v1 起并发请求（每请求独立 session-id、语料不同偏移防前缀缓存互吃、
  prefill/decode 分段计时、A/B 冷启动或双方同热身、seed 固定采样）；
- 方法学样件＝本面 ops/bench_slots.py＋sweep_*.sh（只读自取）；
- 结果按 T1 契约写 registry＋据拐点更新该节点接纳阈值。
T4 NAS 消费口径
- 池内排序用三标量；异构 pack 节点间禁比标量绝对值，
  改比"相对各自档案的达标度"（如当前负载/拐点）；
- /capabilities 暴露 layer 化后的行族，不破既有字段。

【三、边界与依赖】

- 终端侧供原语：官方 basalt-bench/probe（回归报警归终端例行）、/metrics、/tokenize；
  本面将做 P1（夹具 token 级冻结＋seed＋warmup 强化 bench_slots 样件）——
  网关侧 T3 若等样件升级，可先用现版本开工 T1/T2/T4。
- 引擎升级窗口回归三件套（锚行→sweep→覆盖线快扫）仍属 Basalt 运行面，不入本单。
- 验收：新 pack/新机型接入流程走通＝自动出扫描计划→三标量→接纳阈值更新，
  全程无终端侧人工改参。

【四、实测锚（供 T1 迁移与校验）】
002 机（PRO 5000 72GB / 64GB RAM / 1,344 GB/s）×IQ3_S×bench-6x256k-v1：
6 路合计 135.2 / 每路中位 68.2 / 单路 204.3 / prefill 2730 / 覆盖线 90%≈14.6GiB、99%≈24.5GiB。
A/B 必须冷启动或先热身（假低值坑）。本机 HTTP 探测 ProxyHandler({})。
