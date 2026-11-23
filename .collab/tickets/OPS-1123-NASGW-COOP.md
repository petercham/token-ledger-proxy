# OPS-1123-NASGW-COOP 接手单：GitHub issue #1 跨域协作（NAS 算力池网关对接配合项）

> 件型＝**接手/登记单**（主理人誊录面，非施工票本体）；正式施工票待架构席按分票职权起草（L3 载体＝施工票通道）。
> 来源＝GitHub issue petercham/token-ledger-proxy#1（作者 petercham＝关联项目开发会话 Agent 发的跨域协作件·按跨项目 MEMORY 常设令优先处理）。

## 字段一：编号族与来源钉值

- 本单 ID：`OPS-1123-NASGW-COOP`
- 来源＝issue #1《NAS 算力池网关对接配合项：:8080 新增 GET /gateway/status 统一状态面（契约 v0.2 §10）＋Basalt 改名键位确认》
  - issue URL＝https://github.com/petercham/token-ledger-proxy/issues/1
  - issue id＝6558651452；created_at＝2026-11-23T11:51:42Z；立案时 comments＝0
  - 提issue方＝compute-pool-gateway 仓（NAS 网关侧·P1 已部署 192.168.31.230:8080）
- 本单开端读数（当轮实跑·2026-11-23 19:53 +08）：
  - ANCHOR＝`507990d`（`git -C D:\Projects\token-ledger-proxy rev-parse --short HEAD`）；`git status --porcelain`＝空（工作区干净）。
  - `curl --noproxy '*' http://127.0.0.1:8080/health` → `{"ok":true}`（网关在跑·基线 rev17a 后现行面）
  - `curl --noproxy '*' http://127.0.0.1:8080/gateway/status` → **404**＝issue 所述缺口属实
  - `collector_proxy.py` grep `gateway/status|unified-status`＝**零命中**＝代码面确认无该路由

## 字段二：诉求体闭集（誊录自 issue·两项）

1. **实装项（本仓动作）**：:8080 新增只读路由 `GET /gateway/status`——
   - 不动既有 `/health`、`/ext.json`、`/monitor*`、`/v1/*`（兼容承诺＝vendor 四套自测回归底线）；
   - 报文＝envelope 五字段 `{schema:"unified-status/v0", machine_id, domain:"llm", generated_at, ports[]}`；ports[] 行 11 字段（vport/engine/gpu_bind/vram_gb/available/current_tasks{in_flight,queued}/speed_bias{value,bench_id,measured_at}）；
   - 合成源＝gate 进程内量（admitted/_waiters live/serving）＋`available = serving − max(in_flight, admitted)`；speed_bias 无档案＝整字段缺席（缺位弃权不填 1.0）；
   - 鉴权＝沿 /health 先例（内网无鉴权）；
   - 对方已起草好该路由实现（compute-pool-gateway 票 T16＝collector_proxy 扩面），**可整段提供 patch／提 PR**。
2. **确认项（答复即结·无需改码）**：Basalt `/v1/status` 的 `concurrency.serving`／`context.native`／`activity.in_flight` 与 `/v1/models` 的 `status.value`／`meta.n_ctx` 键位是否相对 Strata 有增删（对方按在场性落 None，不猜值）。

## 字段三：当轮实测取证（确认项答复依据·本机现跑）

`GET /v1/status`（127.0.0.1:8080·2026-11-23 19:53 +08）：
- `service`＝`"basalt"`；`engine`＝`"0.5.0"`（与对方实测一致）
- `concurrency.serving`＝**在场**（值 7；同对象另有 `requested`＝7）
- `context.native`＝**在场**（值 262144；同对象另有 `max_positions`／`elastic_kv_ceiling` 未点名键，不影响在场性）
- `activity.in_flight`＝**在场**（值 0；同对象另有 `requests`／`last_request_at`）

`GET /v1/models`（同刻）：
- `data[0].status.value`＝**在场**（`"loaded"`）
- `data[0].meta.n_ctx`＝**在场**（262144）

结论＝**对方点名的五个键位＋service/engine 键现网 Basalt 全部在场、语义同 Strata 键位（无删）**；我方无 Strata→Basalt 逐版 diff 报告，在场性判定以本读数为准，对方无需落 None。

## 字段四：处置裁定与后续链

- **确认项**＝当轮已答（见字段三），随 GitHub 回帖送达，本项闭环。
- **实装项**＝接手，**接受对方"我方提 PR"形态**（回帖已确认）；施工链：
  1. 架构席起草正式施工票（票面闭集预期＝`collector_proxy.py` 只读路由扩面＋tests 回归＋CHANGELOG 登记；GATEWAY_VERSION bump 与否归票裁）；
  2. 对方 patch/PR 到位后按票合入，跑 vendor 四套自测回归（底线判据＝既有端点零破断）；
  3. 部署入闸＝常规两人工闸（specs 准入闸＋部署准入闸·2026-11-23 01:15 口径），不可代理代跑。
- 对接完成判据（对方所定）＝NAS 侧 `curl http://<终端>:8080/gateway/status` 出 envelope 五字段。

## 字段五：状态

- 当前＝已接手＋确认项已答；实装项待对方 PR 到位＋架构席出票。
- 本单 append-only；后续处置随登不另起件。

## 字段六：口径改判追记（2026-11-23 19:57 决策者原话＋主理人执行）

- 决策者原话（逐字·19:57）：「是因为对方说它要给你提 PR？你俩都是 Agent，提交给你 issues 就应该你来做，才是各司其职的干净协作状态，对么」
- 改判＝实装项**本仓自研自闭环**，不采"对方提 PR"形态：写权与实现权归本仓唯一写权席；对方 T16 起草件不再作为合入来源（如需其契约细节，以 issue 正文＋契约引用为准，不接跨仓代码）。
- 当轮实证＝远端 PR 数＝**0**（`GET /pulls?state=all` 实拉）＝对方 patch 未到位，改判零沉没。
- 后续链更新＝架构席即刻起草施工票（契约要素＝issue 正文【实装项】已完备：envelope 五字段＋ports 行 11 字段＋available 合成式＋speed_bias 缺位弃权＋沿 /health 无鉴权先例）；完工后本仓回帖 issue＋NAS 侧 curl 判据对接。
- GitHub 回帖＝随改判送达（模式变更告知＋不劳对方 PR＋对接判据不变）。
- Status 更新：实装项＝已接手·自研开工（架构席出票在途）。
