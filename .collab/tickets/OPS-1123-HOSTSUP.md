 OPS-1123-HOSTSUP 看门狗管辖收缩：ComfyUI 侧只管面门门
Status: 实施中（用户 2026-11-23 裁示，配奔对方仓 TK-F-20261123-2）

【裁示】
guard_services 里 comfyui-full/comfy-tv 两条把 ComfyUI 分段网关的编排知识
（启动顺序、位置、grace、谁等谁）抄进了看门狗清单 = 越界。
实例编排已下沉至面门自身（按 gateway_profile.json 自拉 A/B）；
看门狗对 ComfyUI 侧的全部权利 = “8188 没开就用 start_facade.bat 拉一次”。

【实施】
- config.json guard_services 删 comfyui-full、comfy-tv；facade 条目去掉
  wait_for 20004（看门狗不再持有任何 ComfyUI 内部端口知识）。
- watchdog-launcher.py docstring、watchdog-console.bat 横幅同步。
- 旧链参数（RAM 错峰 600s/300s、stabilize）由面门监护线程接班：
  全局错峰 120s + ram_free_th 水位线闸门，只在对方档案里存活。

【rev2（用户二次裁示）】
看门归看门，该看谁由网关传达：facade 条目挂 watch_url=http://127.0.0.1:8188/watchlist
+ family=comfyui；看门狗按清单逐项探活/代拉（脚本自包含、自带单实例闸）。
清单实例级顺序剥离（wait_for 强制清空）。看门狗唯一自调的分步 = 类型级安全启动：
comfyui 族条目 wait_for 注入引擎端口（8787）+ stabilize≥60s；LLM 族内部不动。
config.json 每周期重读，改动即时生效。

【跨域工单登记】EXT-2026-11-23-百工插件面单缺陷-v1 已落盘本包 .collab／decisions／EXT-2026-11-23-baigong-plugin-defects-v1.md（八字段形制·钉值当轮现取·状态＝已登记待发投递）。

【跨域工单合并登记】应用户令：网关面 v1＋basalt-fork 面交接件（BAIGONG-defects-basaltfork-20261123.md）合并为 EXT-2026-11-23-百工插件面单缺陷-v2（R-1..R-9·全钉值可解引用·落位 .collab/decisions/）。v1 已标作废。
