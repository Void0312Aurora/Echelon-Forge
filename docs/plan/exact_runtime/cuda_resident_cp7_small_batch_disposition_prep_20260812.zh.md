# CP-7 小批量处置——筹备说明

语言版本：
- 英文正本：[cuda_resident_cp7_small_batch_disposition_prep_20260812.md](cuda_resident_cp7_small_batch_disposition_prep_20260812.md)
- 中文伴随本：`cuda_resident_cp7_small_batch_disposition_prep_20260812.zh.md`

文档类型：`plan`
生命周期：`draft`
正本路径：`docs/plan/exact_runtime/cuda_resident_cp7_small_batch_disposition_prep_20260812.md`
责任方：`exact-runtime / CUDA 常驻后端晋升工作线`
最后核实：`2026-08-12`

- 所属程序：[CP 晋升程序](cuda_resident_promotion_program_20260808.zh.md)，
  迭代 CP-7，门禁 G-F
- 权限边界：本说明为 CP-7 决策做准备，不授权任何实现。CP-7 的出口门禁是
  「world 1 不再是静默退化」，既可以用一次经测量的修复满足，也可以用冻结的
  显式 world 数选择规则满足。

## CP-7 要决定什么

CR2-6b 实测常驻通道的 world 1 比 CPU 慢 7-36 倍，并把 world 1 路由到 CPU，
但那只是保留建议，不是维护版选择器。CP-7 必须二选一：修复小批量开销，或把
路由规则显式冻结。CP-4 计数器显示设备在 256 worlds 时都近乎空闲，这使
「每窗口一笔 world 数无法摊薄的固定 host 侧成本」成为矩阵底端退化的头号
假设。CP-5 已消掉最大的一段 launch 链（六个窗口提交 launch 融合为一），
剩下的就是下文盘点的同步与拷贝骨架。

## 已核实的逐窗口固定成本清单

依据当前工作树源码（CP-5 融合后形态）读出，并与冻结 v2 捕获的 API 计数
（5 次 `cudaDeviceSynchronize`、13 次 `cudaMemcpy` = 3 h2d + 7 d2h + 3 d2d）
及性能契约的基准账本（5 launch、5 sync、3 h2d、5 次 4 字节 d2h、3 d2d）
交叉核对。

窗口的每个阶段都遵循同一模式：launch、`cudaDeviceSynchronize`、把一个
4 字节的 `barrier_status` 字读回 host 并 fail-closed。每窗口有五个阶段
这样做：

| 阶段 | 位置 | Sync | D2H |
| --- | --- | --- | --- |
| 输入注入屏障 | `cuda_world_store_cuda_barrier.cu`（launch_apply_barrier） | 1 | 4 B |
| 控制准备 | `cuda_world_store_cuda_control_preparation.cu` | 1 | 4 B |
| 阶段发布屏障 | `cuda_world_store_cuda_barrier.cu` | 1 | 4 B |
| 融合窗口提交体 | `cuda_world_store_cuda_window.cu` | 1 | 4 B |
| 窗口提交屏障 | `cuda_world_store_cuda_barrier.cu` | 1 | 4 B |

每窗口的拷贝骨架：

- 3 次全槽 device-to-device 拷贝（各 `slot_bytes`；256-world 容量下为
  225,792 字节）：输入注入（`cuda_world_store_cuda_storage.cu`）、控制准备、
  阶段发布/窗口提交的双缓冲写时复制。它们随 world **容量**而非活跃 world 数
  缩放，所以除非容量也是 1，world 1 同样要付全容量的拷贝。
- 3 次 host-to-device 控制拷贝（doubles、floats、flags），在
  `inject_flight_controls` 中；大小随容量缩放。
- 设备消费者通道在此之上增加 pack kernel、它的同步与 lease 事件机制
  （契约模型记为 +2 launch、+1 同步）；消费校验的 D2H 按 CR2-3 保持延后。

