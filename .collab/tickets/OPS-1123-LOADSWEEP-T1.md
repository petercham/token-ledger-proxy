# OPS-1123-LOADSWEEP-T1 registry 契约扩展：三标量＋layer 行族＋既有两条迁移为 map 行（施工子票）

## 票头（登记区）

- 票 ID：`OPS-1123-LOADSWEEP-T1`
- 票名：benchmark-registry.json 契约扩展（layer 行族＋三标量槽位＋schema_version＋map 迁移）
- 票型：**施工子票（L3 载体）**；母票＝`OPS-1123-LOADSWEEP`（本仓 .collab/tickets/OPS-1123-LOADSWEEP.md，sha256＝d3273c3a736f7076d84469d58057d4dc17cd2b2b0b644b8a3f34f4a3fcb390c6，5,448 字节，实取）
- 领办面＝本仓（token-ledger-proxy 反代网关）；来源链＝GATEWAY-HANDOFF-20261123 下篇【二】T1 段＋增补节 2"registry＝汇聚点"（副本 .collab/drafts/GATEWAY-HANDOFF-20261123.md，sha256＝91cee3f4605875af12ebba438cb0f99b3a23a709681eea342815cf7e2a62867b，与母票钉值一致，实核）
- 开端读数（本席当轮实跑）：ANCHOR＝`f352023`（`git -C D:\Projects\token-ledger-proxy rev-parse --short HEAD`）；`git status --porcelain`＝空（工作区干净）。
  - `benchmark-registry.json` 开工基线：磁盘 **1,453 字节**（无 BOM、CRLF；`git show HEAD:benchmark-registry.json`＝1,422 字节，差 31＝CR 数，autocrlf 形态差非内容差）；sha256（磁盘）＝`ee9f8261b0ebe66a4023b638214bc6483b05c7259b163c77ce785c88716fbfb6`。
  - proxy 套基线：`python tests/selftest_proxy.py`＝**45/45 PASS**（本席当轮实跑，退出码 0）。
  - 既有 capabilities 用例实核：`tests/selftest_proxy.py` 内 grep `capabilit`＝**零命中**＝现无 /capabilities 用例在册（起草实读）。
- 起草席位／修票权席位：架构席
- 前置票：OPS-1123-LOADSWEEP（母票，append-only，本票不触其面）；rev17i（/capabilities 上线拍，能力面起点）
- 开工前置＝母票 Status 所述"决策者拍板后可即刻先行"（T1 纯本仓写、与在岗服务零冲突）；本票放行＝主理人程序确认。
- 修订记录：**v1**（初稿；母本仓除本票文件外零触碰；票未放行、零施工）

### 准入四判据自查（票面自证）

1. **无 API 变更**：/capabilities 响应结构零改（消费端零代码改动，判定见②-0-判读），账本/事件/config 面零触碰；registry 只增字段不删不改名。
2. **口径已裁**：行族语义＝母票 T1 段＋交接件增补节已裁；本票票裁 A-1～A-7 收装配细节；真未裁面全部上候裁（H-1～H-3），零自行裁定。
3. **可机械验收**：③节＝命令＋期望读数（JSON 合法性＋schema 断言套＋旧值不变比对＋闭集/禁动面 diff 读数＋编码守卫）。
4. **不触真源**：三标量数值不得凭空填写——迁移行只能 null（母票 R 条款＋证据如实性）；引擎面零触碰；母票与交接件 append-only。

---

## 票体四字段（自包含）

### ① 目标

把 `benchmark-registry.json` 从"单点基准记录"扩成**三行族汇聚契约**（交接件增补节 2 最终形态之 registry 面）：

- 顶层加 `schema_version`＋契约自述段（`contract_note`，行族语义一段）；
- 每行加 `layer`（枚举 anchor|map|calibration）、`template_id`、`model_pack`、`engine_version`、`scalars`（三槽位 `saturation_knee` / `steady_tok_s_per_lane_at_knee` / `prefill_tok_s`，允许 null）＋ `scalars_note`；
- 既有两条 `bench-6x256k-v1` 记录迁移为 **map 行**：标量缺测置 null＋注明；**全部旧字段一个不删、不改名、数值零改动**（append-only 证据如实性）；
- 既有消费端（/capabilities 透传、NAS 算力池）零破坏——由②-0 读码判定＋③机检双锁；
- 新增 `tests/selftest_registry.py`：schema 校验＋旧值不变锁＋/capabilities 响应结构不破断言（机械可验证）。

