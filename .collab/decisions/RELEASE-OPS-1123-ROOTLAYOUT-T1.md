# 放行件｜OPS-1123-ROOTLAYOUT-T1（v2）

- 放行时间：2026-11-23 22:1x（决策者皮总人工闸拍板，AskUserQuestion 双问回执在案）
- 放行对象：`OPS-1123-ROOTLAYOUT-T1.md` **v2**（sha256 前 8 = `0405e838`，54,083 B，落链 `b1f4d31`）
- 档位：全量档（声明闭集 ≈30 文件）；人类放行闸＝已过（本件即闸凭证）。

## 一、裁定

1. **放行＝是**。工程师席持本件按 v2 票面闭集复工；`stash@{0}`（抢跑 WIP 隔离取证）仅作对照参考，**不得 pop、不得继承**，完工链闭合后另行处置（候清）。
2. **H-8＝裁①：白名单改九件**。`start-proxy.bat` 入仓根白名单（人用系统入口级脚本，rev17b 引入，符合白名单定位）。连锁落位：
   - ③-1 仓根白名单恰集判据：期望改**九行**（`CHANGELOG.md INSTALL.md MANIFEST.md README.md bootstrap.py start-proxy.bat start.sh start.bat .gitignore` 排序集＋config.template.json 例外照旧）；
   - S-1 映射表**不增** git mv 行（该件留根）；③-6 rename 计数保持 **17**；
   - S-8 该件 :10 改法照 v2 票面 L192 原文执行（`gateway\collector_proxy.py` 前缀，config 仍 `%~dp0` 锚根）；
   - STRUCTURE.md 白名单节按九件写死。

## 二、随放行勘误（放行件注明，票面不再升版）

1. v2 措辞"改 1 行计数不变"（涉 selftest_registry 处）应按定稿 registry 链随动 **2 行**（`tests/selftest_registry.py` :29＋:161 两处 HERE 插桩改 `HERE/gateway`），与 ②-0 G-4 定稿一致；行数判据随之按 2 行口径读。
2. ③-6 基线双读数按 v2/D-4 执行：开工 HEAD＝`b1f4d31`（含本放行件提交则随实际开工 HEAD 记录），A＝**1**（仅 STRUCTURE.md；本放行件与票本体均在基线内）。
3. 双席并跑六套自测时固定端口 18080 族互扰→**错窗条款**：六套自测由工程师席单席净场跑，QA 席 fresh eyes 复核在工程师交回执之后串行，禁同窗并跑。

## 三、验收与后续链

- ③十二条验收全绿→工程师完工回执（开端 HEAD＋逐件 sha 前→后＋③读数原文）→ QA 席 fresh eyes → 落链 push。
- `GATEWAY_VERSION` 不 bump（纯迁移）；六套套数锁 46/31/57/15/6/18。
- 落链后进入**闸②**（部署准入）：部署面同构迁移＋启动夹 VBS 随动＝另呈决策包候拍，不在本放行件射程。
