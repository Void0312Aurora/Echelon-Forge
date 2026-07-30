# CUDA 驻留后端分支迭代账本

语言版本：

- 英文规范版：[cuda_resident_backend_iteration_log_20260729.md](cuda_resident_backend_iteration_log_20260729.md)
- 中文伴随版：`cuda_resident_backend_iteration_log_20260729.zh.md`

- 文档类型：分支内迭代与审阅账本
- 生命周期：`codex/cuda-resident-backend` 活跃期间维护
- 计划权威：[cuda_resident_backend_program_20260729.zh.md](cuda_resident_backend_program_20260729.zh.md)
- 基线：`395e02b7dfeaa87baedb2611ec503d14ab137ce3`

状态：**RB0 至 RB6 已 accepted。当前仅授权 RB7 实现；RB8-RB11 仍受依赖门控。**

本账本只记录分支内证据，不分配中央 `I<n>` 验收行，也不声称分支提交已经落入
维护分支。每行的最终提交身份以本分支历史为准。

## RB0 - 计划冻结

- 提交：`e7f3b144`（`docs: freeze CUDA resident backend program (RB0)`）。
- write set：双语计划、exact-runtime 索引、上级计划索引，以及上级索引要求的
  选择性双语登记记录。
- 非目标：不改 C++、CUDA、Python、CMake、测试、runtime profile、capability
  flag 或 support projection。
- 验证：双语 companion/registry、局部链接审计与 `git diff --check` 通过。
- 独立审阅：`/root/rb0_plan_review`，staged patch
  `09593c539c946f19f4b5bf45c90d35f11b6f62b0`，零 blocker，`APPROVE`。

## RB1 - 语义后端接缝与 CPU adapter

### 冻结 write set

- facade 内部 backend SPI、兼容端口与 `FlecsCpuBackend`；
- `RuntimeFacade` 的所有权及转发实现；
- 为使语义 SPI 不依赖 Flecs runtime 与 GPU visual 类型而需要的共享近期交战
  事件契约；
- 构建登记、C++ 契约探针、聚焦 runtime/architecture 测试、schema freshness
  元数据，以及本账本/状态更新。

### 非目标

- 不增加 `CudaResidentBackend`、CUDA 分配或仿真 kernel；
- 本轮不增加 backend request/profile admission；
- 不晋级公开 support flag 或 capability；
- 不改变 CPU 行为，不增加隐式 fallback、公开 ABI 或进入语义后端契约的 GPU
  指针。

### 结果

- `RuntimeFacade` 现在持有 `std::unique_ptr<IWorldBatchBackend>`，并构造实际使用的
  `FlecsCpuBackend` 组合 adapter；`WorldBatchRuntime` 继续保持非多态。
- 语义请求 DTO 使用指针大小、非 owning 的 `VectorBatchView<T>` 引用仍存活的
  caller vector；删除 rvalue-vector 构造，接缝不会复制热批次或接收临时容器。
- 只读执行评估映射到后端 `evaluate(...) const`，有状态 advance 保持为独立操作。
- 旧 visual/GPU 形态调用隔离在 `IWorldBatchCompatibilityPort` 后，不污染语义 SPI。
- `RecentEngagementEvents` 只有一个共享 contract owner；engine header 仅做兼容
  re-export，生成 schema 与 Python binding 路径指向同一字段源。
- CUDA-disabled 与 CPU-default 行为不变。

### 验证

- CUDA-off Release 的 `ef_test`、`ef_py` 构建：通过。
- `ef_test`：`147/147` test cases、`19,161` assertions 通过。
- runtime-facade architecture/core/counterfactual 与 DTO freshness 选择：
  `104 passed`。
- 审阅修复后的结构/事件选择：本地和独立复跑均为 `11 passed`。
- 变更 C++ 的 `clang-format --dry-run -Werror`、变更 Python 的 `ruff` 以及
  `git diff --check`：通过。

更宽测试中有两个环境/基线项不归因于 RB1，且不进入本轮 write set：一个未改动
的 window-loop 源文本预期，以及本地环境缺少可选 `stable_baselines3` import。

### 独立审阅与修复历史

