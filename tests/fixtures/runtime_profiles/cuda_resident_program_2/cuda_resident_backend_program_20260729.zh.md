# CUDA 驻留第二后端计划

语言版本：

- 英文规范版：[cuda_resident_backend_program_20260729.md](cuda_resident_backend_program_20260729.md)
- 中文伴随版：`cuda_resident_backend_program_20260729.zh.md`

- 文档类型：冻结执行计划
- 生命周期：维护中
- 所有者：exact-runtime / CUDA 驻留后端工作线
- 分支：`codex/cuda-resident-backend`
- 基线：`origin/main` 的 `395e02b7dfeaa87baedb2611ec503d14ab137ce3`
- 日期：`2026-07-29`

状态：**RB0 至 RB11 已经独立复核并 accepted。CUDA 驻留计划无晋级关闭；
未来工作必须建立新的显式计划。** 分支证据与 closure boundary 记录在
[迭代账本](cuda_resident_backend_iteration_log_20260729.zh.md)中。

## 1. 决策

目标是一套拥有设备原生状态与调度的第二运行时后端。它不是 Flecs 的 CUDA
版本，也不是把 Flecs system 逐一替换成 CUDA helper。

维护形态为：

```text
RuntimeFacade
    -> IWorldBatchBackend
         -> FlecsCpuBackend
         -> CudaResidentBackend
```

CPU 后端继续作为维护中的比较参照。当某个执行窗口获准使用 CUDA 后端时，
CUDA 后端在该窗口内拥有其已声明的 operational shards。不得在每个内部阶段后
步进或重建 Flecs。跨后端只通过规范 setup、input、barrier、snapshot、observation
和 diagnostics 契约交换信息。

## 2. 为什么必须是独立后端

当前实现还没有真正的后端接缝：

- `RuntimeFacade` 直接拥有 `std::unique_ptr<WorldBatchRuntime>`；
- `WorldBatchRuntime::step_batch()` 推进一组由 Flecs 支撑的
  `SimulationKernel` world；
- `RuntimeBatchConfig` 当前只有 world 数与 worker 数；
- GPU observation、visual、shaping 和 broadphase 路径仍是主机侧组装请求并返回
  主机可见结果的 helper；
- `resident_state.unmaintained_candidate` 只是 blocked profile，不是可执行后端；
- `DeviceResidentOutputDescriptor` 是增量的 export-only 契约，不授权状态所有权。

逐一迁移会保留实体/组件式物化边界、过宽 live range、能力分支、重复 launch
以及主机/设备协调。独立后端才能采用后端专用 SoA、能力队列、阶段局部中间布局
和 kernel 特化。

架构变化是必要条件，但不是充分条件。寄存器压力仍是 kernel 属性，必须通过
缩短 live range、冷热分离、特化和实测阶段边界控制。

## 3. 权威关系

本计划：

- 消费已验收 WP19 的 shard、barrier、descriptor 与 fail-closed 词汇；
- 只把已归档 exact-GPU 与 resident-state 计划当作溯源材料；
- 保留 `cpu_exact.reference` 为维护比较后端；
- RB0 不改变当前 capability flags；
- 不把 helper-first exact-GPU 实现重新作为迁移基础；
- 把 exact-stage inventory 当作语义/parity 台账，而不是 CUDA launch graph。

本文是这条新工作线唯一的候选执行冻结。调研笔记、归档计划和 checklist 只提供
辅助证据，不能各自授权实现范围。

主要证据输入：

