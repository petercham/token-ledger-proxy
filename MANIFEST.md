# 清单与来源登记

发行版本：`token-ledger-proxy` 2026-11-09（2026-11-21 起更名：仓名/包名 `strata-ledger-proxy`→`token-ledger-proxy`，见 2.27 节；本次修订 2026-11-22 · rev17：看门狗引擎看护（guard_engine 四键＋engine_launch＋grace；一快捷方式拉起全套；见 2.28 节）；rev16：双后端支持（Basalt `models[].parallel` 闸解析＋监视页 `/slots` 逐槽状态＋进度条速度表退路；见 2.26 节）；rev13：日报补排队闸拦截三指标（见 2.24 节）；rev12：排队闸拦截事件独立日志（`gate-events-YYYY-MM-DD.jsonl` 决策证据流：admitted/queued/released 三形态＋临界区在飞读数＋与记账账本严格分离；见 2.23 节）；rev11a：排队闸跟随形态回流（读数源＝`strata_config` 启动配置文件定死 `parallel` 值＋mtime 守卫缓存；rev11 运行时轮询系定向拆除）；rev11：排队闸跟随引擎实际并发（`gate_follow` 开关＋后台 `/v1/status` 读数缓存＋回退链——读源已被 rev11a 回流替换）；rev10a：排队闸 v3 维护小批（入队观测即时可见＋死字段注释＋票面勘误登记）；rev10：网关侧排队闸 v3（对话请求 FIFO 准入＋SSE 等待心跳）；另含 rev9 CPU 卡型号、rev8 后补的 `config-examples/` 样例、README 踩坑登记、真机截屏配图与省钱计算器口径＋价表随包；git 仓形态，无 ZIP）
用途：给另一台机器（代号 5090）替换旧的「旁路边读引擎日志」账本链的**独立工具包**。
运行要求：本机 Python 3.13 实测通过；3.8 未实测，静态检查未见 3.9+ 专有语法（内置泛型下标 `list[...]`、`X | Y` 联合类型、match 语句等均未使用）。主链仅标准库；`psutil` 与 `nvidia-smi` 为监控增强，缺失时自动降级。目标机若用更旧版本，请先跑 `bootstrap.py --selftest` 验证。

---

## 一、文件清单

本发行版共 **35 个文件**（根目录 24 个 + `service-examples/` 3 个 + `legacy/` 3 个 + `config-examples/` 2 个 + `docs/` 3 个；下表把服务示例与兼容件各归并成一行通配登记）。逐项来源见下表，仓内条目以当次实际提交为准，不在此写死随版本变化的计数。

| 文件 | 作用 | 来源 |
|---|---|---|
| `config.template.json` | 配置模板，不含任何本机绝对路径或真人姓名 | 本包新写 |
| `bootstrap.py` | 生成配置 / 只读自检 / 跑回归自测 | 本包新写 |
| `paths.py` | 跨平台路径解析（`@here` / `@pkg` / `~` / 相对 / 绝对） | 本包新写 |
| `README.md` | 安装、验收、迁移、回滚、边界 | 本包新写 |
| `INSTALL.md`（原 `SKILL.md`，rev17j 改名+摘 frontmatter） | 仓根部署工序入口（模式判定、自检、拍板项、工序、验收、投递），人类与宿主 Agent 通用；非平台 skill 包 | 本包新写 |
| `CHANGELOG.md` | 版本改动登记（人读摘要，明细仍以本文件为准） | 本包新写 |
| `MANIFEST.md` | 本文件 | 本包新写 |
| `collector_proxy.py` | 反代 + 按 key 记账 + 日报线程 + 硬件监控合并 | 实例版副本 + 路径补丁 |
| `monitor_ext.py` | 硬件采样（GPU 含 UUID、显存/编解码利用率与每卡 PCIe 链路实测 18 列）、自带 `/monitor` `/monitor.js` `/monitor.css` `/monitor-sprite.svg` `/ext.json` `/health` 路由；**不再向任何页面注入脚本** | 实例版副本 + 2026-11-16 重构（见 2.8 / 2.9 / 2.10 节） |
| `monitor.html` | 自持监控页骨架：官方 Strata 监视页的完整复刻 + 本包硬件卡「融合视图」（状态卡 / 融合卡网格 / Context fill / Recent requests / Conversation cache），页脚自报账本工具自持页面 | 本包新写（2026-11-16，三稿重写为融合视图，见 2.9 节） |
| `monitor.js` | 监控页逻辑：每秒并发 fetch `/ext.json` + `/metrics` 双源独立容错；GPU 卡片与波形历史按 UUID 绑定、槽位号仅展示；引擎 key 读写官方同键 `localStorage["strata.apikey"]` | 本包新写（2026-11-16，三稿重写，见 2.9 节） |
| `monitor.css` | 页面样式：官方 st-* 设计令牌与组件类逐条移植为包内自有文件（深浅色两套），零运行时依赖官方 CSS | 本包新写（2026-11-16 三稿，见 2.9 节） |
| `monitor-sprite.svg` | 页面图标精灵：12 个 symbol 几何逐字拷自官方 sprite 以保视觉一致；由反代在 `/monitor-sprite.svg` 提供，本包从不加载官方 sprite | 本包新写（拷自官方素材，2026-11-16 三稿） |
| `ext.js` | 旧注入式监控脚本，仅为「官方页面尚未恢复原状」的过渡兼容保留；新部署不需要。**注意**：过渡期内它仍按 nvidia-smi 槽位号分桶历史，仍可能串卡——不修复串卡，只兜过渡显示 | 实例版副本 + 2026-11-16 跨源 API 解析（见 2.8 节），退役中 |
| `daily_report.py` | 按天日报 | 母本副本 + 路径补丁 |
| `html_report.py` | 交互式网页报表 | 母本副本 + 路径补丁 |
| `ledger_watchdog.py` | 5 秒巡检、配置热更新、立即补岗、脱离会话拉起服务 | 本机运维脚本副本 + 补丁 |
| `switch_proxy.py` | 唯一切换入口，有会话硬拒绝 | 本机运维脚本副本 + 补丁 |
| `selftest_proxy.py` | 回归自测（假上游 + 临时端口），用例数见 2.4 节 | 本机自测副本 + 补丁 |
| `selftest_watchdog.py` | 临时端口回归用例，用例数按当次实际输出报出 | 本机自测副本，未改 |
| `selftest_monitor.py` | 监控页回归用例（18 列解析 / UUID 身份 / PCIe 链路与零告警纪律 / lead 单线 PCIe 卡 / disks-net innerHTML / mx-sw 10×3 / disk rev6 与 net rev6b 卡形态 / CPU 图例与配色 / 小字基线骨架 / node 冒烟 / 路由与融合页静态资产断言），用例数按当次实际输出报出 | 本包新写（2026-11-16，三稿扩充 + 四稿扩充 + 五稿对齐 + 六稿卡重构/图例/骨架对齐，见 2.9 / 2.10 / 2.11 节） |
| `selftest_daily_report.py` | 日报闸统计节回归用例（fixture 驱动：A/B/C1/C2 四态 + 跨日标注 + 回填口径 + 幂等 + `--day` force + 隐私 scan + 节位 + 既有四节序不变），用例数按当次实际输出报出 | 本包新写（2026-11-19 rev13，见 2.24 节） |
| `start.bat` | Windows 启动（GBK + CRLF） | 本包新写 |
| `start.sh` | Linux / macOS 启动（LF） | 本包新写 |
| `service-examples/*` | 登录自启 / systemd / launchd 示例 | 本包新写 |
| `config-examples/windows-5090-single-gpu.json` | Windows 单卡终端在岗配置样例（IPv6 双栈门面 + 引擎退环回 + lock 避让改值示范） | 000 在岗实机抄录，去 `key_labels`，2026-11-17 |
| `config-examples/ubuntu-pro5000-4090-dual-gpu.json` | Linux 双卡工作站装配参考样例（双卡零配置示范，comment 内嵌降级与 systemd 口径） | 按模板缺省口径组装（非实机抄录），2026-11-17 |
| `docs/monitor-hardware.png` | README 配图：`/monitor` 硬件区真机在岗实拍（浅色主题） | Edge headless 实拍 + 按内容边界裁切，2026-11-17（见 2.15 节） |
| `docs/monitor-ledger.png` | README 配图：`/monitor` 账本区真机在岗实拍（最近请求含合计行、对话缓存） | 同上 |
| `api-price-table.csv` | 省钱计算器价表数据（22 款模型公开 API 牌价，含出处与峰谷/分档备注，2026-11-05 逐家官方页核验）——`html_report.py` 注释一直引用它，rev8 前未随包，本轮补入销掉悬空指针 | 母本副本（与 000 在岗 `usage/api-price-table.csv` cmp 一致），2026-11-17 |
| `docs/savings-calculator.png` | README 配图：网页报表「省钱计算器」近 30天真机账本折算实拍 | Edge headless 实拍 + 裁切，2026-11-17（见 2.17 节） |
| `legacy/collector_log.py` | 旧读日志采集器（可选兼容件） | 母本副本，未改 |
| `legacy/scheduler.py` | 旧定时排程（可选兼容件） | 母本副本，未改 |
| `legacy/README.md` | 兼容件说明 | 本包新写 |

---

## 二、改动登记

下表按「相对源文件做了什么」逐项列出，不设总数（每次交付以本表实际行数为准）。所有改动均限定在路径/端口解析、可选功能降级、断连保护、归因修正与文档同步，**流式逐块转发、响应头透传、按 key 记账、`ts` 取请求开始时刻、32 MiB 记账副本上限、排队数 128、看门狗「只在端口关闭时拉起自己的子进程」、切换时「有会话硬拒绝且 `--force` 不覆盖」这些契约一律未改**。

### 2.1 移植补丁（首版相对源文件）

| 文件 | 改动 | 为什么 |
|---|---|---|
| `collector_proxy.py` | `load_config()` 改走 `paths.load_config()` | `out_dir` / `web_root` 支持相对路径与占位符，配置不再写死盘符 |
| `daily_report.py` | 同上 | 单独命令行跑日报时也能解析相对路径 |
| `html_report.py` | `--config` 分支改走 `paths.load_config()`；`config.json` 位置改用配置里的真实路径 | 配置不在 `out_dir` 时也能读到人名映射 |
| `monitor_ext.py` | 去掉原文件里写死的 Windows 部署根默认值；`web_root` 为空或目录不存在时跳过页面注入，采样器照常工作 | 目标机没有该目录，页面注入必须可跳过 |
| `ledger_watchdog.py` | 默认服务脚本从「用户主目录下 WorkBuddy 技能目录」改成**本包同目录**；环境变量/配置覆盖改用 `paths.expand_path` | 目标机可能没装 WorkBuddy，包必须自包含 |
| `switch_proxy.py` | 判忙时按配置的 `out_dir` 找账本文件，不再固定在脚本旁边 | 数据目录搬走后会话检查不能失效 |
| `selftest_proxy.py` | `PROXY_SCRIPT` 从写死的绝对路径改成 `__file__` 同目录 | 自测在任何机器上都能跑 |
| `selftest_watchdog.py` | 无需改动，已是按 `__file__` 推导 | — |

### 2.2 模块动态加载兜底（首版后补）

`selftest_watchdog.py` 等用 `importlib` 从文件路径加载模块时，包目录不一定在 `sys.path`，直接 `from paths import ...` 会抛 `ModuleNotFoundError: paths`。以下模块在导入 `paths` 前各加一行 `sys.path.insert(0, HERE)`：

| 文件 | 行 | 说明 |
|---|---|---|
| `daily_report.py` | 19 | 供反代进程内日报线程以 import 方式加载 |
| `html_report.py` | 25 | 同上 |
| `ledger_watchdog.py` | 67 | 供自测以 `importlib` 加载 |
| `switch_proxy.py` | 45 | 同上 |
| `bootstrap.py` | 26（本轮补，见 2.6 节） | 清掉 P3-2：宿主用 `importlib` 从文件路径加载本文件时也能找到 `paths` |

注：`collector_proxy.py:66`、`legacy/scheduler.py:52` 也有 `sys.path.insert`，但那是**源文件自带的**、用于导入同目录监控/日报模块，**非本包新增**，不在本表登记范围内。

### 2.3 交付前修复（2026-11-09 轮）

| 文件 | 改动 | 对应项 |
|---|---|---|
| `paths.py` | `expand_path()` 收尾处：非绝对路径且无盘符时先 `os.path.join(base, s)`，纯相对路径改为相对**配置文件所在目录**解析，不再随 cwd 漂移 | 必修 1 |
| `paths.py` | 新增 `ports_from_config()`：从 config 读 `listen`（`rpartition(":")`，兼容 `[::]:端口`）与 `watchdog_lock_port`，坏配置安全回退 | 必修 2 |
| `ledger_watchdog.py` | `--port` / `--lock-port` 默认改 `None`；`main()` 在日志与 `port_is_up()` 之前用 `ports_from_config()` 补齐，显式 CLI 值优先（自测传参不受影响） | 必修 2 |
| `switch_proxy.py` | `main()` 用 `global` 从 config 重绑 `PROXY_PORT` / `WATCHDOG_LOCK_PORT`；`port_up()` 默认值改为**调用时**解析，避免函数定义时固化 8080 | 必修 2 |
| `config.template.json` | 新增 `watchdog_lock_port`；`comment` 说明端口自动跟随、两锁端口须不同、相对路径语义 | 必修 2 |
| `README.md` | 第三步表格补 `watchdog_lock_port` 与「只改 listen 一处」说明；第 11 行改为不依赖外部升级说明文档的自包含说明；补物理硬盘清单的平台差异 | 必修 2 / 3 |
| `MANIFEST.md` | 本节重写、运行要求改为如实口径 | 必修 3 |
| `monitor_ext.py` | `_smi_exe()` 去掉最后一个盘符字面量：`SystemRoot` 为空直接返回 `nvidia-smi`，行为不变 | 必修 4 |
| `collector_proxy.py` | 单实例锁默认值改为 `43177`，与模板一致（原默认值与模板不符） | 必修 4 |
| `collector_proxy.py` | `do_GET` 上游异常分支加 `responded` 保护：已发出响应头时只 `close_connection`，不再追加第二个 502 | 可选（低风险） |
| `README.md` | `key_labels` 示例换成虚构指纹 `01234567` / `abcdef01`，注明须用 `--fp` 实算；全包 4 个真实指纹与 4 个真人姓名 0 命中 | 必修 A |
| `README.md` | 第四节标题与条目如实化：网页报表标注「需手动生成/刷新」，验收清单第 6 条拆成日报 / 网页报表两条独立命令，§八表格增一行网页报表命令 | 必修 B |
| `html_report.py` | 页脚「每天 0 点日报链自动刷新」改为「由 html_report.py 生成 · 手动重跑可刷新」 | 必修 B |
| `README.md` | 启动表「长期运行建议」改为「**生产必须**装 service-examples 自启件」，`start.sh` / `start.bat` 标注仅交互式试跑；第九节新增第 7 条会话消失边界；第五节新增第 8 条关终端后自检 | 必修 C |
| `start.sh` | 顶部注释与 echo 提示加醒目告示：前台 `exec`，关终端 / SSH 断开服务即消失，生产必须装自启件 | 必修 C |
| `ledger_watchdog.py` | `launch_ledger()` 的 `subprocess.Popen`：POSIX 分支加 `start_new_session=True` 让子进程脱离终端会话、不受 SIGHUP 连带；Windows 仍只传 creationflags | 必修 C |
| `switch_proxy.py` | `report()` / `do_switch()` / argparse 里的端口提示由写死 `8080` 改为按 `PROXY_PORT` 动态显示 | 交付前一致性（额外） |
| `MANIFEST.md` | 第三节去掉「8 处」写死计数；第五节扫描断言改为「所有 .py 代码零硬编码；文档以占位方式描述来源」 | 必修 D |