1. 初审阻断了 runtime-shaped interface、机械镜像的 runtime 路径、
   `WorldBatchRuntime` 多态漂移及无法证明 facade cutover 的测试；实现改为语义 SPI
   加组合 adapter。
2. 复审阻断 owning-vector 请求 DTO，以及把 const evaluation 映射到有状态
   advance 的路径；两者分别改为非 owning view 和独立 const 后端方法，同时把
   重复事件批定义收敛到共享 contract。
3. 最终审阅发现两个结构测试仍把旧 header 当作事件定义 owner；已在不放松
   SimulationKernel 隔离门的前提下修正所有权断言。
4. `/root/rb1_backend_review` 独立复跑修复选择，并批准
   `git hash-object --stdin` 标识为
   `3703fcd6f05a57f38df3c310e2fc595bf9cee849` 的 staged code/test 候选。

结论：**允许形成一个 RB1 提交**。下一步只授权 RB2：显式 backend
request/admission、候选 capability manifest/profile，以及 profile-owned
selected-slice parity/barrier budget。CUDA 生命周期与 dynamics 在后续行开启前仍
禁止实现。

## RB2 - 候选准入与冻结 parity 契约

### 冻结 write set

- 显式 backend request/admission DTO 与 facade preflight；
- 有界 fixed-step air-execution capability manifest；
- 既有 `resident_state.unmaintained_candidate` profile 所有的 parity budget、
  selected-slice 字段描述与 barrier 规则；
- 未来 clock、snapshot、event-order 与 export-envelope 的类型化契约；
- Python binding、构建登记、C++/Python 契约测试及本计划/账本状态更新。

### 非目标

- 不增加 CUDA backend object、device allocation、store、kernel 或 dynamics；
- 不替换 active backend，不增加隐式 CPU fallback 或扩展 `RuntimeBatchConfig`；
- 不让 compiled backend 宣称 manifest，不晋级公开 support flag、maintained
  profile 或 capability；
- 不把实现前 comparator threshold 表述成经验 accuracy 或 performance 结论。

### 结果

- CPU reference selection 继续是 maintained 默认。候选选择要求显式 opt-in、
  profile/budget/manifest 所有权精确匹配、受信 compiled-backend 信号，以及精确
  supported-manifest 声明。`RuntimeFacade` 不提供 experimental availability 或
  supported manifest，因此候选继续 fail-closed。
- 有界 manifest 拥有 canonical required、supported、forbidden feature vector；
  已知 manifest 必须与完整 canonical object 相等，所以从 forbidden 删除
  `communications` 再把它加入 supported 会被拒绝。
- parity budget 冻结 11 个 family 与 93 个完整 descriptor：field path、surface
  owner、current/future status、value kind 与 shard。当前 DTO 成员及未来类型化
  contract 成员均有编译期探针。
- `observation.id`、event order、snapshot identity、termination identity 与
  export-envelope identity 使用 exact comparator；近似 comparator 只接受浮点
  字段。kinematics 使用 `1e-9` absolute / `1e-12` relative；instrument、
  observation、reward numeric family 使用 `1e-8` / `1e-10`。这些数值是冻结给
  后续实测的 parity gate，不是已验证的模型误差界。
- Snapshot identity 显式映射 `world_id`、`global_version`、`barrier_id`、
  `barrier_sequence`、`shard_versions` 与类型化 `lineage`。
- `input_injection`、`stage_publish`、禁用的 `partial_sync_commit`、
  `window_commit`、`export` 是精确 canonical rule；event 与 export envelope 字段
  只在 `export` 可见/可比较，也只有该处存在 host truth。

### 验证

- CUDA-off Release 的 `ef_test` 与 `ef_py` 构建：通过。
- `ef_test`：`153/153` test case、`19,297` assertion 通过。
- RB2 C++ 选择：`5/5`、`127` assertion；RB2 Python 选择：`7 passed`。
- 变更 C++ 的 `clang-format --dry-run -Werror`、变更 Python 的 `ruff` 以及
  `git diff --check`：通过。
- 更宽 facade 选择为 `41 passed, 6 failed`：一项是未修改的旧 source-text
  expectation，五项是既有测试 helper 硬编码了工作树中不存在的
  `build-local-win` Flecs 路径。独立审阅已复现并判定它们不属于 RB2 因果面。

