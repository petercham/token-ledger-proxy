# OPS-1123-ROOTLAYOUT-T1 · 仓根分层迁移施工票（git mv＋引用链随动＋STRUCTURE 建档，一张收口）

## 票头（登记区）

- 票 ID：`OPS-1123-ROOTLAYOUT-T1`
- 票名：仓根白名单制分层迁移（gateway/monitor/reporting/data-defs/docs 五区 git mv＋全部引用链随动）＋ STRUCTURE 建档收口
- 票型：**施工票（L3 载体）**；母件＝`OPS-1123-ROOTLAYOUT`（本仓 .collab/tickets/OPS-1123-ROOTLAYOUT.md，append-only，本票不触其面；母件本体 sha256 前缀 `970edc4c5c1f`，起草轮实算）
- 领办面＝**本仓（token-ledger-proxy 母本）＋部署面（`D:/Strata-toolkit/token-ledger-proxy/`＝人工闸②候裁区，本票只出方案不执行，见 H-1/H-2）**
- 开端读数（本席当轮实跑·2026-11-23）：
  - ANCHOR＝`98520fdc26447854e8c243a542448bdb177915b7`（`git -C D:/Projects/token-ledger-proxy rev-parse HEAD`）；`git status --porcelain`＝**空**（工作区净）。
  - 六套基线当轮实跑（全部退出码 0）：
    - `python tests/selftest_proxy.py`＝**46/46 PASS**
    - `python tests/selftest_watchdog.py`＝**RESULT: 31 passed, 0 failed**
    - `python tests/selftest_monitor.py`＝**57/57 PASS**
    - `python tests/selftest_daily_report.py`＝**15/15 PASS**
    - `python tests/selftest_registry.py`＝**6/6 PASS**
    - `python tests/selftest_gateway_status.py`＝**18/18 PASS**
  - `python bootstrap.py --check`（母本仓根）＝**exit 2**（`[FAIL] 还没有 config.json`）＝母本仓根无运行时 config.json，实态如实登记（健康账 6）。
  - 仓根盘面＝26 个非目录文件（`.gitignore`＋4 md＋5 py＋6 monitor 面＋csv/json 两数据＋4 bat/sh＋paths 等）；`git ls-files` 仓根面＝8 件在册＋`config.template.json`＋`service-examples/**`＋`docs/*.png`×3＋`legacy/**`＋`tests/**`＋`.collab/**`。
  - 在岗面旁证（只读）：`GATEWAY_VERSION`＝`rev17k`（collector_proxy.py:84）——母票时序边界所指 rev17k 候静换载自动化已落码，时序前置满足。
  - 部署面 `D:/Strata-toolkit/token-ledger-proxy/config.json` 只读对拍实读：**无 `collector_script` 键**；`out_dir="@here/data"`、`listen=":::8080"`、`upstream="http://127.0.0.1:8787"`、`strata_config="D:\Strata-toolkit\basalt\basalt_config.json"`（绝对）、`engine_launch.cmd/cwd` 全绝对（basalt.exe 路径）——**零 `@pkg` 引用**；部署面根另有 `relaunch-now.flag`、`logs/`、`ledger-watchdog.log`、`collector-proxy.log`、根级 `selftest_*.py` 四份（运行时件，健康账 3/8 登记）。
  - 启动夹实装件（只读）`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Token ledger watchdog.vbs`：`pkg = "D:\Strata-toolkit\token-ledger-proxy"`、拉起 `pkg & "\ledger_watchdog.py" --lock-wait 86400`——＝人工闸②面，本票只出改法（H-2）。
- 起草席位／修票权席位：架构席
- 前置件：OPS-1123-ROOTLAYOUT（母票·已立案）；rev17k 候静换载自动化先行（时序边界§五，已满足）
- 修订记录：**v1**（初稿；本票落盘外零触碰；票未放行、零施工——本票起草全程未执行任何 git mv/git 写操作，全部迁移命令为票内待执行规格）

### 准入四判据自查（票面自证）