- [RuntimeFacade 所有权](../../../src/runtime/facade/runtime_facade.h)
- [RuntimeFacade 构造](../../../src/runtime/facade/runtime_facade.cpp)
- [WorldBatchRuntime 步进](../../../src/core/engine/world_batch_runtime.cpp)
- [runtime batch config 字段](../../../src/runtime/facade/detail/runtime/runtime_batch_config.inc)
- [backend profile 契约](../../../src/runtime/contracts/backend_profile_contracts.h)
- [resident-state parity budget](../../../src/runtime/contracts/parity_budget_contracts.h)
- [exact-stage 语义 inventory](../../../src/core/engine/exact_stage_inventory.cpp)
- [`src/gpu` 边界](../../../src/gpu/README.md)
- [WP19 resident-state sync/shard 契约](../../task/simulation_architecture/archive/wp19_cuda_resident_state_alignment/wp19_resident_state_sync_shard_contract_cluster_20260521.zh.md)
- [WP19 device-output 契约](../../task/simulation_architecture/archive/wp19_cuda_resident_state_alignment/wp19_device_resident_output_contract_cluster_20260521.zh.md)
- [归档 exact-GPU rearchitecture 溯源](../archive/exact_runtime/gpu_exact_world_step_rearchitecture_plan.md)
- [归档 resident-state implementation 溯源](../archive/exact_runtime/gpu_resident_state_implementation_plan.zh.md)

## 4. 计划目标

构建一套显式选择的 `CudaResidentBackend`：它能够从规范 setup/input packet
执行有界 air-execution rollout 切片，在多个 step 间把 operational state 保留在
设备端，并在声明的 barrier 上导出规范 snapshot 或 device observation view，
同时可与 Flecs CPU reference 比较。

第一条可晋级切片刻意保持狭窄：

- 固定步长 air/execution world；
- 固定 platform-capability manifest；
- 所选 fixture 需要的 action/command、flight control、airframe dynamics、
  instruments、observation、reward 和 termination surface；
- 不包含未声明的动态 entity family；
- 已获准 CUDA window 内不得隐式 CPU fallback。

## 5. 非目标

- CUDA 化 Flecs，或向设备代码暴露 Flecs component storage；
- 为每个 exact-stage system 建立对应 kernel；
- 单体 `world_step_kernel`；
- 在第一切片覆盖完整 air、naval、ground、cooperative、sensor、EW、damage 与
  logistics；
- 在 profile gate 通过前晋级 exact-GPU、resident-state、shadow 或
  device-observation support；
- 删除或改写归档 GPU evidence；
- 给 C++ backend 增加 PyTorch、Python 或策略库依赖；
- 只优化孤立 kernel，而端到端 rollout 仍更慢。

## 6. 后端契约

内部 backend SPI 必须使用 facade 所有的 contract type 表达。最低语义操作为：

```cpp
class IWorldBatchBackend {
  public:
    virtual BackendCapabilities capabilities() const noexcept = 0;
    virtual void configure(const BackendConfig&) = 0;
    virtual void reset(const BatchWorldSetupRequest&) = 0;
    virtual void inject(const BackendInputBatch&) = 0;
    virtual BackendWindowResult advance(const BackendWindowRequest&) = 0;
    virtual BackendSnapshotResult export_snapshot(const BackendExportRequest&) = 0;
    virtual DeviceObservationResult export_device_observation(
        const DeviceObservationRequest&) = 0;
    virtual BackendDiagnostics diagnostics() const = 0;
    virtual ~IWorldBatchBackend() = default;
};
```

以上名称在 RB1 完成当前 caller/DTO 普查前只是设计占位。RB1 不得增加无人使用的
平行接口；它必须在同一迭代中引入 SPI，并让现有 CPU 路径经
`FlecsCpuBackend` 使用它。

规则：

1. `RuntimeFacade` 继续作为 public owner；backend 实现类型保持内部化；
2. Flecs handle、component pointer、CUDA pointer 或 backend 专用 state layout
   均不得穿过公开 facade DTO 边界；
3. backend 选择必须显式且 fail-closed；
4. 不支持的场景能力必须在 setup/step 前拒绝 admission；
5. 已获准 CUDA window 不得因缺失阶段而暗中调用 Flecs；
6. host reconstruction 是显式 export 操作，不是每步副作用。

## 7. CUDA 状态模型

`CudaResidentBackend` 拥有使用 backend-private 布局的 `CudaWorldStore`：

