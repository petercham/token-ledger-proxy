# Token 账本部署工序（token-ledger-deploy）

本文件是部署工序：人类读者与宿主 Agent（WorkBuddy / Claude Code 等）均可按此执行。

> 本文件**不是** Agent 平台意义上的 skill 包（不依赖任何 Agent 平台环境，也不会被 skill 装载器加载）。它只是仓根的通用安装/部署工序文档，命名与 Strata 官方 `INSTALL.md` 对齐。运行时（反代、看门狗、日报）是纯独立进程，对 Agent 平台零依赖——这个依赖方向是刻意设计，不得逆转。人读详解见同目录 `README.md`，文件来源与改动登记见 `MANIFEST.md`。本包自包含：纯 Python 标准库，无数据库、无第三方依赖，Windows / Linux / macOS 通用。

**核心不变量（不得破坏）**：
- 看门狗与服务角色无关——**无论反代模式还是旁路模式，采数进程必须挂看门狗**（5 秒巡检、掉了自动补岗）。
- 流式逐块转发（响应头立即发出、每块到达即 flush）与「切换时有会话硬拒绝、`--force` 不覆盖」是契约，任何改动不得触碰。
- 换版本**只能**用 `switch_proxy.py`，不许手工 kill / 直接起 `collector_proxy.py`。

## 触发条件

用户表达以下任一意图时使用本工序：
- 要在某台机器上部署、迁移、重装、修复「用量账本 / token 账本 / 用量统计」；
- 要按人（按 API key）统计团队 LLM 用量、要每日用量日报；
- 反馈账本掉线、服务随会话消失、切换版本把人弄断、监控页不出卡。

## 第一步：模式判定（先判，再动手）

判定问题只有一个：**这台机器需不需要「按 API key 把用量归到具体人」？**

| 需要归人？ | 选哪个模式 | 独有价值 | 代价 |
|---|---|---|---|
| **要** | **反代模式**（本包主链：`collector_proxy.py`） | 按 key 指纹归人 + 入口流量全貌（502、非法请求、断连都被记进账本）+ 官方 usage 权威计数 | **站在业务链路中间**——它挂了团队就断，必须配看门狗 + 切换纪律一起用 |
| **不要** | **旁路模式**（`legacy/collector_log.py`，读引擎日志，不进业务链路） | 完全不碰业务，零故障面 | 归不了人；并行批处理时数字失真（约 3.9%，见「边界与债」）；需按 `legacy/README.md` 手工配 profile，未一键化 |

两种模式下采数进程都要挂看门狗。旁路模式的本包一键化程度不够，见「边界与债」。

## 第二步：前置自检（三条命令，成功判据都是退出码 0）

以下命令全部在**本包根目录**执行（把整包 clone/拷贝到目标机任意位置即可，包内没有写死任何盘符或用户名）。`bootstrap.py` 只支持这三个参数：

| 命令 | 作用 | 成功判据 |
|---|---|---|
| `python bootstrap.py --init` | 生成 `config.json` 和 `data/`；已存在 config.json 时**不覆盖**，可反复跑 | 退出码 0 |
| `python bootstrap.py --check` | 只读自检：文件齐全、数据目录可写、端口未占用、引擎可连、显卡工具在否、`key_labels` 格式对不对。**不启停任何服务、不发业务请求** | 退出码 0（输出无「不合格」项） |
| `python bootstrap.py --selftest` | 在临时端口、假上游/假数据上跑三套回归自测（反代 / 看门狗 / 监控页），**不碰正在运行的正式服务** | 退出码 0（三套回归全过） |

## 第三步：必问人类拍板项（Agent 不得代拍）

以下四项必须由人类给出或确认后才能继续，Agent 不得自行假设：

1. **`listen`** —— 团队接入端口（例：`0.0.0.0:8080`；要同时接 IPv6/IPv4 写 `[::]:8080`）。只改这一处，看门狗与切换工具自动跟随。
2. **`upstream`** —— 引擎真实监听地址（例：`http://127.0.0.1:8787`）。
3. **日报生成时间** —— `report_hour` / `report_minute`，建议 `0` / `0`（即 00:00）。
4. **是否归人**；要归人则请人类提供各成员 key 并逐个实算指纹：
   ```
   python collector_proxy.py --fp <该成员的key>
   ```
   - 提醒人类：`--fp` 算的是**裸 key**，不要把 `Bearer ` 前缀算进去（会算出完全不同的指纹）。
   - 把结果填进 `config.json` 的 `key_labels`（形如 `{ "01234567": "张三", "abcdef01": "李四" }`，指纹须 8 位小写十六进制）。
   - **指纹逐个核对，不得两个指纹填同一姓名**——合并后历史账本无法从历史数据拆开。