**换脑依赖声明**：registry 是运行时被读文件——`_capabilities_payload` 每次请求现读（collector_proxy.py:445-449），落盘即生效，无需重启网关、不依赖换脑。

#### ②-0 消费端兼容判定（起草席读码结论，③机检复核）

**结论：T1 零改动 collector_proxy.py；GATEWAY_VERSION 不 bump（随该判定）。**

读码依据（文件:行，均实读）：

1. `collector_proxy.py:445-449`＝整文件 `json.load` 读 registry，无按字段挑取；`:497`＝`"benchmarks": bench` 原样透传整个解析结果。全仓 grep `benchmark-registry|benchmark_registry|benchmarks` 命中仅三处代码行（:447/:455/:497）＋CHANGELOG 记述行——**registry 唯一消费端即此透传点**。
2. 推论：registry 内容只要是合法 JSON，消费端语义＝原样多带字段，旧字段在位即不破 NAS 消费面（母票 R-C 收口口径＝"只保证暴露 layer 化行族＋不破既有字段"，零代码动作即满足）。
3. 风险面＝registry JSON 解析炸穿：`:450-455` 会降级为 `{"entries": [], "note": "registry unreadable", ...}`——不破结构但丢基准数据＝③-2 JSON 合法性判据＋③-3 R-1 断言为守门。
4. `GATEWAY_VERSION = "rev17i"`（:84，注释 "bump with each functional change"）：T1 对网关代码 diff＝0 行、无功能变更＝不 bump；若主理人要以 bump 作契约变更信号＝改判上候裁 **H-3**，且须另开微票（本票闭集不含 collector_proxy.py）。
5. import 安全性实读：`main()` 在 :1085 定义、:1160 `if __name__ == "__main__"` 卫底下才调用——`import collector_proxy` 不起服务，selftest_registry 可用桩 handler 直调 `_capabilities_payload`（见 S-4 与 A-6）。

### ② 规格

#### ②-1 声明闭集（本票唯一可写仓内面）

```
benchmark-registry.json                      (S-1 契约扩展＋两条迁移)
tests/selftest_registry.py                   (S-4 新建校验套)
CHANGELOG.md                                 (S-5 登记节)
MANIFEST.md                                  (S-6 登记节·第二节)
.collab/tickets/OPS-1123-LOADSWEEP-T1.md     (本票本体，登记面，不计施工验收 diff 面)
```

其余全部不入闭集零触碰（含 `collector_proxy.py`、`config.json`、`config.template.json`、`tests/selftest_proxy.py`、`tests/selftest_monitor.py`、`tests/selftest_watchdog.py`、`tests/selftest_daily_report.py`、`monitor*`、`daily_report.py`、`html_report.py`、`ledger_watchdog.py`、`watchdog-launcher.py`、`monitor_ext.py`、`bootstrap.py`、`paths.py`、`switch_proxy.py`、`README.md`、`INSTALL.md`、`data/**`、`.collab/tickets/OPS-1123-LOADSWEEP.md`（母票）、`.collab/drafts/**`、`logs/**`）。

#### ②-2 禁动面

- `collector_proxy.py` 全部零改动（②-0 判定；③-4 diff＝0 行数机检）。
- **registry 旧字段字节冻结**：顶层 `object`、`template_note` 逐字节不动；两条记录的全部原键名与原值（含字符串内文与数值）逐字节不动——只许在对象尾部**追加**新键（③-5 比对机检）。
- **scalars 数值禁凭空填写**：迁移两行三槽位只能 `null`＋`scalars_note` 实注（未测原因）；任何非 null 数值须有来源行（logs/扫描产物），本票不产生。
- config.json、watchdog 族、monitor* 族、既有端到端语义（RELAY CONTRACT、账本行、排队闸）：零触碰。
- anchor / calibration 行**不在本票立行**（立行候官方社区口径行入池＝T4 侧、覆盖线快照＝TUNEADVISOR T0 产出）；本票只立契约与 map 迁移。
- 引擎面（D:\Strata-toolkit\ 等）、在岗 8080/8787 服务：零触碰。

#### ②-3 逐条施工规格（落位到文件＋结构）

