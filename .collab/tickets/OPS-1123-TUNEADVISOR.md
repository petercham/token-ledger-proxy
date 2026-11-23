# OPS-1123-TUNEADVISOR 调优顾问面立案·网关迭代计划 v1

领办面＝本仓（token-ledger-proxy 反代网关）｜来源交接件＝basalt-fork 面 handoff\TUNEADVISOR-handoff-20261123.md（用户移交）
交接件钉值：basalt-fork HEAD＝00c3209b5425698fda726e9646971cc89da2814c；交接件 sha256＝caaf23a0a96ee3dcc6693b82498f91cf8221f770e044e856b36f0d5e19c6aab5（5,367 字节）；原件路径＝C:\Work\Projects\basalt-fork\handoff\TUNEADVISOR-handoff-20261123.md（只读取用，副本自取归本面）。

## 立项判据（来自交接件第一节，已查证可直接采信）
Strata 有搜索式自动调优器（tune auto，代价 20min–2h）；Basalt 只给建议不改配置（probe "changes and saves nothing"）；两边都没有"按资源预算反推配置"的用户层——这是网关面差异化空档：网关天然看得见资源水位、并发形态、基准注册表（benchmark-registry.json）。定位＝决策层（该不该调、往哪个方向调、预算多少），永不重造 tuner。

## 迭代分期（T 序＝依赖序）
- T0 经验知识库落仓：交接件 §二 A-F 做成结构化档案（tuning-kb/ yaml：每条＝适用条件＋实测值＋出处＋机型标注）。含覆盖线标定（90% 路由覆盖＝前 28.3% 专家≈14.6 GiB 等，PRO 5000 72GB 机型、bench-6x256k-v1 模板锚）、ram-reserve 口径裁定（2048 生产档已落地待引擎重启）、prefill-cpu-share 不改结论、环境坑两条（ProxyHandler({})／engine.log "session is up"）。验收＝每条含出处与适用条件。
- T1 探针副本自取：expert_coverage.py＋prefill_probe.py 只读复制到本仓 tests/probes/，入 selftest 面（可选低频巡检）。
- T2 /tuning 只读接口（或 /capabilities 扩 advice 段）：按当前资源水位＋已登记 bench 返回建议档位（驻留覆盖线／slot 数／ram-reserve）。红线：只建议不改配置（对齐 Basalt manual 哲学）；不破 NAS 算力池既有消费端（/capabilities 骨架 rev17i，GATEWAY_VERSION 随功能拍 bump）。
- T3 环境画像采集（只读、低频）：GPU/RAM 水位、引擎版本、已加载 pack → 与 T0 条目匹配输出（"这台机跑这个 pack，90% 线要 14.6 GiB，空闲 X GiB"）。
- T4 社区案例并入流程：Strata/Basalt 案例持续进 T0 档案，网关成为跨后端唯一经验索引。

## 硬边界（不可逆条款）
1. 勿重造 tune auto：搜索/验证永远留引擎侧官方工具。
2. 依赖方向单向不变：顾问层是纯读＋静态知识，不得引入"调 LLM 做运维决策"；网关不得依赖其看护的后端（死循环红线，此前裁定延续）。
3. 改配置动作不属于网关：留给用户/引擎侧官方 tuner。
4. 引用 002 实测数字处注明机型（PRO 5000 72GB / 64GB RAM / 1,344 GB/s）与模板 ID。

## 不属本面（挂账提醒）
引擎重启/换 exe 属 Basalt 运行面待办（引擎升级窗口）；ram-reserve 2048 生效挂在下次引擎重启。

Status: 已立案，T0 可即刻开工（纯本仓写），T2 待停服窗口随 rev 拍。