- world offsets 与稳定的 `(entity_id, generation)` 身份；
- active/free list 与 barrier-scoped lifecycle queue；
- kinematics、control、force、propulsion、fuel、weapon 与 observation state 的
  hot SoA shards；
- platform config、aerodynamic data、sensor config 和 mission constants 的
  cold/read-only tables；
- aircraft、missile、sensor、comm、EW 及后续领域族的能力专用 active queues；
- contacts、tracks、commands 与 events 的 CSR 或有界 ring buffer；
- 按 seed、world、tick、entity、event identity 寻址的 counter-based RNG；
- 每 shard version、source snapshot identity 与 barrier identity。

静态/配置 shard 只在 setup 或版本变化时上传。动态 shard 在连续 `advance()`
之间保持驻留。dirty host input 只在 `input_injection` 传输；host-visible
reconstruction 只在声明的 `window_commit` 或 `export` barrier 发生。

## 8. 执行图与寄存器压力规则

exact-stage inventory 定义语义顺序与比较点，不决定 CUDA kernel 数。初始执行图
分为四类 phase：

| Phase | 范围 | 物化边界 |
| --- | --- | --- |
| A | action decoding、command delivery、lag、control preparation | 紧凑 control SoA |
| B | aero state、propulsion、forces、转动与平动积分 | committed dynamics SoA |
| C | spatial index、guidance、sensors、comm、fuze/effects | 稀疏 candidate/event queues |
| D | instruments 及其 learner-facing projection、observation、reward、termination、可选 visual output | host snapshot 或 device consumer view |

除 fixture 明确需要的最小部分外，Phase C 不属于第一垂直切片。

每个 CUDA 实现迭代必须记录：

- `ptxas` registers/thread；
- spill stores/loads；
- achieved occupancy 与 resident blocks/warps；
- local/global/shared-memory traffic；
- branch 与 warp divergence；
- launch 数、H2D、D2H 与同步时间；
- 端到端 rollout 时间。

不预先冻结统一寄存器上限。每个 kernel 根据实测工作声明目标 occupancy 形态。
只有 A/B 证明降低 residency 成本不会把工作转移成显著 local-memory spill 后，
才能采用 `--maxrregcount` 或 `__launch_bounds__`。

强制设计控制：

- 拆分 hot/cold fields；
- 按获准 capability family 特化，而不是对全部 Flecs component combination 分支；
- diagnostics output 不进入训练 fast path；
- 在能够缩短 live range 的位置物化紧凑 phase-local intermediate；
- 只有被消除的 memory traffic 大于 occupancy 损失或新增 spill 时才融合；
- 使用稳定 entity/event ordering 与 counter-based RNG，防止 launch 调度成为
  simulation truth。

## 9. 所有权、同步与平价

已验收 WP19 词汇继续具有权威性：

- `input_injection`：规范 setup/action/command delta 变得可见；
- `stage_publish`：默认只在 backend 内部，不是 host-maintained；
- `window_commit`：声明的 backend shards 成为 committed backend snapshot；
- `export`：规范 host snapshot 或 device output descriptor 可被消费；
- counterfactual/replay barrier 继续是 comparison/export surface，不是隐式所有权迁移。

RB2 冻结的 profile-owned selected-slice budget 必须携带以下完整 barrier 映射：

| Barrier | 候选后端规则 |
| --- | --- |
| `input_injection` | 规范 setup/action/command delta 进入已获准 backend window。 |
| `stage_publish` | 只作为 backend-local diagnostics checkpoint；不能单独满足 maintained parity。 |
| `partial_sync_commit` | 只用于 profile 明确声明的 reconstructed shard；没有该声明时不存在 partial host truth。 |
| `window_commit` | 已声明 resident shards 获得 committed backend snapshot 与 shard versions。 |
| `export` | host snapshot 或 device output 携 source snapshot、provenance 与 lifetime metadata 后可消费。 |

