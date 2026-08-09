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

RB10 对 RB9 套用六条冻结门禁，六条全部 Fail。随后 CR2 在结构上修掉了其中大部分。
CR2-7 关闭记录（`cuda_resident_cr2_closure_20260805.json`）是由此产生状态的权威依据，
它报告 `common_spi_full_window_available=true`、
`device_consumer_boundary_available=true`、`selected_slice_parity_complete=true`、
`resource_static_topology_complete=true`、`production_matrix_complete=true`、
`small_batch_selection_advisory_complete=true`，测量类门禁中仅
`achieved_counter_gate_complete=false`。

对照基线 `a4a2b932` 上的实际代码合并两次关闭结论：

| # | 门禁 | 本程序起点状态 | 核实依据 |
| --- | --- | --- | --- |
| G-A | 整窗推进经公共 SPI 测量 | **CR2 已修复** | `cuda_resident_cr2_matrix_session.cpp` 只跑 `inject -> evaluate -> advance -> export_state`；surface id 为 `cuda_resident.full_window_spi.v1`；探针声明 `operation_sequence = [inject, evaluate_empty, advance_world_batch, ...]` |
| G-B | CPU 与 CUDA 调用面等价 | **CR2 已修复** | 同一条纯 SPI 会话驱动两条 lane。`CudaWorldStore::advance_window()` 在窗口仅为 `input_injected` 时自行 publish（`cuda_world_store.cpp:348`），因此调用方无需公共 `publish_stage` |
| G-C | 测量 learner 等价消费 | 边界已存在（CR2-3 lease），真实 learner 消费者不存在 | `cuda_resident_device_consumer.cpp` 已就位；CR2-7 该门禁为 true 指的是**边界**，不是 learner 等价消费 |
| G-D | achieved 硬件计数器完整 | **未决——唯一的硬阻塞** | 两次独立尝试均 `ERR_NVGPUCTRPERM`（RB9、CR2-5b） |
| G-E | selected-slice parity 出隔离区 | **CR2-4b 已修复** | 已释放 12 个字段 |
| G-F | 小批量默认不退化 | 有建议，无修复 | world 1 退化 7-36 倍；CR2-6b 把 world 1 路由到 CPU |

对本程序自身范围的一处更正：G-A 与 G-B **不是**未决的架构工作。`publish_stage` 作为
`CudaResidentBackend` 的公共方法仍然存在，但其剩余调用方只有 C++ 测试和已被取代的
RB9 探针——不是产出关闭证据的 CR2 矩阵或整窗路径。RB10 对这两条门禁的裁定在写下时是
正确的，如今已过期。

实际后果是本程序比「修六条门禁」短得多。真正剩余的工作是 G-D（主机权限问题，不是代码
问题）、G-C、G-F，以及晋升授权本身。

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
| Nsight Compute | 2025.3.1（采集器要求 `2025.3.1.0`） |
| Nsight Systems | 2025.3.2.474（校验器要求 `2025.3.2`） |
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
CPU 参考 parity 以及 replay/shadow harness。它们**不**覆盖 learner 消费者或 achieved
计数器——即下文的 G-C 与 G-D 门禁。SPI 等价整窗由独立的 CR2 矩阵与整窗探针覆盖，
而非由这两个套件覆盖。

## 迭代计划

迭代编号 `CP-<n>`，一次迭代一个连贯 commit，遵循仓库整合协议
（analyze / implement / validate / register / commit）。关键阶段落地前需一次独立评审。