**S-1 `benchmark-registry.json` 顶层契约扩展**：

- 顶层追加两键（`object`、`template_note` 之后、`entries` 之前）：
  - `"schema_version": <H-1 裁定值，票面样张暂按整数 2 写死，放行前若裁定不同则修票替换>`
  - `"contract_note"`：行族语义自述段，逐字模板（英文，与文件现有文风一致）：

```
row families: layer=anchor -> official basalt-bench community-口径 rows (pool admission qualification + upgrade drift alarm); layer=map -> capacity sweep rows, carrying a scan series plus three derived scalars (saturation_knee -> admission ceiling; steady_tok_s_per_lane_at_knee -> per-lane queue-experience promise; prefill_tok_s -> long-prompt queue estimate); single reference points are allowed for map rows until T3 sweeps supply series. layer=calibration -> expert coverage-line snapshots (source = TUNEADVISOR T0). Pre-T1 records migrated as map rows: original fields byte-frozen, scalars null until measured. Scalars are comparable only across the same model, pack and fixture (ticket boundary 5).
```

- 顶层 `entries` 数组名与既有两行键序零动；每行**尾部追加**六键（S-2）。

**S-2 行契约字段（每条 entry 追加，逐文件结构）**：

| 键 | 类型/约束 | 迁移行取值 |
|---|---|---|
| `layer` | 字符串，枚举 `"anchor"` \| `"map"` \| `"calibration"`（闭集小写） | `"map"` |
| `template_id` | 非空字符串（模板 ID，与旧 `template` 值同源的显式契约字段） | `"bench-6x256k-v1"` |
| `model_pack` | 非空字符串 | 行1/行2 均 `"qwen3.8-flash-next-iq3_s"` |
| `engine_version` | 非空字符串（纯版本号，括注留旧 `engine` 字段，见 A-2） | `"basalt 0.5.5+00c3209b"` |
| `scalars` | 对象，恰三键 `saturation_knee` / `steady_tok_s_per_lane_at_knee` / `prefill_tok_s`；值＝null 或 ≥0 数值；键闭集，加槽走另票 | 三槽全 `null` |
| `scalars_note` | 字符串；任一标量为 null 时必为非空（缺测原因实注） | 行1：`"pre-T1 reference point: scalars never measured (no sweep series behind this row); raw fields below are the frozen evidence, measured 2026-11-22"`；行2：`"pre-T1 reference point: scalars never measured; frozen evidence, measured 2026-11-23; comparability per this row's own note (agg/prefill comparable, slot median not)"` |

**S-3 迁移行数值字段零改动锁**：两条记录原 11/9 键（`template` `hardware` `model` `engine` `measured_at` `decode_agg_tps` `decode_slot_median_tps` `prefill_agg_tps` `single_route_decode_tps` `source` `status`；行2 另有 `note`、无 `single_route_decode_tps`）逐字节冻结——施工后 S-4 的 R-4 断言内嵌原值常量逐键比对（数值样张：行1 decode_agg_tps 135.2 / slot_median 68.2 / prefill_agg_tps 2730 / single_route 204.3；行2 141.6 / 51.6 / 2702，与母票实测锚一致，实核）。

**S-4 新建 `tests/selftest_registry.py`**（无网络、不起服务、不进 selftest_proxy 闭集；结构沿 selftest_proxy 的 `rec(name, ok, detail)` 报数风）：

- **R-1 文件可解析**：`json.load(open(..., encoding="utf-8-sig"))` 成功退出。
- **R-2 顶层契约在场**：`object == "gateway.benchmark_registry"`；`schema_version` 在场且＝票定值；`contract_note` 非空；`template_note` 与 `entries` 在场（旧顶层键零丢失）。
- **R-3 逐行 schema 校验**：对每条 entry——`layer in {"anchor","map","calibration"}`；`template_id` / `model_pack` / `engine_version` 为非空字符串；`scalars` 为 dict 且键集**恰等于**三槽位闭集；每槽值 `is None or (isinstance(v,(int,float)) and v>=0)`；任一槽为 null ⇒ `scalars_note` 为非空字符串。
- **R-4 旧两条数值不变锁**：按 `template + measured_at` 定位两条，断言其全部旧键＝S-3 内嵌常量表逐键相等（含 `hardware`/`engine`/`source`/`status`/`note` 字符串逐字）；且两条 `layer=="map"`、三槽 `is None`。
- **R-5 /capabilities 响应结构不破（import 直调）**：`sys.path.insert(0, 仓根)` → `import collector_proxy`；构造桩 handler（`SimpleNamespace(cfg=<临时 config dict：upstream 指向必然不可达的 127.0.0.1 端口>, cfg_path=<临时 config.json 路径>, gate=None)`——:428 `handler.gate is not None` 卫底实读、:443 引擎探活 try/except 实读，桩可安全走通，代价≈2s 超时）；调 `_capabilities_payload(stub)` 断言：顶层键 `ok/object/gateway/capacity/engine_health/benchmarks/server_time` 全在场；`payload["benchmarks"]` 逐字段等于磁盘 registry 解析结果（透传锁）；`payload["benchmarks"]["entries"]` 条数＝文件条数。
- 套尾 `%d/%d PASS`＋失败非零退出码（与 selftest_proxy 同风，供③-3 判红绿）。