### 2.4 按 key 归因修复（2026-11-11 轮）

| 文件 | 改动 | 对应项 |
|---|---|---|
| `collector_proxy.py` | 新增 `key_identity(headers, cfg)` 返回 `(tag, fp)`：先 `raw.strip()`，再用 `raw[:7].lower() == "bearer "` 剥前缀，使 `Bearer` / `bearer` / `BEARER` 按 RFC 7235 大小写不敏感地归一；`key_tag()` 保留为向后兼容 wrapper | A（真 bug） |
| `collector_proxy.py` | 账本 `rec` 构造改为一次 `tag, fp = key_identity(...)`，不重复算 hash；新增 `fp` 字段（8 位小写 hex 或 `none`），原始指纹永久留存，便于事后拆分 / 追查撞码 | A |
| `selftest_proxy.py` | 新增归因用例：`Bearer` / `bearer` 同 `key`+`fp`、混合大小写 `BEARER` 同 `key`+`fp`、`x-api-key` 的 chat 请求记录合法 `fp`、全量账本行 `fp` 格式校验（含无 key 的 `none` 行）；用例数按当次实际输出报出，不写死 | B |
| `bootstrap.py` | 新增 `import re`；`do_check()` 在 `web_root` 之后新增**纯读取**的 `key_labels` 校验：键须 8 位小写 hex（大写判不合格并提示改小写）、值须非空字符串、两指纹映射同一姓名仅 warn、缺失/空 `{}` warn | C |
| `bootstrap.py` | 清掉审计残留 R-3：`lock_port` 与 `watchdog_lock_port` 相同 → `fails.append` | C |
| `README.md` | 第三节补三个坑（`--fp` 算裸 key 别带 `Bearer `、空 `key_labels` 显示 8 位码看似撞车、同姓名合并不可从历史拆开）；第四节字段清单加入 `fp` 并说明不影响出报表；第五节第 3 条验收补 `fp`；第九节新增第 8 条「32 位空间可能撞码、保留 `fp` 便于发现、不做自动碰撞检测」 | D |
| `daily_report.py` / `html_report.py` | **已核查、未改**：两者均按 `r.get("key")` 分组，代码里没有对账本字段做白名单或严格集合断言（`CANON_INT` 只是 `rec.setdefault` 的整型字段），新增 `fp` 不影响出日报 / 网页报表 | A（核查） |
| `MANIFEST.md` | 本文件新增 2.4 节；第一节 `selftest_proxy.py` 用例数不再写死；第五节补「按实际用例数报出」口径 | E |

**回归自测用例数口径**：两套均以 `RESULTS` / `PASS`/`FAIL` 实际计数输出，文档**不写死具体用例数**；每轮增减用例以当次输出为准。交付包内 `selftest_watchdog.py` 与生产 `usage/selftest_watchdog.py` 各按自身当次输出分别报出（生产版另含端口解析与 `--lock-wait` 接管用例，两者数量可以不同）。

### 2.5 文档层重构（docs-r2，2026-11-12）

| 文件 | 改动 | 说明 |
|---|---|---|
| `SKILL.md` | 新增：宿主 Agent 部署工序入口（frontmatter `name: strata-ledger-deploy`；含触发条件、模式判定表、三条前置自检、必问人类拍板项、编号工序、验收判据、运维与故障、边界与债、每日投递工序） | 内容全部取自本包既有事实（README / MANIFEST / legacy README），未发明新能力 |
| `CHANGELOG.md` | 新增：倒序登记 v1（2026-11-09）、rev（2026-11-11）、docs-r2（2026-11-12）三轮 | 人读摘要，逐项明细仍以本文件第二节为准 |
| `README.md` | 仅在顶部引言后插入「Agent 部署入口」短小节（3 行），其余内容一字未动 | 指引宿主 Agent 直接按 `SKILL.md` 执行 |
| `MANIFEST.md` | 第一节登记两个新文件；本小节；「发行版本」行修订日期更新为 2026-11-12 | — |

**本次为纯文档层改动，未改任何 `.py` / `.bat` / `.sh` / 配置模板**：所有运行件（`collector_proxy.py`、`daily_report.py`、`ledger_watchdog.py`、`switch_proxy.py`、`bootstrap.py`、`paths.py`、`monitor_ext.py`、`ext.js`、`html_report.py`、`selftest_*.py`、`legacy/*`、`service-examples/*`、`config.template.json`、`start.bat`、`start.sh`）本轮零改动，上文登记的契约不变量（流式逐块转发、响应头透传、按 key 记账、`ts` 取请求开始时刻、32 MiB 记账副本上限、排队数 128、看门狗「只在端口关闭时拉起自己的子进程」、切换「有会话硬拒绝且 `--force` 不覆盖」）全部未动。

**生产母本同步（只改文件，绝不重启）**：用户主目录下 WorkBuddy 技能目录里的 `collector_proxy.py` 已按 A 的两处改动同步；生产数据目录里的 `selftest_proxy.py` 与本包版同构（唯一差异是 `PROXY_SCRIPT` 写死为生产脚本绝对路径），已同步加等价用例并在临时端口跑通。11-11 轮当时 **磁盘代码已更新 ≠ 进程已生效**，已注明 8080 常驻进程仍加载修改前的模块、需等无会话窗口按纪律走 `switch_proxy.py`。此后主理人已于 **2026-11-12 20:19** 完成切换，**11-11 归因修复版在生产 8080 上实证生效**；本轮（见 2.6 节）又把看门狗磁盘代码两边对齐，但**看门狗进程仍待主理人在无会话窗口自行交接**。本轮全程未启动、未停止、未重启、未连接、未占用任何生产服务端口。

### 2.6 看门狗对齐 / 自启接管 / 重打包（2026-11-12 轮）

本轮把「交付包 / 生产看门狗 / 开机自启」三条线一次对齐并重新打包。生产改动**只改磁盘文件，未重启任何进程**。

| 文件 | 改动 | 对应项 |
|---|---|---|
| 生产 `usage/ledger_watchdog.py` | 新增**自包含** `ports_from_config(path, default_port=8080, default_lock_port=43176)`，语义与包内 `paths.py` 的 `ports_from_config()` 一致，但**不 `import paths`**（`usage/` 目录没有该文件，须保持单文件自包含） | A |
| 生产 `usage/ledger_watchdog.py` | `parse_args()` 的 `--port` / `--lock-port` 默认改 `None`，help 写明默认跟随 `config.json`；`main()` 在 `args.config` 规范化之后、任何日志与 `port_is_up()` 之前用 `ports_from_config()` 补齐，显式 CLI 参数始终优先 | A |
| 生产 `usage/ledger_watchdog.py` | `launch_ledger()` 的 `subprocess.Popen` 改 `popen_kwargs` 字典：Windows 分支保留 `creationflags`，POSIX 分支加 `start_new_session=True` | A |
| 生产 `usage/ledger_watchdog.py` | **未改**：`resolve_collector()` 默认路径仍落到用户主目录下 WorkBuddy 技能目录；`--lock-wait` 候补接管锁循环一字未动 | A（保持） |
| 生产 `usage/selftest_watchdog.py` | 新增端口解析与接管用例：`ports_from_config()` 六种配置形状（正常 / `[::]:端口` / 坏 JSON / 端口非数字 / 缺 `watchdog_lock_port` / 非 dict）与进程级「config `listen` 跟随」「显式 `--port`/`--lock-port` 优先」「`--lock-wait` 候补接管」；原有回归用例逐字保留，用例数按当次实际输出报出 | B |
| 启动夹 `Strata ledger watchdog.vbs` | `sh.Run` 命令行末尾给 `ledger_watchdog.py` 追加 `--lock-wait 86400`，登录副本改为热备候补、旧看门狗退出后零缝隙接管；英文注释写清原因，纯 ASCII + CRLF；`python.exe` 与脚本路径未改 | C |
| `service-examples/Strata ledger watchdog.vbs` | 同步 `--lock-wait 86400` 写法与英文注释；清掉 P3-5：中文注释改纯 ASCII、UTF-8/LF 改 ASCII/CRLF（GBK 友好），可执行语句全 ASCII | C |
| `bootstrap.py` | 顶部 `HERE` 定义后加 `sys.path.insert(0, HERE)` 兜底，清掉 P3-2（`importlib` 从文件路径加载时 `ModuleNotFoundError: paths`） | D |
| `README.md` | 第三节补第 4 个坑（畸形 `Authorization: Bearer ` 记成陌生 8 位指纹而非 `none`，有意为之，便于发现配错客户端）；第九节第 3 条同步边界；第二节补 VBS `--lock-wait` 候补接管说明 | D |
| `MANIFEST.md` | 本文件：第一节文件总数口径改 24 且不写死、清掉写死用例数（P3-4）、2.2 节补登记 `bootstrap.py`、修正 2.5 节「生产 8080 仍跑旧代码」过时断言、新增本小节 | D |
| `CHANGELOG.md` | 新增 2026-11-12 记录，写明本轮改动与生产进程状态 | D |
| `strata-ledger-proxy-2026-11-12.zip` | 重打包为 **24 文件**版，保留 11-09 / 11-11 两个旧 ZIP | D |

**生产进程状态（如实）**：生产 `8080` 已于 2026-11-12 20:19 切换到 11-11 归因修复版并实证生效（由主理人完成，本席未参与）；本轮**看门狗磁盘代码已对齐但进程未重启、未交接**，待主理人在无会话窗口自行完成。本轮全程未启动 / 停止 / 重启 / 连接 / 占用 `8080` / `8787` / `20003`。

**P3-6 处理**：`selftest_watchdog.py` 仍用固定临时端口（`19080` / `43976` 及本轮新增的 `19xxx` / `43xxx` 高位端口），未改成绑定端口 0 取空闲端口。评估：临时端口均取自高位段、且每次运行在全新临时目录，端口冲突概率低，**保留为已知低风险**，本轮不改动，避免牵动原有 16 个已验证用例。

---

### 2.7 终版修正（2026-11-12 晚 · Windows 自启示例静默失败）

| 文件 | 改动 | 为什么 |
|---|---|---|
| `service-examples/Strata ledger watchdog.vbs` | 注释改为「VBS 留在包目录、启动夹只放快捷方式」；可执行语句不再经额外的命令处理器中转，用 `Chr(34)` 拼引号，并支持 `STRATA_PYTHON` 环境变量覆盖解释器（回退 `python`） | 原注释让人把 VBS 复制进启动夹，而脚本按自身目录找 `ledger_watchdog.py`；复制后目录变成启动夹、主程序找不到且静默失败。快捷方式不改变脚本的真实路径 |
| `README.md` | 第二节平台表格、启动逻辑段、第九节第 7 条同步改成「启动夹放快捷方式」，补原因与 `STRATA_PYTHON` 用法 | 文档不能继续把人往坑里带 |
| `SKILL.md` | 第 6 步 Windows 行与紧随的说明同步 | 宿主 Agent 按 SKILL 执行，口径必须一致 |
| `CHANGELOG.md` / 本文件 | 新增本轮人读摘要与本节 | 改动可追溯 |

不变项：包内所有 `.py`、`config.template.json`、`start.bat`、`start.sh` 一字未改；`--lock-wait 86400` 候补接管参数保留；VBS 仍为纯 ASCII + CRLF、引号成对；本轮未启动 / 停止 / 重启 / 连接 / 占用任何生产服务端口。

---

### 2.8 监控页重构：自持独立页，按 UUID 绑卡（2026-11-16 轮）