| 迭代 | 范围 | 出口门禁 |
| --- | --- | --- |
| CP-0 | 本冻结文档；核实基线上 CUDA-on 仍可编译；记录主机/工具链身份；对照现行代码复核 RB10 的门禁裁定 | 程序冻结；CUDA-on 编译结果被如实记录；过期裁定被更正 |
| CP-1 | CUDA-on 编译通道，让这 6,229 行停止腐烂：一个 CI 任务；若无 GPU runner，则为文档化的本地检查点加一条断言 CUDA 源集仍在接线上的架构测试。还须断言每个 CUDA 探针仍能**执行**而非仅能链接——已退役的资源探针作为存根可以正常编译 | 编译回归无法静默落地；被退役成存根的探针能被检出 |
| CP-2 | 把 `EF_ENABLE_CUDA_EXPERIMENTS` 拆成助手面开关与常驻后端开关，使两个语义地位不同的面可独立选择 | 打开其一不再强制打开另一个 |
| CP-3 | 清退使 RB10 的 G-A/G-B 裁定得以成立的私有序列残留：既然只有测试与已被取代的 RB9 探针还在调用，就降级或移除 `CudaResidentBackend` 上的公共 `publish_stage`/`partial_sync_commit`，并加一条断言常驻后端不暴露任何非 SPI 整窗推进入口的门禁 | 没有调用方能绕过 SPI 推进窗口；等价性主张从偶然变为结构强制 |
| CP-4 | **G-D：提权下采集 achieved 计数器**——全部 10 个 kernel 的 occupancy、divergence、global/local/shared 流量。这是唯一的硬阻塞，也是价值最高的一次迭代 | G-D 以真实计数器关闭，或记录第二次外部阻塞 |
| CP-5 | 由 CP-4 结果驱动的 kernel 层优化，已知候选见下 | 相对 CR2-6b 基线有实测改善 |
| CP-6 | G-C：经 CR2-3 lease 的 learner 等价消费，不含隐藏 host 校验回读 | 真实消费者，而非诊断 smoke |
| CP-7 | G-F 处置：修复小批量开销，或冻结带 world 数阈值的显式选择规则 | world 1 不再是静默退化 |
| CP-8 | CP-5/CP-7 落地后重测 1/4/16/64/256 矩阵，顺序对调，两轮 campaign | 优化后证据可与 CR2-6b 比较 |
| CP-9 | 晋升决策：全部门禁加独立评审，或记录带确切缺失授权的 hold | 显式、有证据支撑的裁定 |

CP-1、CP-2、CP-3 与其余项独立，可任意顺序落地。CP-4 是 CP-5 的前置。CP-8 跟随 CP-5
与 CP-7。CP-9 需要 CP-3 至 CP-8 全部完成。

**若按价值排序，CP-4 应当最先做。** 因为 CR2 已经修复了调用面门禁，achieved 计数器
阻塞是现有证据基础与「在测量层面作出晋升决策」之间唯一的障碍。它同时也是成本最低的
一项：需要的是一个提权 shell，而不是代码改动。

## 发现的 CP-4 阻塞：资源探针在 CR2 关闭后被退役

尝试采集计数器时发现，在 G-D 之前还横着第二个阻塞，两份关闭文档都没有记录它——因为它
是在两者都关闭之后才引入的。

`ef_cuda_resident_resource_probe`——CR2-5a 与 CR2-5b 所剖析的那个冻结 Release/SM86
二进制——**已不再是一个可用的探针**。语义阶段迁移
（`cuda_resident_semantic_stage_migration_20260807.md`，随 PR #25 以 `8884146b` 落地）
把它 350 行的主体替换成了一个 18 行的 fail-closed 存根：

```
CUDA resident resource probe retired: semantic kernel catalog requires a
versioned resource-evidence recapture
```

`src/runtime/contracts/cuda_resident_resource_evidence_contract.h` 中的
`kCaptureProbeV1Retired = true` 以 `static_assert` 强制这一点。

**这次退役是正确的，不得简单回退。** 迁移记录把理由写得很清楚：冻结的证据契约及其
捕获的 JSON「描述的是一个历史二进制，而不是被重命名后的当前源码。新的资源主张需要新的
schema 版本和新的捕获；现有探针必须在旧的 trace signature 上 fail closed，而不是把历史
证据重新贴标签。」

### 实际改变了什么，以及没有改变什么

这次重命名是同一批十个 kernel 的纯 1:1 relabel。把契约的冻结目录与当前 `.cu` 源码对照：

| 契约目录（冻结，历史） | 当前源码符号 |
| --- | --- |
| `prepare_phase_a_controls_kernel` | `control_preparation_kernel` |
| `phase_b_forces_kernel` | `flight_dynamics_forces_kernel` |
| `phase_b_aerodynamics_kernel` | `flight_dynamics_aerodynamics_kernel` |
| `phase_b_integrate_kernel` | `flight_dynamics_integrate_kernel` |
| `phase_d_instruments_kernel` | `instrument_projection_kernel` |
| `phase_d_configuration_kernel` | `configuration_projection_kernel` |
| `phase_d_episode_kernel` | `episode_projection_kernel` |
| `phase_d_pack_observation_kernel` | `pack_device_observation_kernel` |
| `phase_d_consumer_smoke_kernel` | `device_observation_consumer_smoke_kernel` |
| `apply_barrier_kernel` | `apply_barrier_kernel`（未变） |