**S-5 `CHANGELOG.md`**：倒序置顶新增节（不占 rev 号——网关代码零改动，不 bump GATEWAY_VERSION；节名样张 `## registry-contract-v2 (2026-11-2x) · OPS-1123-LOADSWEEP-T1`）＝一句话摘要：registry 契约扩展＋两行 map 迁移＋selftest_registry 入册；注明 `/capabilities` 响应结构不变、GATEWAY_VERSION 不动。

**S-6 `MANIFEST.md`**：第二节（改动登记）加同拍节：文件清单变化＝新增 `tests/selftest_registry.py` 一行＋`benchmark-registry.json` 描述更新；其余节零动。

### ③ 验收标准（全机械可判）

> 母本仓根跑，基线＝ANCHOR `f352023`；回执逐条附命令原文与读数。禁 git 写操作（本票验收全程只读 diff）。

1. **闭集核验**：`git diff --name-only f352023 | grep -vE '^(benchmark-registry\.json|tests/selftest_registry\.py|CHANGELOG\.md|MANIFEST\.md|\.collab/tickets/OPS-1123-LOADSWEEP-T1\.md)$' | wc -l` ＝ **0**。
2. **JSON 合法**：`python -c "import json,sys; json.load(open('benchmark-registry.json', encoding='utf-8-sig'))"` 退出码 **0**。
3. **schema 套全绿**：`python tests/selftest_registry.py` 退出码 **0** 且末行 `%d/%d PASS` 两数相等（R-1～R-5 逐名 PASS，回执贴原始输出）。
4. **消费端零改动（②-0 判定机检）**：`git diff f352023 -- collector_proxy.py | wc -l` ＝ **0**；proxy 套零回归：`python tests/selftest_proxy.py` ＝ **45/45 PASS** 退出码 0。
5. **旧值字节不变**：`git show f352023:benchmark-registry.json` 导出至 .scratch 后跑比对脚本：两条原记录的全部旧键名旧值（原 11/9 键）在新文件中逐键相等；`git diff f352023 -- benchmark-registry.json | grep -c '^-[^-]'` 读数供人工目检（预期：仅结构重排行删且每条删除行的内容在新增行中原样再现——R-4 为最终判据，diff 读数为辅）。
6. **禁动面零触碰**：`git diff --name-only f352023 | grep -cE '(config|watchdog|monitor|daily_report|selftest_proxy|collector_proxy)'` ＝ **0**。
7. **编码守卫**：`python -c "raw=open('benchmark-registry.json','rb').read(); assert not raw.startswith(b'\xef\xbb\xbf') and b'\r\n' in raw"` 退出码 **0**（无 BOM、CRLF 保持，与开工基线同形；消费端 :448 `encoding="utf-8-sig"` 实读，BOM 本不致命，但字节形态随基线冻结）。
8. **scalars 如实性**：R-4 已锁迁移行三槽 null；辅检 `python -c "import json; e=json.load(open('benchmark-registry.json',encoding='utf-8-sig'))['entries']; print(sum(1 for r in e if r['layer']=='map' and any(v is not None for v in r['scalars'].values())))"` ＝ **0**（map 行非 null 标量条数＝0，本票期内）。

### ④ 边界约束

