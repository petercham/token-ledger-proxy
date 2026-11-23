# 回流件 · OPS-1123-GWSTATUS（SWB v2.9 §3 回流件模板·完成型）

## 回流头

- 票 ID：OPS-1123-GWSTATUS
- 席位 ID：software-team-engineer（工程师席）
- 实例 ID：本票新鲜实例（一票一新鲜实例·票间串行·未开第二实例）
- 回流态：**完成**
- 迁移登记：待主理人以 state-transition.py 登记（本仓无 B2 账本实体件，落链归主理人·放行件口径）
- 开工 HEAD：`git -C D:\Projects\token-ledger-proxy rev-parse --short HEAD` 实测 = **3b11be3**（开工实跑＝票面③声明的开工前移基线，diff 基线一律用之）
- 完工 HEAD：`git rev-parse --short HEAD` 实测 = **3b11be3**（全程禁 git 写操作，未落 commit——交付形态＝工作区改动＋本回执，commit 归主理人落链程序）
- 交付 diff 形态：`git diff --stat 3b11be3` = `CHANGELOG.md +6 | MANIFEST.md +10 | collector_proxy.py +60/-1 | tests/selftest_proxy.py +15`（4 files changed, 90 insertions, 1 deletion）＋新增未跟踪文件 `tests/selftest_gateway_status.py`（`git status --porcelain` 尾行 `?? tests/selftest_gateway_status.py`）

## 正文四节

### ① 完成范围（与票面②规格逐条对位核销）

| 票面项 | 落位 | 状态 |
|---|---|---|
| S-1 `_gateway_status_payload(handler)` | collector_proxy.py :502-542（置于 `_capabilities_payload` 后、`key_identity` 前）＝票面样张逐字实施（H-1 machine_id 可选键空/缺退 `socket.gethostname()`；H-2 machine_profile 申报·键/子键缺位→null；H-3 speed_bias 整字段不写键；A-2 gate 读数只经 `Gate.snapshot(limit)`；A-3 available＝serving−inflight 不钳位；serving＝`limit if limit else slots`，皆不可得→null） | 核销 |
| S-2 do_GET 路由挂点 | collector_proxy.py :1002-1017（`/capabilities` 分支之后、`local = None` 之前插入）＝样张逐字（精确路径匹配·异常降级体·no-store·CORS·upstream 转发段前 return） | 核销 |
| S-3 GATEWAY_VERSION bump | :84 `rev17i`→**`rev17k`**（H-4 放行件修正值·非票面样张 rev17j；rev17k 开工前 grep 全仓未占用已核实） | 核销 |
| S-4 `tests/selftest_gateway_status.py` | 新建·import 直调桩法·GS-1～GS-5 全部按票面断言面实施（GS-3 含空串/空白/缺席三段；GS-4 含超跑 -1 不钳位、live waiter 计 queued、serving 退引擎槽位、两源皆缺 null 两段补强；GS-5 含半截申报 null 形态补强）＝18 rec 全绿 | 核销 |
| S-5 `tests/selftest_proxy.py` 加 T-GS | 挂 stage-one 第 12 组 GET 断言后·名 `T-GS:route /gateway/status live shape`＝样张断言面（200＋json＋五字段＋vport==PX_PORT＋speed_bias 键缺席）；除此零改动；45→46 | 核销 |
| S-6 CHANGELOG.md | 倒序置顶 rev 节 `## rev17k (2026-11-23) · OPS-1123-GWSTATUS`（一句话摘要＋selftest 两条入册＋bump 说明＋既有路由零改/四套回归读数） | 核销 |
| S-7 MANIFEST.md | 第二节追加 `### 2.31 rev17k` 登记节（collector_proxy.py 描述更新＋新套一行＋T-GS 一行；其余节零动） | 核销 |

放行件补充项处置：config.template.json 两键示例＝按主理人裁定 **(b) 撤回**（票面②-2"改模板候另拍"成立），本票零触碰，已实证于 ③-5＝0。

