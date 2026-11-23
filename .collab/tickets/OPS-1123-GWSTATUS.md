# OPS-1123-GWSTATUS :8080 新增只读路由 GET /gateway/status（统一状态面 unified-status/v0）（施工票）

## 票头（登记区）

- 票 ID：`OPS-1123-GWSTATUS`
- 票名：collector_proxy 扩面——`GET /gateway/status` 统一状态面（unified-status/v0·envelope 五字段＋ports 行契约＋gate 进程内合成）
- 票型：**施工票（L3 载体）**；母件＝`OPS-1123-NASGW-COOP` 接手单（本仓 .collab/tickets/OPS-1123-NASGW-COOP.md；append-only，本票不触其面）
- 来源链＝GitHub issue petercham/token-ledger-proxy#1【实装项】（契约要素已完备，接手单字段六改判＝本仓自研自闭环、不接跨仓 PR/patch）＋契约 v0.2 §10 引用
- 领办面＝本仓（token-ledger-proxy 反代网关）
- 开端读数（本席当轮实跑·2026-11-23）：
  - ANCHOR＝`ccb5892`（`git -C D:\Projects\token-ledger-proxy rev-parse --short HEAD`）；`git status --porcelain`＝空（工作区干净）。
  - `curl --noproxy '*' http://127.0.0.1:8080/health` → **200**（网关在跑）
  - `curl --noproxy '*' http://127.0.0.1:8080/gateway/status` → **404**＝缺口属实
  - `grep -c 'gateway/status' collector_proxy.py`＝**0**；`grep -c 'unified-status' collector_proxy.py`＝**0**＝代码面无该路由
  - 四套回归基线实跑：`python tests/selftest_proxy.py`＝**45/45 PASS**；`python tests/selftest_watchdog.py`＝**RESULT: 31 passed, 0 failed**（exit 0）；`python tests/selftest_monitor.py`＝**57/57 PASS**；`python tests/selftest_daily_report.py`＝**15/15 PASS**；辅套 `python tests/selftest_registry.py`＝**6/6 PASS**（全部退出码 0）
  - `config.json`（仓根·git 外运行时件）实读键表＝name/mode/out_dir/web_root/listen/upstream/lock_port/watchdog_lock_port/report_hour/report_minute/force_include_usage/key_labels/comment——**无 `machine_id` 键**（machine_id 来源须票裁，见 A-4/H-1）
- 起草席位／修票权席位：架构席
- 前置件：OPS-1123-NASGW-COOP（接手单·字段六改判＝架构席即刻起草）；rev17i（/capabilities 上线拍·同族只读探针先例）
- 修订记录：**v1**（初稿；母本仓除本票文件外零触碰；票未放行、零施工）

### 准入四判据自查（票面自证）

1. **无 API 变更（既有面）**：只**新增**一条只读路由；既有 `/health`、`/ext.json`、`/capabilities`、`/monitor*`、`/v1/*` 响应字节与行为零改（vendor 四套自测回归底线＝母件兼容承诺）。账本行、gate 事件日志、config 文件面零触碰。
2. **口径已裁**：契约要素＝issue 正文【实装项】闭集（envelope 五字段＋ports 行字段＋available 合成式＋speed_bias 缺位弃权＋沿 /health 无鉴权先例），已逐条转 S 规格；装配细节本席票裁 A-1～A-8；四个来源/形态面按主理人令上候裁 H-1～H-4（票面样张按本席读码推荐值写死，放行前裁定不同则修票替换）。
3. **可机械验收**：③节＝命令＋期望读数（新套全绿＋proxy 套逐名新增用例＋四套回归读数＋闭集/禁动面 diff 读数＋在岗面零触碰 grep）。
4. **不触真源**：speed_bias 档案值不得凭空填写（registry 三标量现全 null＝缺位弃权，代码零读零猜）；gpu_bind/vram_gb 不从 GPU 采样面推断（网关无从知道哪张卡服务哪个端口——推断即猜，违"不猜值"纪律）；母件 append-only；在岗 8080/8787 服务与引擎面零触碰。

---

## 票体四字段（自包含）

### ① 目标

在 `:8080`（即 `listen` 端口）新增**只读路由 `GET /gateway/status`**，输出统一状态面 envelope，供 NAS 算力池调度侧一发请求读到本机 LLM 网关的身份、容量与在务读数（对接完成判据＝NAS 侧 `curl http://<终端>:8080/gateway/status` 出 envelope 五字段——该 curl 发生在入闸部署之后，不在本票验收面内，见④）。