- **票间关系**：本票＝母票 LOADSWEEP 四段之 T1，与 T2/T3/T4 无文件交集（后三段不依赖本票之外的 T1 产出面：T2 消费 registry 读侧、T3 按本契约写入、T4 若加 layer 过滤候 H-2 另拍）；与 OPS-1123-TUNEADVISOR 零文件交集（calibration 立行归其产出，见 R-A）。
- **同源纪律**：三标量跨机可比前提＝同模型同 pack 同夹具（母票硬边界 5），已写入 `contract_note` 随 registry 自述外发；NAS 侧达标度口径＝跨域工单（R-C），本票不代设计。
- **v1 限速沿用**：本票不产生任何引擎流量（R-B）；R-5 的桩探测指向不可达端口、2s 预算内 try/except 消化，不经生产 upstream。
- **施工面纪律**：临时工作物只落仓根 `.scratch/OPS-1123-LOADSWEEP-T1/`，完工前清零；禁仓外临时路径；单一工程师席新鲜实例、同席禁多实例。
- **交付与回执**：完工回执先行＝开端 HEAD（f352023）＋写入清单＋③八条读数＋`.scratch/` 自查；落位由主理人程序定。
- **票放行**＝主理人程序确认＋母票开工拍板（决策者）双前置；本票 v1 起草不启施工。

## 租约段（票内·经架构签注由 B2 lease-issuer 实例化）

- path_globs：`benchmark-registry.json`、`tests/selftest_registry.py`、`CHANGELOG.md`、`MANIFEST.md`、`.collab/tickets/OPS-1123-LOADSWEEP-T1.md`
- deny_globs：`collector_proxy.py`、`config.json`、`config.template.json`、`watchdog-launcher.py`、`ledger_watchdog.py`、`monitor_ext.py`、`monitor*`、`daily_report.py`、`html_report.py`、`selftest_proxy.py`（仓根与 tests/ 两轨写法并存以匹配实例化器）、`tests/selftest_monitor.py`、`tests/selftest_watchdog.py`、`tests/selftest_daily_report.py`、`paths.py`、`bootstrap.py`、`switch_proxy.py`、`README.md`、`INSTALL.md`、`data/**`、`logs/**`、`.collab/tickets/OPS-1123-LOADSWEEP.md`、`.collab/drafts/**`、`D:\Strata-toolkit\**`
- 灰度判据（票内声明字段·decision-pack 读取）：`python tests/selftest_registry.py` 全绿退出码 0 ＋ `python tests/selftest_proxy.py` 45/45 退出码 0 ＋ ③-4 collector_proxy diff＝0——测试环境判据，不依赖换脑、不依赖在岗服务。
- 席位 ID／票 ID／哈希：由状态机签发，非人工填写

## 票裁已决（A-1～A-7·起草席决；推翻走回流件）

- **A-1｜旧字段字节冻结、新键只追加**：JSON 键序无关但 diff 可读性与证据如实性要求"尾部追加"；旧 `template/model/engine` 与新增 `template_id/model_pack/engine_version` 值冗余并存＝兼容期代价，删除旧键候消费端换代另票。
- **A-2｜engine_version＝纯版本号**："basalt 0.5.5+00c3209b"；行2 旧 `engine` 值带括注（post-upgrade run…）——括注语义留旧字段，新字段只做可分组比对的中性版本键，不重排旧字符串（旧字段冻结红线）。
- **A-3｜scalars 键闭集恰三槽**：多一键＝契约变更走另票；槽值域 null ∪ [0,∞) 数值（并发度/吞吐无负语义）。
- **A-4｜layer 枚举小写三值闭集**：与交接件/母票字面一致（anchor|map|calibration）；大小写宽容消费端不在本仓，从严。
- **A-5｜schema_version 缺席＝v1 语义**：消费端现零版本门（透传），故迁移后在场即可；不在场兼容逻辑不需预建（YAGNI）。取值/类型上候裁 H-1。
- **A-6｜R-5 用 import 直调非起服务**：import 安全性实读（main 在 :1085/:1160 卫底下）；起服务法需端口/配置/清理三族复杂度，直调法覆盖面＝响应结构＋透传锁，与②-0 风险面（解析炸穿→降级体）对判——若施工期 import 遇阻（如模块级副作用新现），按缺陷回流修票换起服务法，不放宽断言。
- **A-7｜map 行的"扫描序列"字段不在 T1 预定义**：母票 T1 语义＝map 行族*将来*存序列＋标量；序列的载体字段（T3 写入时定型）现无生产者，预定义空字段＝无证据的契约膨胀。contract_note 已如实写明"单点暂容"。

