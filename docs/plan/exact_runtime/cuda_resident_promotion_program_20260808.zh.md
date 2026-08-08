# CUDA 常驻后端晋升程序（CP）

语言版本：
- 英文正本：[cuda_resident_promotion_program_20260808.md](cuda_resident_promotion_program_20260808.md)
- 中文伴随本：`cuda_resident_promotion_program_20260808.zh.md`

文档类型：`plan`
生命周期：`maintained`
正本路径：`docs/plan/exact_runtime/cuda_resident_promotion_program_20260808.md`
责任方：`exact-runtime / CUDA 常驻后端晋升工作线`
最后核实：`2026-08-08`

- 程序 id：`cp.promotion_target.cuda_resident.20260808`
- 分支：`codex/cuda-resident-promotion-program`
- 工作树：`.codex/worktrees/cuda-promotion`（被忽略路径）
- 基线：`a4a2b932`（main，PR #25 合并点）
- 前序程序：[RB0-RB11](cuda_resident_rb11_closure_20260731.zh.md)、
  [CR2-0..CR2-7](cuda_resident_cr2_closure_20260805.zh.md)

## 授权

两轮前序程序都以「未晋升」关闭，并要求「新的显式程序与用户授权范围」才能重开。
仓库所有者于 `2026-08-08` 授权本程序，目标明确为**晋升**：让 CUDA 常驻后端成为
可选的维护后端。

该授权覆盖面向晋升门禁的实现与证据工作，**不等于预先批准晋升本身**。晋升仍是一个
独立记录的决策，要求全部门禁转绿并通过独立评审。在此之前 CR2-7 的全部维护边界继续
生效：CPU 保持默认，`compiled_experimental_backend`、`supports_resident_state`、
`supports_device_observation_view` 保持 false。

## 前序程序为何关闭

RB10 对 RB9 套用六条冻结门禁，六条全部 Fail。CR2 在结构上修掉了其中几条，但因两项
仍然缺失而关闭。合并两次关闭结论，本程序起点的实际阻塞集是：

| # | 门禁 | 前序状态 | 性质 |
| --- | --- | --- | --- |
| G-A | 整窗推进经公共 SPI 测量 | CUDA 走私有 `inject -> publish_stage -> advance`；`publish_stage` 不在 `IWorldBatchBackend` 上 | 架构性 |
| G-B | CPU 与 CUDA 调用面等价 | `backend_spi_world_batch` 对 `backend_private_phase_sequence` | 架构性 |
| G-C | 测量 learner 等价消费 | device consumer 只是带隐藏 host 回读的诊断 smoke；CR2-3 加了 lease 边界 | 部分修复 |
| G-D | achieved 硬件计数器完整 | 两次独立尝试均 `ERR_NVGPUCTRPERM`（RB9、CR2-5b） | 主机权限 |
| G-E | selected-slice parity 出隔离区 | CR2-4b 已释放 12 个字段 | **CR2 已修复** |
| G-F | 小批量默认不退化 | world 1 退化 7-36 倍；CR2-6b 建议把 world 1 路由到 CPU | 未决（需修复或冻结显式选择规则） |

**G-B 是根门禁。** 只要两条 lane 调用面不同，RB9 和 CR2-6b 的所有时间比值都是在比较
非等价路径，无论数字多好看都不能支撑晋升。

## 计数器阻塞的确认根因

`ERR_NVGPUCTRPERM` 不是代码缺陷。本机注册表键
`HKLM\SOFTWARE\NVIDIA Corporation\Global\NVTools` 不存在，因此驱动套用默认的
仅管理员计数器策略（`RmProfilingAdminOnly` 默认启用）。所有者决定（2026-08-08）：
以**提权**方式运行 Nsight Compute 采集计数器，**不修改注册表**。系统级
`RmProfilingAdminOnly=0` 方案经评估后被否决，理由是不必要的安全态势变更。

对本程序的影响：计数器采集是需要操作员协助的步骤，不可自动化。每份计数器产物都必须
记录其在提权下采集。

## 已核实的主机与工具链

| 项 | 值 |
| --- | --- |
| GPU | NVIDIA GeForce RTX 3090（SM86） |
| 驱动 | 595.95 |
| CUDA Toolkit | 13.0.88（`nvcc` 位于 `CUDA/v13.0`） |
| 宿主编译器 | MSVC 14.44.35207（VS 2022 BuildTools） |
| 生成器 | Ninja |
| Nsight Compute | 2025.3.1 |
| 操作系统 | Windows 11 build 26200 |

## CP-0 已核实的基线结果

在基线 `a4a2b932` 上，以 `EF_ENABLE_CUDA_EXPERIMENTS=ON` 配
`CMAKE_CUDA_ARCHITECTURES=86`，CUDA-on 的配置、编译与测试全部核实转绿：

| 步骤 | 结果 |
| --- | --- |
| CMake 配置（Ninja，CUDA 13.0.88） | 成功，431 秒 |
| `ef_cuda_resident_backend` | 编译 15/15，静态库链接成功 |
| `ef_cuda_resident_lifecycle_test` | **14 用例 / 599 断言，全部通过** |
| `ef_cuda_resident_replay_test` | **4 用例 / 77 断言，全部通过** |

两个测试可执行文件都在真实 RTX 3090 上运行。ptxas 在全部 CUDA 翻译单元上报告零
spill store、零 spill load，与 CR2-5a 一致。

这个起点比「零 CI 覆盖」所暗示的风险要好得多：尽管没有 CI 通道、工具链已升到
CUDA 13.0，这 6,229 行仍可编译，其 CUDA-on 测试套件仍全部通过。腐烂风险真实存在但
尚未发生，这让 CP-1（编译通道）成为便宜的保险，而不是补救工程。