之前十个 kernel，之后仍是十个；契约中的 launch 次数（12）、grid（`2x1x1`）、
block（`128x1x1`）与 world 数（256）均未改变。因此重捕获是针对重命名符号的重新冻结，
不是重新推导执行图。契约中的 trace signature `cb31675ee34e5015` / 80,469 字节仍与
CR2-5a 的证据 JSON 相符——这正是它必须 fail closed 的原因：该摘要描述的是重命名之前的
二进制。

### CP-4a 结果：重捕获完成并已验证

v2 重捕获已落地，且精确复现了冻结捕获。

契约：`kKernelSpecsV2` / `kLaunchSequenceV2` 承载语义符号，
`kKernelSpecsV2Migration` 钉住与 v1 的 1:1 对应。四条新增 `static_assert` 在编译期强制
它——v2 目录完整性、迁移表双向双射、以及相同索引上的 launch 逐一对应。v1 目录、trace
摘要与 profile id 均未改动。

探针：依照语义访问器恢复，输出 schema `cuda_resident.cp.resource_capture_probe.v2`，
并以 `supersedes_schema_version` 指向 v1。相比 v1 探针增加了两点：
`require_catalog_alignment` 在输出行与 v2 目录漂移时 fail closed；报告携带
`achieved_counters_present: false`，使静态捕获永远不会被误认为计数器捕获。CMake 恢复了
后端、profiler 与 JSON 依赖——退役时提出的前置条件（「带版本的 kernel 目录」）现已满足。

在 RTX 3090 / CUDA 13.0.88 上的验证：

| 检查项 | 结果 |
| --- | --- |
| Trace signature | `cb31675ee34e5015` / 80,469 字节——**与 v1 完全一致** |
| Kernel 资源表 vs 冻结 v1 | **10 个 kernel 零差异**（寄存器、栈字节、共享内存、理论 occupancy、每 SM 块/warp 数） |
| `ef_cuda_resident_lifecycle_test` | 14 用例 / 599 断言通过 |
| `ef_cuda_resident_replay_test` | 4 用例 / 77 断言通过 |
| 内部代号治理审计 | **0 error、0 warning**（这两个文件的基线为 37 error） |

零差异这个结果是承重的：它意味着重命名确实只是表面的，v2 捕获测量的是同一张执行图，
下文三条优化线索可以原样沿用而无需重新推导。它同时确认工具链升到 CUDA 13.0 并未改变
寄存器分配或 occupancy。

治理说明：冻结的 v1 目录以及迁移表的 v1 一侧必然包含字母阶段标识符，内部代号门禁会标记
它们。每一处都按行标注 `internal-code: compatibility` 并写明理由，而不是重命名——重命名
会使它们所索引的证据失效。

### CP-4b 结果：重复目录已消除

`tools/diagnostics/` 下的静态资源解析器自带一份硬编码的 kernel 目录副本。其文件名为
`cuda_resident_cr2_resource_static.py`，其中 `cr2` 表示历史上的 runtime program 2
标签，因重命名模块超出本次范围而保留。这个第二所有者正是漂移的直接成因：迁移重命名 kernel 时，C++ 契约动了，却没有任何
机制强制 Python 侧跟随，于是采集器继续针对已不存在的符号做校验，并且不报任何异常。

该模块现在从 C++ 契约解析两份目录，使契约成为单一所有者。`kernel_catalog(1)` 与
`kernel_catalog(2)` 分别返回冻结目录与语义目录；保留的 `KERNELS` 别名仍指向 v1，因此
所有现存 v1 校验器及其检查的冻结证据都不受影响。未知版本会抛错，而不是静默返回一个看似
合理的结果。

三条测试替换了原先那条退役测试——后者断言探针保持存根状态，因此按设计被 CP-4a 推翻：

- `test_frozen_v1_capture_identity_survives_the_semantic_kernel_migration`——
  v1 的目录、摘要与 profile id 不得跟随重命名。