- 不动既有 `/health`、`/ext.json`、`/monitor*`、`/v1/*`、`/capabilities`（兼容性由四套回归锁）。
- envelope 五字段：`{"schema":"unified-status/v0", "machine_id":<str>, "domain":"llm", "generated_at":<str>, "ports":[…]}`。
- ports 行字段契约（issue 正文闭集）：`vport` / `engine` / `gpu_bind` / `vram_gb` / `available` / `current_tasks{in_flight,queued}` / `speed_bias{value,bench_id,measured_at}`；其中 **speed_bias 无档案＝整字段缺席（缺位弃权，不填 1.0）**。
- 合成源＝gate 进程内量；`available = serving − max(in_flight, admitted)`（真实属性名映射见 ②-0）。
- 鉴权＝沿 /health 先例（内网无鉴权，本地路由直接回答，永不转发 upstream）。
- 新 `tests/selftest_gateway_status.py`（import 直调桩法·A-8）＋`tests/selftest_proxy.py` 加一条在岗用例；GATEWAY_VERSION bump（样张 rev17i→rev17j，H-4 终裁）。

#### ②-0 读码判定（起草席实读，文件:行均实读；③机检复核）

**gate 进程内量·真实属性名与锁语义**（`Gate` 类 collector_proxy.py:132-277）：

1. `Gate._cond = threading.Condition()`（:138）——全部状态变更持此锁；`Gate._waiters = collections.deque()`（:139，元素 `[seq:int, granted:bool]`）＝排队者**在场队列**；`Gate.inflight`（:141）＝已放行未归还计数；`Gate.queued`（:142）＝**单调累计计数器，永不递减**——:142 行内注释明令"display truth via _waiters, do not read this field——snapshot's queued key uses len(self._waiters) live value"。**契约所称 "_waiters live" ≡ `len(Gate._waiters)`**。
2. **契约所称 "admitted" 在 Gate 内无同名计数器**——"admitted" 是 gate-events 事件标签（acquire 快路径 :193；事件语义注释 :152-159）。放行的在场量 ≡ `Gate.inflight`：三个准入点各自 `inflight += 1`（快路径 :181、队头取空槽 :218、等满 gate_wait_s 越权放行 :228），唯一归还出口 `release()` `inflight -= 1`（:265-271）。**故 `max(in_flight, admitted) ≡ Gate.inflight`**（admitted 是 inflight 的子集且同一变量承载，含 :228 的越权超跑），票面合成式落为 `available = serving − Gate.inflight`（serving 见下条）。
3. 唯一被背书的读面＝`Gate.snapshot(limit)`（:273-277）：持 `_cond` 锁返回 `{"inflight", "queued"=len(_waiters) live, "limit", "waited_total", "beat_total"}`。先例＝`_capabilities_payload` :427-428（`_gate_params(handler.cfg_path)` 取 limit → `handler.gate.snapshot(limit) if handler.gate is not None else None`）。**本路由沿此读面，不得直接触 `_waiters`/`inflight` 裸属性**（绕锁读＝撕裂风险）。
4. **契约所称 "serving" 在 Gate 内无此属性**——网关侧容量面候选：`_gate_params(cfg_path)` 现读有效 limit（:374-416，:415 落 `_last_limit`）；引擎槽位 `_strata_parallel_parse`（:293-336，读引擎启动配置 `engine_launch_config` 的 parallel，capabilities 用法 :432-434）；两者优先级先例＝`_capabilities_payload` :491 `"concurrency_ceiling": (limit if limit else slots)`。**票面裁：`serving = limit if limit else slots`；两者皆不可得（闸关且无引擎启动配置）→ serving/available 置 `null`（缺位弃权不猜，沿 :490 `engine_parallel_slots` 可为 None 先例）**。引擎自身 `/v1/status.concurrency.serving` 属引擎面现读（母件字段三实证在场），本路由**不**按请求探引擎（保持零 upstream 流量，见④），serving 取网关侧上限即上式。

**路由挂点与发送形制**：`do_GET`（:949）本地分支先例——`/capabilities` 分支 :952-967（`self.path.split("?",1)[0]` 匹配、JSON 200、`Cache-Control: no-store`、`Access-Control-Allow-Origin: *`、异常降级体）；monitor 本地面经 `_monitor_ext.answer()` :968-986（/health 即此面 answer() monitor_ext.py:617-618＝内网无鉴权先例）；其后才是 upstream 转发段 :987+。新分支插在 `/capabilities` 分支之后、`local = None`（:968）之前，形制照抄 capabilities 分支（A-1）。