### 独立审阅与修复历史

1. 初审阻断了包含 `observation.id` 的近似 comparator、过早的 event/export
   visibility、不完整 barrier 语义及 string-only selected field；契约改为类型化
   descriptor、精确 canonical barrier、成员探针及 mutation test。
2. 复审发现三个可复现假绿：可选 manifest 扩张、exact snapshot identity 不完整、
   测试没有比较完整 descriptor object。canonical manifest equality、完整类型化
   snapshot identity 与独立 93-object 预期清单关闭了这些缺口。
3. `/root/rb2_contract_review` 独立复跑修复候选，并以零 blocker 批准 staged raw
   hash `c9355e69644a81262df23ebe47e802225b6371c3`（stable patch-id
   `8e3531b8fd071579ac6ea431c18d93f540001e6b`）。

结论：**允许形成一个 RB2 提交**。下一步只授权 RB3：实例拥有的
`CudaWorldStore`、`CudaResidentBackend` 生命周期壳与 CUDA-off stub。RB3 不得宣称
有界 manifest，不得实现 simulation dynamics，也不得复用旧 GPU helper experiment
中的全局 singleton cache。

## RB3 - 实例拥有的 CUDA 生命周期壳

### 冻结 write set

- 独立的 `ef_cuda_resident_backend` target 与 target-private CUDA 编译开关；
- 实例拥有的 `CudaWorldStore` allocation/reset/teardown owner 及 CUDA-off stub；
- 实现内部 backend SPI、但拒绝所有语义操作的 `CudaResidentBackend` 生命周期壳；
- CUDA 生命周期元数据 allocator、精确测试 readback/fault seam、聚焦 C++ target、
  架构测试及本双语状态更新。

### 非目标

- 不接管 facade，不宣称有界 manifest，不晋级 support flag，不增加隐式 Flecs/CPU
  fallback；
- 不实现 content load、setup、input injection、evaluation、advance、export、
  simulation dynamics、kernel graph 或 physics state；
- 不复用旧 GPU helper 全局 cache，也不宣称生命周期元数据已构成 maintained
  runtime backend。

### 结果

- `CudaWorldStore` 为每个 backend 实例提供一个不可复制/移动的 PIMPL owner。
  CUDA-off configure/reset fail closed，且不改变 capacity 或 generation。
- CUDA-on 生命周期元数据由一块有边界检查的 device allocation 持有两个 epoch。
  Reset 先在 host 构造完整新 epoch，再以一次 copy 写入 inactive slot，只有 copy
  成功才切换 active slot，因此 seed 与 reset-generation 不会形成可见混合状态。
- allocation/release/reset fault 按 store 注入，不使用全局状态。精确 device readback
  证明显式 seed、空 seed 归零、generation、成功 reconfigure，以及 allocation、
  reset-copy 或 release 失败后旧 active allocation 仍被保留。
- 仅在同步与 `cudaFree` 都成功后才清空 owner。active release 失败保留旧 owner；
  replacement 若也不能释放，则由 `pending_cleanup` 保持可达，供后续
  configure/teardown/destructor 重试。
- allocation/reset generation 在 `uint64_t` 回绕前 fail closed。backend 必须提供的
  `configuration() noexcept` 只读标量 capacity accessor，不再复制 diagnostic error
  string。
- 所有语义 backend 操作继续明确抛出 `logic_error`，compatibility port 继续为空，
  `RuntimeFacade` 也继续不暴露 compiled experimental backend 或 supported manifest。

### 验证

- CUDA-off Release 的 `ef_test`、`ef_py` 与聚焦 lifecycle target 构建通过。聚焦
  lifecycle：`2/2`、`32` assertions；完整 `ef_test`：`155/155`、`19,329`
  assertions。
- 相关 admission/lifecycle Python 选择：`9 passed`。
- CUDA-on MSVC/NVCC 聚焦 target 编译全部 RB3 production source：`2/2`、`95`
  assertions。Compute Sanitizer memcheck：`0 errors`、`0 bytes leaked in 0
  allocations`。
- 变更 C++ 的 `clang-format --dry-run -Werror`、变更 Python 的 `ruff` 与
  `git diff --check`：通过。
