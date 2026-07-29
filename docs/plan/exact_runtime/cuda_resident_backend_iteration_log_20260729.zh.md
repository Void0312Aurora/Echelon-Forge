# CUDA 驻留后端分支迭代账本

语言版本：

- 英文规范版：[cuda_resident_backend_iteration_log_20260729.md](cuda_resident_backend_iteration_log_20260729.md)
- 中文伴随版：`cuda_resident_backend_iteration_log_20260729.zh.md`

- 文档类型：分支内迭代与审阅账本
- 生命周期：`codex/cuda-resident-backend` 活跃期间维护
- 计划权威：[cuda_resident_backend_program_20260729.zh.md](cuda_resident_backend_program_20260729.zh.md)
- 基线：`395e02b7dfeaa87baedb2611ec503d14ab137ce3`

状态：**RB0 至 RB3 已 accepted。当前仅授权 RB4 实现；RB5-RB11 仍受依赖门控。**

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
