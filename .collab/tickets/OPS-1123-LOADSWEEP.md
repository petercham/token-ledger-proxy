# OPS-1123-LOADSWEEP 容量压测归网关：参数决策与编排（registry 三标量契约＋扫描计划）

领办面＝本仓（token-ledger-proxy 反代网关）｜来源交接件＝GATEWAY-HANDOFF-20261123 下篇（Basalt 会话，用户持转）
副本钉值＝本仓 .collab/drafts/GATEWAY-HANDOFF-20261123.md，sha256＝91cee3f4605875af12ebba438cb0f99b3a23a709681eea342815cf7e2a62867b（11,233 字节），登记时仓 HEAD＝83f041d。
同源互引＝上篇调优顾问面归 OPS-1123-TUNEADVISOR（追记 rev-addendum-1），本票只领下篇四段，双票禁重复立项。
用户裁定留痕（19:2x，主理人逐字誊录）：「bench 归终端，压测归网关」。
采纳判定（主理人评估，2026-11-23 19:3x）：可采纳，附三处调整（已并入本票票面＝R-A/R-B/R-C）。

## 裁定与动机（交接件下篇【一】，采信）
槽数与档长不是模板常数：槽数＝f(显存−专家驻留预算, KV 池容量, 档长)；档长＝f(模型 rope 上限, KV 每 token 成本, RAM/SSD 分层水位)。现状 6 槽×256K 仅是 002 机（PRO 5000 72GB / 64GB RAM / 1,344 GB/s）IQ3_S 的实测点。换 pack／换机型须重扫。决策放网关的理由：网关是唯一同时看见池内全部节点资源与请求形态的位置。

## 主理人采纳调整三条（票面生效条款）
- R-A 防同源双开：上篇（调优顾问/经验档案/覆盖线标定）只沿 OPS-1123-TUNEADVISOR 演进；本票仅消费其 calibration 产出，不得重立。
- R-B 面划界＋v1 限速：本票所领＝**容量面（主动打探测流量进引擎）**，与 TUNEADVISOR 票红线"顾问面＝纯读＋静态知识"分面并存、互不豁免。v1 触发一律手动＋空闲窗口（压测流量占引擎槽位＝与生产请求抢资源）；自动重扫（入池/升级/换 pack 触发）＝v2 候裁，决策者点头前不实现。
- R-C 射程收口：T4 NAS 消费口径中"池内排序用达标度"属 NAS 仓消费端设计，本仓领办面只保证 /capabilities 暴露 layer 化行族＋不破既有字段；NAS 侧口径以跨域工单形式待发投递，不代设计。

## 领办四段（T 序＝依赖序，交接件下篇【二】）
- T1 registry 契约扩展（先行、可独立开工、纯本仓写）：benchmark-registry.json map 行族改存"扫描序列＋三导出标量"（①饱和拐点＝边际收益跌破阈值的并发度→接纳上限；②拐点处每路稳态 tok/s→排队体验承诺；③prefill tok/s→长提示排队时长预估），不存单点；行加 layer(anchor|map|calibration)、template_id、model_pack、engine_version；anchor 行族收官方 basalt-bench 社区口径（入池资格＋升级漂移报警）；calibration 行族收覆盖线快照（来源＝TUNEADVISOR T0）。向后兼容＝既有两条 bench-6x256k-v1 迁移为 map 行（标量缺测置 null＋注明）。
- T2 节点档案＋扫描参数决策器：按 /capabilities（engine_parallel_slots、concurrency_model）＋引擎 pack 元数据＋calibration 行推算候选槽数×档长组合；输出＝扫描计划（例：该 pack 支持 256K→扫 1/2/4/6；48G 机型→上限 2×128K）；触发点按 R-B＝v1 手动。
- T3 压测编排器（调终端原语，零引擎侵入）：经 /v1 起并发请求；方法学红线＝每请求独立 session-id、语料不同偏移防前缀缓存互吃、prefill/decode 分段计时不混聚合、A/B 冷启动或双方同热身、seed 固定采样。方法学样件原件＝C:\Work\Projects\basalt-fork\ops\bench_slots.py＋sweep_*.sh＋expert_coverage.py（只读自取归本仓 tests/probes/，与 TUNEADVISOR T1 探针自取合并办）。终端侧 P1（夹具 token 级冻结＋seed＋warmup）未交付前可先用现版本开工 T1/T2/T4。
- T4 对外口径（按 R-C 收口）：/capabilities 暴露 layer 化行族，既有字段（NAS 算力池消费面）零破坏；GATEWAY_VERSION 随功能拍 bump。

## 硬边界（沿用＋新增）
1. 不重造官方 bench/probe：标准化回归与对外口径永远留终端侧（basalt-bench/probe）。
2. 依赖方向单向不变：网关不得依赖其看护的后端做决策（死循环红线延续）。
3. 改引擎配置动作不属于网关：接纳阈值写本仓 registry/config，引擎侧参数改配留用户/官方 tuner。
4. 引用 002 实测数字处注明机型（PRO 5000 72GB / 64GB RAM / 1,344 GB/s）与模板 ID。
5. 三标量跨机可比前提＝同模型同 pack 同夹具；异构 pack 禁比标量绝对值（NAS 注意项，随 R-C 外发）。

## 不属本面（挂账提醒）
引擎升级窗口回归三件套（锚行→sweep→覆盖线快扫）＝Basalt 运行面例行；终端 P1 样件强化＝basalt-fork 面待办；NAS 侧达标度排序＝NAS 仓。

## 实测锚（供 T1 迁移与校验）
002 机×IQ3_S×bench-6x256k-v1：6 路合计 135.2 / 每路中位 68.2 / 单路 204.3 / prefill 2730 / 覆盖线 90%≈14.6GiB、99%≈24.5GiB。A/B 必须冷启动或先热身（假低值坑）。本机 HTTP 探测 ProxyHandler({})（环境代理伪造 502）。

## 验收判据（交接件下篇【三】末，采信）
新 pack/新机型接入流程走通＝手动触发→自动出扫描计划→跑扫描→三标量入 registry→接纳阈值更新，全程无终端侧人工改参。

Status: 已立案·未开工（开工候决策者拍板；T1 纯本仓写、与在岗服务零冲突，拍板后可即刻先行）。