本清单**没有**确立的事情：每一项花多少墙钟时间，乃至骨架究竟是不是瓶颈。
CP-4 计数器测的是设备侧利用率，不是 host API 延迟或 kernel 时长，所以本
说明不给出任何成本数字，也不声称这副骨架解释了实测的 7-36 倍。计数器显示
设备每次 launch 几乎无事可做（近乎空闲的 occupancy、零 local 流量、零
divergence），这使 host 侧骨架成为头号**假设**——不是已确立的原因。确认或
否证它、并按实测贡献对下文候选排序，需要一次 host 侧时间线捕获（对
world-1 窗口跑 Nsight Systems），这是 CP-7 的第一个动作。

## 修复候选，按预期收益对爆炸半径排序

以下均未经测量；CP-7 采纳哪个就必须测哪个，并经 CP-8 复测。任何执行图
变更都是新的证据世代（v4）——得益于契约派生的计数器链，这如今收敛为一次
契约扩展外加一次性的身份/单位注册，而不再是对采集器的重新钉定。

1. **每窗口一次同步 + 合并状态数组。** 给每个阶段一个独立的设备端状态字
   （小数组），各阶段在设备上保持 fail-closed，但 host 只在窗口结束时同步
   并一次读回整个数组（或对状态字用 mapped pinned 内存）。最多消掉 5 次
   同步中的 4 次、5 次状态回读中的 4 次。爆炸半径：fail-closed 语义从
   「每阶段后 host 检查」变为「每窗口检查一次、状态仍逐阶段」；replay 与
   parity fixture 应不受影响（失败窗口本就丢弃暂存槽），但期望「host 在
   精确阶段失败」的错误归因测试需要按窗口重述期望。
2. **退役全槽写时复制链。** 每窗口三次 `slot_bytes` 的 d2d 拷贝是为了让
   各阶段写入新槽。候选：槽指针轮转 + 只拷贝该阶段不重写的字段，或收敛
   暂存使一次（乃至零次，配合写穿约定）拷贝服务整个窗口。字节量收益最大、
   也是唯一同时惠及大批量的项；爆炸半径最高，因为它动的是 replay、回读与
   屏障契约共同依赖的状态槽模型。
3. **三次控制拷贝合并为一次。** 把 doubles/floats/flags 打包进一个 pinned
   暂存缓冲，一次 h2d。小、低风险、收益有界（省两次拷贝提交）。
4. **整窗 CUDA Graph 捕获。** 包含候选 1 的收益并消掉剩余 launch 开销。
   结构变更最大：新的执行图、新的捕获方法学、证据链的第一个 graph-launch
   世代。只有当候选 1-3 之后 world 1 仍退化、且程序仍要「修复」而非
   「规则」时才有辩护余地。
5. **改为冻结显式选择规则。** 把 CR2-6b 的建议（world 1 走 CPU）升级为
   冻结的、有文档的阈值，交叉点由 CP-8 矩阵实测给出。这是不修复的处置；
   它同样满足门禁，因为退化不再是静默的。

## 顺序

1. 先等 CP-5 落地并读到融合后矩阵（含 world 1）：每窗口消掉五次 launch
   本身就可能改变小批量格局；候选 5 的交叉点也要用这份数据。与之并行，
   捕获一次 world-1 的 host 侧时间线（Nsight Systems），把固定成本归因到
   清单各项之后再选候选。
2. 若尝试修复，优先能过门禁的最小集合（3 先于 1 先于 2；4 需所有者显式
   授权范围），一个迭代一个候选，执行图变更配套新一代捕获证据。
3. learner 等价消费者（CP-6）经同一矩阵通道测量；CP-6 与 CP-7 落地顺序由
   所有者冻结决定，但两者的测量不得混在同一次 campaign 里。

## 非目标

- 不授予晋升、支持标志或调优权限；四个授权标志全部保持 false。
- 不变更公共 ABI、Python 名称、CLI 标志或配置键。
- 本说明不构成性能主张：清单是结构性的；成本归因等待 world-1 时间线捕获。