- CUDA-on 完整 `ef_test` graph 仍受 `ef_core` 既存 MSVC portability debt 阻断
  （`__builtin_ctz`、`M_PI` 及相关既有诊断）。聚焦 target 有意隔离该 graph，但
  编译完整 RB3 target；这是环境/基线限制，不代表完整 CUDA-on suite 已通过。

### 独立审阅与修复历史

1. 初审阻断了忽略 `cudaFree` 结果/owner 丢失、可能暴露新 seed 与旧 generation 的
   两次 copy reset、无法发现 device no-op 的 host-only 测试、
   `configuration() noexcept` 下的 allocating 路径及 generation 回绕。
2. allocator 改为单 allocation 双缓冲设计；release ownership 改为感知状态且可
   重试；增加精确 device readback、按实例 allocation/reset-copy/release fault 与
   exhaustion 测试。第二次 `cudaMalloc` 的泄漏窗口由结构性删除，而不是遮蔽。
3. `/root/rb3_lifecycle_review` 独立复跑修复候选，并批准 staged raw hash
   `7ce020d5e055302d3ac38c85e85e42ab2af37f0c`（stable patch-id
   `1c6bc2c884077796b2dc97341d10f999fcb98b7c`），无 blocking 或 non-blocking
   finding。

结论：**允许形成一个 RB3 提交**。下一步只授权 RB4：setup/reset、input
injection、device clock 与 shard version、RB2 已冻结的 partial-sync/window/export
barrier，以及最小 fixture 的显式 snapshot reconstruction。RB4 必须维持零隐藏
Flecs step/fallback，不得提前实现 RB5-RB7 dynamics 或宣称有界 manifest。

## RB4 - 固定空战驻留状态与 barrier 壳

### 冻结 write set

- CPU reference 测试与 CUDA candidate 独立消费的共享固定空战 fixture
  identity/schema contract；
- backend-private 双 slot SoA 状态：identity、选定 pilot controls、kinematics、
  clock、snapshot/barrier identity 与 shard versions；
- setup/reset、选定 input injection、stage publish、禁用 partial sync、window
  commit 与显式最小 snapshot reconstruction；
- CUDA-on/CUDA-off 聚焦测试、CPU reference identity 测试、架构守卫、kernel
  resource 报告、CMake 接线与本双语状态更新。

### 非目标

- 不实现 Phase A/B/D dynamics、instruments、observation、reward、termination、
  event production、learner device view、facade takeover 或 manifest/support 宣传；
- 不调用 Flecs step 或 `WorldBatchRuntime`，不增加 CPU fallback，不逐 stage host
  write-back，也不声称当前局部 export 已满足完整 RB2 comparison/host-truth contract；
- 不宣称 zero-copy：完整 slot D2D staging 是明确的 RB4 事务基线，留待后续实测
  迭代优化。

### 结果

- Setup 产生与独立 `FlecsCpuBackend` reference 相同的基线锁定
  `(world_index, entity_id, generation)` identity，且两侧测试互不调用；重复 setup
  递增 entity generation。
- 一块 device allocation 持有两个 lifecycle epoch 与两个 packed SoA state slot。
  每次 reset、input、stage 与 window mutation 都先在 inactive slot 构造；各操作仅在
  其适用的 copy 成功后切换 active slot，其中 input、stage 与 window 还要求窄
  barrier kernel、同步与 overflow status readback 全部成功。
- input barrier 提交选定 pilot controls；stage publish 只推进 barrier identity；
  partial sync 保持禁用；window commit 推进 device clock，且只递增 RB4 已实际物化
  的版本，未实现 dynamics/episode/output shard 保持 version `0`。
- 显式 export 重建类型化 clock、snapshot identity、lineage、kinematics 与 exact
  field-set envelope。它同时报告 RB2 required visible shards 与较小的 RB4
  materialized set，因此在后续 phase 补齐完整 contract 前，contract satisfaction、
  comparison eligibility 与 host truth 均明确为 false。pilot controls 不经 export 泄漏。
- state readback 仅对 export/testing 私有，并在任何 D2H 前检查 host setup 状态。
  configure-only、reset-only 与 failed-setup 状态均 fail closed，不读取未初始化 device
  storage；zero capacity 明确产生空 snapshot。