重构动机（生产实证缺陷）：官方页注入混合体把 Pro5000 的负载波形画到 4090 卡片上。根因在旧 `ext.js`：波形历史按 nvidia-smi 的 `index` 存、卡片标签按卡名重建，而本机槽位序会漂（历史事故：gpu:0 错落 4090 时 decode 210→13.7 tok/s；开机计划任务还会 disable→enable 4090）。本机铁律：判卡一律 UUID/卡名，槽位号不作身份判据。用户已拍板**彻底弃用官方 webui 集成**。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `monitor_ext.py` | `GPU_QUERY` 10 列 → 14 列（新增 `uuid,utilization.memory,utilization.encoder,utilization.decoder`；**11-16 二稿更正**：首稿写的 `encoder.utilization/decoder.utilization` 在 621.24 驱动下让整条 nvidia-smi 查询 rc=2 失败、所有显卡消失，已换成驱动实证可用的名字）；解析改 `parse_gpu_csv()`：csv 模块 + `skipinitialspace`（卡名含逗号不串列）、不足 14 列整行丢弃（旧驱动不得错位填值）、缺 UUID 退卡名身份（绝不退 index）；每行 JSON 新增 `uuid/mem_util/enc_util/dec_util` | 身份必须稳定；旧口径把波形画到别的卡上 |
| `monitor_ext.py` | **删除 `attach()` / `pages()` / `Watcher` / `_write()` / `MARK` / `SCRIPT` / `ELEMENT` / `PAGE_GLOBS` 整套注入机制**；`start()` 不再起 Watcher；`web_root` 配置字段弃用（留着不报错） | 本工具不再写任何它不拥有的页面 |
| `monitor_ext.py` | `answer()` 新增 `/monitor`（回 `monitor.html`）与 `/monitor.js`（回 `monitor.js`）两个自持路由；`/ext.js` 保留为退役过渡 shim；`/ext.json`、`/health`、`/` 不认领等语义不变 | 页面结构与数据接口分离，页面归本包所有 |
| `monitor.html` / `monitor.js` | 新增自包含页面与脚本：卡片排布 Speed→GPU→RAM→Disk→Net 风格（大数字+副行+180 点 1s sparkline），100% 自写、零第三方、内联 CSS、深浅色跟随 `prefers-color-scheme`；GPU 卡片与波形历史一律按 `uuid` 绑定（DOM id 由 uuid 哈希），uuid 消失时卡片与历史一并移除；GPU 主数字=SM util，副行含显存 used/total、显存/编码/解码利用率、温度、功率/限、SM 时钟、驱动模式，标题显示卡名+驱动模式+`#index`（标注仅展示） | 修根因：槽位号不可作身份 |
| `collector_proxy.py` | 仅 docstring 与一行启动提示改口径（监控页在 `/monitor`）；代码接线未动（`_monitor_ext.answer()` / `start()` 签名不变） | 最小改动 |
| `ext.js` | 数据源解析改为按 `document.currentScript` 的 src 推断 origin（跨源加载时也能读到反代的 `/ext.json`，反代对 `/ext.json` 发 `Access-Control-Allow-Origin: *`；同源加载行为不变，仍是 `""`） | 官方控制台页在 :8787、`/ext.json` 在反代端口，过渡期跨源取数必须可用 |
| `selftest_monitor.py` | 新增 21 个用例（本轮实测 21/21 PASS）：14 列解析、N/A→None、短行丢弃、带引号逗号卡名、缺 UUID 退卡名、**index 0/1 互换而 UUID 稳定→身份不串卡**、注入机制确认已删、`/monitor` `/monitor.js` 内容与路由、`/` 不认领、临时端口 19091 最小服务 HTTP 级断言 | 防回归 |
| `bootstrap.py` | `REQUIRED` 加 `monitor.html` `monitor.js` `selftest_monitor.py`（13 项）；`--check` 的 `web_root` 提示改为「已弃用，监控页自带 /monitor」；`--selftest` 跑三套 | 口径一致 |
| `config.template.json` | `comment` 重写：web_root 弃用说明 + 监控页地址 + 按卡身份绑定说明 | 模板不把人往坑里带 |
| `README.md` | 第二节配置表 `web_root` 行移除并注明弃用；第五节第 5 条改为打开 `/monitor`；第六节整节重写（自持页 + UUID 绑定 + 6.1 从旧注入式升级的一次性操作：重启一次走 `switch_proxy.py`、给 `index.html.orig` 恢复命令（不执行）、旧 `ext.js` 退役路径）；自测口径改三套 | 部署说明必须如实 |
| `SKILL.md` | 第 3 步 `web_root` 口径、验收第 5 条 `/monitor`、`--selftest` 三套口径同步 | Agent 工序与人类文档一致 |

**11-16 二稿补修（工程复核后，同一轮登记）**：①`monitor_ext.py` `GPU_QUERY` 编解码字段名改驱动实证名（见上表，真 bug）；②`selftest_monitor.py` 对字段名断言收紧（断言含 `utilization.encoder/utilization.decoder` 且不含旧名）；③`CHANGELOG.md` 更正 11-12 段不存在的 `archive/` 回滚件说法；④`README.md` 第八节 / `SKILL.md` 运维段 / 本节补**看门狗划界**：本包 `ledger_watchdog.py` 只守护本包记账反代（`listen` 端口），Strata 官方引擎壳（`terminal/serve/server.py`）自带引擎进程看护，与本包看门狗无关、不碰不依赖；⑤`bootstrap.py` docstring 与用法行「两套」改「三套」、本节第五节「两套回归」改三套；⑥`README.md` 6.1 第 3 条补「旧注入页过渡期仍按槽位分桶、仍可能串卡」提示，第六节补 `/monitor` 自身故障退回路径（退旧 ZIP 整包；shim 不兜 /monitor 故障）。

**契约不变量未动**：流式逐块转发、响应头透传、按 key 记账、`ts` 取请求开始时刻、32 MiB 副本上限、排队 128、看门狗「只在端口关闭时拉起自己的子进程」、切换「有会话硬拒绝且 `--force` 不覆盖」。`/ext.json` 只增字段（`uuid/mem_util/enc_util/dec_util/gpu_query_fields`），向后兼容：旧 `ext.js` 过渡期照常渲染。

**生产侧待办（本轮不执行，README 6.1 已给命令）**：生产 `terminal/serve/web/index.html` 里已注入的 `<script src="/ext.js">` 与 `<!-- monitor-ext -->` 需从同目录 `index.html.orig` 恢复；8080 记账反代需按切换纪律（先 `switch_proxy.py --check` 无人在线）重启一次才吃到新代码。本轮未启动 / 停止 / 重启 / 连接 / 占用任何生产服务端口。

---

### 2.9 监视页三稿：官方监视页完整复刻 + 硬件卡融合视图（2026-11-16 三稿）

升级动机（用户拍板终极形态）：把二稿的「简单自持卡片页」重写为「官方 Strata 监视页的完整复刻 + 本包硬件卡」融合视图——视觉与之前寄宿在官方页的形态一致，但页面、CSS、图标、数据请求、渲染全部是本包自有文件，零注入、零依赖官方页 DOM / CSS / sprite。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `monitor.css` | **新增**：官方 `tokens.css` 全套 `--st-*` 设计令牌（light/dark 两套，accent 等同值）、`components.css` 组件类子集（st-card / st-metric__* / st-progress / st-gauge / st-table / st-badge / st-btn / st-input）、`app.css` 监视布局段，逐条移植为包内自有文件；字体退系统栈（官方 Outfit woff2 不拷） | 视觉一致但运行时零依赖官方 CSS 文件 |
| `monitor-sprite.svg` | **新增**：从官方 sprite.svg 逐字提取页面用到的 12 个 symbol（gauge/gpu/layers/thermometer/bolt/link/cpu/disk/memory/experts/sun/moon）；文件头注释自报出处 | 图标几何一致但本包从不加载官方 sprite |
| `monitor.html` | 重写为融合视图骨架：`mx-header`（含 `#mx-status` 断源指示 + 主题按钮，主题读写官方同键 `strata.theme`）；模型状态卡（6 中文徽章 + 进度条）；`#metrics` 融合卡网格；Context fill 卡（环形仪表 dasharray/rotate 同官方 + Experts in VRAM / System RAM / GPU temperature 三条进度）；Recent requests 表 9 列（中文表头）+ totals；Conversation cache 卡；`#apikey-row` 小输入框（401/缺 key 时出现）；页脚自报「本页为 Strata 账本工具自持页面…不加载其他网站资源」 | 页面结构照官方监视页复刻，内容归本包所有 |
| `monitor.js` | 重写：每秒 `Promise.all` 并发 fetch `/ext.json`（本包硬件采样）与 `/metrics`（反代原样转发引擎 8787），两源独立容错、任一失败只影响自己半边渲染；渲染函数对照官方 app.js 口径：renderState（徽章点亮条件同官方）、renderSpeed（tok_s 主曲线 + prefill 副曲线，波形优先引擎 `history` 数组、无则本地 180 点缓冲）、renderCpu（`/metrics` 有 `hardware.cpu` 才画）、renderGpus（每卡按 **uuid** 绑卡与历史、index 仅展示、含显存/显存利用率/编码/解码/温度/功率/SM 时钟——不含官方单卡 load/VRAM 重复卡）、renderRam（`/ext.json` 含 swap）、renderDisks/renderNet（每物理盘、每已连接网卡 + 合计行）、renderCtx（ctx 环表 + 三条进度，双源混用）、renderRequests（9 列 + badge 映射 + hit_rate/PCIe/prefill 速率 + totals + 「全部」开关走 `/metrics?requests=all`）、renderConvCache；引擎 key 读写官方同键 `localStorage["strata.apikey"]`（JSON 字符串口径同官方 app.js），401/403 触发页面输入框存回同键；每张网格卡带 `data-mx-section`，`pruneSection()` 只清本区卡防跨区误删 | 融合数据来自两个源且必须互不拖垮；GPU 身份 UUID 契约不得回归 |
| `monitor_ext.py` | **唯一 py 改动**：`answer()` 增两条静态路由 `/monitor.css`（text/css）与 `/monitor-sprite.svg`（image/svg+xml），均走既有 `_read_asset()`（每请求现读磁盘，改静态资产不需重启 8080；此 py 改动上线需按切换纪律重启窗口，时机主理人定）。采样器 / 14 列 GPU_QUERY / `parse_gpu_csv()` / `start()` 签名一行未动 | 路由是唯一必须过 py 的部分；契约不变量全部保留 |
| `selftest_monitor.py` | 第 7 段断言改为融合页元素（`id="metrics"` / state-badges / ctx-fill / req-body / cc-card / `/monitor.css` / `/monitor-sprite.svg` 引用、页面不含 `web/sprite.svg` / `app.css` / `components.css`、js 含 `strata.apikey` 与 `/metrics`、css 含 `--st-accent`、sprite 含 8 个被引用 symbol）；HTTP 段新增 `/monitor.css`（text/css）与 `/monitor-sprite.svg`（svg content-type + 非空 body）用例；docstring 同步。用例数按当次实际输出报出 | 静态资产与「零官方依赖」是可自动化的断言 |
| `bootstrap.py` | `REQUIRED` 加 `monitor.css`、`monitor-sprite.svg`（13 → 15 项）：静态资产齐全断言落在装机自检 | 缺文件在 `--check` 就能看到而不是页面 404 |

**未动清单（三稿）**：GPU 采样线程、14 列契约与字段名、`parse_gpu_csv()`、`/ext.json` 结构、`collector_proxy.py`（反代本来就把 `/metrics` 原样转发引擎）、看门狗、切换纪律、记账主链、`ext.js` shim。官方 `terminal/serve/web/` 下任何文件未写。ZIP 未重打（打包由主理人统一做）。

**生产上线提醒（本包不代做）**：`monitor_ext.py` 的两条新路由需 8080 按切换纪律（先 `switch_proxy.py --check` 无人在线）重启一次才生效；`monitor.html/css/js/sprite` 四个静态资产本身是每请求现读磁盘，路由生效后替换即时可见、无需再重启。

---

### 2.10 监视页四稿：每卡 PCIe 链路字段 + 每卡多色实时线路波形（2026-11-16 四稿）

动机（用户指令，同日口径修订覆盖首版告警设计）：融合页此前只有一张来自引擎 `/metrics` 的 "PCIe" 卡，只描述引擎所用那张卡（Pro5000）；4090 实际 Gen4 ×8 在页面完全看不到。**用户修订口径**：本机 ×8 就是稳态正常值（7950X 平台双卡各 8 lane），Gen/宽度只作**中性信息展示，不做任何退化告警/红标**；展示形态 = 一张 PCIe 卡、每 GPU 一条彩色实时线路波形、图例标注卡名 + 链路规格 + 当前吞吐。首版实现过的退化徽章机制已全部移除，selftest 断言其不再出现。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `monitor_ext.py` | `GPU_QUERY` 追加 4 列 `pcie.link.gen.current,pcie.link.width.current,pcie.link.gen.max,pcie.link.width.max`（14→18）；`GPU_FIELDS` 14→18；`parse_gpu_csv()` 新增 key `pcie_gen/pcie_width/pcie_gen_max/pcie_width_max`（`_num()` 容错 N/A；「不足 `GPU_FIELDS` 列整行丢弃」规则保留——旧 14 列形态同样被丢弃）。**每卡吞吐**：621.24 驱动无 `pcie.throughput.tx/rx` 查询字段（真机 rc=2 实证），改用 `nvidia-smi dmon -s t -c 2` 读 rxpci/txpci MB/s（取最后一行=完整 1s 窗样本），新增 `parse_dmon_txrx()` + `gpu_txrx_sample()`；采样线程 GPU tick 上**同 tick 按枚举序**与 uuid 配对写入每卡 `pcie_rx_mb/pcie_tx_mb`（跨 tick 身份一律 uuid 的契约不变）；`/ext.json` 顶层新增 `pcie_txrx_supported`（dmon 不可用时页面显示「不支持」） | dmon 单次 ~1.4s 在采样线程内跑，不阻塞反代与 /ext.json；引擎 `/metrics` 的 gpu_pcie_rx_mb 只描述引擎所用那张卡，不能当通用每卡数据源 |
| `monitor.js` | 顶部 PCIe 卡升级为「PCIe 线路」多序列图：`drawMultiSpark()` 每 GPU 一条固定色板线（6 色板，深浅色主题都可读），`hist.pcie[uuid]` 按 uuid 绑历史（卡消失清历史，与 GPU 卡同契约）；图例每卡一行 `卡名 · Gen5 ×8 · 360 MB/s`（纯文字，无 warn/danger tone）；引擎 `/metrics` rx 作「引擎侧实测」一条并入同图。GPU 卡副行加**中性** `PCIe Gen5 ×8` 文字段。首版的退化徽章机制（`badgeSlot`/`mx-badge--danger`/degraded 判据）**已全部移除** | 用户口径：×8 稳态正常、空闲降代 Gen1 也正常，不告警 |
| `monitor.css` | 新增 `.mx-legend`/`.mx-legend__row`（中性图例行，10×3px 色块与波形同色）；首版 `.mx-bdg`/`.mx-badge--danger` 已删除 | 样式表零告警元素 |
| `selftest_monitor.py` | 假 CSV 全部改 18 列（4090 行是空闲 Gen1 样本，按中性数据断言）；新用例：4 个 PCIe key 解析、链路字段中性断言、`GPU_QUERY` 含 4 条 pcie 查询且 `GPU_FIELDS==18`、**旧 14 列形态整行丢弃**、`parse_dmon_txrx()`（末行样本覆盖/垃圾行跳过/空输出）、js 含多序列渲染（`drawMultiSpark`/`SERIES_COLORS`/`mx-legend__row`/`pcie_rx_mb`）且**零告警残留**（`mx-badge--danger`/`degraded`/`badgeSlot` 必须缺席） | 防回归 + 防告警设计复活 |

**真机实证（621.24 驱动，只读）**：链路查询 rc=0——Pro5000 当前 Gen5 ×8 / max Gen5 ×16，4090 当前 Gen1 ×8（空闲降代）/ max Gen4 ×16，代码不写死代际；`pcie.throughput.tx/rx` 查询字段不存在（rc=2）→ 走 dmon 兜底；`dmon -s t` 可用：两卡 rxpci/txpci 有值（空载 Pro5000 rx≈0-19/tx≈3-303 MB/s、4090 全 0），采样线程集成后同 tick 配对实证写入成功。