1. **无 API 变更**：零对外行为变化——路由面（/health /monitor* /ext.json /capabilities /gateway/status /v1/*）、账本行、gate 语义、看门狗行为、报表输出全部零改；功能 diff＝0 由 ③-10 白名单 grep 机检。
2. **口径已裁**：目标形态树＝母票§一闭集照录；随动点全部**读码证实**（②-0 逐条文件:行，无一凭母票措辞）；装配细节票裁 A-1～A-8；五个来源/时序/形制面上候裁 H-1～H-6。
3. **可机械验收**：③十二条全带可执行命令＋期望读数（恰集命令／六套套数不变全绿／bootstrap 三绿／throwaway 真服务三面 curl／看门狗集成新深度重跑／rename 读数／功能语义零变更白名单 grep／文档与 GBK 件随动读数）。
4. **不触真源**：不改任何功能语义、不碰两域 config.json、不改 benchmark-registry.json/api-price-table.csv 内容、不碰在岗 8080/8787、不执行启动夹实装件与部署面任何动作；tests 用例断言语义零改（只改定位路径，六套套数 46/31/57/15/6/18 迁移后必须不变＝改断言即判红）。

---

## 票体四字段（自包含）

### ① 目标

按母票§一把仓根收敛到白名单恰八件（`README.md INSTALL.md CHANGELOG.md MANIFEST.md start.bat start.sh bootstrap.py .gitignore`），其余运行时件按角色下沉 `gateway/ monitor/ reporting/ data-defs/ docs/` 五区：**全部移动走 `git mv`（rename 检测在册），每一处路径引用链随动改到落位，另立 `docs/STRUCTURE.md`＋`.workbuddy/swb-anchor` 收 STRUCTURE 建档面**。

明确不做（负声明）：
- **不改任何功能语义**：功能 diff＝0，纯迁移＋引用随动＋文档登记；任何函数体、路由匹配串、判定逻辑、断言语义出现 diff＝越界（③-10 机检）。
- **不碰部署面**（`D:/Strata-toolkit/**` 零触碰＝人工闸②，H-1/H-2 候裁）。
- **不改 tests 用例断言语义**（只改定位路径；六套套数不变）。
- **不改 config.json（两域）、benchmark-registry.json / api-price-table.csv 内容、任何功能逻辑、在岗 8080/8787 服务、启动夹实装 VBS（只出改法）**。
- 不 bump `GATEWAY_VERSION`（rev17k 不动——本票零功能变更；`git diff` 中出现 GATEWAY_VERSION 行＝判红）。

### ②-0 读码判定（起草席当轮实读，全部文件:行实读；③机检复核）

**A. paths.py 包根假设**（paths.py:20）：`PKG_DIR = os.path.dirname(os.path.abspath(__file__))`——`@pkg` 与裸相对路径的兜底基（:31 `base = config_dir or PKG_DIR`、:35-37 `@pkg`）现值＝仓根（因 paths.py 现居仓根）。文件下沉 `gateway/` 后 PKG_DIR 变 `gateway/`，`@pkg` 语义漂移＝**必改**：定义改为上溯一层（见 S-2）。

**B. 看门狗四锚**（ledger_watchdog.py 实读）：
- 默认 collector 解析 `resolve_collector()`（:117-137）三级＝env `STRATA_COLLECTOR_PATH` → config `collector_script` → **`os.path.join(HERE, "collector_proxy.py")`（:137，同目录默认）**——两者同迁入 gateway/，**同目录语义保持，零改**；部署面 config 无 collector_script 键（票头实读）→ 在岗走第三级默认，迁移后自动指向 `gateway/collector_proxy.py`，config 零改可跑。
- config 锚（:83）`CONFIG_PATH = os.path.join(HERE, "config.json")`；日志锚（:84-86）`LOG_DIR = HERE/logs`＋`os.makedirs(LOG_DIR)`（:86 **import 期副作用**，被 selftest_watchdog:91 importlib 加载时同样触发）；wake flag 锚（:700）`os.path.join(os.path.dirname(args.config), WAKE_FLAG_NAME)`＝**锚 config 旁**；锁＝端口面 `watchdog_lock_port`（:93/:693，与目录无关）。**HERE 若不动语义，config/logs/flag 三锚随迁 gateway/＝部署面在岗运行时件（根级 config.json、logs/、relaunch-now.flag）全部失联**——票裁 A-1：HERE 改锚包根（上溯一层），三锚留部署根。

**C. switch_proxy.py 认岗与写侧探测（纠母票措辞）**：`--check` 认岗**不存在进程命令行匹配串**——认岗面＝端口/netstat PID（:63-84）＋看门狗锁端口 bind 试探（`watchdog_on_duty()` :202-214，沿 `ports_from_config` 重绑 :362-364）＝**与代码目录深度无关，零改**。随动点只有三处：`HERE`（:44）、`sys.path.insert(0, HERE)`（:45，找 paths.py——paths 同迁入 gateway/，须保持指脚本目录）、`CONFIG_PATH`/`WAKE_FLAG`（:46-47，HERE 锚根＝A-1，与看门狗 flag 锚 `dirname(config)` 保持同锚——若只 HERE 随目录漂移而看门狗锚 config 旁，**flag 两侧不同锚＝补岗唤醒断链**，此为 B/A-1 的同锚性依据）。账本写侧探测 `ledger_recent()`（:175-199）按 config `out_dir` 现读，fallback `out = HERE`（:182/184）→ A-1 后仍＝根，语义不变。

**D. collector_proxy.py 静态件与跨目录 import**：
- `sys.path.insert(0, <脚本目录>)`（:71）→ 同目录可寻 `paths.py`（:76 `from paths import expand_path`）；**`monitor_ext` 现也靠 :71 同目录 import（:72-75）**——迁后分属 gateway/ 与 monitor/，须补 monitor/ 到 sys.path（S-5）。
- benchmark-registry 读取两坐标（:446-447、:453-455）＝`os.path.dirname(os.path.abspath(__file__)) + "benchmark-registry.json"`＝现锚仓根 → 须改锚包根＋`data-defs/`（S-5）。
- 报表调度线程（:1118-1126）`scripts_dir = <脚本目录>` 插 sys.path 后 `import daily_report`——迁后 daily_report 在 reporting/，须改插 reporting/（S-5）。
- `api-price-table.csv`：全仓 grep 实读＝**运行代码零读**；仅 html_report.py:311/:314/:337 注释/前端文案引用文件名（无路径）→ 随动＝注释文案补目录（S-7），csv 内容零动。
- **monitor 静态件路由挂法结论（前端引用是否随动的判据）**：`monitor_ext.answer()`（monitor_ext.py:596-615）＝**按 URL 文件名硬路由**（`/monitor`→monitor.html、`/monitor.js`、`/monitor.css`、`/monitor-sprite.svg`、`/ext.json`、`/ext.js` 逐名匹配），文件读取＝`_read_asset`（:588-593 `HERE / name`，HERE=monitor_ext 所在目录=monitor/，**前后端同区同目录随迁，读取链自洽**）。`monitor.html` 引用面（实读 :13/:21/:109）＝**绝对 URL 路径**（`/monitor.css`、`/monitor-sprite.svg#i-moon`、`/monitor.js`），不含目录段。**结论：路由按文件名、前端按绝对 URL——前端引用零随动，monitor.html/js/css/svg/ext.js 内容一行不动**。

**E. reporting 互 import（纠母票措辞）**：读码＝**daily_report 与 html_report 互不 import**（html_report 零引用 daily_report，反向亦然；daily_report 只出 .md :255-265，html_report 独立出 usage-report.html :428）。真实随动链＝两件套各自对 `paths.py` 的**同目录假设**：daily_report.py:19 `sys.path.insert(0, <脚本目录>)`＋:23 `from paths import load_config`；html_report.py:25 同法——迁 reporting/ 后 paths.py 不在同目录＝**必改**（补 gateway/ 到 sys.path，S-7）。另＋collector_proxy 调度线程 import daily_report 一条（D 已登记）。

**F. 启动器族（实读现值）**：
- `start.bat`（**GBK+CRLF 字节面实核**：iconv 可解＝GBK、CRLF、含非 ASCII）：`cd /d "%~dp0"`＋`python bootstrap.py --init/--check`（留根，零改）＋**:7 `start "Token ledger watchdog" /min python ledger_watchdog.py`＝须随动 `gateway\ledger_watchdog.py`（纠母票预设：start.bat 并非零改件）**。
- `start.sh`（UTF-8/LF）：**:13 `exec "$PY" ledger_watchdog.py`＝随动 `gateway/ledger_watchdog.py`**（:11-12 bootstrap 两行留根零改）。
- `start-proxy.bat`（GBK 家族·纯 ASCII 字节＋CRLF）：**:11 `"%PY%" collector_proxy.py --config "%~dp0config.json"`＝随动 `gateway\collector_proxy.py`**；此件＝`proxy_launch` 脚本化补岗的人机同入口（看门狗 :376-403 读 config 的 proxy_launch 调它），在岗 config 现无 proxy_launch 键（直发默认），改法为部署面换载时的同构项（H-1 素材）。
- `watchdog-console.bat`（GBK+CRLF，含非 ASCII）：cd/拉起全为**硬编码绝对路径** `C:\Work\LLM\token-ledger-proxy` 两处＋`...\watchdog-launcher.py`＝本仓无该路径（他机样例形态），随动＝两处在 GBK 字节面替换为 `...\token-ledger-proxy\gateway`（S-9 字节纪律）。
- `watchdog-launcher.py`（**UTF-8+BOM+CRLF** 实核）：:22-24 硬编码 `ROOT = r"C:\Work\LLM\token-ledger-proxy"`、`WD = os.path.join(ROOT, "ledger_watchdog.py")`＝ROOT 保持指包根、**WD 随动 `"gateway", "ledger_watchdog.py"`**；:57 `os.chdir(ROOT)` 语义不变（A-1 下 ROOT＝包根仍对）。该件迁入 gateway/（母票树），但其路径为绝对常量、与自身位置无关。
- `service-examples/Token ledger watchdog.vbs`（ASCII+CRLF）：注释 :4-5「留在包目录 next to ledger_watchdog.py」随动改措辞＋launch 行 `here & "ledger_watchdog.py"`（:31）→ `here & "gateway\ledger_watchdog.py"`（VBS 以自身所在目录解析 `here`，样例随包目录不变、只改子路径）。
- `com.token.ledger.plist` :12/:16 与 `token-ledger.service` :11/:13：`/opt/token-ledger-proxy/ledger_watchdog.py`＋WorkingDirectory → 补 `gateway/` 段（日志/data 路径不动）。
- 启动夹实装 VBS（票头已读）：`pkg & "\ledger_watchdog.py"` → `pkg & "\gateway\ledger_watchdog.py"`＝**人工闸②面，只出改法（H-2）**。仓内 `legacy/startup_bat_backup_20261123/` 两件均 `.disabled/.fromStartup` 后缀＝已退役备份，不入任何启动链。

**G. 六套 selftest 定位面（逐套实读结论：每套都只需改定位行，断言零动）**：
1. `selftest_proxy.py`：:33 HERE=tests→仓根（保持）；**:34 `PROXY_SCRIPT = <根>/collector_proxy.py` → `gateway/`**（:529/:782 spawn 用它）。其余全落 tmp 沙箱。**改 1 行**。
2. `selftest_watchdog.py`：:22 ROOT=仓根（保持）；**:23 `WD_SCRIPT = <根>/ledger_watchdog.py` → `gateway/`**（:91 importlib 加载＋:162 集成 spawn＝母票§四-4"新 `__file__` 深度重跑"所指即此）。**改 1 行**。
3. `selftest_monitor.py`：:45 HERE=仓根（保持）；**:209 `spec_from_file_location(..., <根>/monitor_ext.py)` → `monitor/`**；**:465-468 四处字节读 `<根>/monitor_ext.py` → `monitor/`**；**:513/:696 两处 node 跑 `<根>/monitor.js` → `monitor/`**。**改 6 行**。
4. `selftest_daily_report.py`：:23 HERE=仓根；**:24 `sys.path.insert(0, HERE)` → 补 `gateway`（paths.py 新家；daily_report 自身经 :31 `import daily_report` 由其自举 S-7 兜住）**。**改 1 行**。
5. `selftest_registry.py`：:28 HERE=仓根（保持）；**:29 `REGISTRY = <根>/benchmark-registry.json` → `data-defs/`**；:161-162 `sys.path.insert(0, HERE)`＋`import collector_proxy`——collector_proxy 迁入 gateway/ 后此 import 依赖 S-5 自举（collector_proxy 自带 :71 脚本目录插路径）→ 本行可保持 HERE 不改亦可，**票面裁：保持 :161 不动，import 经 S-5 自举成立**（读码：import 机制经 spec 定位的模块自带路径引导，先例＝②-0 D）。**改 1 行**。
6. `selftest_gateway_status.py`：:24 ROOT=仓根；:25 `sys.path.insert(0, ROOT)`＋:27 `import collector_proxy as cp` → **:25 改插 `ROOT/gateway`**（:31 SCRATCH 锚 ROOT/.scratch 不动——与 dev-discipline §8 已一致）。**改 1 行**。

**H. 文档/模板引用面（实读）**：README.md 命令行引用十处（:29/:30/:65/:97/:108/:113/:120/:131/:138/:163-165/:180/:185-186/:216/:240/:248-254）中随目录者＝`python ledger_watchdog.py`（:108）、`python collector_proxy.py --fp`（:131/:138）、`python daily_report.py` / `python html_report.py`（:163-165/:185-186/:252-253）＋:113 叙述句；INSTALL.md :36-38/:49/:58/:61/:73-75/:85/:90-93/:97 同类。`config.template.json:25` comment 两处措辞（`python collector_proxy.py --fp`、"collector_script 留空即使用本包内的 collector_proxy.py"）。部署面 config.json 的 comment 同款措辞——**运行时件，不改**（健康账 3）。

### ②-1 声明闭集（本票唯一可写仓内面）

**git mv 映射表（恰 19 条，逐行旧→新；全部 `git mv` 一步落位，rename 检测自动跟）**：

| # | 旧路径 | 新路径 | 方式 |
|---|---|---|---|
| 1 | paths.py | gateway/paths.py | git mv |
| 2 | collector_proxy.py | gateway/collector_proxy.py | git mv |
| 3 | ledger_watchdog.py | gateway/ledger_watchdog.py | git mv |
| 4 | switch_proxy.py | gateway/switch_proxy.py | git mv |
| 5 | watchdog-launcher.py | gateway/watchdog-launcher.py | git mv |
| 6 | watchdog-console.bat | gateway/watchdog-console.bat | git mv |
| 7 | monitor_ext.py | monitor/monitor_ext.py | git mv |
| 8 | ext.js | monitor/ext.js | git mv |
| 9 | monitor.js | monitor/monitor.js | git mv |
| 10 | monitor.html | monitor/monitor.html | git mv |
| 11 | monitor.css | monitor/monitor.css | git mv |
| 12 | monitor-sprite.svg | monitor/monitor-sprite.svg | git mv |
| 13 | html_report.py | reporting/html_report.py | git mv |
| 14 | daily_report.py | reporting/daily_report.py | git mv |
| 15 | api-price-table.csv | data-defs/api-price-table.csv | git mv（内容零动） |
| 16 | benchmark-registry.json | data-defs/benchmark-registry.json | git mv（内容零动） |
| 17 | legacy/README.md | docs/README.md | git mv |
| 18 | （新建） | docs/STRUCTURE.md | 新建（S-12） |
| 19 | （新建） | .workbuddy/swb-anchor | 新建（gitignore 域，S-13） |

**引用随动文件（闭集内，只改 S-x 声明行）**：`gateway/` 五件 py＋gateway/watchdog-console.bat、`monitor/monitor_ext.py`（仅 :43 一行注释性锚不动、实际零改——**如零改则整文件不入随动面**，见 S-6 裁定）、`reporting/` 两件、`bootstrap.py`、`start.bat`、`start.sh`、`start-proxy.bat`、`service-examples/Token ledger watchdog.vbs`、`service-examples/com.token.ledger.plist`、`service-examples/token-ledger.service`、`README.md`、`INSTALL.md`、`config.template.json`（仅 comment 串）、`tests/selftest_*.py` 六件（仅定位行）、`CHANGELOG.md`、`MANIFEST.md`、`.collab/tickets/OPS-1123-ROOTLAYOUT-T1.md`（本票本体，登记面）。

**其余全部不入闭集零触碰**（含 `config.json`、`benchmark-registry.json`/`api-price-table.csv` 内容、`legacy/**`（迁 README 外）、`monitor.js/html/css/svg/ext.js` 内容、`docs/*.png`（原位不动）、`data/**`、`logs/**`、`.scratch/**`、`.collab/tickets/OPS-1123-ROOTLAYOUT.md`（母件）、`D:\Strata-toolkit\**`、启动夹）。

### ②-2 禁动面

- 两域 `config.json`（母本仓根运行时件即便由 bootstrap --init 临时生成，验收后必须清除并如实登记，见 ③-5）、`config.template.json` 除 comment 串外零键改、`benchmark-registry.json` 与 `api-price-table.csv` **内容**（仅换目录）。
- 任何功能逻辑：Gate 类、handler、看门狗循环、认岗算法、报表算法、断言语义——③-10 白名单 grep 机检。
- `GATEWAY_VERSION`（rev17k）零 bump；前端五件（monitor.html/js/css/svg/ext.js）零字节改（③-9）。
- 在岗 8080/8787 与引擎面零接触；启动夹 VBS 实装件、`D:\Strata-toolkit\**` 全部零触碰（＝H-1/H-2 人工闸②面）。
- 部署面根级 `selftest_*.py` 四份、`run-ledger-watchdog.bat`、日志/flag＝运行时件，本票任何 S-x 不触（H-1 素材）。

### ②-3 逐条施工规格（落位到文件:行＋目标代码片段）

> 施工顺序＝**先 S-1 全部 `git mv`，后 S-2～S-14 随动改，最后 ③ 全量验收**（中间态自测必红属预期，验收只在 S-14 后判定）。全程禁仓外临时路径；临时工作物只落 `.scratch/OPS-1123-ROOTLAYOUT-T1/`。

**S-1 迁移命令序列（19 步中的 17 条 git mv）**：
```bash
mkdir gateway monitor reporting data-defs
git mv paths.py collector_proxy.py ledger_watchdog.py switch_proxy.py watchdog-launcher.py watchdog-console.bat gateway/
git mv monitor_ext.py ext.js monitor.js monitor.html monitor.css monitor-sprite.svg monitor/
git mv html_report.py daily_report.py reporting/
git mv api-price-table.csv benchmark-registry.json data-defs/
git mv legacy/README.md docs/README.md
```

**S-2 `gateway/paths.py` :20**：`PKG_DIR = os.path.dirname(os.path.abspath(__file__))` → `PKG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`；:8 docstring `@pkg -> <directory containing this package>` 补注 `(= parent of the package's gateway/ dir)`。——`@pkg`/兜底基语义保持＝包根。

**S-3 `gateway/ledger_watchdog.py`（HERE 锚性＝A-1）**：:80-86 段
```python
HERE = os.path.dirname(os.path.abspath(__file__))          # gateway/
PKG_ROOT = os.path.dirname(HERE)                            # 包根＝config/logs/flag 锚
sys.path.insert(0, HERE)              # find paths.py (同目录 gateway/)
CONFIG_PATH = os.path.join(PKG_ROOT, "config.json")
LOG_DIR = os.path.join(PKG_ROOT, "logs")
LOG_PATH = os.path.join(LOG_DIR, "ledger-watchdog.log")
os.makedirs(LOG_DIR, exist_ok=True)
```
其余 HERE 用法（:137 默认 collector 同目录、:417/:623/:651 launch cwd）**逐字不动**——cwd 落 gateway/ 属新实态；部署 engine_launch.cwd/guard cmd 全绝对（票头实读）不受影响。:82 注释补"paths.py lives in this dir"。

**S-4 `gateway/switch_proxy.py`**：:44-47 段同 A-1 形制：
```python
HERE = os.path.dirname(os.path.abspath(__file__))          # gateway/
PKG_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)              # paths.py 同目录
CONFIG_PATH = os.path.join(PKG_ROOT, "config.json")
WAKE_FLAG = os.path.join(PKG_ROOT, "relaunch-now.flag")
```
:182/:184 fallback `out = HERE` → `out = PKG_ROOT`（保持"config 旁"语义＝迁移前实态）。认岗面（:202-214/:362-364）零字动。

**S-5 `gateway/collector_proxy.py`（三处）**：
1. :71 后插两行（跨包 import 引导）：
```python
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))   # gateway/
_PKG_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _SCRIPT_DIR)                             # 原 :71 语义保持
sys.path.insert(0, os.path.join(_PKG_ROOT, "monitor"))      # monitor_ext 新家（:73 import 随动）
sys.path.insert(0, os.path.join(_PKG_ROOT, "reporting"))    # daily_report 新家（调度线程 import 随动）
```
2. 注册表两坐标 :446-447、:453-455：`os.path.dirname(os.path.abspath(__file__)), "benchmark-registry.json"` → `_PKG_ROOT, "data-defs", "benchmark-registry.json"`（两处同法；`looked_at` 字段值随之为新路径——对外读数变化如实登记④）。
3. 调度线程 :1118-1120：`scripts_dir = os.path.dirname(os.path.abspath(__file__))` → `scripts_dir = os.path.join(_PKG_ROOT, "reporting")`（:1126 `import daily_report` 行不动；:1126 行尾注释 "lives next to this file" 改 "lives in reporting/"）。
GATEWAY_VERSION :84 **零动**。

**S-6 `monitor/monitor_ext.py`**：**零改**（读码 D：`HERE = Path(__file__).resolve().parent` :43＝前后端同区随迁自洽；路由按文件名 :596-615；csv 运行零读）。声明"改 0 行"即为规格。

**S-7 reporting 两件**：
- `reporting/daily_report.py` :19：`sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # find paths.py however this module is loaded` →
```python
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gateway"))  # find paths.py (gateway/) however this module is loaded
```
（:23 `from paths import load_config` 行不动；读写面全走 config `out_dir`，其余零改。）
- `reporting/html_report.py` :25：同法替换为插 `gateway/`；:311/:314/:337 三处注释/前端文案中 `api-price-table.csv` → `data-defs/api-price-table.csv`（纯注释字符串随动，计算器逻辑零动——csv 内容本身零动）。
- 读码 E 实证两件套互不 import，"互 import"随动项＝不存在，如实收空。

**S-8 仓根启动三件**：
- `start.bat`（**GBK 字节纪律见 S-9 同条**；CRLF 保持）：第 7 行 `start "Token ledger watchdog" /min python ledger_watchdog.py` → `start "Token ledger watchdog" /min python gateway\ledger_watchdog.py`。余行零动（`cd /d "%~dp0"`＋bootstrap 两行留根）。
- `start.sh`（UTF-8/LF）：:13 `exec "$PY" ledger_watchdog.py` → `exec "$PY" gateway/ledger_watchdog.py`。
- `start-proxy.bat`（ASCII 字节＋CRLF）：:11 `"%PY%" collector_proxy.py --config "%~dp0config.json"` → `"%PY%" gateway\collector_proxy.py --config "%~dp0config.json"`（config 仍锚 bat 所在目录＝部署根，A-1 同锚）。

**S-9 GBK/字节面件改法纪律（重申并钉死）**：`start.bat`、`start-proxy.bat`、`watchdog-console.bat`、`service-examples/Token ledger watchdog.vbs` 四件——**改动必须按原字节编码写回**：先 `iconv -f GBK -t UTF-8` 解码、改目标行、`iconv -f UTF-8 -t GBK` 编码回写、CRLF 行尾保持（`file`/cmp 判据见 ③-11）；禁止以 UTF-8 直接写回（chcp 936 窗口即乱码）。`watchdog-launcher.py`＝UTF-8+BOM+CRLF：编辑保 BOM 保 CRLF，只动 :24 一行：`WD = os.path.join(ROOT, "ledger_watchdog.py")` → `WD = os.path.join(ROOT, "gateway", "ledger_watchdog.py")`（:22 `ROOT` 常量值不动——它是部署机绝对路径，指包根语义仍对；健康账 7 登记其绝对路径实态）。`watchdog-console.bat`：两处 `cd /d C:\Work\LLM\token-ledger-proxy`（:5）与末行 launcher 绝对路径 `"C:\Work\LLM\token-ledger-proxy\watchdog-launcher.py"`（:13）→ 均补 `\gateway` 段（GBK 字节面替换）。

**S-10 `service-examples/` 三件＋启动夹方案（只出改法）**：
- `Token ledger watchdog.vbs`：注释 :4-5 "Leave it in the package directory next to ledger_watchdog.py" → "Leave it in the package directory (the watchdog now lives in the gateway/ subdirectory)"；:31 `launchLine = q & py & q & " " & q & here & "ledger_watchdog.py" & q & " --lock-wait 86400"` → `... & here & "gateway\ledger_watchdog.py" & ...`（`here` 仍＝VBS 所在包根，CurrentDirectory 保持根＝与 A-1 锚性一致）。
- `com.token.ledger.plist`：:12 `<string>/opt/token-ledger-proxy/ledger_watchdog.py</string>` → `.../gateway/ledger_watchdog.py`（WorkingDirectory :16、日志 :19-20 不动＝锚包根）。
- `token-ledger.service`：:13 `ExecStart=/usr/bin/python3 /opt/token-ledger-proxy/ledger_watchdog.py` → 补 `/gateway/`（WorkingDirectory :10、日志不动）。
- 启动夹实装 VBS（仓外·人工闸②）改法登记于 H-2，本票不执行。

**S-11 文档与模板 comment 随动**：
- `README.md`：:108 表内 `python ledger_watchdog.py` → `python gateway/ledger_watchdog.py`；:113 叙述句 `python collector_proxy.py` → `python gateway/collector_proxy.py`；:131/:138 `python collector_proxy.py --fp` → `python gateway/collector_proxy.py --fp`；:163-165/:185-186/:252-253 `python daily_report.py` / `python html_report.py` → 补 `reporting/` 前缀；:185 报表两条独立命令句同步。`--config config.json` 相对锚不变。
- `INSTALL.md`：:49 `python collector_proxy.py --fp`、:73-75 启动叙述、:90-93 运维表同类补前缀；:36-38 bootstrap 三行不动（bootstrap 留根）。
- `config.template.json` :25 comment 串两处：`python collector_proxy.py --fp` → `python gateway/collector_proxy.py --fp`；"collector_script 留空即使用本包内的 collector_proxy.py" → "…本包 gateway/ 内的 collector_proxy.py"。JSON 其余键零动（母票§二-5 所指注释随动即此）。
- 部署面 config.json comment 同款措辞漂移＝运行时件不改（健康账 3，人工闸②换载时随 config 准入面另裁）。

**S-12 `docs/STRUCTURE.md` 成稿（六目规范）**：新建，六目齐备——①四区枚举完备：规范域 `docs/`、治理域 `.collab/`、运行时 ignore 域 `data/`＋`logs/`＋根级 `config.json`/`relaunch-now.flag`/`*.log`（.gitignore 在册实证）、人类域 `sources/` **按本仓实态＝不建**（本仓无外部投料流；候裁 H-4）；②delivery_paths 清单＝白名单八件＋五区目录逐一；③锚定行 `project_root: "."` 与 `.workbuddy/swb-anchor` 对等；④**仓根白名单条款**：仓根文件恰＝`README.md INSTALL.md CHANGELOG.md MANIFEST.md start.bat start.sh bootstrap.py .gitignore` 八件（`config.json` 等 gitignore 域运行时件除外），**第 9 个受版本管理的仓根文件长出＝机检判红**（命令＝③-1）；⑤目录语义表（照录母票§一表格）；⑥变更纪律：新目录/新仓根件必经架构席票面声明（本票先例引用）。

**S-13 `.workbuddy/swb-anchor`**：新建（`.workbuddy/` 在 .gitignore 域＝本机锚件，不入 git diff 面）：首行 `project_root: .`＋`structure: docs/STRUCTURE.md`＋锚定日。

**S-14 CHANGELOG/MANIFEST 登记**：`CHANGELOG.md` 倒序置顶新节（样张 `## (2026-11-2x) · OPS-1123-ROOTLAYOUT-T1 仓根分层迁移`）＝一句话：仓根收敛白名单八件、代码下沉 gateway/monitor/reporting/data-defs、引用链随动、docs/STRUCTURE.md 建档——**注明 GATEWAY_VERSION 零 bump（无功能变更）＋六套套数不变**。`MANIFEST.md` 改动登记节加同拍＝19 行映射表照录＋随动文件行数清单。

### ③ 验收标准（全机械可判）

> 母本仓根跑，diff 基线＝开工 `git rev-parse HEAD`（开工若因放行落链前移，以开工实拍为基线并在回执声明，沿 GWSTATUS 先例）。验收全程禁 git 写操作（只读；`git mv` 属施工动作已在 S-1 完成，不重复执行）。在岗 8080/8787 不入判据（④）。

1. **仓根白名单恰集**：`git ls-files | grep -v / | grep -v '^config.template.json$' | sort` 期望读数＝**恰八行** `CHANGELOG.md INSTALL.md MANIFEST.md README.md bootstrap.py start.bat start.sh .gitignore` 的排序集（`.gitignore` 计入八件白名单＝母票§一恰集；`config.template.json`＝模板运行时件，按母票表"config-examples 保留现位"同理留根入 git——**若放行裁模板也须入白名单恰集，则 S-15 候裁 H-5 补一条 `git mv config.template.json config-examples/…` 或改白名单九件，票面按八件＋模板例外写死**）。辅判盘面：`ls -1A -p | grep -v '/$' | grep -v '^config.json$\|^relaunch-now.flag$'`＝白名单八件＋config.template.json＋gitignore 域运行时件（data/logs 目录），不得长出其他文件。
2. **六套全绿（套数不变＝断言语义零改的机检）**：`python tests/selftest_proxy.py` 末行 **46/46 PASS** exit 0；`python tests/selftest_watchdog.py` 末行 **RESULT: 31 passed, 0 failed** exit 0；`python tests/selftest_monitor.py` **57/57 PASS** exit 0；`python tests/selftest_daily_report.py` **15/15 PASS** exit 0；`python tests/selftest_registry.py` **6/6 PASS** exit 0；`python tests/selftest_gateway_status.py` **18/18 PASS** exit 0。任何套数增减＝改断言＝判红。
3. **bootstrap 三绿**：throwaway config 下（见 5）`python bootstrap.py --check` 输出含 **`必需文件齐全（16 个）`** 且退出码 **0**（REQUIRED 清单经 S-16 bootstrap 随动后按新路径核对——见下 S-16 补充行）；`python bootstrap.py --selftest` 输出 **`三套回归全部通过`** exit 0。
   - **S-16 补充（bootstrap.py REQUIRED 面随动，闭集内）**：bootstrap.py :25-26 HERE/sys.path（bootstrap 留根＝包根，:26 找 paths.py **已不可同目录寻**）→ :26 后补 `sys.path.insert(0, os.path.join(HERE, "gateway"))`；:30-36 `REQUIRED` 元组按新落位改前缀：`"gateway/collector_proxy.py", "monitor/monitor_ext.py", "monitor/monitor.html", "monitor/monitor.js", "monitor/monitor.css", "monitor/monitor-sprite.svg", "monitor/ext.js", "reporting/daily_report.py", "reporting/html_report.py", "gateway/ledger_watchdog.py", "gateway/switch_proxy.py", "tests/selftest_proxy.py", "tests/selftest_watchdog.py", "tests/selftest_monitor.py", "tests/selftest_daily_report.py", "gateway/paths.py"`（原 tuple 实点 **16 项**照改前缀，**项数不变 16**；:87 拼合逻辑 `os.path.join(HERE, f)` 支持相对子路径，零改）；:206-209 `--selftest` 三套路径 → `"tests/selftest_*.py"` 前缀补 `tests/`（现值＝`os.path.join(HERE, name)` name 无 tests/ 前缀——读码 :206＝**bootstrap 现假定 selftest 与 bootstrap 同目录**；现仓根无 selftest 文件（盘面实读），推断 bootstrap --selftest 现即 FAIL（本席未实跑 --selftest，此为读码推断）——健康账 7 如实登记；S-16 修为 `tests/` 前缀＝**行为修复非语义变更**，若放行认为越界则候裁 H-6）。
4. **throwaway 真服务三面 curl**（施工席在 throwaway 端口起活，`--config` 指 throwaway config，`listen 127.0.0.1:18080`／`upstream` 指 bind(0) 即放的上游或任一假端口）：起 `python gateway/collector_proxy.py --config .scratch/OPS-1123-ROOTLAYOUT-T1/cfg.json` 后——`curl --noproxy '*' -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18080/health`＝**200**；`.../gateway/status`＝**200** 且 JSON `.schema=="unified-status/v0"`；`.../capabilities`＝**200** 且 `gateway.version=="rev17k"`；`curl ... /monitor`＝**200** 且 body 含 `monitor.css`（前端面在新深度经 monitor_ext 自读仍活）。测毕杀进程、清零 `.scratch/OPS-1123-ROOTLAYOUT-T1/`。
5. **看门狗集成在新深度重跑绿**：③-2 的 selftest_watchdog 即集成面（:91 importlib 新深度加载＋:162 起真看门狗进程 spawn WD_SCRIPT 新路径）；另跑 `python gateway/ledger_watchdog.py --config <throwaway cfg> --port <free> --lock-port 43999 --log .scratch/…/wd.log --cycles 2` exit 0 且日志含 `watchdog started` 与 `relaunch-now.flag` 路径＝**throwaway cfg 所在目录**（flag 锚 config 旁实证）＋`ls <根>/logs/` 出 `ledger-watchdog.log`（日志锚根实证）＋import 期 makedirs 副作用不再在 `gateway/logs/` 长出目录（`git status` 无 `gateway/logs` 辅判）。bootstrap --check 三绿所需 throwaway config 于测后删除：`git status --porcelain | grep config.json`＝**空**。
6. **rename 全覆盖**：`git diff --find-renames --name-status <基线> | grep '^R' | wc -l` ＝ **17**（映射表 1-17 行全为 rename）；`git diff --find-renames --name-status <基线> | grep -c '^A'`＝**2**（STRUCTURE.md＋票本体；swb-anchor 在 gitignore 域不入 diff）；`grep '^D'`＝**0**。
7. **越领地核验**：`git diff --name-only <基线> | grep -vE '^(gateway/|monitor/|reporting/|data-defs/|docs/|README\.md|INSTALL\.md|CHANGELOG\.md|MANIFEST\.md|bootstrap\.py|start\.bat|start\.sh|start-proxy\.bat|config\.template\.json|service-examples/|tests/selftest_|\.collab/tickets/OPS-1123-ROOTLAYOUT-T1\.md|legacy/README\.md)' | wc -l` ＝ **0**。
8. **功能语义零变更（collector_proxy diff 白名单）**：`git diff <基线> -M -- gateway/collector_proxy.py | grep -E '^[-+][^-+]' | grep -vE 'sys\.path|_SCRIPT_DIR|_PKG_ROOT|benchmark-registry|data-defs|scripts_dir|lives (in|next)|import 引导注释|monitor_ext 新家|daily_report 新家' | wc -l` ＝ **0**（diff 变更行全部落路径常量/引导行白名单）；辅判 `git diff <基线> -M | grep -c 'GATEWAY_VERSION'` ＝ **0**。
9. **前端五件零字节**：`git diff <基线> -M -- monitor/monitor.html monitor/monitor.js monitor/monitor.css monitor/monitor-sprite.svg monitor/ext.js data-defs/benchmark-registry.json data-defs/api-price-table.csv | wc -l` ＝ **0**（rename 后内容零 diff＝数据/前端逐字节不动）。
10. **config 两域零触碰**：`git diff --name-only <基线> | grep -c config.json` ＝ **0**；`config.template.json` 仅 comment 行：`git diff <基线> -- config.template.json | grep -E '^[-+]' | grep -vE 'comment|^\+\+\+|^---' | wc -l` ＝ **0**。
11. **GBK 件字节纪律**：`iconv -f GBK -t UTF-8 start.bat >/dev/null && iconv -f GBK -t UTF-8 gateway/watchdog-console.bat >/dev/null && iconv -f GBK -t UTF-8 start-proxy.bat >/dev/null && echo GBK-OK`＝**GBK-OK**（改后仍 GBK 可解）；`python -c "d=open('gateway/watchdog-launcher.py','rb').read(); assert d[:3]==b'\xef\xbb\xbf' and b'\r\n' in d; print('BOM-CRLF-OK')"`＝**BOM-CRLF-OK**；四 bat/vbs `grep -c $'\r' <file>` 全 >0（CRLF 保持）。
12. **STRUCTURE 面在册**：`head -1 .workbuddy/swb-anchor`＝**`project_root: .`**；`grep -c '仓根白名单' docs/STRUCTURE.md` ≥**1**；`grep -c 'project_root' docs/STRUCTURE.md` ≥**1**。

### ④ 边界约束

- **票间关系**：本票＝ROOTLAYOUT 母票§二/§三/§四-1~4 唯一施工载体；母票§四-5（部署面同构＋换载）＝人工闸②不入本票（H-1/H-2）；母票§四-6（`.scratch/` 清理）＝收口链另拍不入本票判据；与 rev17k 候静换载自动化互不混拍（时序§五：rev17k 已在基线，本票以其后在岗态为基线——开工 ANCHOR 若含 rev17k 后续落链，按③基线声明条款处理）。
- **`looked_at` 对外读数变化如实登记**：/capabilities `registry.looked_at` 字段值从 `<根>/benchmark-registry.json` 变为 `<根>/data-defs/benchmark-registry.json`（:453-455 路径常量随动之必然；消费侧 NAS 面按文件存在性消费则无感——健康账 5）。
- **cwd 语义变化如实登记**：看门狗补岗子进程 cwd 从仓根变 `gateway/`（launch_ledger :623 `cwd=HERE`）——collector_proxy 内所有路径均为绝对解析（config 现读＋`expand_path`），无相对路径依赖（读码 D 实证运行零相对读）；engine_launch/guard_services 的 cmd/cwd 由 config 申报绝对路径（部署面实读佐证），不受代码深度影响。
- **在岗服务零接触**：全部验收在 throwaway 端口/import 桩；在岗 8080/8787 换新布局＝部署面换载链（H-1），生效需在岗重启走 `switch_proxy.py` 纪律＝人工闸②时序面。
- **`git mv` 即写操作但属施工**：起草与本验收全程禁 git 写；施工席执行 S-1 时 `git mv` 为票内许可动作，提交落位由主理人程序定（本票不规定 commit 形态）。
- **施工面纪律**：临时工作物只落 `.scratch/OPS-1123-ROOTLAYOUT-T1/`，完工前清零；单一工程师席新鲜实例、同席禁多实例。
- **交付与回执**：完工回执＝开端 HEAD＋写入清单（字节数＋sha256 前→后逐件）＋③十二条读数原文＋`.scratch/` 自查。票放行＝主理人程序确认；A-x 随票生效；H-1～H-6 随放行件裁定，裁定不同则修票替换对应 S/③行。

## 租约段（票内·经架构签注由 B2 lease-issuer 实例化）

- path_globs：`gateway/**`、`monitor/**`、`reporting/**`、`data-defs/**`、`docs/**`、`legacy/README.md`、`bootstrap.py`、`start.bat`、`start.sh`、`start-proxy.bat`、`config.template.json`、`service-examples/**`、`README.md`、`INSTALL.md`、`CHANGELOG.md`、`MANIFEST.md`、`tests/selftest_*.py`、`.workbuddy/swb-anchor`、`.collab/tickets/OPS-1123-ROOTLAYOUT-T1.md`、`.scratch/OPS-1123-ROOTLAYOUT-T1/**`
- deny_globs：`config.json`、`benchmark-registry.json`（内容）、`api-price-table.csv`（内容）、`monitor/monitor.html`、`monitor/monitor.js`、`monitor/monitor.css`、`monitor/monitor-sprite.svg`、`monitor/ext.js`（rename 后内容禁改）、`monitor/monitor_ext.py`（rename 后内容禁改——S-6 裁零改）、`legacy/**`（除 legacy/README.md 迁移）、`docs/*.png`、`data/**`、`logs/**`、`.scratch/**`（T1 区外）、`.collab/tickets/OPS-1123-ROOTLAYOUT.md`、`.collab/tickets/OPS-1123-GWSTATUS.md`、`.collab/drafts/**`、`D:\Strata-toolkit\**`、`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\**`
- 灰度判据（票内声明字段·decision-pack 读取）：③-2 六套全绿（46/31/57/15/6/18 套数不变）＋③-3 bootstrap --check/--selftest 绿＋③-4 throwaway 三面 curl 200——测试环境判据，不依赖换脑、不依赖在岗 8080/8787、不依赖部署面。
- 席位 ID／票 ID／哈希：由状态机签发，非人工填写

## 票裁已决（A-x·起草席决；推翻走回流件）

- **A-1｜看门狗/切换器 HERE 改锚包根（PKG_ROOT＝parent）**：读码 B/C 实证 config/logs/flag 三锚现值均＝仓根（部署面根级 config.json、logs/、relaunch-now.flag 实证在场）；若 HERE 随文件沉到 gateway/，在岗部署不换 config 即三锚失联＝服务断链。HERE（脚本目录）保留用于 paths.py 同目录寻径与 launch cwd；新增 PKG_ROOT 承载锚性。启动器族（launcher ROOT、bat `%~dp0`、VBS `here`、service WorkingDirectory）全部维持"锚包根"同构，两侧同锚＝flag 唤醒链不断（读码 C 的同锚性判据）。
- **A-2｜paths.py 上溯一层修 PKG_DIR**：`@pkg` 是对用户承诺的便携语义（paths.py:8 docstring），必须继续指"包"而非包内子目录；文件域无 `@pkg` 在场引用（两域 config 实读零 @pkg），修复零风险。
- **A-3｜collector 同目录默认不改**：watchdog:137 `HERE/collector_proxy.py` 与 collector 同迁入 gateway/＝默认解析自动随迁，改它反而引入双源。
- **A-4｜前端引用零随动**：读码 D 结论＝路由按 URL 文件名硬路由（monitor_ext.py:602-613），前端引用为绝对 URL（monitor.html:13/:21/:109），代码深度变化不触及 URL 面；前端五件零字节（③-9 锁）。
- **A-5｜跨包 import 用 sys.path 插目录，不建包/不建 `__init__.py`**：仓内 import 先例全部是"脚本目录插 sys.path＋裸模块名"（collector:71、daily:19、html:25、watchdog:82、switch:45）；改包结构＝改 import 语句＝语义改动面扩大，违"纯迁移"负声明。
- **A-6｜bootstrap REQUIRED 补前缀＋selftest 路径修 tests/**：REQUIRED 是文件存在性核对面（:87 join），补前缀＝随迁必改；`--selftest` 现值无 `tests/` 前缀在现仓即 FAIL（健康账 9 实跑登记＝既存缺陷），S-16 顺手修复＝路径定位修复非断言语义变更；如放行判越界则按 H-6 剥离回原值。
- **A-7｜watchdog-launcher 绝对 ROOT 常量不改值、只补 gateway 段**：该件路径是他机绝对申报（C:\Work\LLM\...），本仓不持该机实态；改法保持"ROOT＝包根、WD＝ROOT+gateway+脚本"同构（A-1 族），绝对路径实态入健康账 7 备查——不在本票顺手改成相对（改相对＝行为变更）。
- **A-8｜docs/README.md（原 legacy/README.md）迁移入 docs/**：母票表列"docs/＝STRUCTURE.md＋既有截图"未列 legacy/README；读码实态＝legacy/README.md 是 legacy 族导读（登记 legacy 三件的来历），其语义属说明域非废弃件本体；迁 docs/ 使 legacy/ 只剩废弃件＋备份夹。**若放行裁 legacy/README.md 应留守 legacy/＝删 S-1 最后一行 git mv＋映射表 17 行即回滚（候裁 H-3）**。

## 候裁单列（H-x·决策者/主理人拍板，本席不裁）

- **H-1｜部署面同构迁移＋换载时序（人工闸②）**：`D:/Strata-toolkit/token-ledger-proxy/` 按同一映射表 git mv（部署面是 git 仓副本与否由主理人确认），换载＝停载→迁移→`switch_proxy.py` 换脑→看门狗热备接管；时机＝无会话安全窗。本票只出方案＋映射表＋start-proxy.bat/proxy_launch 同构项。
- **H-2｜启动夹实装 VBS 改法执行时点**：`pkg & "\gateway\ledger_watchdog.py"` 一行改法已出（②-0 F）；与 H-1 同窗执行（VBS 改早于部署面迁移＝下次登录起看门狗找不到脚本静默失败；改晚于＝中间窗仍指旧路径但旧件已迁＝同样失败——**必须与 H-1 同窗原子执行，此序为硬约束**）。
- **H-3｜legacy/README.md 归属终裁**：票面样张＝迁 docs/（A-8）。留守则 legacy/README.md 原位，映射表 17 撤。
- **H-4｜`sources/` 人类域是否建**：STRUCTURE 六目之一按实态裁＝本仓无外部投料流，票面建议**不建**（S-12 已按不建成稿）；若要建＝S-12 ①目补一行＋`.gitignore` 视情况补条目（另走本票修票）。
- **H-5｜config.template.json 仓根例外终裁**：白名单八件恰集下模板留根＝例外（③-1 按"八件＋模板例外"写死）。若裁零例外＝白名单改九件（模板入列）或模板迁 `config-examples/`（连锁：bootstrap :27 TEMPLATE 路径随动一行）。
- **H-6｜bootstrap --selftest tests/ 前缀修复是否随本票**：票面样张＝随（A-6）；剥离则 S-16 只改 REQUIRED，`--selftest` 既存 FAIL 另开修复票。
- **H-7｜legacy/ 内旧引用是否随动**：读码＝`legacy/scheduler.py`（:51-53 同目录 import daily_report——legacy 件现无人加载，退役件）、`legacy/comfy_watchdog.py`/`collector_log.py`（文档性提及，无路径加载链）、`legacy/startup_bat_backup_*`（退役备份）。票面建议＝**全部不动**（退役件随迁引用＝给死件续命的语义改动）；若要随动＝另票。

## 健康账登记（回流素材）

1. **代码内硬编码绝对路径实存三处**（任务点名如实登记）：`watchdog-launcher.py` :22-23（ROOT/PY 全绝对 `C:\Work\LLM\...`——且与本机实际部署域 `D:\Strata-toolkit\` 不一致＝该 launcher 系他机形态样例在本仓在册）；`watchdog-console.bat` :5/:13（同 `C:\Work\LLM\` 域两处）。本票按 A-7 只补 gateway 段不修绝对性（修绝对性＝行为变更另票）。
2. **部署面 config `strata_config`/`engine_launch` 全绝对路径**：迁移无关（A-3/④ 实证），换载 H-1 时零改可跑。
3. **部署面根级运行时件与仓根 gitignore 域同名族**（relaunch-now.flag/logs/日志/根级 selftest_*.py 四份/run-ledger-watchdog.bat）：换载时须逐一确认新深度不产生锚漂移（A-1 已锁代码侧；文件侧＝H-1 清单面）。部署面根级四份 selftest＝旧链遗留，随 H-1 处置。
4. **`watchdog-console.bat` 标题/echo 显示 `watchdog-launcher.py` 所在域暗示仓根**：迁移后 cd 到 gateway 的显示文案与 ③-11 字节纪律共存，无功能影响。
5. **`/capabilities.registry.looked_at` 对外读数随路径变**（④登记）：NAS 消费侧若对该字符串有等值断言需知会（主理人对接面）。
6. **母本仓根无 config.json**（bootstrap --check exit 2 实跑）＝母本为开发态母本仓实态；③-3/③-5 用 throwaway config 并测毕清除（③-5 末判据）。
7. **bootstrap `--selftest` 三套路径无 tests/ 前缀＝现仓即 FAIL**（既存缺陷，S-16/H-6/A-6）。
8. **`legacy/startup_bat_backup_20261123/` 两件均 .disabled/.fromStartup**＝启动夹历史处置备份（ROOTCLEAN-1123 前奏的落点），不在任何启动链，本票零触碰。

## 可施工性判定（架构席自评）

- 全部随动点实读在册：paths :20/:31/:35-37；watchdog :80-89/:117-137/:700；switch :44-47/:175-199/:202-214；collector :71-76/:446-455/:1118-1126/:84；monitor_ext :43/:588-615；monitor.html :13/:21/:109；daily :19/:23；html :25/:311-337；六套定位行逐套（②-0 G）；启动族逐件（②-0 F，GBK/CRLF/BOM 字节面 iconv/python 实核）；service 三件逐行；启动夹实装件只读；两域 config 只读对拍；六套基线当轮全实跑（46/31/57/15/6/18）。
- 判别力自评：③-1 对"仓根长出第 9 件"判红；③-2 对"借迁移改断言"判红（套数锁）；③-6/③-7 对"漏 mv／越领地／cp 代 mv（rename 计数缺）"判红；③-8 对"collector 顺手改功能行／bump 版本"判红；③-9 对"前端/数据件被改字节"判红；③-10 对"config 面被触"判红；③-11 对"GBK 件写成 UTF-8／BOM 丢失"判红；③-5 对"A-1 锚漂移（flag 落 gateway/logs 落 gateway）"判红。
- 未实跑面（留施工/QA）：throwaway 三面 curl 首跑；看门狗 `--cycles 2` 探针首跑；bootstrap 修复后 --selftest 首跑；③-8 grep 白名单对注释行的误报率（若命中，回执贴读数＋人工目检注记，判据不放宽）。
- **判定＝可施工**，无阻塞点；放行＝主理人程序确认＋H-1～H-7 随放行件裁定。本票 v1 起草不启施工，起草全程零 git 写、零仓外写（除本票文件与 .collab 治理域）。

—— 架构席 · OPS-1123-ROOTLAYOUT-T1 v1 · 开端 HEAD 实测 `98520fdc26447854e8c243a542448bdb177915b7` · 起草实核居本仓 .collab/ · 2026-11-23