## 候裁单列（H-x·决策者拍板，本席不裁）

- **H-1｜`schema_version` 取值与类型**：票面样张按整数 `2`（v1＝无此键的现网形态）；若裁字符串 `"2"` 或别值＝修票替换 S-1 与 R-2 断言常量。
- **H-2｜/capabilities 是否暴露 layer 过滤参数**（如 `?layer=map`）：属 T4 面对外口径；T1 默认零加（R-C 只要求"暴露 layer 化行族＋不破既有字段"＝透传已满足）。加与不加、参数形态＝T4 开工前决策者拍。
- **H-3｜GATEWAY_VERSION 是否因 registry 契约变更而 bump**：本席读码结论＝不 bump（网关代码 diff 0、无功能变更；:84 注释 "bump with each functional change"）。若主理人/决策者要以 bump 作契约变更对外信号＝改判，且需扩本票闭集或另开微票（当前闭集不含 collector_proxy.py）。

## 健康账登记（回流素材）

1. **registry 无 BOM＋CRLF＋utf-8-sig 读法**：消费端容 BOM 但字节形态是历史偶然；后续任何工具改写此文件都须守③-7 守卫，否则 diff 噪音吞内容 diff。
2. **/capabilities 无既有用例**：selftest_proxy 45 名不含 capabilities（实读）；R-5 是首个锁。若 import 直调法确立为 capabilities 测试惯例，后续可考虑并入 proxy 套（另票）。
3. **旧键/新键冗余（A-1）**：`template≈template_id` 双轨并存期，若后续出现按旧键消费的新读方＝冗余冻结期延长信号，入 T4 决策参考。

## 可施工性判定（架构席自评）

- 挂点实读在册：registry 全文实读（两条 11/9 键样张入 S-3）；`_capabilities_payload` 419-499 全读；桩 handler 三依赖（cfg/cfg_path/gate）卫底实读；import 卫底实读；selftest_proxy 基线 45/45 实跑。
- 判别力自评：R-3 对"layer 走样/scalars 键漂移/null 无注"判红；R-4 对"旧值被手改"判红；③-4 对"顺手动消费端码"判红；③-1/③-6 对"越领地"判红；③-7 对"编码走样"判红。
- 未实跑面（留施工/QA）：R-5 桩直调首跑（A-6 副作用面）；③-5 比对脚本实跑。判定＝**可施工**，无阻塞点；放行双前置（决策者开 T1 拍板＋主理人程序）满足即开工。

—— 架构席 · OPS-1123-LOADSWEEP-T1 v1 · 开端 HEAD 实测 `f352023`（git -C D:\Projects\token-ledger-proxy rev-parse --short HEAD）· 起草实核居本仓 .collab/ · 2026-11-23


---

## 完工回执读数登记（工程师席 append-only · 2026-11-23）

- 开端 HEAD 实跑＝`a6b9f97`（`git rev-parse --short HEAD`；票面 ANCHOR `f352023`＋本票登记 commit，无其他改动，主理人放行件已声明，验收 diff 基线一律 `a6b9f97`）；开工 `git status --porcelain`＝空。
- 候裁采纳（主理人放行件）：H-1＝整数 `2`（S-1/R-2 照写）；H-2＝零加；H-3＝不 bump（collector_proxy.py 零改动）。

### 写入清单（字节数＋sha256 前→后）

| 文件 | 前 | 后 |
|---|---|---|
| `benchmark-registry.json` | 1,453 B / `ee9f8261b0ebe66a4023b638214bc6483b05c7259b163c77ce785c88716fbfb6` | 3,174 B / `0dda1f6cded9ede1f9aa2bbea7af19ba69ae152020ce2d7ee1f826836afe685d` |
| `tests/selftest_registry.py` | （新建·不存在） | 10,234 B / `f6428eee4e916409b85624dafc4f6d4ae5bd4612276f86539b04fd8583c74a80` |
| `CHANGELOG.md` | 57,922 B / `eca9dfef74cc469c7d92d00af8ac1c0a6a68b6e0d2a7989406108bbdddfd9dc6` | 58,738 B / `6914dec0640abc9ecd1004cc527db4112fe8bfceb043e90191122c28f725070e` |
| `MANIFEST.md` | 105,795 B / `5789d9693cb0b55076fc46277f887e24f0a4ffe38ae37f91e7a2255f68958d67` | 107,552 B / `5b1e21d619100c5e94dbc3fa33ce2212a7f96af1995c8ede3a08c8f93af01479` |
| 本票本体 | 21,530 B / `cd65e2ef9ed8944cd4b56ae61500dbed663adbd29034c9a2f3234d0a613ca4e5` | 本节追加（append-only·登记面不计施工验收 diff 面） |

