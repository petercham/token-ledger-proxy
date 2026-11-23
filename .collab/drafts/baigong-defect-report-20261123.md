# 百工软件团队（baigong-software-team v0.1.36）缺陷报告

日期：2026-11-23 ｜ 报告面：token-ledger-proxy 会话 ｜ 环境：Windows, WorkBuddy

## 缺陷一：hooks.json 钩子命令用相对路径（阻断级）[用户已确认，上游将修]
现象：四条钩子命令写 ../skills/sop/scripts/*.py，以会话 cwd 展开成幻象路径，
钩子进程起不来——write-guard/commit-audit 静默全失效（deny/放行都不出现）。
根因：插件清单不以插件安装根目录为基准解析路径。
临时处置：两处 hooks.json 改绝对路径（.bak-relpath 备份），升级会被覆盖。
建议：命令生成注入插件根绝对路径或 {PLUGIN_ROOT} 占位符由宿主展开；
钩子加载失败必须打日志，禁止静默。

## 缺陷二：无席位会话 fail-closed 拦正门、Bash 侧门全开（纪律失效级）
现象：agent_type=cli / agent_id=None 时 Write/Edit 一律 deny（连开票都不行），
但 Bash/PowerShell 写同路径完全放行——本次全部票/补丁实际经 Bash 落盘。
机制守了一个没人能走的正门，侧门敞开；deny 也不给出"如何开票"的出路。
建议：区分席位/无席位策略（降级提醒或仅守租约区）；deny 报错附开票指引。
（本条即现场复现：本报告 Write 通道被拦后改 PowerShell 落盘。）

## 缺陷三：用户级记忆文件被无差别 deny（误拦级）
现象：Edit ~/.workbuddy/user-*/MEMORY.md 被"写目标路径缺席→deny"。
建议：宿主自有区 ~/.workbuddy/** 列入白名单或独立策略。

## 缺陷四：跨工作面写无机制闸门（治理缺口，功能建议）
现象：本会话（工作面=token-ledger-proxy）顺手改了另一仓 comfy-split-gateway
的代码/档案/票并 commit，无任何机制拦截，靠用户人工发现纠正；对面票面
明写"勿在本会话实施"机制不读。
建议：写/提交目标落在另一 git 仓根时至少 warn+确认；跨面施工显式化
（跨面票登记）而非无人拦。

## 缺陷五：commit-audit 提交身份只在席位链注入（轻微）
现象：席位链提交有身份（workspace-watchdog）；同仓普通会话提交报
Author identity unknown 失败，无引导。
建议：装配/初始化时对业务仓检查 git 身份并提示。

## 证据索引（本环境）
- hooks 补丁备份：plugins/.../hooks/hooks.json.bak-relpath（两处）
- 本面票：.collab/tickets/OPS-1123-HOSTSUP.md（治理全记录）
- 跨面事故登记：comfy-split-gateway/.collab/decisions/2026-11-23-watchlist-contract.md


---
作废声明（同日）：本件为不成形制的工作稿（证据仅裸路径、无钉值成对、无效力域声明），已由 EXT-2026-11-23-百工插件面单缺陷-v1（落位 .collab／decisions／EXT-2026-11-23-baigong-plugin-defects-v1.md）取代。内容真源以 EXT 件为准。