**config 读取面**：per-request `load_config(cfg_path)`（:103-107→paths.load_config）无键即 `c.get(key)` 缺席语义，现例满仓（:383/:401/:432）。`socket` 已在 :59 导入——`socket.gethostname()` 零新依赖。

**speed_bias 档案面实读**：`benchmark-registry.json`（schema_version 2 后现行面）＝map 两行，`scalars` 三槽 `saturation_knee/steady_tok_s_per_lane_at_knee/prefill_tok_s` **全部 null**（registry:23-27、:46-50）；行内**无任何与 vport/端口相联的 join 键**。→ 现网 registry 状态即"无档案"＝按契约规则整字段缺席；且行↔端口联接键契约不存在，按行填值＝猜。**票裁 A-6：v1 speed_bias 一律缺席（payload 构建零 registry 读取）；将来接档案（需 join 键＋非 null 标量）候 H-3。**

**gpu_bind/vram_gb 实读**：网关现无机读 GPU↔端口绑定面。monitor 采样面有每卡 `uuid/name/mem_total_mib`（monitor_ext.py:258-263）但**无从知道哪张卡承载哪个端口的模型**（Basalt 单机单卡为运行时事实、非配置事实，collector_proxy.py:309-310 注释实证其单脑语义）——从采样行推断绑定＝猜，违"对方按在场性落 None，不猜值"同族纪律。**票裁 A-5：config 新增可选键 `machine_profile`（对象，`{"gpu_bind": <str>, "vram_gb": <number>}`），人工申报绑定；键/子键缺席 → 该行 `gpu_bind`/`vram_gb` 置 `null`（在场但 null，沿 :490 先例）。**

**GATEWAY_VERSION**：`rev17i`（:84，注释 "self-reported in /capabilities; bump with each functional change"）。本票对网关代码**有**功能变更（新增对外只读路由），按 :84 注释语义应 bump。**票面样张＝rev17i→rev17j；是否以 bump 作对外信号终裁候 H-4（决策者），改判则删 S-3 一行即回滚。**

**import 安全性**（桩直调用据）：`main()` 定义于 :1085，:1160 `if __name__ == "__main__"` 卫底下才调用；模块级仅有路径/常量/单例定义——`import collector_proxy` 不起服务、零端口、零线程。`_gateway_status_payload` 无 upstream I/O（见上），桩 handler（SimpleNamespace：`cfg`/`cfg_path`/`gate`）可全量走通，沿 LOADSWEEP-T1 A-6 先例。

### ② 规格

#### ②-1 声明闭集（本票唯一可写仓内面）

```
collector_proxy.py                          (S-1 payload 构建函数＋S-2 路由挂点＋S-3 版本号)
tests/selftest_gateway_status.py            (S-4 新建桩直调套)
tests/selftest_proxy.py                     (S-5 新增一条在岗用例·T-GS 名)
CHANGELOG.md                                (S-6 登记节)
MANIFEST.md                                 (S-7 登记节·第二节)
.collab/tickets/OPS-1123-GWSTATUS.md        (本票本体，登记面，不计施工验收 diff 面)
```

其余全部不入闭集零触碰（含 `config.json`、`config.template.json`、`benchmark-registry.json`、`monitor_ext.py`、`monitor*`、`daily_report.py`、`html_report.py`、`ledger_watchdog.py`、`watchdog-launcher.py`、`paths.py`、`bootstrap.py`、`switch_proxy.py`、`tests/selftest_monitor.py`、`tests/selftest_watchdog.py`、`tests/selftest_daily_report.py`、`tests/selftest_registry.py`、`README.md`、`INSTALL.md`、`data/**`、`logs/**`、`.collab/tickets/OPS-1123-NASGW-COOP.md`（母件）、`.collab/tickets/OPS-1123-LOADSWEEP*.md`、`.collab/drafts/**`）。

#### ②-2 禁动面