候裁四点实施对齐：H-1＝A-4 已实施；H-2＝A-5 已实施（在场但 null，GS-5 锁死半截申报形态）；H-3＝A-6 已实施（v1 一律缺席，GS-2/GS-5 键缺席锁＋③-7 grep 锁）；H-4＝bump 采纳·rev17k。

### ② 未完范围／阻塞点

无（完成态）。

### ③ 验收自测读数（票面③九条·基线 3b11be3·命令原文＋实测读数·申报载体不自判合格）

**③-1 闭集核验**
```
git diff --name-only 3b11be3 | grep -vE '^(collector_proxy\.py|tests/selftest_gateway_status\.py|tests/selftest_proxy\.py|CHANGELOG\.md|MANIFEST\.md|\.collab/tickets/OPS-1123-GWSTATUS\.md)$' | wc -l
```
实测 = **0** ✅（diff 面另有 `.collab/returns/engineer/OPS-1123-GWSTATUS-return.md`＝本回流件，席位写域件非仓根 diff 面——`git diff --name-only` 于未跟踪新文件不列出，本件与 GS 新套同态；GS 新套经 ③-1 白名单在册）

**③-2 新套全绿**
`python tests/selftest_gateway_status.py` → 退出码 **0**，末行 **18/18 PASS**（两数相等）✅
原始输出全文（逐名）：
```
PASS  GS-1: envelope keys == {schema, machine_id, domain, generated_at, ports}  got=['domain', 'generated_at', 'machine_id', 'ports', 'schema']
PASS  GS-1: schema/domain/machine_id/generated_at/ports one row  schema=unified-status/v0 domain=llm mid='We4AI' gen='2026-11-23 20:21:25' ports=1
PASS  GS-2: row keys == {vport, engine, gpu_bind, vram_gb, available, current_tasks}  got=['available', 'current_tasks', 'engine', 'gpu_bind', 'vport', 'vram_gb']
PASS  GS-2: speed_bias key ABSENT (no archive = field absent, not null)
PASS  GS-2: current_tasks keys == {in_flight, queued}  got=['in_flight', 'queued']
PASS  GS-2: gate off + no launch config -> available None, counters 0, vport from listen  row={'vport': 18181, 'engine': None, 'gpu_bind': None, 'vram_gb': None, 'available': None, 'current_tasks': {'in_flight': 0, 'queued': 0}}
PASS  GS-3: declared machine_id wins  got='nas-box-7'
PASS  GS-3: machine_id empty string -> socket.gethostname()  got='We4AI' want='We4AI'
PASS  GS-3: machine_id blank string -> socket.gethostname()  got='We4AI' want='We4AI'
PASS  GS-3: machine_id absent -> socket.gethostname()  got='We4AI' want='We4AI'
PASS  GS-4: limit 2, inflight 1 -> available 1  got=1
PASS  GS-4: inflight 3 over-run -> available -1 (no clamp)  got=-1
PASS  GS-4: live waiter -> current_tasks.queued == 1  got={'in_flight': 3, 'queued': 1}
PASS  GS-4: gate off + engine slots 4 -> available 3  got=3
PASS  GS-4: no limit + no readable launch config -> available None  got=None
PASS  GS-5: declared gpu_bind/vram_gb/engine pass through verbatim  row={'vport': 1, 'engine': 'basalt', 'gpu_bind': 'GPU-abc123', 'vram_gb': 72, 'available': None, 'current_tasks': {'in_flight': 0, 'queued': 0}}
PASS  GS-5: declared row keys stay the closed set; speed_bias still ABSENT  got=['available', 'current_tasks', 'engine', 'gpu_bind', 'vport', 'vram_gb']
PASS  GS-5: machine_profile without gpu_bind -> gpu_bind None (present but null)  row={'vport': 1, 'engine': None, 'gpu_bind': None, 'vram_gb': 72, 'available': None, 'current_tasks': {'in_flight': 0, 'queued': 0}}

18/18 PASS
```
（桩 handler＝SimpleNamespace(cfg=cp.load_config(临时config), cfg_path, gate)；临时 config 落 `.scratch/OPS-1123-GWSTATUS/`，套尾 rmtree 清零。首版桩 cfg 用裸 dict 致 GS-4 引擎槽位退路一项 FAIL（缺 config_dir 键→相对路径解析基准漂移），改经 cp.load_config 构桩＝与在岗 main() 同构后全绿——修的是桩不是断言，未放宽任何判据。）