**显示规则基线（主理人在生产副本热修，包内已同版，selftest 锁死不回归）**：GPU 卡标题只留卡名 + `#槽位`（无模式徽章）；大数字 = `util%` 后接模式徽章（`height:20px`，不再写 "% SM"、模式不挤标题）；卡图标统一走 `cardHtml opts.icon`，label 不带图标（修双图标偏右）。2026-11-16 晚实证：生产 `~\.workbuddy\skills\token-ledger\scripts\` 与包内 monitor.js/css/html/sprite/monitor_ext/collector_proxy/ext.js/paths.py **逐字节一致**——该目录即 8080 生产加载目录（热读），两边无版本落差；基线三条已写成 selftest 断言防下次改动覆盖回去。

**契约不变量未动**：UUID 身份、`/ext.json` 只增字段（`pcie_*` 链路四个 + 每卡 `pcie_rx_mb/pcie_tx_mb` + 顶层 `pcie_txrx_supported`，旧消费者向后兼容）、路由、记账主链。四稿含 `monitor_ext.py` 改动，上线需要 8080 按切换纪律重启一次窗口。

---

### 2.11 监视页五稿收口：PCIe 卡单卡化对齐 selftest + 重打 ZIP（2026-11-16 五稿）

背景：四稿上线后主理人在生产副本连续热修前端（已落母本与生产两边、字节级一致），最终形态与四稿描述有差：PCIe 卡从「每 GPU 一条线 + 独立图例区」简化为**单卡单线**——大数字 = 本轮 `pcie_rx_mb` 最大那张卡的即时 MB/s，小字固定两行（第一行固定文案「当前最高读速」，第二行 = `mx-sw` 短线图例 + 显卡名），独立图例区删除（`cardHtml` 不再传 `legend:true`、`mx-legend` 容器 `innerHTML` 置空）；磁盘/网卡卡小字改走 `innerHTML`（小字内嵌 `mx-sw` 短线图例 HTML）；`mx-sw` 为 10×3 短线。零告警纪律与显示基线不变。本轮**只改 `selftest_monitor.py` 断言与文档/打包**，功能代码一字未动。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `selftest_monitor.py` | 作废「js 含 `mx-legend__row`（每卡图例行）」断言；对 PCIe 卡的断言改为五稿终态：lead 选择关键串（`if (!lead \|\| rx > (lead.pcie_rx_mb \|\| 0)) lead = g;`）、小字第一行固定文案「当前最高读速」、第二行 `sub.innerHTML = \`当前最高读速<br>${sw(leadColor)}…`；**新增**独立图例区缺席断言（js 不含 `mx-legend__row`、不传 `legend: true`、`-lg` 容器置空）；**新增** disks/net 小字走 `innerHTML` 断言；**新增** `.mx-sw` 10×3 短线断言；「告警缺席」断言保留并**加强**（js/css 同时断言 `mx-bdg`/`mx-badge--danger`/`degraded`/`badgeSlot` 全缺席）；「显示基线」断言原样保留。docstring 同步。当次 39/39 全绿 | 断言必须锁住前端终态而不是四稿旧形态；两组防回归纪律只增不减 |
| `README.md` | 第六节 PCIe 线路卡条目改为五稿终态描述（单卡单线 + 两行小字 + 图例区取消 + 磁盘/网卡短线图例），删除「图例逐行标注卡名/链路规格/引擎侧实测对照」的旧描述 | 文档与页面终态一致 |
| `MANIFEST.md` | 本节新增；头部修订口径更新 | 登记 |
| `CHANGELOG.md` | 新增五稿收口条目 | 登记 |

**母本↔生产实证（本轮）**：`monitor.html` / `monitor.js` / `monitor.css` / `monitor-sprite.svg` / `monitor_ext.py` / `collector_proxy.py` / `ext.js` / `paths.py` / `daily_report.py` / `html_report.py` 逐一 `cmp` 字节级一致（生产目录 `~\.workbuddy\skills\token-ledger\scripts\` 缺 `ledger_watchdog.py`/`selftest_*` 等属部署子集，不算分叉——生产侧另有本机运维版看门狗）。

**追加（磁盘/网卡大数字排版热修锁断言 + 再重打）**：主理人又一处前端热修（已落生产+母本、字节级一致）——磁盘/网卡卡大数字只留数值大号，单位 MB/s 与 `sw(RW_DOWN)` 读/下行标记全部收进 `<small>` 小字档。`selftest_monitor.py` 对应新增一条「disk/net 大数字的 读/下行 标记必须在 `</small>` 内」的精确形态断言（含反例守卫：标记不得回到大数字档），当次 **40/40** 全绿。ZIP 再次覆盖重打，仍 **29 文件**口径。

**追加（前端热修事故 + 三项形态锁断言 + 再重打）**：主理人再一批前端热修（monitor.js + monitor.css，已落生产+母本、cmp 字节级一致），其中含一起**线上事故**：上一版热修引用了未定义常量 `SPEED_DECODE`/`SPEED_PREFILL`，页面 JS 抛 ReferenceError，**所有读数全部消失**（用户线上实锤）。修复为 CSS 类方案：js 顶部 `swc(cls)` 助手 + 速度卡小字图例 `swc("mx-sw--decode")`/`swc("mx-sw--prefill")`；css 新增 `.mx-sw--decode{background:var(--st-accent)}` / `.mx-sw--prefill{background:color-mix(in srgb,var(--st-accent) 65%,black)}`（与波形两线同色随主题）。本轮 `selftest_monitor.py` 新增四组锁定：①**事故回归**——js 中 `SPEED_DECODE`/`SPEED_PREFILL` 标识符永不允许出现 + swc 定义与两个 CSS 类必须在位；②速度卡图例形态（subD/subP innerHTML 以 swc decode/prefill 开头）；③磁盘/网卡大数字 **`&nbsp;` 形态**更新（作废上一轮普通空格逐字节断言，反例守卫保留）；④CPU 单插槽路径原形态锁死 + 多插槽分支（`hw.cpu_sockets` >1 → speed 版式 + `hist.cpuSock` 分桶）存在性断言。**另新增 node 冒烟守卫**（内联在 selftest，运行时生成临时 harness，不增包内文件数）：以最小 DOM stub 真跑 monitor.js IIFE + tick 渲染链（/metrics 先 401 后 200 含多插槽 CPU 数据），任何 ReferenceError/TypeError/未处理 rejection 即红——`node --check` 抓不到未定义标识符，只有真跑能抓（正是本次事故的类）。无 node 的机器该守卫记跳过不记失败。当次 **45/45** 全绿；ZIP 再覆盖重打，仍 **29 文件**口径。

**追加（磁盘/网卡卡重构 + CPU 卡图例 + 小字基线对齐，断言对表 + 再重打）**：主理人同批四路前端热修（monitor.js + monitor.css，均已落生产+母本、cmp 字节级一致）：①**磁盘卡重构**——标题 `#编号 盘符 型号 · 容量`（`const head = [\`#${d.number + 1}\`]`，内部 0 基、显示从 #1 起），大数字 = 数值 + `<small>` 单位 + 总线规格徽章（`d.bus` 去 `Disk N · ` 前缀），读/写移入小字两行（绿/橙短线）；②**网卡卡**——无线标题「无线网卡」且**不出徽章**、有线标题 = 适配器真名 + 「有线」徽章（中途方案 `NET_KIND_LABEL`/WLAN 徽章已废，断言反向锁死其永不复活），下/上行小字两行；③**CPU 卡图例**——多插槽小字左右 `swc("mx-sw--cpu1"/"mx-sw--cpu2")` + `subOf()`，单插槽小字 `swc("mx-sw--cpu1")` + 核/线程或「整机」兜底（旧 `setSub(id + "-s", st.threads…)` 作废），css 新增 `.mx-sw--cpu1/--cpu2`（info 主题变量），`.st-metric__spark .speed-prefill` 由写死 accent 改 `currentColor 65%` 使右线恒与所在卡主线同色加深；④**小字基线对齐骨架**——`cardHtml` 标题文本包 `<span class="mx-label-t">`（恒一行+省略号），css `.st-metric__value` 加 `min-height:var(--st-fs-stat);white-space:nowrap`（大数字行定高，徽章不撑行）；⑤**GPU 卡序号前置（rev7c）**——标题 = `<span class="muted" title="槽位号会漂，仅供对照，不作为身份">#index+1</span> 卡名`（与磁盘同款、从 1 起），旧 0 基 `${esc(g.index)}` 形态转反例守卫。追加 CSS 微调（rev7b，用户定位小字被压低的真凶=大数字后 `.st-badge` 行内块按基线对齐撑高行框）：中途做过 `.st-metric__value` 加 `inline-flex` 的方案，因间距副作用**已撤销**——终态只新增 `.st-metric__value .st-badge{vertical-align:middle}`，`.st-metric__value` 规则行保持原串+`min-height`+`white-space:nowrap`。断言对表：作废旧「&nbsp; 大数字」两条与 `NET_KIND_LABEL`/`cardHtml … esc(a.name)`/单插槽 `setSub` 旧锁，新锁 disk rev6（`#${d.number + 1}`、spec 徽章、&nbsp; 反例守卫）、net rev6b（无线标题/有线徽章串逐字节、`NET_KIND_LABEL`+`WLAN` 缺席守卫）、cpu 图例（三形态串 + `setSub` 旧行缺席守卫）、图例配色三条 CSS、骨架两条（label 包装行 + `mx-label-t`/`min-height` CSS + `.st-metric__value .st-badge{vertical-align:middle}` 在位与 `display:inline-flex;align-items:center;gap:0` 反例守卫）、gpu 标题 rev7c（muted `#${esc(g.index + 1)}` 前置整串逐字节 + 旧 0 基 `${esc(g.index)}` 缺席守卫）。node 冒烟 stub 的 disks 行含 `number/model/bus/drives/size`、net 行含 `name/kind/down_mb/up_mb`，两卡渲染真跑不抛。当次 **50/50** 全绿；ZIP 再覆盖重打，仍 **29 文件**口径。另：CHANGELOG 顶部补写 **monitor-rev6** 条目收拢本批叙事（含 ReferenceError 事故）。

**重打包**：`strata-ledger-proxy-2026-11-16.zip` 覆盖旧 27 文件版，按包内实际全量重打（根 23 + `service-examples/` 3 + `legacy/` 3 = **29 文件**，`__pycache__` 不入包），打包后以 `zipfile.namelist()` 核对数量。未启动 / 停止 / 重启任何生产进程；8080 未动。

---

### 2.12 rev8 后补：`config-examples/` 样例 + README 真机实测登记（2026-11-17 · 纯文档/样例，功能代码零改动）

背景：两台机器（000 · Windows 5090 单卡、002 · Linux PRO 5000 + 4090 双卡）跑过之后，皮总问「这两台的样例/经验能不能进仓」。判定＝**硬件型号不是本包配置项**（监控按 UUID 动态逐卡发现，配置里没有也无需有机型字段），所以机型不进 `config.json`；可进仓的是两样：①结构示范（脱敏实例配置），②与本包功能相关的实测结论（免得下一台机器重踩）。真实拓扑、真实 IPv6、key 指纹、成员姓名一律不进。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `config-examples/windows-5090-single-gpu.json`（新增） | 000 在岗 `config.json` 实机抄录，仅 `key_labels` 清空；comment 改写为示范口径（IPv6 双栈门面、引擎退环回、lock 避让改值） | 在岗跑通的形态比模板抽象描述更有说服力；直接示范 rev8 双栈写法 |
| `config-examples/ubuntu-pro5000-4090-dual-gpu.json`（新增） | 按模板缺省口径组装的 Linux 双卡装配参考（**非实机抄录**，comment 内如实注明）；示范双卡零配置、缺依赖降级、systemd 口径 | 双卡异构组合最容易让人以为要配显卡——样例的 comment 就是把这层口径随身带上 |
| `README.md` | 第二节第 3 步末尾加「两份真机形态样例」导读表；**新增第十一节「真机实测登记」**（6 条：双栈类属性修与换脑定式 / Win11 注册表 `~MHz` 废源与 PDH 正确源 / 消费卡 ASPM Gen1↔Gen5 链路本态 / 双卡 UUID 自动发现与 `ext.js` 串卡退役 / 缺依赖降级与「装进服务实际用的解释器」/ 登录环境无交互 PATH→自启件绝对解释器路径）。章节编号追加在末尾，既有「第 N 节第 M 条」交叉引用不受影响 | 实测结论不登记，下一台机器就会重踩；登记限定在与本包功能相关的范围 |
| `MANIFEST.md` | 修订口径更新；第一节文件数 29→**31**（新增 `config-examples/` 2 个）并补两行通配登记；本节新增 | 登记 |
| `CHANGELOG.md` | 新增 rev8 后补条目 | 登记 |

**脱敏实证**：两份样例全包扫描——真实 IPv6 地址 0 命中（000 在岗文件里的 `listen` 是 `:::8080` 通配写法，本就不含地址字面量）、真实指纹与真人姓名 0 命中、机器代号（000/002）不出现在样例正文（只按「Windows 单卡终端 / Linux 双卡工作站」中性描述），git 提交信息同口径。

---

### 2.13 第十一节改版：结论式 → 症状式踩坑登记（2026-11-17 · 纯文档，功能代码零改动）

背景：皮总问「两台终端踩过的坑是否也该入仓做经验参考」。判定＝该沉淀，但不进 `config-examples/`——那里是实体样例位（可直接拷改的配置件），坑是知识不是配置，混入会稀释目录语义；正确容器就是第十一节。改版方向：排障的人先看到症状、不知道要找什么，所以六条结论式全部改写为「**症状 → 根因 → 对策**」三段式，节名同步改「真机踩坑登记」。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `README.md` | 第十一节整节改写：原 6 条转三段式；**新增 4 条**——②「gaierror 11001 无限重拉」独立成条（002 首版在跑的人升级指引）；③「引擎区红≠本工具坏」（`/metrics` 浏览器直连引擎、与反代两条独立链路、先分半页再查引擎）；⑨「端口口径全网统一：门面 8080 / 引擎环回 8787，漂移一处全网记例外」；⑩「listen+防火墙+看门狗三件套同轮改，防『端口通但没人守』」。共 10 条 | 结论式对人不可检索，症状式可对照；后 4 条全是实机交过学费的，不登记下一台照踩 |
| `MANIFEST.md` | 本节新增；2.12 历史条目保留当时口径不回改 | 登记 |
| `CHANGELOG.md` | 新增改版条目 | 登记 |