- **既有路由零改**：`/health`、`/ext.json`、`/capabilities`＋`/v1/capabilities`、`/monitor*`、`/v1/*`（含 do_POST 闸面、RELAY CONTRACT、账本行、gate 事件日志）——既有 handler 段一行不动，只**插入**新分支；回归底线＝四套既有套读数不回归（③-3/③-4）。
- **Gate 类零改动**：②-0 读面已够用；改 Gate＝并发红线，本票禁。
- **speed_bias 禁凭空填值**：v1 代码零 registry 读、零档案合成；任何非缺席 speed_bias 出现＝判红。
- **gpu_bind/vram_gb 禁推断**：只认 `machine_profile` 申报值或 null；不得从 nvidia-smi/psutil 采样面推断绑定。
- `config.json`（运行时件、git 外）、`config.template.json`（本票不新增示例键——新键可选、缺席即缺省，改模板候另拍）、`benchmark-registry.json`、在岗 8080/8787 服务、引擎面（D:\Strata-toolkit\ 等）：零触碰。
- `do_POST` 零改动：`POST /gateway/status` 落 `_pass_post` 转发 upstream（upstream 答 404/405 由上游定夺）——只读路由承诺＝本路由只经 do_GET 本地回答，此边界如实登记（④）。

#### ②-3 逐条施工规格（落位到文件＋结构）

**S-1 `collector_proxy.py` 新模块级函数 `_gateway_status_payload(handler)`**：置于 `_capabilities_payload`（:419-499）之后、`key_identity`（:502）之前；无 upstream I/O、无新线程、无新锁（只经 snapshot 既有锁面读 gate）。构建规则（全部来源实现在函数内）：

```python
def _gateway_status_payload(handler):
    """GET /gateway/status - unified-status/v0 envelope for the NAS compute pool.
    Read-only; every reading is gate-local or config-declared, zero upstream I/O."""
    cfg = handler.cfg
    machine_id = (cfg.get("machine_id") or "").strip() or socket.gethostname()
    # listen 端口（:1102 rpartition 先例，IPv6 host 含冒号安全）
    try:
        vport = int(str(cfg.get("listen", "")).rpartition(":")[2])
    except ValueError:
        vport = None
    limit, _beat, _wait = _gate_params(handler.cfg_path)          # :374 现读
    snap = handler.gate.snapshot(limit) if handler.gate is not None else None
    in_flight = snap["inflight"] if snap else 0                    # :275
    queued = snap["queued"] if snap else 0                         # len(_waiters) live :275
    slots = None
    raw_e = cfg.get("engine_launch_config")
    if raw_e:
        slots = _strata_parallel_parse(expand_path(raw_e, cfg.get("config_dir")))  # :293
    serving = limit if limit else slots                            # :491 先例
    available = (serving - in_flight) if serving else None         # ②-0 第2条：max(in_flight,admitted)≡inflight
    profile = cfg.get("machine_profile") or {}
    row = {
        "vport": vport,
        "engine": cfg.get("engine_backend") or None,
        "gpu_bind": profile.get("gpu_bind"),
        "vram_gb": profile.get("vram_gb"),
        "available": available,
        "current_tasks": {"in_flight": in_flight, "queued": queued},
        # speed_bias：无档案＝整字段缺席（契约规则；v1 一律缺席，A-6/H-3）——构建即不带此键
    }
    return {
        "schema": "unified-status/v0",
        "machine_id": machine_id,
        "domain": "llm",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),   # :854 ledger ts 口径先例
        "ports": [row],
    }
```

- envelope 五字段名与值域逐字契约；ports 恰一行（本网关单机单 upstream——多上游形态候另票，见④）。
- `engine` 取 config 可选键 `engine_backend`（config.template.json:21 在册；本仓现跑 config.json 无此键 → null，健康账登记）。issue 正文未钉 engine 值域语义（母件字段三实证引擎侧 `/v1/status` 里 `service`="basalt"、`engine`="0.5.0" 两读并存），票裁 A-7＝取申报名（backend kind），null 缺位。

**S-2 `do_GET` 路由挂点**：在 `/capabilities` 分支（:952-967）之后、`local = None`（:968）之前插入新分支，形制逐字沿 capabilities 分支（含异常降级体、`Cache-Control: no-store`、`Access-Control-Allow-Origin: *`）：

```python
        if self.path.split("?", 1)[0] == "/gateway/status":
            try:
                body = json.dumps(_gateway_status_payload(self)).encode("utf-8")
            except Exception as e:
                body = json.dumps({"ok": False, "error": repr(e)}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
```

- 只匹配 `"/gateway/status"` 精确路径（不带 query 匹配、不接 `/v1/*` 前缀）；零鉴权（沿 /health 先例·母件契约）；本分支在 upstream 转发段（:987+）之前 return，**永不转发、零账本行**（沿 :51-52 本地路由纪律）。