对 CUDA candidate 而言，CPU 是 reference implementation，不是并发 writer。Parity
run 让同一冻结 input trace 独立经过两个 backend，并在声明 barrier 上比较；不得在
每个 CUDA stage 后同步 Flecs component。

numeric state 默认 exact。任何允许容差的 field family 都必须在 profile-owned
parity budget 中声明 comparator 与 threshold。event order、snapshot identity、
barrier identity、schema、provenance、termination 与 capability admission 保持 exact。

RB2 拥有 candidate profile id、selected-slice field inventory、comparator/tolerance
声明与完整 barrier set。RB4 实现这些 barrier。RB5-RB7 针对已经冻结的 budget
产出 parity evidence。RB8 只增加消费该 budget 的 replay/shadow harness，不得在
实现开始后才定义 budget。

## 10. 迭代协议

工作线沿用现有仓库纪律：

```text
analyze -> freeze write set/non-goals -> implement -> focused validation
        -> independent read-only review -> repair/re-review
        -> one commit -> landing-ledger registration
```

分支内 `RB<n>` 标签标识候选工作包，不是中央 `I<n>` 验收声明。经过评审的提交
落地时，才在 `docs/plan/repository_consolidation/README.md` 中领取下一个可用
中央迭代行。这避免并行分支演进期间预占过时的全局编号。

每轮 RB 迭代必须：

- 从 clean worktree 开始，并刷新 `origin/main` ancestry；
- 编辑前普查 caller 与当前行为；
- 冻结精确 write set 与非目标；
- 只产生一个可独立审阅的提交；
- 除非该轮明确拥有经过评审的晋级，否则 CUDA-off build 与 CPU default 不变；
- 记录 focused command、结果、diff 统计、残余、review revision、finding 与 verdict；
- 存在 blocking finding 或必需验证未完成时停止，不提交。

## 11. 候选迭代队列

| ID | 范围 | 退出门 |
| --- | --- | --- |
| RB0 | 冻结本文、当前代码普查、权威链接、worktree 与 branch。仅文档。 | 双语 companion、索引、适用的严格登记记录、链接、`git diff --check`、独立复核。 |
| RB1 | 引入内部 backend SPI 与实际使用的 `FlecsCpuBackend`；让维护 CPU 路径经它运行，不改变公开行为或 ABI。 | `RuntimeFacade::runtime_` 所有权切换到 interface/CPU adapter；move/sizeof tripwire 更新；CUDA-off build、CPU focused parity 与架构门通过；facade 中不保留 backend-specific 或闲置平行 owner。 |
| RB2 | 增加显式 backend request/admission、capability-manifest contract、candidate profile id 与 profile-owned selected-slice parity budget。除非存在已编译实验后端且 manifest 受支持，CUDA 选择继续拒绝。 | 默认字节不变；缺失/不支持 profile fail closed；selected fields、exact/default comparator、任何显式 tolerance，以及 `input_injection`/`stage_publish`/`partial_sync_commit`/`window_commit`/`export` 映射被冻结；不晋级 support flags。 |
| RB3 | 增加 `CudaResidentBackend` 生命周期壳与 `CudaWorldStore` 分配/版本控制，并提供 CUDA-off stub。不含 simulation dynamics。 | configure/reset/teardown 测试；无全局 singleton cache；可用时运行 sanitizer/ownership check。 |
| RB4 | 为最小 fixture 实现 setup/reset、input injection、device clock、shard version、RB2 已冻结的 partial-sync/window/export barrier 行为与显式 snapshot reconstruction。 | 针对 RB2 budget 的固定 seed reset/identity parity；零隐藏 Flecs step/fallback；完整 barrier/provenance 门。 |
| RB5 | 为有界 air-execution manifest 实现 Phase A。 | 针对 RB2 budget 的 stage-local CPU-reference parity；寄存器/spill 报告；不支持 control feature 拒绝 admission。 |
| RB6 | 为同一 manifest 实现 Phase B airframe dynamics；instruments 保持 Phase D output projection。 | 在声明比较点针对 RB2 budget 的固定 replay parity；无逐阶段 host 同步；资源报告。 |
| RB7 | 实现 Phase D instruments、observation、reward、termination 与生命周期安全的 device observation export。 | 针对 RB2 budget 的 host export parity；直接 device consumer smoke；不得把 snapshot D2D ownership copy 伪称 zero-copy。 |
| RB8 | 增加消费 RB2 parity budget 的独立 CPU/GPU replay 与 shadow comparison harness，且 shadow result 不得修改任一 backend。 | mismatch localization、deterministic rerun、quarantine 与完整 selected-slice budget consumption。 |
| RB9 | 建立 production-shaped performance 与 break-even 证据，不扩语义。 | worlds `1/4/16/64/256`；P50/P95；传输、launch、register/spill/occupancy、memory 与端到端 collect 指标。 |
| RB10 | 决定后续：优化实测 phase boundary、准入有界 spatial interaction slice，或 hold backend。 | 声明 eligible batch 上端到端收益超过噪声；小批量 default 不退化；记录 owner decision。 |
| RB11 | 仅在前述门全部通过后选择性晋级/收口。 | maintained profile review、reconstruction/export contract、support projection、rollback、完整验证与独立验收。 |