- `RuntimeFacade` 仍不宣称 compiled experimental backend、supported manifest、
  resident-state support、exact-GPU support 或 device observation view。

### 验证与资源证据

- CUDA-on MSVC/NVCC 聚焦 target：`4/4`、`233` assertions；Compute Sanitizer
  memcheck：`0 errors`、`0 bytes leaked in 0 allocations`。
- `apply_barrier_kernel` 的 `ptxas`：每 thread `30` registers、`0` spill stores、
  `0` spill loads、`0`-byte stack frame、`0` barriers。本机 RTX 3090 的 runtime API
  报告 128 threads/block、每 SM 12 active blocks、48 active warps、theoretical
  occupancy `1.0`。这些是 resource/theoretical 值，不是 achieved counter 实测。
- 聚焦且 readback-heavy 的 fault-test workload 下，Nsight Systems 记录 3 次 barrier
  kernel、总计 `6,176 ns`（median `1,984 ns`）；4 次 D2D、总计 `5,409 ns`；18 次
  H2D、总计 `11,170 ns`；38 次 D2H、总计 `59,522 ns`。cold allocation 与
  diagnostic export 主导该测试 trace，不能作为 production performance 证据。
- Nsight Compute counter collection 受 `ERR_NVGPUCTRPERM` 阻断，因此不推断
  achieved occupancy、divergence 或 memory counter，留待权限可用后补测。
- CUDA-off 完整 `ef_test`：`158/158`、`19,346` assertions；CUDA-off 聚焦 target：
  `4/4`、`35` assertions；相关 admission/lifecycle 架构选择：`7 passed`。变更 C++
  clang-format、变更 Python ruff 与 `git diff --check` 均通过。
- CUDA-on 聚焦 target 编译全部 RB4 production source。完整 CUDA-on `ef_test`
  graph 仍不纳入本轮通过声明，因为存在 RB3 已记录的既有 MSVC portability debt。

### 独立审阅与修复历史

1. `/root/rb4_state_review` 初审阻断了给空 dynamics/episode shard 分配版本，以及把
   RB2 完整 required set 误标为已 materialized 的 export evidence。修复后
   required/materialized evidence 分离，空 shard version 保持 0，且不完整 host truth
   明确可见。
2. 复审阻断了 post-configure 未初始化 slot 的 D2H，以及遗漏 `seed`、
   `reset_generation` 与 `source_barrier_id` 的 export envelope。host setup gate 加
   configure/reset/failed-setup 拒绝测试关闭前者；exact field-set equality 关闭后者。
3. 审阅者批准 implementation raw hash
   `a65387063425f2fe867b2eaee9898acfbe29716d`（stable patch-id
   `f2deb2a3ade9a6ddf810631ff8024a0d39aa59e9`），零 blocking、零 non-blocking finding。

结论：**允许形成一个 RB4 提交**。下一步只授权 RB5：为同一有界 fixed-air slice
实现 Phase A，形成 stage-local CPU-reference parity 与新的 register/spill 报告，并
继续拒绝 unsupported control feature。RB5 不得吸收 Phase B airframe dynamics 或
Phase D output projection，也不得提前宣称有界 manifest。

## RB5 - Phase A 直接飞行员控制准备

### 冻结 write set

- 共享的 direct-pilot Phase A fixture contract：冻结输入、滤波期望、deadband、
  rudder 符号以及 CPU `ecs_ftime_t` 精度规则；
- backend-private prepared-control SoA、valid/manual-takeover 标志、phase version、
  kernel resource query 与 Phase A stage 事务；
- 与维护 CPU command surface 一致的 assignment `active` 规范化，同时保持 raw
  controls 与 prepared controls 分离；
- input、stage publish、window commit 之间的 `phase_a_ready` freshness gate；
- CUDA-on/CUDA-off CPU 与 CUDA 测试、不支持 radar/weapon 拒绝、架构守卫、CMake
  接线与本双语账本更新。

### 非目标

- 不实现 Phase B airframe dynamics、propulsion、forces、surfaces/actuators、
  instruments、observation、reward、termination、events、mission commands 或
  learner/device projection；