**S-3 `GATEWAY_VERSION` bump**：:84 `"rev17i"` → `"rev17j"`（理由＝新增对外只读路由＝功能变更，:84 注释语义；终裁候 H-4，改判＝本行撤销）。`/capabilities` 的 `gateway.version` 自动跟随（:461 透传，零额外改动）。

**S-4 新建 `tests/selftest_gateway_status.py`**（无网络、不起服务、零在岗端口接触；结构沿 selftest_proxy 的 `rec(name, ok, detail)` 报数风，套尾 `%d/%d PASS`＋失败非零退出码）：

- 前置：`sys.path.insert(0, 仓根)` → `import collector_proxy as cp`；桩 handler＝`SimpleNamespace(cfg=<dict>, cfg_path=<临时 config.json 路径>, gate=<Gate 实例或 None>)`（②-0 import 安全性＋:428 卫底实读）。gate 侧构造＝`cp.Gate()` 后**直接**置 `.inflight/.queued/_seq` 模拟在场（测试进程内本地对象，非并发环境，合法）。
- **GS-1 envelope 五字段锁**（gate off，cfg 无 machine_id/machine_profile/engine_backend）：顶层键集**恰等于** `{schema, machine_id, domain, generated_at, ports}`；`schema=="unified-status/v0"`；`domain=="llm"`；`machine_id` 非空字符串；`generated_at` 匹配 `^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$`；`ports` 为 list 且恰 1 行。
- **GS-2 ports 行闭集锁（无档案形态）**：行键集**恰等于** `{vport, engine, gpu_bind, vram_gb, available, current_tasks}`——**`speed_bias` 不在场**（缺位弃权＝键缺席，非 null）；`current_tasks` 键集恰 `{in_flight, queued}`；gate off＋无 engine_launch_config → `available is None`、`in_flight==0`、`queued==0`、`vport==<桩 cfg listen 端口>`、`engine is None`、`gpu_bind is None`、`vram_gb is None`。
- **GS-3 machine_id 来源锁**：cfg 加 `"machine_id": "nas-box-7"` → 输出 `machine_id=="nas-box-7"`；cfg `machine_id` 为空串/缺席 → 输出==`socket.gethostname()`（A-4 两段都锁）。
- **GS-4 available 合成式锁**：cfg `"max_inflight": 2`＋Gate 实例置 inflight=1 → `available == 1`；置 inflight=3（越权超跑态，:228 语义）→ `available == -1`（**不钳位**，如实读数，A-3）；`queued` 在场量经 `_waiters.append([0,False])` 构造 → `current_tasks.queued == 1`。
- **GS-5 machine_profile＋engine_backend 在场形态**：cfg 加 `"machine_profile": {"gpu_bind": "GPU-abc…", "vram_gb": 72}`＋`"engine_backend": "basalt"` → 行值逐键等于申报值；仍无 `speed_bias` 键（任何形态下 v1 都不出）。

**S-5 `tests/selftest_proxy.py` 新增一条在岗用例 `T-GS:route /gateway/status live shape`**：挂在 stage-one（gate off）段第 12 组 GET 断言（:670-677）之后：真起服务态 `GET /gateway/status` → status==200、`Content-Type` 含 json、JSON 顶层五字段在场、`ports[0]["vport"]==PX_PORT`、`"speed_bias" not in ports[0]`、既有 `GET /health`/`/v1/models` 用例前后照跑（回归自证）。**除此一条外 selftest_proxy.py 零改动**；套总数由 45 → 46（③-3 期望读数随之钉 46/46）。

**S-6 `CHANGELOG.md`**：倒序置顶新增 rev 节（节名样张 `## rev17j (2026-11-2x) · OPS-1123-GWSTATUS`）＝一句话摘要：新增只读路由 `GET /gateway/status`（unified-status/v0·NAS 算力池对接）＋selftest 两条入册＋GATEWAY_VERSION bump；注明既有路由零改、四套回归不回归。

**S-7 `MANIFEST.md`**：第二节（改动登记）加同拍节＝`collector_proxy.py` 描述更新＋新增 `tests/selftest_gateway_status.py` 一行；其余节零动。

### ③ 验收标准（全机械可判）

> 母本仓根跑，基线＝ANCHOR `ccb5892`（施工开端 HEAD 若因放行落链前移，一律以开工 `git rev-parse --short HEAD` 为 diff 基线并在回执声明，沿 LOADSWEEP-T1 先例）。禁 git 写操作（验收全程只读）。在岗 8080 服务不入判据（④）。

