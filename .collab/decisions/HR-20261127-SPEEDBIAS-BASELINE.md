# 人类裁定登记 HR-20261127-SPEEDBIAS-BASELINE

- 时间＝2026-11-27 02:2x 皮总原话（逐字）：「那就把 5090 32gb + 96gb 内存环境当做基线吧，4090 24gb 是 ComfyUI 的测试基线，没必要非得追求一样，后端基座完全不同」

## 裁定语义（〔主理人蒸馏〕，可回溯上段原话）

1. **LLM 域 speed_bias 基线环境＝RTX 5090 32GB + 96GB RAM**（本机 We4AI 实况，nvidia-smi 实测 32607 MiB／内存 95GiB 显示值坐实）——LLM 域速度维参考以该环境为基线刻度，不必对齐 NAS 侧 `bench_gateway/v1`（4090＝1.0）那把尺。
2. **4090 24GB＝ComfyUI（生成域）测试基线**，维持 NAS 侧现刻度不动。
3. **两域基线不求同**——后端基座完全不同（Basalt vs ComfyUI），跨域同尺无意义；域内相对读数即可满足路由参考用途。

## 连带事实登记（裁定前实测）

- 在岗 envelope（8080 /gateway/status）speed_bias＝法定缺席（GWSTATUS A-6：registry 三标量全 null＋行↔vport 无 join 键）——裁定不改变缺席现状，只定"接线后按什么基线折算"。
- **registry 归因疑点**：现行两条 map 行 hardware 标签＝"RTX PRO 5000 72GB / 1344GB-s / 64GB RAM"（engine basalt 0.5.5+00c3209b），≠本机形态（5090 32GB/96GB，引擎 0.5.0）＝既有参考点**非**本基线环境读数，其宿主归属待核（logs/bench_prod_6.log 不在本仓）。按本基线口径，5090 环境基线行需另产＝LOADSWEEP T3 扫描产出。

## 效力与后续

- 效力＝speed_bias 域基线口径真源（对外措辞与 H-3 接线票折算基准随动）；代码零变更。
- 随动动作＝①issue petercham/token-ledger-proxy#1 回帖知会 NAS 侧（两域两基线口径＋registry 归因疑点＋非 null 值候 T3）；②H-3 接线票（registry join 键＋envelope 读取）与 T3 扫描排期候另拍；③当日日志登记。