**不入仓边界（同轮裁定，如实登记）**：宿主平台行为（automation 模型绑定、工具假报成功）、本机网络形态（push 走代理回退 HTTP/1.1）、执行沙箱限制（计划任务黑名单）、另一条产品线的档案（生成网关的 speed_bias 与池拓扑）——均与本包无关，写入会误导部署方，一律不入。

---

### 2.14 README 开头重写：价值主张开场，实操保持专业口径（2026-11-17 · 纯文档，功能代码零改动）

背景：皮总问「README 有没有把优势用吸引 git 用户的表达呈现，实操部分才走技术专业口径」。自查结论＝没有：开头是平铺功能罗列；最强卖点（逐块流式、首字节 0.01 秒）藏在引用块里且指向外部访客不存在的内部路径；可信度信号（零依赖、5 秒自愈、带会话拒切换、边界不粉饰）没被当卖点用。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `README.md` | 标题区重写为价值主张开场：问题式定位（谁在用/用了多少/扛不扛得住）＋五条卖点（归人且官方数字、长生成不掐线〔含整包缓冲坑的实机 A/B 实证口径〕、开箱监控页、自愈与拒切换、零依赖）＋「代价也先说清楚」段（引流第九节）＋「三分钟上手」命令块。第一节主语从内部旧链改为「自己写个脚本读引擎日志」的通用做法，表格保留、补一句话交换口径。**顺带清掉过程口径泄漏**：开头引用块里指向 `skill-token-ledger/scripts/...` 的内部路径提醒删除（该分叉事实仍如实登记于 MANIFEST 第三节与 SKILL.md 对应节，仓内访客向说明挪到卖点条的通用表述）。macOS 措辞如实化：「实测跑通」改「Windows/Linux 在岗实机；macOS 同套启动件＋平台模拟验证」——macOS 无实机，不能混称实测 | 对 git 访客，前 20 行决定去留；卖点要前置、要给人话利益而不是机制描述。同时公开仓不该出现只有我们自己可达的内部路径 |
| `MANIFEST.md` | 本节新增；头部修订口径更新 | 登记 |
| `CHANGELOG.md` | 新增条目 | 登记 |

**分叉登记不受影响**：母本 `resp.read()` 整包缓冲的事实仍在 MANIFEST 第三节（对照表处）与 SKILL.md「与旧 skill-token-ledger 的关系」节，两处未动。

---

### 2.15 README 配真机在岗截屏两张（2026-11-17 · 纯文档，功能代码零改动）

| 文件 | 改动 | 为什么 |
|---|---|---|
| `docs/monitor-hardware.png`（新增） | 真实在岗机器 `/monitor` 截屏上半区（模型状态 + 速度/GPU/PCIe/CPU + 内存/两盘/网卡 + 网卡合计），Edge headless 实拍后按内容边界裁切 | 皮总提议配图说明好处；用真机在岗实拍而非示意图，与「不卖幻觉」口径一致 |
| `docs/monitor-ledger.png`（新增） | 同页下半区（上下文占用 / 最近请求表含合计行 / 对话缓存） | 账本区是「谁在用、用了多少」主张的直接证据 |
| `README.md` | 卖点区后插入两张图＋两句图注（真机实拍口径、深浅主题与 UUID 绑卡口径）；账本图配一句「82% 输入 token 复用 ↔ 解码稳 110+ tok/s」的解读 | 图要带读法，不然访客不知道看什么 |