1. **闭集核验**：`git diff --name-only <基线> | grep -vE '^(collector_proxy\.py|tests/selftest_gateway_status\.py|tests/selftest_proxy\.py|CHANGELOG\.md|MANIFEST\.md|\.collab/tickets/OPS-1123-GWSTATUS\.md)$' | wc -l` ＝ **0**。
2. **新套全绿**：`python tests/selftest_gateway_status.py` 退出码 **0** 且末行 `%d/%d PASS` 两数相等（GS-1～GS-5 逐名 PASS，回执贴原始输出全文）。
3. **proxy 套不回归＋新用例在册**：`python tests/selftest_proxy.py` ＝ **46/46 PASS**（45 既有名＋`T-GS:route /gateway/status live shape` 逐名 PASS）退出码 **0**。
4. **三套回归**：`python tests/selftest_watchdog.py` 末行＝**RESULT: 31 passed, 0 failed** 退出码 0；`python tests/selftest_monitor.py` ＝ **57/57 PASS** 退出码 0；`python tests/selftest_daily_report.py` ＝ **15/15 PASS** 退出码 0。辅套 `python tests/selftest_registry.py` ＝ **6/6 PASS**（registry 消费面旁证）。
5. **禁动面零触碰**：`git diff --name-only <基线> | grep -cE '(config|watchdog|monitor|daily_report|benchmark-registry|selftest_(monitor|watchdog|daily_report|registry)|paths\.py|bootstrap\.py)'` ＝ **0**。
6. **Gate 类零改动**：`git diff <基线> -- collector_proxy.py | grep -cE '^[-+].*(class Gate|def acquire|def release|def snapshot|_cond|_waiters|inflight)'` ＝ **0**（diff 内不得出现 Gate 成员行）。
7. **speed_bias 零合成**：`git diff <基线> -- collector_proxy.py | grep -c 'speed_bias'` ＝ **0**（新代码不出现该键的合成/读取行——缺位＝不写键）；辅判 GS-2/GS-5 PASS（键缺席断言）。
8. **零 upstream 新调用**：`git diff <基线> -- collector_proxy.py | grep -cE '^\+.*(urlopen|urlreq)'` ＝ **0**（新 payload 函数不引任何 HTTP 客户端调用；serving 全本地）。
9. **版本号面**：`git diff <基线> -- collector_proxy.py | grep -E '^[+-].*GATEWAY_VERSION' | wc -l` ＝ **2**（一删一增＝rev17i→rev17j；H-4 若裁不 bump 则＝0 且 S-3 撤销）。

### ④ 边界约束

- **票间关系**：本票＝NASGW-COOP 实装项唯一施工载体；与 OPS-1123-LOADSWEEP 族零文件交集（registry 面零触碰，speed_bias 档案接线另拍＝H-3）；与 TUNEADVISOR 零交集。母件 NASGW-COOP 对接闭环（GitHub 回帖＋NAS 侧 curl 判据）不入本票，归主理人收尾链。
- **在岗服务零接触**：验收全部在测试环境（throwaway 端口＋import 直调）；生产 8080 的 `curl /gateway/status` 出 envelope＝**部署入闸后**对接判据（两人工闸·specs 准入闸＋部署准入闸，2026-11-23 01:15 口径，不可代理代跑），不入③。
- **只读面承诺**：路由经 do_GET 本地回答，零账本行、零 gate 事件、零 upstream 转发；`POST /gateway/status` 不承诺（落 `_pass_post`，上游自答）——只读契约限于 GET，如实登记。
- **多端口形态不在 v1**：ports[] 恰一行（单机单 upstream 实态）；多引擎/多端口拆分＝另票。
- **config 新键可选**：`machine_id`/`machine_profile` 缺席即缺省（hostname/null），现网 config 零改可跑——部署侧要出真实绑定档案时才申报，属 config 准入闸面非本票写域。
- **施工面纪律**：临时工作物只落仓根 `.scratch/OPS-1123-GWSTATUS/`，完工前清零；禁仓外临时路径；单一工程师席新鲜实例、同席禁多实例。
- **交付与回执**：完工回执先行＝开端 HEAD（ccb5892 或开工实拍）＋写入清单（字节数＋sha256 前→后）＋③九条读数＋`.scratch/` 自查；落位由主理人程序定。
- **票放行**＝主理人程序确认；候裁 H-1～H-4 随放行件采纳或修票。本票 v1 起草不启施工。
- **部署不入票**：合入后部署入闸＝常规两人工闸（specs 准入闸＋部署准入闸），NAS 侧对接 curl 在部署后跑，闭环登记归母件 NASGW-COOP（append-only 随登）。

