# OPS-1123-DOCSRENAME · 仓根工序文档改名（维护票）

- 日期：2026-11-23 · 来源：用户裁示（对话裁决，事故窗口内维护级小改）
- 范围：`SKILL.md` → `INSTALL.md`（git rename）；摘除平台 skill frontmatter；README/CHANGELOG/MANIFEST 同步。
- 理由：原名易被误解为"依赖 Agent 平台环境的通用 skill 工具"；实为仓根通用部署工序文档，命名对齐 Strata 官方 INSTALL.md。
- 验收：正文开头含"非 skill 包"声明；README 引用改齐；MANIFEST 第一节登记；无代码/运行时改动（git show --stat 应只含 4 个 md 与 1 个 rename）。
