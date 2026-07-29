# CUDA 驻留后端分支迭代账本

语言版本：

- 英文规范版：[cuda_resident_backend_iteration_log_20260729.md](cuda_resident_backend_iteration_log_20260729.md)
- 中文伴随版：`cuda_resident_backend_iteration_log_20260729.zh.md`

- 文档类型：分支内迭代与审阅账本
- 生命周期：`codex/cuda-resident-backend` 活跃期间维护
- 计划权威：[cuda_resident_backend_program_20260729.zh.md](cuda_resident_backend_program_20260729.zh.md)
- 基线：`395e02b7dfeaa87baedb2611ec503d14ab137ce3`

状态：**RB0 至 RB2 已 accepted。当前仅授权 RB3 实现；RB4-RB11 仍受依赖门控。**

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