## 租约段（票内·经架构签注由 B2 lease-issuer 实例化）

- path_globs：`collector_proxy.py`、`tests/selftest_gateway_status.py`、`tests/selftest_proxy.py`、`CHANGELOG.md`、`MANIFEST.md`、`.collab/tickets/OPS-1123-GWSTATUS.md`
- deny_globs：`config.json`、`config.template.json`、`benchmark-registry.json`、`monitor_ext.py`、`monitor*`、`daily_report.py`、`html_report.py`、`ledger_watchdog.py`、`watchdog-launcher.py`、`paths.py`、`bootstrap.py`、`switch_proxy.py`、`ext.js`、`README.md`、`INSTALL.md`、`tests/selftest_monitor.py`、`tests/selftest_watchdog.py`、`tests/selftest_daily_report.py`、`tests/selftest_registry.py`、`data/**`、`logs/**`、`.collab/tickets/OPS-1123-NASGW-COOP.md`、`.collab/tickets/OPS-1123-LOADSWEEP*.md`、`.collab/tickets/OPS-1123-TUNEADVISOR.md`、`.collab/drafts/**`、`D:\Strata-toolkit\**`
- 灰度判据（票内声明字段·decision-pack 读取）：`python tests/selftest_gateway_status.py` 全绿退出码 0 ＋ `python tests/selftest_proxy.py` 46/46 退出码 0 ＋ `python tests/selftest_monitor.py` 57/57 ＋ `python tests/selftest_watchdog.py` 31 passed 0 failed ＋ `python tests/selftest_daily_report.py` 15/15——测试环境判据，不依赖换脑、不依赖在岗 8080 服务。
- 席位 ID／票 ID／哈希：由状态机签发，非人工填写

## 票裁已决（A-1～A-8·起草席决；推翻走回流件）

- **A-1｜新分支照抄 capabilities 分支形制**：`do_GET` :952-967 是仓内"本地 JSON 路由＋异常降级体＋no-store＋CORS"最新先例；沿其插入点与发送序列，既有一行不动只插段。
- **A-2｜gate 读数只走 `snapshot(limit)`**：②-0 第 3 条——裸属性读 `_waiters`/`inflight` 绕锁＝撕裂风险；snapshot 是唯一背书的持锁读面（:273-277），capabilities 已用两年（rev10 起）。
- **A-3｜available＝serving−inflight，不钳位**：`max(in_flight, admitted) ≡ Gate.inflight`（②-0 第 2 条读码：admitted 无独立计数器，三准入点共担 inflight）；越权超跑态（:228）下 available 可为负＝如实读数，钳位＝掩盖超跑违证据如实性；serving 不可得→null 缺位（沿 :490-491 先例），不猜。
- **A-4｜machine_id＝config 可选键 `machine_id`，空/缺退 `socket.gethostname()`**：现网 config 实读无此键（票头读数）；hostname 零依赖（socket :59 已导入）、与 NAS 侧机器身份语义对齐；空串按缺席处理（申报为空≠申报身份）。GS-3 两段都锁。
- **A-5｜gpu_bind/vram_gb＝config 可选键 `machine_profile` 申报，缺位＝null**：网关无机读 GPU↔端口绑定面（②-0 实读：monitor 采样有卡但无"哪张卡承载哪个端口"的事实源；Basalt 单脑路由的在岗卡是运行时事实非配置事实）——从采样推断＝猜，禁。申报制把绑定事实的所有权留给部署人，null 形态沿 :490 先例；候选"从 /ext.json 合成"已否（读码判定＝ext.json 无端口维度绑定信息，合成必致推断）。
- **A-6｜speed_bias v1 一律缺席**：registry map 行三标量全 null（registry:23-27/:46-50 实读）且行↔vport 无 join 键——任何合成路径都违"无档案＝整字段缺席（不填 1.0）"契约或缺证填值。v1 代码零 registry 读；接档案＝registry 行补 join 键＋非 null 标量后另票（H-3）。
- **A-7｜engine＝config `engine_backend` 申报名（缺位 null）**：issue 未钉该字段值域语义；网关 config 唯一在册引擎标识键＝engine_backend（config.template.json:21）；取申报名与 gpu_bind 同族（申报制、不猜），引擎版本字符串属引擎面现读，本路由不探（④零 upstream 流量）。
- **A-8｜新套用 import 直调桩法＋proxy 套补一条在岗用例双轨**：桩法沿 LOADSWEEP-T1 A-6 先例（import 安全性②-0 实读：main :1085/:1160 卫底下、模块级零副作用），可全量锁 envelope/行闭集/合成式/来源态且不碰端口；在岗形态由 selftest_proxy 真起服务态 T-GS 用例锁（curl 在岗不可测之解＝既有用例风格内真起 throwaway 服务，比 LOADSWEEP-T1 纯桩更进一步——本票动 collector_proxy.py，路由挂点必须过真服务）。