## 第四步：部署工序（按编号执行，每步给出具体命令）

1. **落位**：把整个 `token-ledger-proxy` 目录 clone / 拷贝到目标机任意位置（放哪都行）。
2. **生成配置**：`python bootstrap.py --init`
3. **改配置**：编辑 `config.json`，落实第三步拍板的 `listen` / `upstream` / `report_hour` / `report_minute` / `key_labels`；`out_dir` 默认 `@here/data`；`web_root` 已弃用（监控页自带在 `http://<主机>:<端口>/monitor`，本工具不再向任何外部页面注入脚本；旧配置留着不报错，可删）；`force_include_usage` 保持 `true`（流式强制带 usage，关掉＝流式请求全记成 0 token 且不报错）；`lock_port` / `watchdog_lock_port` 默认 43177 / 43176，一般不动但必须互不相同。路径支持 `@here` / `@pkg` / `~` / 相对 / 绝对；纯相对路径按配置文件所在目录解析。
4. **只读自检**：`python bootstrap.py --check` —— 退出码 0 才能继续。
5. **包体自测**：`python bootstrap.py --selftest` —— 退出码 0。
6. **安装自启件（生产必须，三平台各对应一个文件）**——`start.sh` / `start.bat` 只是前台交互式试跑，关掉终端/SSH 断开服务即消失，**不得用它长期供服务**：
   | 平台 | 装这个文件 | 机制 |
   |---|---|---|
   | Windows | 启动夹里放**指向** `service-examples/Token ledger watchdog.vbs` **的快捷方式**（VBS 留在包目录） | 登录自启 |
   | Linux | `service-examples/token-ledger.service` | systemd `Restart=always` |
   | macOS | `service-examples/com.token.ledger.plist` | launchd `KeepAlive` |

   Windows 启动夹 VBS 带 `--lock-wait 86400`：登录时若旧看门狗仍占着防重复锁，新副本作为热备候补等待、旧看门狗退出后零缝隙接管，不会「another watchdog already runs」后永久退出。

   VBS 按自身所在目录找 `ledger_watchdog.py`，所以**不能把 VBS 复制进启动夹**（目录会变成启动夹、主程序找不到且不报错）；快捷方式不改变脚本真实路径。Windows 的 Python 若不在 PATH，设用户环境变量 `TOKEN_LEDGER_PYTHON` 指向 `python.exe` 全路径。

   启动逻辑只有一条：**先起看门狗，由看门狗把服务拉起来**；绝不在启动脚本里直接 `python collector_proxy.py`。
7. **验收**：按下面「验收判据清单」逐条走一遍，其中在岗确认用 `python switch_proxy.py --check`（只读）。
8. **旧链迁移纪律（从读日志旧链切过来时）**：**并排跑，不要一刀切**——旧链不动，本工具先用临时端口起来跑几天；确认按人统计、日报、监控页都对后，需要历史连续就把旧 `requests-*.jsonl` 拷进新 `out_dir`（核心字段两边一致，混着出报表，无需转换）；选无人跑长任务的窗口，先跑 `python switch_proxy.py --check` 通过后再把团队接入地址切到新端口；旧链先留着随时切回，稳定后再停。回滚 = 接入地址指回引擎端口 + 停看门狗和服务，账本不丢。

## 验收判据清单（浓缩自 README 第五节 8 条）

1. `python bootstrap.py --check` 无「不合格」项。
2. `http://<本机IP>:<端口>/health` 返回 `{"ok":true}`。
3. 用真实接入地址发一轮对话，`data/requests-今天.jsonl` 多一行，`key`（姓名）、`fp`（8 位码）、`prompt`、`gen` 正确。
4. 发一个流式请求，**第一块数据立刻到达**（不是等生成完才一起出来）。
5. `http://<本机IP>:<端口>/ext.json` 能看到全部显卡（每张带唯一身份码）；打开 `http://<本机IP>:<端口>/monitor` 能看到卡片，显卡波形按卡的唯一身份绑定。
6. 日报与网页报表是两条独立命令：`python daily_report.py --config config.json --all` 出 `.md` 日报；`python html_report.py --config config.json --all` 出/刷新网页报表（不自动生成）。
7. `python switch_proxy.py --check`：此刻若有人在跑任务，必须显示拒绝。
8. **脱离会话自检**：装好自启件后关掉启动它的终端/结束启动会话，`/health` 仍 200、`/ext.json` 仍返回数据；任一不可用说明服务还挂在会话上，**不得交付**。

