# QA fresh eyes 回执｜OPS-1123-ROOTLAYOUT-T1

- 验收席：QA（fresh eyes，不继承前席读数）
- 基线实拍：HEAD＝0c45424（工作区净）；迁移笔＝17d5e2c；开工基线＝f014fe1
- 测毕清理：.scratch/qa-ROOTLAYOUT/ 清零、临时 config 删除、throwaway 进程杀净、端口无残留、worktree 移除＋prune、git status 空

## 总判定：放行建议＝是

③十二条实质全绿；两处红（watchdog 套＋连带 bootstrap --selftest）＝环境 flaky（基线 f014fe1 worktree 复跑同红实证），无迁移引入缺陷。

## 逐项读数摘要

- ③-1 白名单恰九行（含 start-proxy.bat＝H-8 裁①口径）PASS
- ③-6 rename：f014fe1..17d5e2c 与 ..0c45424 两口径均 R=17/A=1/D=0 PASS
- ③-2 六套：proxy 首跑 41/46（gate 时序 5 红）→2/3 跑 46/46＝负载 flaky；watchdog HEAD×3＋基线×1 均 30/1 同红点"relaunched pid is the fake service"＝既存 flaky 非迁移引入；monitor 57/57、daily_report 15/15、registry 6/6、gateway_status 18/18；套数锁 46/31/57/15/6/18 在册
- ③-3 bootstrap --check "可以启动" exit 0；--selftest exit 1＝watchdog 同根因 flaky（A-6 路径修复本身生效＝三套均寻径成功）
- ③-4 throwaway 真服务（18099/18098 死端口）：/health 200；/gateway/status schema=unified-status/v0；/capabilities rev17k；/monitor 含 monitor.css×2；/monitor.css 200＝monitor/ 区随动实证 PASS
- ③-5 看门狗：wake 锚 throwaway cfg 旁＋日志锚根 logs/＋gateway/logs 未长出＋spawn cmd＝gateway\collector_proxy.py PASS
- ③-7 越领地＝0（两口径）PASS
- ③-8 修正读数（pathspec 双路）＝白名单外仅 2 行续行残段；人工全读真实变更 13 行＝引导×3＋sys.path×2＋registry 坐标×4＋scripts_dir×2＋注释×2＝零功能行；GATEWAY_VERSION 两态均 rev17k PASS
- ③-9 双路读数＝28 行全 rename 元数据行零内容 diff；blob 哈希逐件对拍全 SAME PASS
- ③-10 config.json 零触碰；template 非 comment 变更＝0 PASS
- ③-11 GBK-OK／BOM-CRLF-OK／四件盘面 CRLF 14/13/13/30>0（注：票面 grep $'\r' 在本 Bash 恒 0＝传参失真假阴性，字节面直读为实值）PASS
- ③-12 swb-anchor 首行 project_root: .；STRUCTURE 白名单节九件写死 PASS
- 纪律面：stash@{0} 恰一条未 pop；在岗 8080(5596)/8787(23740) 全程未触

## 新问题登记（QA 呈报，未修复）

1. **判据命令缺陷**：③-8/③-9 票面 pathspec 只指新路径→git 拆散 rename 对（假红 1127/1652）。勘误口径＝pathspec 必带新旧双路（`-- collector_proxy.py gateway/collector_proxy.py`）。凡照原文跑的席必撞假读数。
2. watchdog flaky 红点在本机负载下稳定复现（pid 断言竞态），非迁移引入；建议另票观察。
3. proxy 套 gate 时序组首跑 5 红＝并发负载所致，重跑即绿；与错窗条款互证。
4. **/capabilities 键名口径**：实键＝`benchmarks`（无顶层 registry 键；looked_at 仅在 registry unreadable 错误分支，基线同形）。NAS 消费侧若按票面"registry.looked_at"措辞核对会落空＝知会口径。
5. 合并笔 HOSTSUP（tail 接管 15 行）落在迁入 gateway/ 的 watchdog-launcher.py 上→该件相似度降至 R071；本票 R17/A1/D0 不受影响，后续席勿混判。
6. autocrlf 预存态：仓 core.autocrlf=true，bat/vbs blob 存 LF、盘面转 CRLF（基线同态）；换载/异机检出留意行尾。
7. bootstrap --selftest "三套全部通过"读数满载机器不可稳现（watchdog flaky 连带），净场可复现＝非回归。