- 不从 CUDA candidate 步进 Flecs，不加 CPU fallback、不逐阶段 host write-back，
  不接管 facade、不晋级 capability manifest、不改变 support flags；
- 不从本阶段局部 trace 声称性能收益，不在端到端证据前使用 `--maxrregcount` 或
  launch-bound tuning。

### 结果

- `prepare_phase_a_controls_kernel` 读取既有 `[pitch, roll, rudder, throttle, brake]`
  raw SoA，写入独立语义 `[roll, pitch, yaw, yaw_cmd]` prepared SoA。manual takeover
  使用维护 CPU 的严格 `> 0.05` primary-axis deadband；rudder 取负；一阶滤波
  `tau=.15 s`，并显式镜像 Flecs 当前 `float` 时间标量边界。
- 一次 pilot assignment 会规范化为 `active=true`，与维护中的
  `SimulationKernel::set_pilot_action` 一致；exact-deadband 与 payload 规范化案例
  都进入共享 trace。prepared 值携带 valid、takeover 与单调 phase-version 元数据，
  但不进入 RB2 export shard contract。
- stage publish 先复制 active slot 到 inactive slot，再运行一个专用 Phase A kernel，
  检查 device status/同步，最后执行现有 stage barrier 才切换 active。overflow 与
  non-finite fail closed；copy、kernel status 或 barrier 失败都保留旧 active slot。
  window commit 在成功 Phase A publish 前拒绝；成功 window 消费 freshness token。
- radar、weapon 及其他未声明 controls 仍拒绝；facade 仍不宣称 experimental backend、
  supported manifest 或 fallback path。

### 验证与资源证据

- CUDA-off Release 完整 `ef_test`：`159/159` test cases、`19,374` assertions；RB5
  CPU oracle：`1/1`、`28` assertions。
- CUDA-on MSVC/NVCC 聚焦 target：`5/5` test cases、`276` assertions。`sm_86` 的
  `ptxas`：`apply_barrier_kernel` 为 `30` registers/thread，
  `prepare_phase_a_controls_kernel` 为 `34`，两者均为零 spill stores、零 spill loads、
  零字节 stack frame。runtime API 报告 128 threads/block、12 active blocks、48 active
  warps、theoretical occupancy `1.0`（本机 RTX 3090）；这些是 theoretical 值，不是
  achieved counters。
- 最终 RB5 Compute Sanitizer memcheck：`0 errors`、`0 bytes leaked in 0 allocations`。
  相关架构选择：`10 passed`；变更 C++ clang-format、变更 Python ruff、`git diff --check`
  均通过。Python 选择绑定到隔离 CUDA-off 构建目录中的本地 `ef_py` artifact。
- CUDA-on 聚焦 target 是本轮编译通过证据；完整 CUDA-on `ef_test` graph 仍不纳入通过声明，
  因为 RB3 已记录的既有 MSVC portability debt 仍在。

### 独立审阅与修复历史

1. 第一轮长时间运行的审阅未修改工作树且未返回结论，随后启动新的独立只读审阅，避免
   把不可观测进程当作批准。
2. `/root/rb5_review_final` 独立检查未提交 candidate，返回 `APPROVE`，零 blocking finding；
   明确核验 SoA 顺序、rudder 符号、deadband、float time-step parity、active 规范化、
   inactive-slot 事务、freshness gate、fail-closed guards、测试隔离与无 manifest/fallback
   晋级。
3. reviewer 提出一个 non-blocking 文档机会：新 input 失败后保留旧的成功 active stage 是
   有意的事务语义。本节已明确记录该行为。

经审阅的 code/test staged raw hash 为
`fc23a4d34173c0de2b70bc14b70b44caf4b7cf8d`（stable patch-id
`6a8101f6cbaaa4ea63bbf83b1006682a07295722`）；唯一提交身份由本分支历史记录。

结论：**允许形成一个 RB5 提交**。下一步只授权 RB6：实现有界 Phase B airframe-dynamics
切片，不吸收 Phase D projection，也不改变 facade support 声明。

## RB6 —— 有界 Phase B airframe dynamics（独立复核后 accepted）

### 已冻结的写集与非目标

