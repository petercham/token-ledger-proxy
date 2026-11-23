# STRUCTURE · 仓结构与仓根白名单（规范域）

- 建档票：OPS-1123-ROOTLAYOUT-T1（S-12）；母票＝OPS-1123-ROOTLAYOUT（dev-discipline §十 S1–S6 补票）
- 本文件＝仓根布局与目录语义的唯一规范真源；`.workbuddy/swb-anchor` 首行 `project_root: .` 与本文件 `project_root: "."` 锚定行对等。

project_root: "."

## 一、四区枚举（完备）

| 区 | 路径 | 语义 |
|---|---|---|
| 规范域 | `docs/` | 规范＋说明域（本文件、README.md〔原 legacy/README.md〕、截图配图） |
| 治理域 | `.collab/` | 票/决策/回流/账本（治理登记面） |
| 运行时 ignore 域 | `data/` · `logs/` · 根级 `config.json` / `relaunch-now.flag` / `*.log` | 本机运行态件，`.gitignore` 在册实证，永不入库 |
| 人类域 `sources/` | 不建 | 本仓无外部投料流（H-4 裁定按实态＝不建） |

## 二、delivery_paths（交付面清单）

仓根白名单九件＋五区目录逐一：

```
README.md  INSTALL.md  CHANGELOG.md  MANIFEST.md
start.bat  start.sh  start-proxy.bat  bootstrap.py  .gitignore
gateway/  monitor/  reporting/  data-defs/  docs/
```

保留现位区：`config-examples/` · `service-examples/` · `tests/` · `legacy/` · `.collab/`。
模板例外：`config.template.json` 留根入 git（＝母票表"config-examples 保留现位"同理的运行时模板件例外）。

## 三、锚定行

与 `.workbuddy/swb-anchor`（首行 `project_root: .`）对等；本文件上行 `project_root: "."`。

## 四、仓根白名单条款（写死·九件）

仓根受版本管理的文件恰＝`CHANGELOG.md INSTALL.md MANIFEST.md README.md bootstrap.py start-proxy.bat start.sh start.bat .gitignore` 九件的排序集（`config.template.json`＝模板例外照旧不计入恰集；`config.json` 等 gitignore 域运行时件除外）。

**第 10 个受版本管理的仓根文件长出＝机检判红**。机检命令：

```bash
git ls-files | grep -v / | grep -v '^config.template.json$' | sort
# 期望恰九行（上述排序集）
```

start-proxy.bat 入白名单＝H-8 裁定①（人用系统入口级脚本，与 start.bat/start.sh 同级；proxy_launch 人机同入口）。

## 五、目录语义表（照录母票§一）

| 新目录 | 迁入件 | 语义 |
|---|---|---|
| `gateway/` | collector_proxy.py · ledger_watchdog.py · switch_proxy.py · watchdog-launcher.py · watchdog-console.bat · paths.py | 服务主链（反代＋看护＋换载闸＋主控台） |
| `monitor/` | monitor_ext.py · ext.js · monitor.js · monitor.html · monitor.css · monitor-sprite.svg | 硬件监视面（前后端同区） |
| `reporting/` | html_report.py · daily_report.py | 报表面 |
| `data-defs/` | api-price-table.csv · benchmark-registry.json | 随包分发数据定义 |
| `docs/` | STRUCTURE.md＋README.md＋既有截图 | 规范＋说明域 |
| 保留现位 | config-examples/ · service-examples/ · tests/ · legacy/ · .collab/ | 已治理区不动 |

锚性约定（票裁 A-1）：`gateway/` 内代码的 config/logs/relaunch-now.flag 三锚＋`@pkg` 语义（A-2）全部上溯锚**包根**＝仓根（部署面＝部署根），代码深度变化不漂移。

## 六、变更纪律

新目录、新仓根件、白名单任何增减＝必经架构席票面声明＋放行后由执行席落位（本票 OPS-1123-ROOTLAYOUT-T1＝先例）。未声明的仓根长出件在 ③-1 类机检即判红。
