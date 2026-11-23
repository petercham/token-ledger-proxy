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
