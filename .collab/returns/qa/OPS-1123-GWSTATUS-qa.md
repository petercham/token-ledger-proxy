# QA 验收回执 · OPS-1123-GWSTATUS（基线 3b11be3 → 完工落链 e8fa875）

终态判定＝**通过**（QA 席独立实跑，工程师回流件仅作对照）。全文回执要点：

## ③九条读数
③-1 闭集＝1（多出行＝本回执同族回流件＝席位写域件非施工面；实际施工 diff 面 5 文件恰＝闭集）｜③-2 新套 18/18｜③-3 proxy 46/46（T-GS 在册）｜③-4 watchdog 31/monitor 57/report 15/registry 6 全绿｜③-5 禁动面 0（config.template.json 零触碰＝(b) 兑现实证）｜③-6 ＝1（误报，见下）｜③-7 speed_bias 零合成 0｜③-8 零 upstream 0｜③-9 版本号 2 行（rev17i→rev17k）。

## ③-6 独立判定＝红线未违（误报成立）
- 命中行＝`+    in_flight = snap["inflight"] if snap else 0`（JSON 键字符串，非 Gate 成员访问）。
- Gate 区段双切片独立重算：区间一（class Gate:→_last_limit = 0）前后均 7395 B·sha256 一致 `b402c2d5…d024`；区间二（类体至下一顶层 def）前后均 7453 B·sha 一致 `adc13915…66c4`。
- 写面专检（.inflight 赋值/增减/.waiters/.cond/.acquire/.release）＝0 命中；diff 恰三 hunk，Gate 类体 :132-277 无 hunk。

## 真流量证明（throwaway 18099，upstream→不可达，--noproxy）
`GET /gateway/status` → 200 envelope 五字段逐字合契约；QA 独立断言 16/16：machine_id="We4AI"（hostname 退路态）、speed_bias 键不在场（H-3 态）、gpu_bind/vram_gb/engine/available＝null（未申报缺位态）、available 数值语义由 GS-4 四态锁（1/−1 不钳位/3/null）。只读承诺实证：测后无 gate-events、账本仅启动行。

## 既有面回归
/health 200｜/capabilities 200 且 gateway.version＝**rev17k** 透传证实｜/ext.json 200。

## 问题清单（非阻断）
1. ③-6 grep 对该 diff 形态天然误报（票面已预告＋预案实际走法合规）；建议将来同类票改 Gate 区段哈希锁为主判据。
2. 在岗 config.json 无三可选键→部署后现网出 hostname/null 形态；NAS 对接 curl 判据候部署入闸。
3. 工程师自报 sha（513ff200…/7368B）与 QA 独立重算（b402c2d5…/7395B）差异＝切片止点口径微差，前后一致性结论双方独立成立，不构成可信度否定；以 QA 读数入册。

放行建议＝可进入落链收尾链；部署入闸＝人工闸（决策者），不可代理代跑。

—— QA 席 · 2026-11-23 · throwaway 实例已杀、.scratch/QA-GWSTATUS/ 清零、零 git 写