本 candidate 的写集仅限 resident-store device layout/API、CUDA resident
backend 的私有 RB6 export identity、新 Phase-B fixture contract、CPU/CUDA
聚焦测试、CMake 接线、架构守卫与本双语账本。不修改 public capability
manifest、facade support projection、CPU backend，也不接管 Phase-D
instrument/observation/reward/termination owner。

准入 envelope 是 airborne fixed-step 切片：`Aircraft`、高度
`100..10000 m`、速度 `50..350 m/s`、受限横向/垂向速度与姿态、标准大气且
不接受 environment assignment、attached-flow `|alpha| <= 14 deg`，不做
ground/damage/fuel/mass update，不支持 dynamic entity families。post-stall
表、terrain/ground effect、wind assignment、mission autopilot、instrument
与 learner projection 仍 fail-closed 或不在本轮范围。

### 实现

- `CudaWorldDynamicsState` 是独立 resident SoA shard，保存角速度、实际舵面
  位置、发动机 spool/current thrust、气动缓存与起落架伸出量。setup 从专用
  Phase-B contract 初始化 cold F-16 fixture 常数；状态不会通过 Flecs 重建。
- 一个 window 复制 active slot 后连续 launch 三个 kernel，中间不做 host
  synchronization：控制/气动状态/推进加重力与推力；气动力/力矩累加；旋转与
  leapfrog 积分。只有在声明的 window barrier 前做一次 status synchronization；
  inactive-slot 失败会保留上一个已提交状态。
- export reconstruction 现在携带 dynamics，使用显式 v2 schema 与 RB6
  provenance，并在 `window_commit` 增加冻结的 `dynamics` 与 `episode`
  shard version；Phase-D shards 不会被虚假标记为完成。

### 验证与资源证据

- CUDA-off Release 完整 `ef_test`：`160/160` test cases、`19,456`
  assertions。独立 RB6 CPU oracle 运行维护 CPU 的完整阶段顺序，并按 RB2
  kinematics comparator 固定两世界结果。
- CUDA-on MSVC/NVCC 聚焦 target：`6/6` test cases、`353` assertions，覆盖
  inactive-slot 事务重试、dynamics export 与 envelope 拒绝。Compute Sanitizer
  memcheck：`0 errors`。
- `sm_86` `ptxas`：barrier `30`、Phase A `34`、Phase-B control/propulsion
  `66`、Phase-B aerodynamics `66`、Phase-B integration `64`
  registers/thread；全部 zero spill stores/loads。runtime resource query 在
  128 threads/block 下给出三个 Phase-B kernel 理论 occupancy 约
  `0.5833`、`0.5833`、`0.6667`。kernel 仍有 ptxas/runtime 报告的 40-byte
  stack frame；没有使用 `--maxrregcount` 或 launch-bound 约束。
- 聚焦 architecture/ruff/style 检查：`13` 个 architecture tests passed，
  Ruff passed，`git diff --check` passed。完整 CUDA-on `ef_test` graph 仍不纳入
  通过声明，因为 RB3 已记录的既有 MSVC portability debt。

### 独立复核与修复记录

1. `/root/rb6_phase_b_review` 独立检查 candidate，返回 `APPROVE` 且无
   blocking finding；核验了精确写集、CPU/CUDA 测试分离、三 launch/无中间
   host sync、envelope guard、shard/export 语义与寄存器/资源证据。
2. reviewer 指出两处 non-blocking 文档漂移：CUDA 注释仍写 two launches，
   focused CMake 注释仍停在 RB5。两处均已修复，未改变行为。
3. 同一 reviewer 对修复后的树再次只读复核并再次返回 `APPROVE`，复查了
   launch 顺序、零中间 host sync、三个 architecture guard 与精确写集，未
   发现新问题。

经审阅的 code/test staged raw hash 为
`2b07c57f67b7d868ff20b130d8761c0ee2a6bfef`（stable patch-id
`e86033b1a304cb1c4c0d37b762ba0275338b025e`）；唯一提交身份由本分支历史记录。

结论：**允许形成一个 RB6 提交**。该提交后只授权 RB7：有界 Phase D
instrument/observation/reward/termination projection 与 lifetime-safe device
observation export；不提前打开 replay harness 或性能声明。