范围说明：这些套件覆盖固定空域 fixture 的生命周期、状态屏障、Phase A/B/D 的
CPU 参考 parity 以及 replay/shadow harness。它们**不**覆盖 facade 等价窗口、learner
消费者或 achieved 计数器——这三项正是下文的 G-A/G-B、G-C 与 G-D 门禁。

## 迭代计划

迭代编号 `CP-<n>`，一次迭代一个连贯 commit，遵循仓库整合协议
（analyze / implement / validate / register / commit）。关键阶段落地前需一次独立评审。

| 迭代 | 范围 | 出口门禁 |
| --- | --- | --- |
| CP-0 | 本冻结文档；核实基线上 CUDA-on 仍可编译；记录主机/工具链身份 | 程序冻结；CUDA-on 编译结果被如实记录 |
| CP-1 | CUDA-on 编译通道，让这 6,229 行停止腐烂：一个 CI 任务；若无 GPU runner，则为文档化的本地检查点加一条断言 CUDA 源集仍在接线上的架构测试 | 编译回归无法静默落地 |
| CP-2 | 把 `EF_ENABLE_CUDA_EXPERIMENTS` 拆成助手面开关与常驻后端开关，使两个语义地位不同的面可独立选择 | 打开其一不再强制打开另一个 |
| CP-3 | **G-B/G-A 根因修复**：把常驻后端的整窗推进搬上公共 SPI。要么把 stage-publish 概念提升进 `IWorldBatchBackend` 供所有后端使用，要么让 CUDA lane 通过现有 `inject/evaluate/advance/export` 序列达到同一可观测状态。CPU lane 不得退化 | 两条 lane 经同一调用面测量 |
| CP-4 | 在已等价的调用面上重测 1/4/16/64/256 矩阵，顺序对调，两轮 campaign | 时间证据成为同类比较 |
| CP-5 | 提权下采集 achieved 计数器：全部 10 个 kernel 的 occupancy、divergence、global/local/shared 流量 | G-D 以真实计数器关闭，或记录第二次外部阻塞 |
| CP-6 | 由 CP-5 结果驱动的 kernel 层优化，已知候选见下 | 相对 CP-4 基线有实测改善 |
| CP-7 | G-C：经 CR2-3 lease 的 learner 等价消费，不含隐藏 host 校验回读 | 真实消费者，而非诊断 smoke |
| CP-8 | G-F 处置：修复小批量开销，或冻结带 world 数阈值的显式选择规则 | world 1 不再是静默退化 |
| CP-9 | 晋升决策：全部门禁加独立评审，或记录带确切缺失授权的 hold | 显式、有证据支撑的裁定 |

CP-1 与 CP-2 与其余项独立，可任意顺序落地。CP-3 是 CP-4 的前置；CP-5 是 CP-6 的前置。
CP-9 需要 CP-3 至 CP-8 全部完成。

## 已知优化空间（来自 CR2-5a 静态证据）

CR2-5a 已测得全部十个 kernel 的静态资源。三条具体线索，全部需等 CP-5 的 achieved
计数器后才可动手：

1. **四个 kernel 各带 40 字节/线程的栈**：Phase B forces、Phase B aerodynamics、
   Phase B integrate、Phase D instruments。每个含三条 `LDL.64` 与两条 `STL.64`
   SASS 指令。ptxas 报告**零 spill store、零 spill load**，所以这些是真实的栈/局部
   操作，不是编译器 spill。消除栈流量是一条真线索，但不得被描述为消除 spill。
2. **occupancy 下限 58.33%**：两个 66 寄存器的 Phase B kernel（forces、
   aerodynamics）；integrate 与 Phase D instruments 为 64 寄存器 / 66.67%。其余六个
   均为 100%。构建用 `-maxrregcount=0`（无上限），因此寄存器压力实验是可行的——该实验
   在已关闭的程序下被明确禁止，仅在本程序 CP-5 之后解锁。
3. **launch 形状统一且偏小**：256 worlds 下全部 12 次 launch 均为 grid `2x1x1`、
   block `128x1x1`，即每次 launch 共 256 线程，一个 world 一个线程。该分解方式是否
   合适是开放问题，需 achieved occupancy 提供依据。

小批量开销（G-F）另有可疑成因：每个被捕获窗口有 5 次 `cudaDeviceSynchronize` 与
13 次 `cudaMemcpy`。在 world 1 上这笔固定成本占主导，与观测到的 7-36 倍退化吻合。

CR2-5a 的理论 occupancy 不得在任何 CP-6 论证中替代 achieved occupancy。

## 约束

- 直到 CP-9 另有裁定，CPU 在整个程序期间保持维护版 world-step 真值。
- 无兼容外壳与迁移说明时，不得变更公共 ABI、Python 名称、CLI 标志或配置键。
- 证据产物保持内容寻址、`utf8_lf` 规范化与 `-text` gitattributes，遵循 CR2 先例。
- 计数器产物必须记录提权事实；不得将理论值填入 achieved 计数器字段。
- 不修改注册表或驱动策略。
- 本单机采集的时间证据是主机特定的。没有文档化的第二台主机或显式的单机接受声明，
  它不能成为维护版性能契约。
- 独立评审者不得编辑受评审的实现。

## 回滚边界

本程序不触碰 `main`。全部工作位于被忽略工作树中的
`codex/cuda-resident-promotion-program` 分支。放弃本程序只需删除该分支与工作树，
无需维护版回滚。