**③-3 proxy 套不回归＋新用例在册**
`python tests/selftest_proxy.py` → 退出码 **0**，末行 **46/46 PASS** ✅
新用例逐名行：
```
PASS  T-GS:route /gateway/status live shape  status=200 ports=[{'vport': 18080, 'engine': None, 'gpu_bind': None, 'vram_gb': None, 'available': None, 'current_tasks': {'in_flight': 0, 'queued': 0}}]
```
同段回归自证邻行：`PASS  GET /health local route`；`GET upstream 401 passes through`、`GET Content-Encoding relayed` 均在全文 PASS 列。全 46 名 PASS（含 gate 族全段），失败名清单未打印（bad 空）。

**③-4 三套回归＋辅套**
- `python tests/selftest_watchdog.py` → 末行 **RESULT: 31 passed, 0 failed**，退出码 **0** ✅（沿票面③-4 实态读数）
- `python tests/selftest_monitor.py` → **57/57 PASS**，退出码 **0** ✅
- `python tests/selftest_daily_report.py` → **15/15 PASS**，退出码 **0** ✅
- 辅套 `python tests/selftest_registry.py` → **6/6 PASS**，退出码 **0** ✅

**③-5 禁动面零触碰**
```
git diff --name-only 3b11be3 | grep -cE '(config|watchdog|monitor|daily_report|benchmark-registry|selftest_(monitor|watchdog|daily_report|registry)|paths\.py|bootstrap\.py)'
```
实测 = **0** ✅（config.template.json 按裁定 (b) 未入面）

**③-6 Gate 类零改动**
```
git diff 3b11be3 -- collector_proxy.py | grep -cE '^[-+].*(class Gate|def acquire|def release|def snapshot|_cond|_waiters|inflight)'
```
实测 = **1** ⚠️＝**如实贴读数（不放宽判据）**。命中行逐字：`+    in_flight = snap["inflight"] if snap else 0`——新 payload 函数对 `snapshot()` 返回 dict 的 **JSON 键字符串**消费行，非 Gate 成员行。辅行人工目检＋机械旁证（票面"可施工性判定"节预告的 grep 误报率场景，按预案贴读数辅证）：
- diff 仅三 hunk，全部在 Gate 区外：`@@ -84`（版本号行）、`@@ -501,0 +502,42`（插新函数）、`@@ -959,0 +1002,16`（do_GET 插分支）；Gate 类体 :132-277 无 hunk。
- Gate 区段字节级不变锁：`class Gate:` 起至 `_last_limit = 0` 止（7368 字节）改动前后 sha256 **一致** = `513ff200995499a39893e662660946544aac80aaa880bc90dc77ce1c7eb99464`（Python 切片＋hashlib 实测，非目测）。
- 禁动红线本体（Gate 类零改动·②-2）＝未违；本读数属 grep 关键词面误报，判定权在 QA/CI 面。

**③-7 speed_bias 零合成**
```
git diff 3b11be3 -- collector_proxy.py | grep -c 'speed_bias'
```
实测 = **0** ✅（新代码不出现该键任何合成/读取行；辅判 GS-2/GS-5 键缺席断言 PASS）

**③-8 零 upstream 新调用**
```
git diff 3b11be3 -- collector_proxy.py | grep -cE '^\+.*(urlopen|urlreq)'
```
实测 = **0** ✅