RB5-RB7 不得合并为一个超大迭代。RB10 不能只因孤立 broadphase kernel 很快就
扩大为 sensor/comm 工作。

## 12. 性能矩阵与门槛

最小公共矩阵：

- worlds：`1`、`4`、`16`、`64`、`256`；
- 固定的有界 air-execution fixture 与 seeds；
- CPU reference、CUDA resident、显式 CPU/GPU comparison 模式；
- cold first step 与 warmed steady state；
- host snapshot export 关闭/开启；
- device observation consumer 关闭/开启。

必需指标：

- 完整 facade/window advance；
- 完整 rollout collection，以及可用时的 learner consumption；
- P50/P95 latency；
- H2D、D2H、synchronization 与 launch 数；
- 每 kernel register、spill、occupancy、divergence 与 memory 指标；
- allocated/peak device memory；
- parity 与 determinism 结果。

RB10 的候选性能验收要求：在声明的 eligible production batch 上取得统计上清晰的
端到端收益。临时目标是在所选 production batch 上比 CPU reference 至少快 15%，
并为更小 batch 给出实测 backend-selection threshold。该数字是计划 gate，不是性能
预测；只能根据 RB9 证据重新冻结。

仅有 kernel speedup、helper timing，或仍执行隐藏 host reconstruction 的结果均不通过。

## 13. 停止与 held 条件

以下任一情况持续存在时，工作线停止或保持 candidate：

- backend seam 变成第二个 public facade，或复制 contract DTO；
- CUDA admission 在 execution window 内暗中回退 Flecs；
- parity 依赖逐 stage host write-back；
- 不支持能力没有 fail closed，而是进入分支密集的通用 kernel；
- 只靠产生显著 material spill traffic 的方式降低寄存器数，导致端到端收益消失；
- backend 只在孤立 kernel 更快，rollout 不快；
- snapshot、barrier、event order、provenance 或 lifetime 无法重建；
- 必需独立复核或验证不可用。

此时 branch/evidence 保持研究候选；当前维护 CPU 行为与 capability flags 不变。

## 14. RB0 冻结 write set

RB0 只允许修改：

- 本英文/中文计划对；
- `docs/plan/exact_runtime/README.md` 与 `.zh.md`；
- `docs/plan/README.md` 与 `.zh.md`；
- `plan/README` 的选择性严格双语登记记录。`exact_runtime` 子树不属于当前严格
  登记范围，因此其两组变更 pair 直接验证，不通过全树登记重写强行加入。

RB0 不得修改 C++、CUDA、Python、CMake、tests、runtime profiles、capability flags、
examples、归档计划或中央 accepted iteration ledger。