## 候裁单列（H-x·决策者拍板，本席不裁）

- **H-1｜machine_id 来源终裁**：票面样张＝A-4（config 可选键 `machine_id` 缺省退 hostname）。若裁别的来源（如复用 key_labels 命名体系/独立身份文件）＝修票替换 S-1 一行＋GS-3 断言常量。
- **H-2｜gpu_bind/vram_gb 缺位形态终裁**：票面样张＝A-5（在场但 null，config 申报制）。若裁"整字段缺席"（同 speed_bias 缺位式）＝修票替换 S-1 行构建＋GS-2/GS-5 断言；NAS 侧按在场性读 null 还是按缺席读 absent，需与对方契约口径对齐后拍。
- **H-3｜speed_bias 接线与否**：票面样张＝v1 一律缺席（A-6）。若要在本票期接 registry 档案＝需先裁 registry 行↔vport join 键契约（registry 面变更另票，本票闭集不含 benchmark-registry.json），且三标量须有实测非 null 值（T3 扫描产出前无从满足）。
- **H-4｜GATEWAY_VERSION bump 终裁**：本席读码结论＝要 bump（rev17i→rev17j；:84 注释 "bump with each functional change"，新增对外只读路由＝功能变更，且 /capabilities.gateway.version 是 NAS 侧差分信号面）。若裁不 bump＝撤 S-3 一行，③-9 期望读数改 0。

## 健康账登记（回流素材）

1. **config.json 现网无 engine_backend 键**：现跑 config 键表（票头实读）不含此键→`engine` 现网出 null。NAS 侧若按 engine 值分流，需在部署 config 准入闸时补申报（模板键在册，现网件滞后）。
2. **`Gate.queued` 计数器陷阱**：:142 字段名合法但语义＝单调累计（永不递减），仓内注释已明令不读；本路由经 snapshot 隔离之。后来者若裸读 `gate.queued` 即引入排队数虚高——建议 monitor 侧契约文档已守（monitor_ext.py:564 走 snapshot 键），入册备查。
3. **/gateway/status 与 /capabilities 读数面部分重叠**（gate 快照/engine 槽位两源同源）：两路由并存后 NAS 侧选面口径（一发统一面 vs 老能力面）属对方消费决策；本票两面包互不破坏（capabilities 零改）。

## 可施工性判定（架构席自评）

- 挂点实读在册：`do_GET` 分支插点前后行（:952-968）实读；`_capabilities_payload` :419-499 全读作形制母版；Gate 类 :132-277 全读（属性名/锁语义/三准入点/归还出口逐行引用）；`GATEWAY_VERSION` :84 实读；config 读取面 :103-107/:374-416 实读＋现网键表实跑；monitor_ext 采样行 :231-281 实读（gpu_bind 否决依据）；registry 标量态实读；import 卫底实读；四套＋辅套基线全部当轮实跑（45/45、31/31、57/57、15/15、6/6）。
- 判别力自评：GS-2 对"speed_bias 被填 1.0/null/行键膨胀"判红；GS-4 对"合成式用错属性（读 Gate.queued 计数器）/钳位"判红；GS-3 对"machine_id 来源漂移"判红；③-6 对"顺手动 Gate"判红；③-7 对"偷偷接 registry"判红；③-8 对"新路由引 upstream 探测"判红；③-1/③-5 对"越领地"判红。
- 未实跑面（留施工/QA）：GS 套首跑；T-GS 在岗用例首跑（throwaway 端口段）；③-6 grep 对 diff 形态的误报率（若注释行含关键词，回执如实贴读数并辅行人工目检，判据不放宽）。判定＝**可施工**，无阻塞点；放行＝主理人程序确认＋H-1～H-4 随放行件裁定。

—— 架构席 · OPS-1123-GWSTATUS v1 · 开端 HEAD 实测 `ccb5892`（git -C D:\Projects\token-ledger-proxy rev-parse --short HEAD）· 起草实核居本仓 .collab/ · 2026-11-23