registry 生成方式＝行级插入（旧行逐字节保留，A-1 尾部追加）；新文件无 BOM＋CRLF 保持、无裸 LF。

### ③八条读数（母本仓根·基线 a6b9f97）

1. `git diff --name-only a6b9f97 | grep -vE '^(benchmark-registry\.json|tests/selftest_registry\.py|CHANGELOG\.md|MANIFEST\.md|\.collab/tickets/OPS-1123-LOADSWEEP-T1\.md)$' | wc -l` ＝ **0** ✅
2. `python -c "import json,sys; json.load(open('benchmark-registry.json', encoding='utf-8-sig'))"` 退出码 **0** ✅
3. `python tests/selftest_registry.py` 退出码 **0**，末行 **6/6 PASS**（R-1～R-5 逐名 PASS，输出全文见下节）✅
4. `git diff a6b9f97 -- collector_proxy.py | wc -l` ＝ **0**；`python tests/selftest_proxy.py` ＝ **45/45 PASS** ✅
5. `git show a6b9f97:benchmark-registry.json` 导出 .scratch 比对脚本：顶层 `object`/`template_note` 相等＋两条原记录全部旧键旧值逐键相等＝`all old keys/values identical: True`（原键数 11/9）；辅检 `git diff a6b9f97 -- benchmark-registry.json | grep -c '^-[^-]'` ＝ **2**（仅两条 entry 尾行加逗号的结构删行，内容在新增行原样再现，符合票面预期）✅
6. `git diff --name-only a6b9f97 | grep -cE '(config|watchdog|monitor|daily_report|selftest_proxy|collector_proxy)'` ＝ **0** ✅
7. 编码守卫 `python -c "raw=open('benchmark-registry.json','rb').read(); assert not raw.startswith(b'\xef\xbb\xbf') and b'\r\n' in raw"` 退出码 **0**（另实测：无裸 LF，字节形态随基线同形）✅
8. `python -c "import json; e=json.load(open('benchmark-registry.json',encoding='utf-8-sig'))['entries']; print(sum(1 for r in e if r['layer']=='map' and any(v is not None for v in r['scalars'].values())))"` ＝ **0** ✅

### selftest_registry.py 输出全文

```
PASS  R-1:registry-json-parses  top-level keys: object,template_note,schema_version,contract_note,entries
PASS  R-2:top-level-contract  object='gateway.benchmark_registry' schema_version=2 contract_note_len=703 template_note=present entries=present
PASS  R-3:entry-row-schema  2 entries validated
PASS  R-4:frozen-row-2026-11-22  map row, scalars null
PASS  R-4:frozen-row-2026-11-23  map row, scalars null
PASS  R-5:capabilities-shape-and-passthrough  missing=none benchmarks==on-disk-registry:True entries:2/2

6/6 PASS
```

### .scratch 自查

临时工作物＝`.scratch/OPS-1123-LOADSWEEP-T1/`（registry_base.json 基线导出件＋build_registry.py 生成器＋compare 跑于 stdin），完工前已 `rm -rf` 清零（.scratch 不入 git·未跟踪）。

### 健康账补记（施工实感）

- ③-5 辅检读数 2＝"加逗号"结构删行，即票面预告形态；R-4 常量为最终判据。
- R-5 import 直调法首跑通过（A-6 副作用面＝无新现副作用；桩探测在不可达端口上由 :443 try/except 消化，全程零引擎流量）。
- registry 新文件含中文「口径」（contract_note 逐字模板），JSON 内为非 ASCII 原文（与 ensure_ascii=False 一致），文件仍为 UTF-8 无 BOM；消费端 utf-8-sig 读法实读兼容。

—— 工程师席 · OPS-1123-LOADSWEEP-T1 完工回执 · 开工/完工均零 git 写操作（未 add/commit）· 落链归主理人