**③-9 版本号面**
```
git diff 3b11be3 -- collector_proxy.py | grep -E '^[+-].*GATEWAY_VERSION' | wc -l
```
实测 = **2**（一删一增）✅
```
-GATEWAY_VERSION = "rev17i"            # self-reported in /capabilities; bump with each functional change
+GATEWAY_VERSION = "rev17k"            # self-reported in /capabilities; bump with each functional change
```

**写入清单（字节数＋sha256 前→后）**

| 文件 | 前 | 后 |
|---|---|---|
| collector_proxy.py | 57426 B · 87360d5705f39eb06c14e08e273b43465f3c1de9c55046a7f7420a773e31a5e6 | 60242 B · f45cc65ad83f72c02f707c52601514937f5ee3a3e8bc283062084d9d465354be |
| tests/selftest_gateway_status.py | （不存在） | 8776 B · 95e8ba2aa602d5fea885dcea33d163af63c9f88b38d9e46d60216ee6c2bdc662 |
| tests/selftest_proxy.py | 80436 B · 9e611ebb73482f28a7141fb9782df42782066540136ccac07079791d002cdae5 | 81283 B · 130f9e1d2550fe6417f2caed6f5d6abc18ec76261961dafa6d5712858db2e5cc |
| CHANGELOG.md | 58738 B · 6914dec0640abc9ecd1004cc527db4112fe8bfceb043e90191122c28f725070e | 60120 B · aa64f3c24fedb0f43564727a1b94c5a55b6d088a710c7edf6cff61403330b3d2 |
| MANIFEST.md | 107552 B · 5b1e21d619100c5e94dbc3fa33ce2212a7f96af1995c8ede3a08c8f93af01479 | 110977 B · 0badd631513e38096a0a8523c54a06946e29a216dcf2ff36909e33dd7ec7b058 |

（sha256 均为 `sha256sum` 实算；改动前后各跑一次。`py_compile` collector_proxy.py 编译通过。）

### ④ 边界申报

- **越界零申报**：写入清单＝票面②-1 闭集五文件＋本回流件（`.collab/returns/engineer/`＝席位写域·回流件模板指定落位）＋`.scratch/OPS-1123-GWSTATUS/`（临时件·已清零：GS 套套尾 `shutil.rmtree` 自清，目录本身已不存在，`ls` 实证）。config.json / config.template.json / benchmark-registry.json / monitor* / 看门狗 / 日报 / paths / bootstrap / 母件票＝零触碰（③-1、③-5 读数为证）。在岗 8080/8787 服务零接触（验收全在 throwaway 端口 18080＋import 直调）。
- **git 纪律**：全程零 git 写操作（无 add/commit/amend/stash）；只读命令（rev-parse/log/status/diff/show）已用。工作区改动待主理人落链。
- **候裁处置单列**：H-1/H-2/H-3/H-4 按放行件（含 rev17j→rev17k 修正）全部实施，无遗留候裁项；config.template.json 放行件滑点已由主理人裁定 (b) 撤回，票面②-2 原口径维持。
- **运行残留清理声明**：`.scratch/OPS-1123-GWSTATUS/` 清零（含 GS 套临时 config/engine.json 全部）；proxy 套自带临时目录由该套自身 rmtree（既有纪律）；本席未在任何仓外路径落临时件。
- **健康账素材（供母件 NASGW-COOP 随登）**：在岗 config.json 无 machine_id/machine_profile/engine_backend 三可选键→现网 `/gateway/status` 出 machine_id=hostname、gpu_bind/vram_gb/engine=null、available 取决于 max_inflight/engine_launch_config——路由现跑态与票面健康账登记 1 一致；NAS 侧对接 curl 仍候部署入闸（不入③，沿票面④）。

—— 工程师席 · OPS-1123-GWSTATUS 完工回流 · 2026-11-23
