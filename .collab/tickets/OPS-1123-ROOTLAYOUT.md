# OPS-1123-ROOTLAYOUT · 仓根分层治理＋STRUCTURE 建档（母票）

- 票型＝母票（治理登记面，主理人执笔）
- 开端 ANCHOR＝`6ad35aa`（登记时实跑；工作区净）
- 来源＝决策者裁定（2026-11-23 21:01 逐字要义：「我们应该刚刚经过按最佳实践的一轮治理，根目录应该只保留了几个系统入口级的脚本而已！」；21:03「那你就开票」；21:05「开始执行吧」）
- 前案关联＝远端卫生轮（83f041d 系）只治 `tests/`/`.collab/`/`legacy/` 三角落，根目录扁平代码堆未动＝本票动机；仓根运行时残留清理（ROOTCLEAN-1123，21:00 盘面已处置）＝本票前奏。

## 一、目标形态（仓根白名单制）

仓根最终只准出现「人类第一眼要碰的」＋「包身份」两类件，恰八件：

```
README.md  INSTALL.md  CHANGELOG.md  MANIFEST.md
start.bat  start.sh  bootstrap.py  .gitignore
```

其余按运行时角色分层：

| 新目录 | 迁入件 | 语义 |
|---|---|---|
| `gateway/` | collector_proxy.py · ledger_watchdog.py · switch_proxy.py · watchdog-launcher.py · watchdog-console.bat · paths.py | 服务主链（反代＋看护＋换载闸＋主控台） |
| `monitor/` | monitor_ext.py · ext.js · monitor.js · monitor.html · monitor.css · monitor-sprite.svg | 硬件监视面（前后端同区） |
| `reporting/` | html_report.py · daily_report.py | 报表面 |
| `data-defs/` | api-price-table.csv · benchmark-registry.json | 随包分发数据定义 |
| `docs/` | STRUCTURE.md（新建）＋既有截图 | 规范＋说明域 |
| 保留现位 | config-examples/ · service-examples/ · tests/ · legacy/ · .collab/ | 已治理区不动 |

## 二、路径链随动点（迁移硬内容，逐处读码核实，禁凭本票措辞）

1. 启动目录 VBS（仓内样例＋部署面＋启动夹实装件三处同构）：硬写 `<pkg>\ledger_watchdog.py` → `<pkg>\gateway\ledger_watchdog.py`。
2. `paths.py` 包根假设：代码下沉一层后 `parent` 语义全部重核。
3. 看门狗补岗／日志目录／wake flag／锁：flag 锚 config 旁、日志锚部署面——是否受代码目录深度影响须读码证实（不猜）。
4. `bootstrap.py` / `switch_proxy.py` 的 `HERE`/`sys.path` 语义＋进程命令行匹配串（`--check` 认岗形态随动）。
5. 在岗 `config.json`（部署面）可能含 `collector_script` 绝对路径；`config.template.json` 注释随动。

## 三、STRUCTURE 建档（dev-discipline §十 S1–S6 补票）

- S1 锚定＝`.workbuddy/swb-anchor`（首行 `project_root: .`）；
- S2 四区＝`docs/`（规范域）`.collab/`（治理域，已在）＋ignore 运行时域（`data/`+`logs/`）声明；`sources/` 人类域按本仓实态裁（候裁）；
- S5/S6＝架构席按六目规范成稿 `docs/STRUCTURE.md`：四区枚举完备／delivery_paths／`project_root: "."` 行／仓根白名单条款（第 9 个文件长出＝机检判红）。

## 四、验收要点（机检面，细则归迁移子票）

1. 仓根文件数＝白名单恰集（命令可判）；
2. 六套自测全绿（proxy 46 / watchdog 31 / monitor 57 / daily_report 15 / registry 6 / gateway_status 18）＋真服务轨在新布局起活（/health /gateway/status /capabilities）；
3. `bootstrap.py --check` 新布局三绿；
4. 看门狗集成断言在新 `__file__` 深度重跑全绿；
5. 部署面 `D:/Strata-toolkit/token-ledger-proxy/` 同构迁移＋换载＝**人工闸②（部署准入）**，集中于链尾呈决策者，不可自动跑；
6. `.scratch/` 遗留票区清理入收口判据（QA-LOADSWEEP-T1 区除外——候 T1 QA 回执补案取证，处置随登）。

## 五、时序与边界

- rev17k 候静换载自动化（7d5d9296）＝只换文件不改结构，先行；本票分层迁移以其后的在岗态为基线。两票不混拍。
- 本票不改任何功能语义：纯 `git mv`＋引用链随动＋文档登记；任何功能 diff＝越界。
- 子票＝OPS-1123-ROOTLAYOUT-T1（迁移映射＋逐条规格＋机检验收＋候裁），架构席起草。

## 六、状态

- 当前＝已立案；T1 派架构席起草中。
- 本单 append-only；处置随登不另起件。