- `test_v2_capture_supersedes_v1_without_reviving_the_retired_probe`——v2 存在、
  退役标记存续、五条 `static_assert` 齐备，且每个 v2 符号都是当前 `.cu` 源码真实产出的。
- `test_python_kernel_catalog_has_no_second_owner`——字面目录不可被重新引入、两份解析出的
  目录与契约一致、v1/v2 形状相同而命名不同。

第三条测试正是原本能抓住这次漂移的那一条。

### CP-4c：在花掉一次提权运行之前发现的阻塞

单靠提权无法产出可用的计数器证据。把采集链对照 v2 探针检查后，又浮现两个阻塞，值得在
请求操作员介入之前记录下来。

**1. 两个采集器都钉在 v1 身份上。** 计数器采集器设置 `PROFILE = resource.PROFILE`，
其值为冻结的 v1 profile id `cr2.resource.steady_full_window_body.sm86.v1`，其中 `cr2` 表示历史上的 runtime program 2 标签。
它随后校验
`parent["profile_id"] == PROFILE`。v2 探针输出的是
`cp.resource.steady_full_window_body.sm86.v2`，因此该次运行会因 profile 不匹配被拒。
计数器采集器还要求一份**父级资源证据 JSON**，并用它核对 v2 报告的 `binary_sha256` /
`probe_sha256`——而目前不存在 v2 父级产物，因为产出它本身需要先跑一次自己的采集。

所以真实的链条是：必须先产出并接受 v2 静态证据 JSON，v2 计数器尝试才可能通过校验。
两个采集器都需要一条版本感知的身份路径，与 CP-4b 对 kernel 目录所做的一致。

**2. ~~已安装的 Nsight Systems 版本低于钉住的版本。~~ 撤回——这条阻塞是我的错误。**
资源 schema 校验器要求 `nsight_systems_version == "2025.3.2"` 精确匹配，而**本机确实装有
2025.3.2.474**。原先「只有 2024.6.2 与 2022.4.2」的说法源于我列出 Nsight 安装根目录时只读了
前两项，没有枚举全部条目。Nsight Compute 同样没问题：已装 2025.3.1，采集器要求恰好
`2025.3.1.0`。

因此当初给出的三条路径——安装 2025.3.2、把钉定放宽为版本区间、接受无父级计数器——全部
失效。钉定与实际一致，无需改动，也不必削弱任何溯源门禁。此处保留记录而非删除，因为所有者
据此选择了「安装 2025.3.2」，而结果不应看起来像真的执行过一次安装。

### CP-4c-B 结果：采集器已版本感知

阻塞 2 撤回后，阻塞 1 是唯一真实的前置条件，现已关闭。

- schema 校验器（`cuda_resident_cr2_resource_schema.py`：其中 `cr2` 表示历史上的
  runtime program 2 文件名前缀，全文沿用）新增 `SCHEMA_V2` / `PROFILE_V2` 与
  `schema_version_of()` 分派器。`validate_report` 现在按报告自身声明的世代校验：v1 保持其
  精确冻结的 `evidence_date`、`baseline_commit` 与 `candidate_state` 钉定；v2 接受自己的
  ISO 日期与 commit，但仍必须声明 `*_unpromoted_worktree` 状态——重捕获不授予任何权限。
- `LAUNCH_SEQUENCE` 是契约数据的第三份副本，现已改为经静态模块新增的
  `launch_sequence(version)` 从契约派生，与 `kernel_catalog(version)` 并列。
- 证据采集器，其 `cr2` 表示同一历史标签：`cuda_resident_cr2_resource_evidence.py`。
  它新增 `PROBE_SCHEMA_V2`，接受两个世代各自的键集。
  v2 探针还必须声明它取代的 schema、断言 `trace_signature_matches_v1`，并携带
  `achieved_counters_present: false`，使静态捕获永远不会被读成计数器捕获。

已核实：冻结的 v1 证据仍逐字节按 v1 通过校验；v2 探针输出现已被采集器接受；未知世代
fail closed 而非回退到 v1；25 条测试通过。

这相对 CP-0 的估计是一次真实的成本上升，值得说明它为何发生：语义迁移正确地拒绝了给冻结
证据重新贴标签，但它在没有替代物的情况下退役了唯一的捕获工具，于是下一次计数器尝试继承了
一笔重捕获债务。CP-1 的编译通道**抓不到**这个问题——存根本身编译正常。探针可执行性检查
应当纳入 CP-1 的范围。

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