**脱敏实证（截图前目检＋入仓前复检）**：两图无 8 位指纹（该机无 key 模式，请求表本就无身份列）、无姓名、无 key、无 IPv6/内网地址；画面内出现的均为硬件型号与运行时读数（盘型号、5090、温度、tok/s）。截图为浅色主题（README 静态图无主题跟随，图注注明）。原始全页截图留存于本机 `D:\Strata\.workbuddy\shots\`，不入库。

---

### 2.16 rev9：CPU 卡标题带型号（2026-11-17 · 功能改动 · 三套全绿）

| 文件 | 改动 | 为什么 |
|---|---|---|
| `monitor_ext.py` | 新增模块函数 `cpu_name()`（注册表 `ProcessorNameString` / `/proc/cpuinfo` model name，纯标准库）；`Sampler` 新增 `_cpu_name` 一次读取缓存；`_sample()` 在 `cpu_mhz` 块**之外**（两平台通用）出 `out["cpu_name"]`；失败/空 → 字段缺席 | 皮总要求 CPU 卡标题带型号；与任务管理器显示同源；缺 psutil 时整组扩展数据降级属既有边界 |
| `monitor.js` | `renderCpu` 顶部构 `cpuLabel`（`CPU · esc(cpu_name)`，无字段保持 `CPU`）+ `setCpuTitle`（查 `.mx-label-t` 幂等刷新）；两分支 `ensure(...)` 外包 `setCpuTitle(...)` | ensure 只在首建写标题，ext.json 晚到需补写；esc 走转义链（型号名可含任意字符） |
| `selftest_monitor.py` | 冒烟 stub ext 喂 `cpu_name: "Smoke CPU Model <x>"` + `cpu_mhz`；新增两条断言（标题两分支逐字节＋幂等刷新在位＋裸标题 `cardHtml(id, "cpu", "CPU",` 永不复活反例守卫；采样端四源锁）；当次 **52/52** | 锁终态＋防旧形态回魂 |

**在岗换脑实况（如实登记）**：三文件已同步在岗位（cmp 字节级一致）；第一轮 `switch_proxy.py` 读到 2 条 ESTABLISHED idle 连接 → 硬拒绝未 force。第二轮（17:41，操作会话处工具段、无在飞生成的安全窗）`--force` 切换成功：1.52 秒回岗、新 pid 38164、`/health` 200；`/ext.json` 出 `cpu_name: "AMD Ryzen 9 7950X 16-Core Processor"` + `cpu_mhz` 正常。前端实拍复核：CPU 卡标题 `CPU · AMD Ryzen 9 7950X 16-Core Processor`，一行不撑。README 硬件区截图同步刷新（commit 8ccba89）。

---

### 2.17 rev8 后补五：省钱口径入 README + 价表 csv 补入仓（2026-11-17 · 纯文档/数据，功能代码零改动）

背景：皮总指出本地算力用户最核心的一句话＝「想知道自己用了多少、相比接入 API 省了多少钱」，且本机网页报表早已内置省钱计算器。自查：该功能在 README 卖点区**完全没提**（藏在 html_report 实现里）；且 `html_report.py` 注释「见 api-price-table.csv」是**悬空指针**——csv 从未随包，002 拉到的是指向空气的引用。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `api-price-table.csv`（新增） | 价表随包（22 款模型公开牌价，含各家出处、峰谷/分档备注；与 000 在岗 csv cmp 字节一致） | 销掉悬空指针；计算器数字的出处必须可查 |
| `docs/savings-calculator.png`（新增） | 网页报表近 30 天折算实拍：GPT-6 Astra $5,600（≈¥39,300）～最便宜可比 $29（≈¥205）；账本两行口径与 KPI 在图上不含身份列 | 省钱是本地算力叙事的核心卖点，图比文字有力；实拍不示意 |
| `README.md` | 卖点区新增「想知道省了多少钱，一键算」条目（排第二条，紧跟账按人算）；第四节命令块后加计算器导读段＋配图 | 用户最关心的事不能在 README 里缺席 |

**脱敏实证**：csv 全部为公开牌价与厂商官方页出处，0 处内部数据；截图裁切区为价格折算表＋通用 KPI 条（请求数/解码 tok/s/tokens 总量），无人名、无指纹、无 key、无 IP。截图生成于临时合并盒（`calcbox`，35 天旧链+新链账本合并出表），在岗 `data/` 未动。

### 2.18 rev8 后补六：README 边界条改写＋看护声明补核对出处（2026-11-17 · 纯文档）

背景：皮总两点质疑。①「官方壳自带引擎看护」是否属实、有没有和上游核对过——此前确实未核对过，本轮补核：本机 `D:/Strata` 即上游仓（github.com/Niko1221/Strata），HEAD 钉 tag `v0.2.6`，用 `git show HEAD:serve/server.py` 读 pristine blob（工作区 1700+ 行本地改动均未提交，不构成干扰）。官方 blob 实有 `restart(tries=3)`、`RESTART_RETRY_S=15.0`、`ENGINE_SILENCE_S=300.0`（#481）、#1317 quick watchdog 注释、官方跟踪的 `test_fatal_recovery.py`/`test_restart_waiters.py`/`serve/lifeline.py`。声明属实，README 该句补上出处口径。如实窄口径：origin/main 领先基线数百 commit，GitHub 通路当时 502 未核——README 所述针对包所依赖的发布基线，成立。
②「非流式长请求仍会静默」列为本包边界不当——本包定位＝对体验零改变、只加细粒度记账；长生成期连接无字节是**非流式协议本性**，不接反代同样存在，不应进本包代价清单。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `README.md` 第九节第 2 条 | 改写为「不改变任何使用体验＋协议物理现象不归本工具背」口径；≥600 秒读超时建议保留但定性为对所有链路成立的环境建议 | 边界清单只登记本工具引入的代价，不替协议本性背锅 |
| `README.md` 第八节看护划界段 | 补「已对上游核对属实」＋pristine v0.2.6 的具体符号名与 issue 号 | 声明可核、出处随身 |

功能代码零改动。

### 2.19 rev10：排队闸 v3——网关侧对话请求 FIFO 准入闸＋SSE 等待心跳（2026-11-17 · 功能改动 · 三套全绿）

背景（决策输入件 `gate-v3-design-2026-11-17`，票 `2026-11-17-ledger-gate-v3`）：Strata 引擎并行模式准入环节无闸、无 FIFO 序，多请求并发时会话降成龟速（实测双满每行 ~32 tok/s vs 独行 ~110）。缺口在网关补：反代是唯一能看见全部入栈请求的中立层，不给引擎源码再背调度器补丁。**红线三条**：不引入任何拒绝态（429 重试风暴事故实证在先）；闸只推迟新入口、绝不触碰在飞请求；缺省 `max_inflight=0`＝行为与 `9bfcf0d` 字节级一致。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `collector_proxy.py` | 模块级 `GATE_DEFAULTS=(0,10.0,600.0)`；新增 `Gate` 类（`threading.Condition`＋FIFO `deque`＋计数；`acquire` 快路直取/排队路只有队首可取位/等满 `gate_wait_s` **超时强放照样转发**；`release` 把空位**直接移交队首**防新到者截胡；`snapshot` 五键）；`_gate_params(cfg_path)` 每对话请求重读一次 config（改阈值不重启，坏值按缺省）；`main()` 挂 `Handler.gate`/`Handler.cfg_path`；`do_POST` 对话分支在 body 定型后、`urlopen` 前挂闸（`responded`/`truncated` 初始化纯位置前移），整段转发包进 `try/finally`——`finally` 是槽位归还唯一出口；新增 `_start_gate_chunked`（心跳承诺：替排队中的 SSE 请求先发响应头，形状同 `_start_chunked`）与 `_write_gate_hb`（`: ping` SSE 注释帧走 `_pump` 同款 chunk 帧格式，写失败只 `close_connection`）；转发段 `gate_headers_sent` 三态适配（头已上线→不再发头直接 `_pump` 接引擎真实流；客户端称 stream 而上游回非 stream→定长体重新分帧泵进已开 chunk 流）；异常路径零改动（`responded` 语义天然覆盖「心跳后上游 HTTP 错误→不写第二响应」）；账本新增 `queue_wait_ms`（等待过才写，未等待字段缺席）；`_push_gate` 观测推送三调用点（acquire 返回后/release 后/心跳计数后），monitor_ext 无通道即静默 | 排队不拒绝＝最坏情况回到现状；一次响应原则（RELAY CONTRACT §4）是心跳设计的第一约束 |
| `monitor_ext.py` | 新增 `push_gate(state)`/`get_gate()` 注入通道（`_GATE_LOCK` 保护，push 附 `_at` 时刻，任何异常吞掉）；`Sampler._sample()` 在 push 新鲜（≤30s）时出 `out["gate"]`（五键 `inflight/queued/limit/waited_total/beat_total`）；闸从未启用＝`gate` 字段整体缺席（现有前端与 selftest 天然兼容）；`start()`/`answer()`/路由表/`SAMPLER` 零改动 | 观测走既有注入通道，绝不影响记账 |
| `monitor.js` | 新增 `renderGate(ext)`（`data-mx-section="gate"` 独立区，享受 ensure/pruneSection 分区纪律）：`queued==0`（含字段缺席）→ 不渲染＋清旧卡——防与引擎原生 queued 语义混淆；`queued>0` → 「等待中」卡，小字「网关等待 · 在飞 N/max」；`tick()` 两挂点（ext 在→`renderGate`；ext 断→本区 prune）；不新增波形历史桶，`renderState`（引擎原生 queued 文案）零改动 | 两语义分卡分文案，互不混淆 |
| `config.template.json` | `force_include_usage` 后新增 `"max_inflight": 0, "queue_beat_s": 10, "gate_wait_s": 600`（缺省全关）；comment 追加排队闸口径段（含义／改值即效／永不经闸路径清单） | 缺省零回归从模板起 |
| `selftest_proxy.py` | 二阶段：原 15 组断言（**逐字零改动**）跑完＝缺省零回归面；读 `/ext.json` 无 `gate` 键；随后同 cfg_path 重写 config（`max_inflight=1, queue_beat_s=0.4, gate_wait_s=1.0`）重启 proxy 跑 9 组 `gate:` 断言——判据②第二请求拿上游真实响应、判据③SSE 心跳先于真实流（`data:` 帧完整＋`[DONE]`＋单一状态行）、判据④等满照样转发、判据⑤FIFO 到达序、判据⑥故障注入 inflight 归零（500/ssebreak/客户端断 三读数 [0,0,0]）、判据⑦非对话路径开闸满位与关闸两组读数均不变、判据⑧`queue_wait_ms` 等待行在场/未等待行缺席、gate 段五键形状。stub 新增 `hold` case（`HOLD_GATE` 事件逐个放行）。当次 31/31 | 判据全部机械化 |
| `selftest_monitor.py` | H-1 态甲（主理人裁定纳入闭集）：新增独立 node 行为冒烟——ext stub 喂 `gate` 段三态（字段缺席→无卡；`queued=2`→卡出现且文案含「网关等待」；回到 0→卡被 prune）；既有 52 组断言逐字零改动。当次 54/54 | queued=0 不渲染的**行为**保证不能只靠静态 grep |
| `README.md` | 第八节补排队闸使用口径段；第九节新增第 9、10 条边界（心跳承诺后上游 HTTP 错误降为流内/流断形态，账本 `error` 如实登记；非流式排队全程静默） | 边界不许粉饰 |

**契约不变量核验**：`_pump` 帧语义、`_start_chunked`/`_send_fixed`/`_pass_post`/`do_GET`/`_read_body`/`_forward_headers`/`_clean_headers` 本体零改动；账本既有字段语义与写入条件零改动（新增字段仅 `queue_wait_ms`）；RELAY CONTRACT §1–4 未回归（`grep -cE '(429|409)' collector_proxy.py` ＝ 0）。`ledger_watchdog.py`/`switch_proxy.py`/引擎侧/在岗位零触碰。三套回归当次：proxy 22→31、monitor 52→54、watchdog 16 不变。

**文件数不变**（本轮无新增/删除文件，仍 35 个）；`selftest_monitor.py` 描述行按 2.19 口径理解为含 gate 行为冒烟。**在岗同步属票后置动作**（安全窗口由主理人另排；本机在岗首值 `max_inflight: 1` 属换脑窗口口径，不在本票执行）。

### 2.20 rev10a：排队闸 v3 维护小批——入队观测即时可见＋死字段注释＋票面勘误登记（2026-11-17 · 观测时效修复 · 三套全绿）

背景（票 `2026-11-17-ledger-gate-v3-rev10a`，决策输入件＝QA 对 rev10 双重审计三项建议）：QA C3 探针实测 `queued_seen_in_ext=0`——请求入队后、首个 `queue_beat_s` 心跳前，`/ext.json` 的 `gate.queued` 滞后至多一个心跳周期才可见；另 rev10 票 ②-3 S-5 伪码与 S-8 声明自相矛盾需登记（零代码·仓外勘误件）；`Gate.queued` 死计数需就近注释。**红线三条沿 rev10**：无拒绝态；不触在飞；缺省 `max_inflight=0` 行为不变。闸语义零变化，纯观测时效修复。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `collector_proxy.py` | E-2：`Gate.acquire` 入列与等待内环拆两段临界区——入列段（快路判断＋入列＋局部标志 `enqueued_now`）退出锁后、首次 `_cond.wait` 前**锁外** `_push_gate` 恰一次（与 `on_beat` 同纪律），等待内环重新进锁；快路不入列不 push、每次 acquire 至多一次入队 push、既有三处 push 调用点内容零改动、`_last_limit` 时序依赖不变（`do_POST` acquire 前已 `_gate_params`）。E-3：`Gate.__init__` `self.queued = 0` 行就近注释（display truth via `_waiters, do not read this field`；`snapshot` 的 `queued` 键用 `len(self._waiters)` 实时值），语义零改动 | 入队瞬间即推＝消除观测滞后至多 `queue_beat_s` 的损失（QA C3 根因）；持锁不得做 monitor 侧推送 |
| `selftest_proxy.py` | T-2 新增 gate 组断言 `gate:queued visible in ext before first beat`：每请求重读 config 调 `queue_beat_s=10.0`/`gate_wait_s=8.0` 不重启→hold 占满唯一槽→第二请求入队→3s 轮询 `/ext.json` 见 `queued>=1` 记 `t_seen`→断言 `t_seen < 10.0`（修复前判红＝首 push 点在 10s 心跳；修复后典型读数 ≈1–2s）→`HOLD_GATE.set()` 收尾→cfg 恢复 gate 阶段值。既有 15＋9 组断言逐字零改动。当次 32/32 | 判别力对修复前判红成立（QA boxA 实跑坐实），观测时效修复须有机械守卫 |
| （仓外）`rev10-gate-v3-erratum.md` | E-1 勘误登记件落治理族 `D:\Strata\.workbuddy\collab\tickets\`：登记 rev10 票 ②-3 S-5 伪码（`_gate_beat` 未置 `responded = True`）与 S-8 声明矛盾；实现事实（81783d5 已置位）＝必要纠正；rev10 票本体 append-only 不回改 | 照票复建者须以登记件为准，勿照 S-5 字面省略 `responded = True`（否则违 RELAY CONTRACT §4 第二状态行） |

**验收读数（票③七条）**：闭集 diff 外零文件；proxy **32/32**（31＋新 1）、monitor **54/54**、watchdog **16** 不变；`grep -c '^PASS  gate:'`＝10；`_push_gate` 实得 5 行＝def 1＋调用 4（新调用在 acquire 两段临界区之间·锁外）；死字段注释 grep 命中同行；红线机检 `grep -cE '(429|409)' collector_proxy.py` ＝ 0；勘误件在场含双锚点。

### 2.21 rev11：排队闸跟随引擎实际并发——闸阈值从网关自填值改为上游引擎运行时读数（2026-11-17 · 功能改动 · 三套全绿）

背景（票 `2026-11-17-ledger-gate-follow`，决策输入＝人类 21:08 裁定「网关不需要自己创造，就看 Strata 实际的启动配置就好了」〔INTK-0001〕＋20:56「按 2slot 守住关卡」裁定＋人类 21:18 补令「主要是测试第3路不会被误杀，一定有心跳机制通讯保活」）：rev10 的闸上限 `max_inflight` 是人在网关侧另填的数，与引擎运行时实际并发（显存 `fit_parallel` 降级、引擎自调 `batch_slots` 都会改它）存在两处填数漂移风险。本轮加开关 `gate_follow`（缺省 false＝与 `e791a75` 行为一致）：置 true 后闸的有效 limit 取引擎 `/v1/status` → `concurrency.serving` 运行时读数（后台 daemon 线程周期 GET、缓存于模块级单写元组，对话热路径只解引用缓存——零新增上游同步调用、零新增锁）。读数不可得按回退链：最后成功值（无限期）→ 静态 `max_inflight` 兜底 → 0 关闸；无「临时全通」档。**红线五条沿 rev10 加读数 GET 旁路**：无拒绝态；不触在飞（跟随下调不回收）；缺省零回归；热路径零新增打点/零新增锁；读数 GET 不经闸不进账本。**验收重心＝防误杀族**：满队列第 3 路流式请求经 `: ping` 心跳保活端到端拿到上游真实响应、全程不断连不误杀。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `collector_proxy.py` | F-1 `FOLLOW_DEFAULTS=(False,5.0)`；F-2 模块级 `_engine_reading=None` 单写元组缓存（唯一写者＝gate-follow 线程；整体重绑 GIL 原子；读侧无锁）；F-3 `_engine_status_fetch(cfg)`：`GET {upstream}/v1/status` 超时 5.0s，成功判据＝200＋JSON＋`concurrency.serving` 存在且 `int>=1`，任一不满足返回 None 不抛异常（鉴权与 `do_GET` 同口径）；F-4 `_follow_loop(cfg_path)` daemon 线程（挂 `main()` `reporter.start()` 后）：每轮 try 外先绑 `poll_s` 缺省值（D2 修·QA 探针B：首轮 config 异常不 NameError 线程死）＋函数体首行 `global _engine_reading`（D1 修·QA 探针A：缺 global 写被判局部→先读后写异常被自身 except 吞→跟随静默失效）＋poll_s 坏值钳缺省/下限钳 0.5s＋follow 假时零上游请求仅重读 config（改开关不重启）＋值变化记 `ledger-service.log` 一行＋读数失败缓存不动（回退链第一级）＋异常吞掉线程永不死；F-5 `_gate_params` limit 决定处：读得的 int 改名 `static_limit`，follow 真时 `limit = r[0] if r is not None else static_limit`，假走原路径；`_last_limit = limit` 照旧＝监视页 limit 动态化的全部所需（R-5 零改动链路）；F-6 acquire 内 limit＝进闸时刻快照（登记，代码不变）；F-7 回退链汇总 | 引擎改并发闸自动跟随，人不用两处填数；缓存单写读侧无锁＝热路径零新增锁（红线四）；回退无全通档＝不违 20:56 裁定 |
| `config.template.json` | `gate_wait_s` 后新增 `"gate_follow": false, "gate_follow_poll_s": 5`；comment 追加跟随口径段（含兜底建议与缺省行为说明） | 缺省零回归从模板起 |
| `selftest_proxy.py` | T-0 stub `do_GET` 新增 `/v1/status` 分支（`STATUS_MODE` good/broken＋`STATUS_SERVING`＋带锁 `GET_STATUS_HITS` 计数；既有 GET case 零改动）；T-2 跟随 5 断言（`gate:follow off by default never polls status` 缺省态 hits=0／`gate:follow boot fallback to static max_inflight` 读数不可得回退用静态 1 不用假引擎值 2／`gate:follow limit tracks engine serving` ext `gate.limit` 1→2 跟随引擎值（监视页动态化行为证）／`gate:follow last-good on status loss` 读数丢失后 ext limit 仍＝最后成功值 2 非静态 1／`gate:follow poll bypasses gate and records nothing` 闸满窗口内 hits 增长而账本行数增量 0）；T-4 防误杀 4 断言（v4 钉态：共用 cfg `gate_follow:false` 固定数值闸态＋stub 显式 good＋组首清 hits 基线——族验排队＋心跳闸本体语义，与 limit 来源正交）：`gate:3rd stream survives full queue with heartbeats`（第 3 路流式排队收 ≥2 帧带时间戳 `: ping`、首帧 ≤0.8s、单一状态行不断连、空位后收全 8 帧 SSE 真实响应、账本行 `queue_wait_ms>=400` 无 error）／`gate:in-flight pair rate unaffected by queued 3rd`（在飞两路各自完整收尾且耗时 ≤ 基线+1.0s）／`gate:queued drop after heartbeat releases slot clean`（排队中心跳期客户端强断：不 crash、在飞不受染、终态 inflight=0 queued=0 无幽灵占位、账本行如实在场）／`gate:3rd non-stream waits out gate_wait_s and forwards`（非流式静默排队等满照样 200 转发真实响应体不拒）；调参断言全部自恢复 cfg。既有 32 断言（22 基础＋10 gate 组）名称表达式 stub 行为逐字零改动。当次 41/41 | 八组红面逐条对应五红线与补令子项；防误杀族＝验收重心（人类 21:18 补令）；引用归组三条（heartbeat before slot / expiry forwards / no slot leak）零改动计入族 |
| `README.md` | 第八节补「闸跟随引擎并发」用法口径（两键含义＋在岗建议 `gate_follow:true` 保留人类已裁值兜底＋改键即效）；第九节新增第 11、12、13 条边界（轮询时延＋进闸快照／下调瞬间在飞可超新 limit 不回收／回退次序含 fit_parallel 降级衔接句「跟随运行时值是 21:08 口径正常结果，非违 20:56」） | 边界不许粉饰；防后续读者误判跟随违背并发裁定 |
| `MANIFEST.md` / `CHANGELOG.md` | 本节＋rev11 条目 | 登记 |

**契约不变量核验**：`Gate` 类本体（`acquire`/`release`/`snapshot`/等待环/心跳路径）零改动——`git diff e791a75 -- collector_proxy.py | grep -cE '^[+-].*(def acquire|def release|def snapshot|self\._waiters|self\._cond|_gate_beat|_start_gate_chunked|_write_gate_hb)'` ＝ 0；`monitor_ext.py`/`monitor.js`/`monitor.html`/`monitor.css`/`selftest_monitor.py`/`ledger_watchdog.py`/`switch_proxy.py`/`selftest_watchdog.py` 零触碰；账本字段面零新增字段；`_pump`/`_start_chunked`/`do_GET` 转发本体/`_pass_post`/RELAY CONTRACT §1–4 零改动。热路径锁计数逐值不变：`threading.(Lock|RLock|Semaphore)`=1、`threading.Condition()`=1；`urlopen` 3→4（新点＝`_engine_status_fetch` 体内唯一新增）；红线一机检 `grep -cE '(429|409)'`＝0。三套回归当次：proxy 32→**41**、monitor **54/54**、watchdog **16 passed 0 failed**。**文件数不变**（无新增/删除文件）。**在岗动作属票后置**（`config.json` 加 `gate_follow:true` ＋换脑窗口由主理人另排，不在本票验收面）。

### 2.22 rev11a：排队闸跟随形态回流——读数源从引擎运行时轮询改为启动配置文件定死值（2026-11-18 · 口径变更回流 · 三套全绿）

背景（票 `2026-11-17-ledger-gate-follow-rev11a`，效力来源＝人类 23:13 裁定 INTK-0003 逐字「引擎侧自己往下压和网关有什么关系？网关只负责卡住上限，引擎自己爱干什么干什么！」＋00:31 续话 INTK-0004「难道这个数字启动之后还会变吗？只要 Strata 启动一次没有死掉就不用重读啊！」）：rev11 的 R-2 读源（后台线程轮询 `/v1/status` 读运行时 `concurrency.serving`）被 23:13 裁定替换——那是引擎内部降级事务，越出网关「卡上限」职权。本票续工改造 db87ddd 现头（非回退重开）：跟随的有效 limit＝`strata_config` 所指 Strata 启动配置文件顶层 `"parallel"` 定死值；每请求仅一次 `os.stat`，`(st_mtime_ns, st_size)` 守卫命中用缓存（零 open 零解析），变了才重读——改文件保存即效、无需重启（00:31 口径：数字启动一次定死不重读；守卫≠被禁的引擎运行时读数缓存）。失败态两态同一条＝缓存作废＋当请求退 `max_inflight` 静态兜底（不沿旧值、不缓存坏值）。回退链收缩两级。**红线五条**：无拒绝态；不触在飞；缺省零回归（基数锚 db87ddd，除 X-4 明列作废三条外全部原样通过）；热路径零新增上游调用零新增锁（跟随态亦零上游 GET，每请求一次 os.stat ~4µs）；裁定落实＝轮询系六项 grep 归零（`_follow_loop`/`_engine_status_fetch`/`_engine_reading`/`gate_follow_poll_s`/`global _engine_reading`/main() 挂点）。**验收重心不变＝防误杀族③-13~17/T-4 四断言零改动**（limit 来源与等待环正交）。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `collector_proxy.py` | X-1 拆净 `_engine_status_fetch`/`_follow_loop`/`_engine_reading` 声明注释/main() `gate-follow` 线程挂点；X-2 `FOLLOW_DEFAULTS` 整删（缺省 False 由 `c.get("gate_follow") is True` 承载，poll 键消费体已拆＝留之即死码）；X-3 `_gate_params` follow 分支重写＝两级回退（文件读数→静态兜底），last-good 档作废；A-1 `_strata_parallel_parse(path)` 纯解析 helper（int≥1 取原值不钳制＝钳制归引擎 A-4；False/None/缺席/bool/非 int/负→1＝引擎单发语义 `server.py:3594-3602` 实证；一切读失败 None 不抛）；A-2 `_strata_parallel_limit(c)`＋模块级 `_strata_parallel_cache=(path,(mtime_ns,size),limit)`——函数体首行 `global _strata_parallel_cache`（B-1 修·rev11 D1 同族坑第二次·教训注释就近登记）、`os.stat` 抓 `except Exception`（NUL 路径抛 ValueError 非 OSError 族·QA 探针实证）、守卫命中零 open 零 parse、stat/解析失败＝缓存作废退静态、无锁纪律＝单名整体重绑元组（GIL 原子）并发 miss 重复解析幂等；A-3 注释＝`max_inflight` 仅两用途（follow 假固定值＋follow 真读失败兜底，在岗两值同填人类已裁数 2）；顶部 `from paths import expand_path`（paths 本就是硬依赖） | 网关只卡启动配置上限（23:13 字面执行）；mtime 守卫贴 00:31「不重读」且消掉纯启动一次形态的换脑滞后窗口（票裁 A-2 三条理由在册）；无文件 last-good＝事故退兜底比沿旧值可解释 |
| `config.template.json` | 删 `"gate_follow_poll_s": 5`；`gate_follow` 后新增 `"strata_config": ""`；comment 跟随段整改写（含「rev11 运行时轮询读法已废」如实登记＋mtime 守卫口径＋兜底建议） | 缺省零回归从模板起；不留死键 |
| `selftest_proxy.py` | X-4 作废三断言逐名删除登记（`gate:follow limit tracks engine serving`/`gate:follow last-good on status loss`/`gate:follow poll bypasses gate and records nothing`——对象＝R-2 作废面，非断言质量缺陷）；X-5 stub `/v1/status` 分支降形＝只计数＋回固定值（保留理由＝③-4 判据证据面·票裁 A-5），`STATUS_MODE`/`STATUS_SERVING` 声明与非 T-4 消费删除，**T-4 组头钉态行保留原样**（②-2 禁动面·v3 C-1 写死；删声明后成无害死写）；K-1 `gate:follow boot fallback to static max_inflight` 改体留名（`strata_config` 指不存在路径替代 STATUS_MODE 机制，主张不变）；A-4 新断言 `gate:follow limit from strata_config parallel`（文件 1 vs 静态 2 判别＋改写文件 mtime 守卫失效 ext limit 1→2＋第四请求守卫命中恒 2）＋`gate:follow file failure falls back to static`（缺文件退静态 1＋运行中改指坏 JSON 读数仍 1＝坏值不入缓存）；A-5 `gate:follow on still never polls upstream`（跟随组全程 stub hits=0）；T-4 防误杀组零改动 | 新三断言承接作废面行为验证；③-4 判据机械承载；防误杀族＝验收重心零降级 |
| `README.md` | §八 跟随段改写＝文件读形态口径（「不跟、不问」字面＋缓存≠「不缓存」禁语的区分句就近写明）；§九 11/12/13 改写（11＝mtime 守卫即时性＋进闸快照不变；12＝沿原文含文件改小；13＝两级回退＋「引擎往下压网关不跟＝设计语义非缺陷」换写句＋中途不可读事故退兜底补句） | 边界不许粉饰；防「不缓存」禁语误读自相矛盾 |
| `MANIFEST.md` / `CHANGELOG.md` | 本节＋rev11a 条目（根因段如实登记 R-2 被 23:13 裁定替换·INTK-0003 指针逐字引用，不粉饰不静默覆盖） | 登记 |

**验收读数（票③逐条）**：闭集 diff 外零文件；proxy **41/41**（41−3＋3）连续三跑稳定、monitor **54/54**、watchdog **16 passed 0 failed**；`grep -c '^PASS  gate:'`＝**19**（10＋防误杀 4＋保留跟随 2＋新增 3）；作废三名输出归零；`urlopen`＝**3**（回 e791a75 基线）、`v1/status`＝0、`threading.Thread`＝**1**（回基线）、`global _engine_reading`＝0、六名复合 grep＝0、`gate_follow_poll_s`（代码）＝0；锁计数逐值不变 Lock=1/Condition=1；缓存面落位 `_strata_parallel_cache`≥1/`_strata_parallel_limit`≥2/`st_mtime_ns`≥1/`global _strata_parallel_cache`≥1/float `st_mtime` 禁语＝0；新断言两枚 PASS＋boot fallback 仍 PASS（改体留名）；防误杀族四名 PASS＋族面 diff 零行；Gate 本体零改动；红线一机检 `(429|409)`＝0；模板落位 OK；README `gate_follow_poll_s`/`fit_parallel`/`最后一次成功读数` 三枚归零＋「不跟、不问」≥1＋CHANGELOG `23:13`/`INTK-0003` ≥1 各。**文件数不变**。**在岗动作属票后置**（删 `gate_follow_poll_s`＋加 `"strata_config": "D:/Strata/strata-unsloth-ud-iq4_xs.json"`＋换脑窗口主理人另排，不在本票验收面）。

### 2.23 rev12：排队闸拦截事件独立日志——每个入栈请求留「核实在飞＋放行决策」证据（2026-11-18 · 功能新增 · 三套全绿）

背景（票 `2026-11-18-ledger-gate-log`，效力来源＝人类 08:02 逐字 INTK-0005「如果真实出现了拦截，我希望你能够做成独立的日志」＋08:04 补令（续 INTK-0005）「让我能够确定，你对每次入栈请求都做到了核实在飞进程并决策是否放行，不要和记账日志放在一起」）：拦截可见性此前全押观测快照面（ext.json push＋总账 `queue_wait_ms` 字段），事件流面缺席——快照答不了「拦了几次、拦了谁、等了多久、有没有被强发」，也证不了「每次入栈都核实过在飞并做过决策」。本票只加观测输出，闸语义零变化。

**事件行字段闭集（写死·禁增禁减·禁记请求体内容）**——文件 `data/gate-events-YYYY-MM-DD.jsonl`，Recorder 按天分文件同总账机制：
- `admitted` 行＝`{ts, event:"admitted", route, model, key, fp, limit, stream, inflight_at_decision}`（快路直放；`inflight_at_decision` < limit＝「核实到有空位才直放」）；
- `queued` 行＝`{ts, event:"queued", seq, route, model, key, fp, limit, stream, inflight_at_decision}`（进闸瞬间；读数 ≥ limit）；
- `released` 行＝`{ts, event:"released", seq, route, model, key, fp, limit, stream, waited_ms, heartbeats, forced}`（放行/强发时刻；`seq`＝queued/released 互查键；`heartbeats`＝实发帧数口径；`forced`＝等满 `gate_wait_s` 强发可辨识）。
`key`/`fp` 与总账同款口径（密钥标签/指纹，非请求内容）。`event/seq/inflight_at_decision/heartbeats/forced` 禁入 `requests-*.jsonl` 键面（红线六·补令字面）；总账 `queue_wait_ms` 保留不动、双写互证、事件日志＝拦截/决策查证权威源（票裁 A-4）。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `collector_proxy.py` | G-0 `Recorder.__init__` 加 `prefix="requests"` 默认参＋`self.prefix`＋文件名 f-string 参数化（默认值使既有 `Recorder(out)` 调用逐字节同形）；G-1 `Gate.acquire` 尾参 `on_event=None`（返回类型仍 `-> int`）＋局部量 `forced/beats/enq_at/fast_admit/adm_at`＋**锁内决策读点**（快路 `adm_at = self.inflight` 在 `inflight += 1` 前；入队 `enq_at = self.inflight` 同锁内）＋快路出锁发 admitted 后 `return 0`（②-2 唯一允许语义触碰：返回值/条件/零等待不变）＋入队 off-lock queued 挂点（rev10a push 同刻同纪律）＋expired 分支 `forced = True`＋`on_beat()` 成功返回后 `beats += 1`（实发口径）＋返回前 off-lock released 挂点；三挂点全 `except Exception: pass`；G-2 `Handler.gate_rec` 类属性＋`tag, fp = key_identity(...)` 上提复用（try 块内原调用删除，同请求值逐位相同）＋`_gate_event` 闭包装配闭集字段；G-3 main() `Handler.gate_rec = Recorder(out, "gate-events")`（构造不建文件＝闸关零文件零新字节） | 08:04「核实在飞」落点＝读数与判定同一临界区，禁出锁补读污染；off-lock 纪律沿 rev10a；冻结 token 面 `-w` 口径 ±行＝0 |
| `selftest_proxy.py` | K-0 新标记键三枚 `KEY_GE1/KEY_GE2/KEY_GE3`（＋FP＋cfg2 三行 label；禁复用 KEY_FAST/KEY_WAIT/KEY_3RD——QA 票前审 D-1 断言 23 撞计数案）；H-0 `gate_events(tmp)` helper＋`GEV_FIELDS`/`GEV_SEP_KEYS` 闭集常量＋`import glob`；G-C `gate:gate-events no file with gate off`（T-1 全程闸关零文件＋总账在场对照）；G-A `gate:gate-events queued line visible while still queued`（排队中 queued 行已在盘＝进闸即写行为证＋读数 1/1＋route 去 query 值＋总账 scan 无决策键＋released seq 吻合/forced False/heartbeats≥1/waited≥400；收尾 cfg 自恢复）；G-B `gate:gate-events forced line on gate_wait_s expiry`（非流式强发 forced True/waited≥900/heartbeats=0/stream False/行序 queued<released）；G-D `gate:gate-events admitted line carries decision reading`（专用 KEY_GE3 直放留痕 0/1＋无 queued/released＋闭集＋总账 scan）；既有 41 断言零改动零作废；T-4 防误杀族零改动 | 验收重心族③-13＝每次入栈决策可查证；键专用防计数污染 |
| `README.md` | §八 新增「排队闸拦截事件独立日志（rev12）」段（三形态＋决策证据口径＋分离红线＋双写互证＋**不记请求体内容**隐私口径＋heartbeats 实发 vs beat_total 应发不混读＋缺省零回归＋写失败沿总账纪律）；§九 新增第 14 条（写失败丢行不毁流不进账本＋无 fd 自愈不粉饰） | 边界不许粉饰；隐私闭集口径登记 |
| `MANIFEST.md` / `CHANGELOG.md` | 本节（含事件行三形态字段闭集全表）＋rev12 条目（发行头 rev12 行） | 登记；08:02/08:04/INTK-0005 指针入 CHANGELOG |

**验收读数（票③逐条）**：闭集 diff 外零文件＝0；proxy **45/45** 两跑稳定（41＋新 4 只增不减）、monitor **54/54**、watchdog **16 passed 0 failed**（两套测试文件 diff 零触碰）；`grep -c '^PASS  gate:'`＝**23**（基线 19＋新 4）；防误杀族四名 PASS＋族面 diff 零行＝0；既有 gate 断言删除行＝0；`urlopen`＝3/`threading.Thread`＝1/Lock＝1/Condition＝1 逐值不变；`(429|409)`＝0；冻结 token（`-w` 口径·v3 扩 `self.inflight <`/`self._seq +=` 两枚）±行＝**0**＋`on_event=None) -> int`＝1；`queue_wait_ms`＝1＋diff ±行＝0＋diff `rec[` 加行＝0；落位 `gate-events`≥1/`gate_rec`≥3/`inflight_at_decision|adm_at|enq_at`≥6；README `不记请求体内容`/`gate-events-`/`核实在飞`、CHANGELOG `08:02`/`INTK-0005`/`08:04`、MANIFEST `rev12` 各≥1。**无新配置键·模板零触碰·文件数不变**。**在岗换脑属票后置**（主理人另排安全窗口；监视页/日报消费 gate-events＝另票）。

### 2.24 rev13：日报补排队闸拦截三指标——`## 排队闸拦截统计` 节四态口径（2026-11-19 · 功能新增 · 四套全绿）

背景（票 `2026-11-19-ledger-gate-daily-stats`，效力来源＝人类 00:19 逐字 INTK-0007「网关日报需要补充报告当前拦截入栈次数，拦截请求的最长等待时间和平均等待时间」）：rev12 事件日志已落但日报未消费（rev12 票④明示「日报消费 gate-events＝另票后置」，本票即该后置票）。日报新增 `## 排队闸拦截统计` 节（落位＝「覆盖窗口」后、「按小时分布」前），三指标＝拦截入栈次数（当日 `gate-events` `queued` 行数）、最长等待／平均等待（当日 `released` 行 `waited_ms` max/mean，ms 取整＋秒一位小数）；四态状态机两态禁混淆：A 有当日事件文件（三指标＋补充观察列 released/forced/heartbeats＋跨日口径标注「N 项等待自前日跨入」）／B 无文件但总账有 `queue_wait_ms` 行→**回填口径**（在岗 11-18 及以前换脑前不产事件文件，逐事件数据不可恢复——同源字段回填＋显式降级标注，非编造）／C1 config 静态关闸→「闸未启用」文案不出数字／C2 开闸（含 gate_follow）无事件→0／—＋「按生成时刻 config 判定、回填历史日时该判定可能失真」诚实标注。`daily_report.py` 纯插入（diff 删除行＝0），`build_report` 签名不变、幂等/skip/`--day`/`--all`/`--reported` 机制零触碰。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `daily_report.py` | G-0 新 helper 两枚（`pct()` 尾后、`build_report` 前）：`load_gate_day(out_dir, day)` 按日读 `gate-events-<day>.jsonl`（Recorder 按 ts 路由＝无需跨文件扫描）＋`gate_section(out_dir, day, req, cfg)` 四态统计（只出聚合量·隐私红线四；缺数据标注缺口不外推·红线五）；G-1 挂点两行（覆盖窗口节尾 `out.append("")` 后）：`out.extend(gate_section(cfg["out_dir"], day, req, cfg))` ＋ `out.append("")`——全部纯插入，既有行零修改零删除 | 三指标＝00:19 已裁口径直译；B 态回填＝A-3（禁编造≠禁回填：同源字段证据＋显式标注）；两态判别证据链＝A-2（文件→总账佐证→config 现值三级） |
| `selftest_daily_report.py` | **新文件**：fixture 驱动回归套（纯标准库、无网络、不起服务、每态临时盒用完即弃），15 断言全 `report:` 前缀——节位／A 态四读数＋跨日计数＋补充列／B 态回填标注＋三指标／C1 文案／C2 零值文案／C1-C2 互斥双向 scan／隐私 scan／幂等 True→False／`--day` force 重写／既有四节序不变（红线一行为证） | 四态＋跨日＋回填＋幂等＋隐私＋节位机械可验收（②-4 N≥14）；独立成文件不入 proxy 套＝A-6（45 断言冻结面不碰） |
| `bootstrap.py` | `REQUIRED` 加 `selftest_daily_report.py`（一行，其余零改） | 新测试套入必需文件清单 |
| `README.md` / `MANIFEST.md` / `CHANGELOG.md` | 日报条目补闸统计节口径一句／本节＋文件清单新行／rev13 节（含 00:19 需求字面＋四态口径＋「在岗 11-18 及以前逐请求闸数据不可恢复→回填口径」登记） | 登记 |

**上线不依赖换脑**（路由件⑧）：A/C1/C2 及 B（fixture 总账）验收全在测试环境；生产闸数据产出依赖换脑自动任务（票外观察面）。网页报表 `html_report.py` 消费 gate-events、监视页闸统计＝仍另票后置。

### 2.25 rev15：监视页排队显示改版——独立「等待中」卡撤销并入状态卡＋汇总行日期口径（2026-11-19 · 人类直令 · 四套全绿）

背景（票 `2026-11-19-ledger-monitor-date`＋人类 13:45 直令与 INTK-0010）：「等待中」独立卡信息量过低——排队信息并入顶部模型状态卡，区分网关队列/引擎队列、有排队时标签带数字；汇总行「自 周二00:21」跨周歧义→至少实际年月日期（写死可锁格式 `YYYY-MM-DD HH:MM`，票 A-1 弃 `toLocaleString`）。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `monitor.js` | `renderState(m, gate)` 增 gate 参：排队徽标任一队列 >0 亮＋带总数（`排队 N`）；标签行三文案「网关队列 N 个在等闸」／「引擎队列 N 个在排队」／「排队 N（网关 a · 引擎 b）」；rev10 `renderGate` 撤销换 `pruneStaleGateCard()`（每 tick 清 `card-gate` 缓存残留）；汇总行 `sinceStr` 格式化 `{weekday,hour,minute}`→`{year,month,day,hour,minute}` | 两队列语义分置（`/ext.json gate.queued` vs `/metrics live.queued`）不混读；旧在岗页缓存防残留 |
| `selftest_monitor.py` | 7c 段 gate smoke 断言改版：独立卡三态永不出卡＋状态卡标签承载「网关队列」字样＋归零回退 idle（断言数不变 54） | 行为守卫随改版反转 |
| `README.md` / `MANIFEST.md` / `CHANGELOG.md` | 闸段监视页口径一句改写／本节／rev15 节 | 登记 |

生效＝同步在岗即生效（`_read_asset` 每请求现读盘），不依赖换脑。

### 2.26 rev16：双后端支持——Basalt 启动配置闸解析＋监视页逐槽状态＋进度条速度表退路（2026-11-19 改动 · 2026-11-21 合仓转正 · 四套全绿）

背景：在岗引擎新增 Basalt（basalt_config.json 形态）后，rev11a 的 `gate_follow` 只认 Strata 顶层 `parallel`，Basalt 形态会被判为「读失败」退静态兜底；监视页对 basalt `/slots`（带 `state` 逐槽）与 `live.max_tokens=None` 两态无呈现口径。

**形态警示（如实登记）**：本 rev 四文件改动直接发生在运行时部署面而非本地仓＝「部署面裸改」窗口实例；2026-11-21 会话对拍发现，按「仓为基底＋仅四较新文件覆盖」合回（禁单向覆盖——部署面当时还缺 9 个仓跟踪文件），备份 `strata-ledger-proxy-BACKUP-20261121`，commit `542eb74`。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `collector_proxy.py` | `_strata_parallel_parse` 双形态：顶层 int `parallel`（Strata，语义沿 rev11a）；无顶层键而有 `models[]` 列表（Basalt）→取各条目有效 parallel 的 **max**，无效条目贡献 1；两形态皆无＝None＝失败态退静态，绝不猜 | Basalt 单显存一轮一脑，在岗条目文件不可判→闸只卡上限（INTK-0003 裁定口径延伸）；失败态语义与 rev11a 一致 |
| `monitor.js` | `renderState` 增 slots 参＋闸态固定行（`state-gate`）：最大并发＋逐槽「读取 n · 生成 n」（basalt）／「运行 n」（Strata `is_processing`）／live 聚合退路＋闸排队＋引擎排队；`fetchSlots()` 2.5s abort；进度条两口径（`max_tokens` 完成度／速度表基线 227 tok/s＝本机 basalt 满载实测 226.9） | 人类 2026-11-19 口径＝闸态一行常驻；两引擎 `/slots` 同路径不同形状，取数与形状解析分离；basalt 不报 max_tokens 时进度语义不谎报 |
| `monitor.html` | `state-gate` 锚点行 | 闸态固定行落位 |
| `selftest_monitor.py` | 闸行三态断言（无 slots／basalt 逐槽／Strata 聚合）54→**57/57** | 三退路各有守卫 |

selftest 2026-11-21 转正复跑：monitor 57/57、proxy 45/45、watchdog 16 passed 0 failed、daily_report 15/15。`gate_follow` 缺省 false 行为不变＝缺省零回归沿例。

### 2.27 仓名/包名更名：strata-ledger-proxy → token-ledger-proxy（2026-11-21 · 决策者拍板 · 四套全绿复跑）

背景：命名评估中「搜索发现性」为最弱一层（旧名无 llm/token/usage 任一搜索词）；决策者 2026-11-21 拍板彻底更名（曾议「保留 strata 蹭主仓热度」口径作废）。

| 改动面 | 内容 | 兼容处理 |
|---|---|---|
| GitHub 远程仓 | `petercham/strata-ledger-proxy` → `petercham/token-ledger-proxy`（API PATCH 2026-11-21） | GitHub 自动重定向旧 clone 链接，老用户不断 |
| 服务示例三件改名 | `strata-ledger.service`→`token-ledger.service`；`com.strata.ledger.plist`→`com.token.ledger.plist`（Label 同步 `com.token.ledger`）；`Strata ledger watchdog.vbs`→`Token ledger watchdog.vbs` | **已装旧自启件的老机器不用动**——旧文件名在旧安装里已复制/挂快捷方式，路径引用自身；仅新装用新名 |
| VBS 解释器变量 | `STRATA_PYTHON` → `TOKEN_LEDGER_PYTHON` | 代码级兼容：旧名 `STRATA_PYTHON` 保留为退路，两旧新机器行为不变 |
| `config.template.json` / `config-examples/*` | `"name"` 改 `token-ledger-proxy` | 在岗 `config.json` 属机器本地文件不随仓改；`name` 键仅展示用途，新旧混用无行为差 |
| `README.md` / `SKILL.md` | clone 地址、cd 目录、自启件文件名、标题区（新标题「Token 账本反代工具（Strata / Basalt 兼容）」——Strata 关键词保留在标题括号内，蹭热与通用化兼顾）；SKILL frontmatter `name: token-ledger-deploy` | 宿主 Agent 按新名加载；旧会话缓存旧名不报错 |
| `ledger_watchdog.py` argparse 描述 / `monitor-sprite.svg` 注释 / `start.bat` 窗口标题 | 旧名→新名（start.bat 保持 GBK+CRLF，仅字节级替换 ASCII 串） | 纯展示文案，零契约触碰 |
| `tickets/` 三张历史票 | **不改**——append-only 证据件，其中 `D:\Projects\strata-ledger-proxy` 路径字样为当时事实 | 历史如实性优先 |
| CHANGELOG/MANIFEST 历史节旧名 | **不改**——历史登记当时事实；仅发行版本表头加更名说明 | 同上 |

功能代码零触碰（除 argparse 描述行与注释）；更名后四套自测复跑全绿（见 2.26 复跑读数口径）。

### 2.28 rev17：看门狗引擎看护——一快捷方式拉起全套（2026-11-22 · 功能新增 · 四套全绿）

背景（人类直令）：看门狗同时看守反代与其后端引擎；当前后端（Strata/Basalt）直接在看门狗配置里声明；Windows 启动目录只留一个看门狗入口即可拉起全套。此前引擎自启挂在独立登录自启链（Strata autostart.bat），与看门狗双入口并存。

| 文件 | 改动 | 为什么 |
|---|---|---|
| `ledger_watchdog.py` | 新增 `read_engine_settings()`（每轮热读：`guard_engine`/`engine_backend`/`engine_launch{cmd,cwd}`/`engine_grace_s`）＋`launch_engine()`（detached 子进程，同反代纪律）＋主循环引擎看护段（独立 try，异常不拖垮反代循环）；upstream 尾端口解析（含 IPv6 括号形制）；启动日志 guard ON/off 两态明示 | 缺省 `guard_engine=false`＝与 rev16 逐字节一致＝缺省零回归沿例；cmd 非法当轮静默关闸＝坏配置不崩循环；grace（缺省 120s）＝模型加载期端口本就关，防重复拉爆显存 |
| `config.template.json` | 四键入模板＋comment 登记（含划界：Strata 官方壳自带 restart，用 Strata 保持 false 勿双看护） | 配置即口径真源 |
| `selftest_watchdog.py` | 16→**31**：看护单测 8＋集成 7（热开闸/拉起/宽限抑制计数=1/宽限后补拉计数=2/反代存活/缺省日志态/日志标注） | 行为面全覆盖 |

划界：引擎带外启动＝看门狗不认领进程所有权、仍按端口探测；Basalt 的 serve 壳自带"壳内引擎"restart，壳进程本身无人看＝Basalt 开 guard；Strata 官方壳自带引擎看护＝保持 guard 关。在岗部署＝config.json 加四键（basalt 形制 cmd 抄 `basalt/run-basalt.bat`）＋启动目录收敛为单入口（旧两条自启链件移出留档，旧 usage 采集链随 autostart 退役——账本已由本包接管）。

selftest：watchdog 31/0、proxy 45/45、monitor 57/57、daily_report 15/15（2026-11-22 本机复跑）。

### 2.29 rev17a：引擎看护首查修复 `last_engine_launch` 0.0→None（2026-11-22 · 缺陷修复）

`ledger_watchdog.py` 看护循环：宽限判定 `now - last_engine_launch < grace` 在进程从未拉过引擎时误吞首查——Windows 快开机时 `time.monotonic()` 起点值小（实测开机后仅 ~85s < grace 120s），看门狗上岗后近两分钟不拉引擎。修＝初值 `None` 显式表达"从未拉过"，首查立即放行；仅约束本进程自拉后的窗口。触发场景＝重启实机验证（01:32 开机→01:33:53 反代补岗→01:34:26 引擎补岗→90s 后就绪；断连窗口≈开机至看门狗上岗 1.5 分钟＝用户报"本地后端连不上"的直接归因）。既有集成断言（宽限内抑制/宽限后补拉）不回归＝watchdog 31/0。单文件改动，配置面/探测面/反代面零触碰。

## 三、如实登记：代码分叉

这套脚本与 5090 工具包里的 `skill-token-ledger/scripts/collector_proxy.py`（母本，260 行）**不是同一份文件**：

- 母本是原型：按 key 归因的能力已有，但转发是 `resp.read()` 整包缓冲，且没有看门狗、日报合并、硬件监控、切换保护、回归自测。
- 本包基于本机实例版（641 行），已修整包缓冲并补齐上述能力，又额外打了 2.1 节登记的那些移植补丁（数量以该表实际行数为准，不写死）。

⇒ **以后改功能要两边对照同步**，不存在单点收口。本包是独立发行版，改它不会自动影响另一台机器上的生产脚本，反之亦然。2026-11-11 轮的归因修复已按此原则两边同步改磁盘，当时两边进程都未重启；此后生产 8080 已于 2026-11-12 20:19 切换到 11-11 修复版并实证生效。2026-11-12 轮又按此原则把看门狗的「端口跟随 config / POSIX 脱离会话」行为两边对齐（生产看门狗进程待主理人交接，见 2.6 节）。

带过来的 5090 母本能力（`force_include_usage`、非 2xx 落账、`--fp` 算指纹、按 key 映射）都保留了，没有丢。

---

## 四、明确没有带过来的东西

| 5090 旧链有 | 本包情况 | 影响 |
|---|---|---|
| 完全不进业务链路 | 做不到，反代天然在中间 | 故障面更大，靠守护进程 + 切换纪律兜住 |
| 断点续读（offset）、断线回放 | 不需要，代理直接截获响应，没有日志可追 | 无 |
| 开机补跑昨天日报 | 改为「服务启动先查一次」，效果等价 | 无 |
| `prefill_tok_s` 字段、并发事件行 | 本链不产生 | 旧数据在网页报表里少一列，日报不受影响 |

---

## 五、交付前验证（由 QA 独立复核）

- 包内全部 `.py` 语法编译通过。
- 在**全新临时目录**复制整包、生成配置、用临时端口跑 `selftest_proxy.py`、`selftest_watchdog.py` 与 `selftest_monitor.py`；三套回归按**实际用例数**报出，不写死历史数字。
- 生产 `usage/selftest_watchdog.py` 单独跑通并按当次实际用例数报出；单独实测生产看门狗新增的自包含 `ports_from_config()`（正常配置 / `[::]:端口` / 坏 JSON / 端口非数字 / 缺 `watchdog_lock_port`）与显式 `--port` / `--lock-port` 优先语义。
- 两个启动夹 VBS 可执行语句与注释全 ASCII、CRLF 换行，命令行含 `--lock-wait 86400`；可由 VBScript 解析（静态检查，不真执行）。
- 2026-11-12 ZIP 为 24 文件，只含 `config.template.json` 不含 `config.json`，`start.sh` 包内权限 0755，`start.bat` 保持 GBK + CRLF；全包（源 24 + 包内 24）真实指纹与真人姓名 0 命中。
- `bootstrap.py --check` 用临时端口配置跑通；坏配置（大写 hex 键、空姓名、同姓名合并、`lock_port == watchdog_lock_port`、空 `key_labels`）确实能报出对应的 fail / warn。
- 全包扫描：所有 `.py` 代码零硬编码（无盘符、无用户名、无 Python 版本路径）；文档以占位方式描述来源，不含真实 key 指纹与真人姓名。
- 伪装 `sys.platform` 为 `linux` / `darwin` 跑路径与端口分支，不崩；缺 `lsof` 时安全降级。
- 确认全程未连接、未占用、未重启生产端口；8080 监听 PID 在交付前后保持一致。