## 运维与故障

- **看门狗**：每 5 秒巡检端口（`watchdog_interval_s`，改配置每轮重读热生效、不用重启），掉了立刻补岗；换版本时用 `switch_proxy.py` 的「立即补岗」标记让它不等下一轮。
- **看门狗划界**：本包 `ledger_watchdog.py` 只守护本包记账反代（`listen` 端口）；Strata 官方引擎壳（`terminal/serve/server.py`）自带引擎进程看护，与本包看门狗无关，本包不碰不依赖。不得向用户暗示要跑官方那套看护来保活记账反代。
- **换版本/重启**：只能 `python switch_proxy.py`——它只停旧进程、唤醒看门狗拉新进程，不会自己起服务。**有客户端会话时硬拒绝，`--force` 也不覆盖**；判忙窗口 5 分钟（长生成只在完成时记账，窗口短会误判空闲）。
- **热生效项（直接改 config.json，不用重启）**：`key_labels`（下一笔生效）、`watchdog_interval_s`（每轮重读）、`listen`（改后用 `switch_proxy.py` 切换进程即跟随）。`lock_port`（默认 43177，反代进程防重复）与 `watchdog_lock_port`（默认 43176，看门狗防重复）必须不同。
- 未配 `key_labels` 的指纹原样显示 8 位码（便于发现未登记的 key）；引擎关 key 校验且客户端不带 key 会记 `none`，无法归人。
- 非流式长请求协议上就是「生成完一次性返回」，中间层无法改变；设备侧读超时建议调到 **≥600 秒**（实测最长单次生成 393 秒）。
- 缺 `psutil` / `nvidia-smi` 只是监控降级，不影响记账；物理硬盘清单仅 Windows（PowerShell `Get-PhysicalDisk`）有。

## 每日投递工序（宿主 Agent 被定时触发时）

1. 读 `out_dir/pending-report.txt`（默认 `data/pending-report.txt`）。
2. 有积压则逐日读 `out_dir/usage-report-YYYY-MM-DD.md` 向用户汇报（聊天只作导读，报告本体在盘上）。
3. 汇报后执行清账：`python daily_report.py --config config.json --reported <日期,逗号分隔>`
4. pending 为空则回「无待报」，**不编造内容**。

日报由服务进程内的日报线程在 `report_hour:report_minute` 自动生成（服务启动时先补查一次），采集与报告层与宿主 Agent 无关——Agent 离线日报照常生成，断线不漏报。

## 边界与债清单（不许粉饰，浓缩自 README 第九节 8 条）

1. 反代在业务链路上，它停了团队就断；看门狗与切换纪律必须配套一起用，不许拆开只拿代理脚本。
2. 非流式长请求仍会静默，可能撞中间设备读超时（建议 ≥600 秒）；流式路径已无此问题。
3. 关 key 裸连无法归人，记 `none`。
4. 切换必须等没人用；判忙窗口 5 分钟。
5. 单实例靠 `lock_port` 防重复，重复启动自己退出。
6. 缺 `psutil` / `nvidia-smi` 仅监控降级。
7. `start.sh` / `start.bat` 是前台交互式试跑，生产必须装 `service-examples/` 自启件并按验收第 8 条自检。
8. 8 位指纹（SHA-256 前 8 位 hex，32 位空间）理论上可能撞码；账本每行永久保留 `fp` 便于事后发现/拆分，但代码**不做自动碰撞检测**。

另有两条精度与工程化边界：
- **log 模式数字失真约 3.9%**（并行批处理时日志自报口径失真）。改进方向 = 引擎在请求完成时**原子写结构化 usage 行**（与响应 usage 同源）——**这是未来规划，尚未实现**，不得当作已有能力向用户承诺。
- **本包当前只有 proxy 模式做到一键化**：log 模式需按 `legacy/README.md` 手工配 profile，且把看门狗配到 log 采集器当前需手工（看门狗原则上必须配，但此路径未一键化）。

## 与旧 skill-token-ledger 的关系

本包是独立发行版，与另一台机器上的 `skill-token-ledger` 母本存在代码分叉（母本代理是 `resp.read()` 整包缓冲原型，直接上生产会复现 502）。改功能要两边对照同步，不存在单点收口。旧链 `requests-*.jsonl` 历史数据核心字段与本包一致，可直接拷进 `out_dir` 混着出报表。