理论 occupancy 不得在任何 CP-5 论证中替代 achieved occupancy。上述三条线索是针对重命名
之前的 kernel 名陈述的；CP-4a 已针对当前符号逐一重建，数值零漂移，因此它们可以直接沿用
（把 `Phase B forces` 读作 `flight_dynamics_forces`，其余按迁移表类推）。

## G-D 已关闭：achieved 计数器采集完成（2026-08-09）

阻塞 RB9 与 CR2-5b 的外部障碍**已解决**。在提权下，Nsight Compute 2025.3.1 完成了
全部 12 次 launch 的 profiling（每次 42-43 个 replay pass），写出 19,049,324 字节的
报告（`sha256 ebdec20b3f8b37a42ccb409855013112b6df196948ea1edd5c9d643baee59553`），
没有 `ERR_NVGPUCTRPERM`。未提权的一轮先行执行并精确复现了前序阻塞，因此差异可完全归因于
提权本身。

`--set full` 捕获了 1,699 个 metric 列。256 worlds 下五个必需族的逐 launch achieved 值：

| 族 | Metric | 结果 |
| --- | --- | --- |
| achieved occupancy | `sm__warps_active.avg.pct_of_peak_sustained_active` | 8.33-10.89%，均值 9.24% |
| divergence | `smsp__thread_inst_executed_per_inst_executed.ratio` | 每次 launch 均为 32.00 |
| local 流量 | `l1tex__t_sectors_pipe_lsu_mem_local_op_{ld,st}.sum` | 全部 12 次 launch **为 0** |
| global 流量 | `l1tex__t_sectors_pipe_lsu_mem_global_op_{ld,st}.sum` | 读 64-3,664 / 写 72-3,904 sector |
| shared 流量 | `l1tex__data_pipe_lsu_wavefronts_mem_shared.sum` | 8-24 wavefront |

### 三条静态线索全部被否证，而非被确认

1. **40 字节栈帧没有可测代价。** 每次 launch 的 local-memory sector 精确为零，包括
   ptxas 报告带 40 字节栈帧和 `LDL.64`/`STL.64` 指令的那四个 kernel。这些指令确实存在于
   SASS 中，但不产生任何可测 local 流量——与地址在 L1 内解析、未触及 local memory 路径
   一致。线索 1 关闭：没有栈流量可供消除。
2. **occupancy 不受寄存器限制。** `launch__occupancy_limit_registers`、`_blocks`、
   `_shared_mem` 均报告 16，而 `_warps` 报告 12，因此寄存器不是约束条件。寄存器压力实验
   不会改变 achieved occupancy。线索 2 按原表述关闭。
3. **线索 3 才是全部原因，且它是一个 grid 尺寸问题。** 每次 launch 都是 256 线程
   （2 blocks x 128）= 8 个 warp。RTX 3090 有 82 个 SM x 48 驻留 warp = 3,936 个 warp
   槽位，因此该 grid 只占用机器的 0.20%，落在 82 个 SM 中的 2 个上。achieved 9.24% 比
   CR2-5a 的 58.33% 理论下限还低 6.3 倍，原因是理论 occupancy 是「若驻留则每 SM」的
   指标，完全不说明 grid 是否大到足以占满设备。

divergence 为 32.00 是 32 lane warp 上的最大值，即**零 divergence**——完全收敛，不是
32 倍 divergence。一 world 一线程的分解在分支效率上是好的，它只是太小了。

### 这对后续的重定向

CP-5 不应追求寄存器压力或栈消除。实测结论是这些 kernel 在一台近乎空闲的设备上受延迟约束，
因此 CP-5 的候选变成分解方式本身：每个 world 提供更多并行度（使 256-world 批次产生远多于
256 个线程），或把多个窗口合批以提高 grid 尺寸。这一点也很可能关系到 G-F——设备在 256
worlds 时就如此空闲，可以解释 world 1 为何以 7-36 倍落后于 CPU。

以上两点都是测量结果，尚不是已验证的优化。CP-5 在任何改动后必须重新测量；本节记录的是
计数器所显示的事实，不是「更大的 grid 一定更快」的承诺。

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
