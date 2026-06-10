# WP23 Legacy Retirement Recovery And Reset

状态：`2026-05-24` 已以 `blocked` 关闭。WP23 取代 WP22；由于在有边界实现窗口内无法
安全删除或迁移，WP23 被允许并实际以 `blocked` 结束。`WP23-A` 到 `WP23-D` 提供
source-backed recovery baseline；`WP23-E` 因没有识别出 deletion-ready
implementation surface 而跳过；`WP23-F` 记录 blocked close-out。尚未开始
implementation dispatch。

文档预算：

- WP23 的 canonical planning surface 只有本文和英文主文。
- 除非 owner 明确批准，WP23 期间不得新增 task-cluster、salvage-ledger 或
  acceptance-rule sidecar。
- 如果 WP23 需要超出本文承载能力的规划表面，这是 scope failure signal；应停止并
  re-baseline，而不是继续创建文档。

输入：

- [WP22 legacy compatibility retirement](../wp22_legacy_compatibility_retirement/legacy_compatibility_retirement_wp22_20260522.zh.md)
- [WP22 remaining task clusters](../wp22_legacy_compatibility_retirement/wp22_remaining_task_clusters_20260523.zh.md)
- [WP22 dispatch queue](../wp22_legacy_compatibility_retirement/wp22_subagent_dispatch_queue_20260522.zh.md)
- [architecture refactoring audit](../../../review/architecture_refactoring_audit_20260522.zh.md)
- [Subagent 使用规范](../../../../standards/governance/subagent_usage_policy.zh.md)
- [WP Closure Lane Policy](../../../../standards/governance/wp_closure_lane_policy.zh.md)

## 1. 停止令

WP23 从硬停止开始，不是另一轮 WP22 wave。

- WP22 implementation dispatches 已终止或冻结。
- WP22 queues 只作历史 provenance，不得派发。
- Kepler 中断的 TaskOrder wiring 是未验证 partial work。
- Hubble 的 TaskOrder maintained-batch contract 是 partial evidence，在审计前有
  dual-representation 风险。
- Galileo/Locke preflight 是历史 source facts，不是 implementation evidence。
- Poincare shutdown 不提供 closure evidence。

任何 `partial`、`preflight-only`、`timeout`、`shutdown`、quarantine label 或旧 queue
row 都不能解锁 WP23 implementation 或 closure。

## 2. 恢复原则

WP22 的失败是控制过程失败：R2 扩张到二十多轮，partial evidence 变成 next-step fuel，
quarantine 开始像 completion 一样运作。WP23 的目标是防止这个模式重演。

规则：

- 每个业务概念只有一个 maintained truth。
- 能安全删除或迁移就删除/迁移；否则停为 `blocked`。
- `blocked` 是可接受的 WP23 结果，不是需要掩盖的失败。
- `blocked` 不是 pass state，也不能长期不复查。
- 不能因为 worktree 里已经有沉没成本，就保留相关 work。
- 除非同一判定中移除、迁移或明确阻塞旧 maintained truth，否则不得新增 DTO、bridge、
  helper 或 compatibility layer。

## 3. 当前工作桶

这里不会重置 worktree。WP23-A 必须在实现开始前把当前 dirty work 分类到以下桶。

| Bucket | 含义 | 初始例子 |
|--------|------|----------|
| `keep-after-audit` | 有证据支撑、收窄 maintained path 且没有制造第二 truth 的更改。 | typed command/control 收窄、terrain/setup 默认值归一、command-link pending transport 收窄、guard hardening。 |
| `audit-before-keep` | 看起来有用，但存在 dual-representation、incomplete wiring 或 unvalidated shutdown 风险。 | `TaskOrderMaintainedBatchContract`、`WorldTaskOrderMaintainedAssignment`、maintained TaskOrder runtime/facade/binding APIs、Python `hasattr` fallbacks。 |
| `delete-or-migrate-target` | 仍像 maintained default 一样工作的 compatibility 或 flat-shell surface。 | whole-shell assignment truth、default-factory behavior-bearing `MovementCommand` / `LaggedCommand` projection、非 opt-in runtime escape-hatch consumers。 |
| `blocked-target` | 当前无法删除，否则会破坏缺少 replacement ownership 的 public API 或 consumer。 | `RuntimeFacade::runtime()`、`WorldBatchRuntime::world()`、`vec_env.batch_runtime`、public `World*Assignment` batch methods、diagnostics bindings。 |
| `rollback-candidate` | 审计或验证失败的 interrupted/speculative edits。 | 无法验证或保留 dual truth 的 Kepler-era wiring。 |
| `historical-only` | 解释 provenance 但不授权工作的旧 packets 与 queues。 | WP22 waves、read-only preflights、shutdown records、说明 `WP22-F not eligible` 的 closure notes。 |

## 4. Blocked-State Contract

`blocked` 不能变成新的 `quarantine`。每个 blocked item 必须包含：

- 精确 surface 与当前 caller；
- 当前 deletion/migration 不安全的原因；
- 负责 replacement 或 public API decision 的 owner；
- 所需 replacement 或 deletion condition；
- validation command 或 missing guard；
- forced review trigger。

强制复查触发：

- replacement API 落地；
- public consumer 被移除；
- guard 开始失败；
- 一批 implementation 完成；
- blocked item 超过下一个 WP23 review point。

只有当所有 blocked items 都显式记录，且没有任何 item 被错误标成 retired、migrated
或 accepted 时，WP23 才可以以 `blocked` 结束。

## 5. 任务簇

WP23 只有六个有限 cluster。任何 worker 若不能映射到下表，不得派发。

| Cluster | 轮次上限 | 目的 | 退出 |
|---------|----------|------|------|
| `WP23-A Freeze And Salvage Audit` | 1 diagnostics/docs round | 将所有 WP22-era dirty changes 分类到上述桶。 | 不存在未命名的 "next step" 桶。 |
| `WP23-B Delete-Or-Block Table` | 1 diagnostics/docs round | 对每条 live legacy surface 判定 `delete now`、`migrate then delete`、`blocked` 或 `rollback`。 | 每行都有 owner、validation 与 forced review trigger。 |
| `WP23-C Tasking Single Representation` | 1 implementation/design round | 先解决 TaskOrder：keep、rollback 或 block maintained-batch work。之后才决定 LeaderIntent/PilotReport。 | 一个 maintained tasking truth，或显式 blocked close-out。 |
| `WP23-D Public API Exit` | 1 implementation/design round | 判定 raw runtime/world/batch escape hatches 与 diagnostics/public whole-shell APIs。 | deleted、migrated，或带 public API reason 的 blocked。 |
| `WP23-E Minimal Implementation Batch` | 1 implementation round | 只执行 B-D 已证明 ready 的决定。 | patch set 落地，或 WP23 停为 blocked。不创建 follow-up wave。 |
| `WP23-F Close-Out` | 1 serial closure round | 发布 accept/reject/blocked 结果并归档 WP22 queue 状态。 | 若依赖 partial evidence、dual truth 或 unowned legacy path，则失败。 |

如果任一 implementation cluster 无法在单轮内完成，WP23 停为 `blocked`；只有 owner
批准时才 re-baseline。默认不得创建“第二轮”。

## 5.1 WP23-A Salvage Audit Baseline

审计日期：`2026-05-24`。

工作区状态：

- 分支为 `main`，领先 `origin/main` 两个 commit。
- WP22 queues 已冻结，只作历史 provenance。
- WP23 planning surface 仍在预算内：只有本文和英文主文。
- 当前 dirty work 包含 WP22-era code、tests、governance edits、WP22 freeze notes 与
  WP23 reset docs。本审计不整体接受或整体拒绝任何代码。

救援分类：

| Surface | 源码锚点 | 分类 | 判定 |
|---------|----------|------|------|
| WP22 freeze / governance docs | `docs/task/simulation_architecture/README.md`、`docs/standards/governance/subagent_usage_policy.md`、`docs/standards/governance/wp_closure_lane_policy.md` | `keep-after-audit` | 作为流程纠偏保留；它们降低 WP22 重入风险，并补入 document-budget / blocked-state governance。 |
| Scenario terrain/setup normalization | `python/scenario/compiler/common.py:114-132`、`python/scenario/runtime/world_setup_compat.py:17-54`、`tests/runtime/core/test_world_setup_compat.py:147-161` | `keep-after-audit` | 验证通过则保留。缺省 terrain 现在为 `flat` / `default_mainline`；显式 legacy terrain 标为 compatibility。 |
| Command/control typed-state narrowing | `src/components/command/default_factory_legacy_spawn_compat.h:9-18`、`src/systems/core/operation_system.h:46-111`、`src/systems/systems/command_link_system.h:29-120` | `keep-after-audit` with residual blockers | 保留 guarded narrowing，但只要 `MovementCommand`、`LaggedCommand`、`ActionCommand` 与 pending shells 仍是 behavior-bearing compatibility surfaces，就不能称为 retirement。 |
| TaskOrder maintained-batch contract and wiring | `src/runtime/contracts/world_batch_contracts.h:563-720`、`src/core/engine/world_batch_runtime.h:109-116`、`src/core/engine/world_batch_runtime.cpp:738-857`、`src/runtime/facade/runtime_facade.h:97-129`、`src/runtime/facade/runtime_facade.cpp:2649-2768`、`src/interfaces/python/bindings_runtime.cpp:1165-1173`、`src/interfaces/python/bindings_runtime.cpp:1444-1457`、`src/interfaces/python/bindings_runtime.cpp:1535-1582`、`src/interfaces/python/bindings_runtime.cpp:1692-1735`、`python/rl/runtime/world_batch/adapter.py:118-141`、`python/rl/runtime/world_batch/adapter.py:773-887`、`python/rl/runtime/world_batch_vec_env.py:1261-1315` | `audit-before-keep` | 暂不接受为 pass。它在 whole-shell write/read、observation packet、bindings 与 Python fallback 仍 live 时，引入了 maintained-looking TaskOrder path。 |
| TaskOrder / LeaderIntent / PilotReport whole-shell assignments | `src/runtime/contracts/world_batch_contracts.h:596-655`、`src/core/engine/world_batch_runtime.cpp:766-797`、`src/runtime/facade/runtime_facade.cpp:2655-2665`、`src/interfaces/python/bindings_runtime.cpp:1444-1469` | maintained truth 为 `delete-or-migrate-target`；public API 为 `blocked-target` | 不得接受为 maintained truth。只有 public replacement 被证明后才能删除/迁移，否则标 blocked。 |
| Observation task-order whole-shell read | `src/runtime/facade/runtime_facade.cpp:2779-2788`、`src/runtime/facade/runtime_facade.cpp:3008-3031`、`src/interfaces/python/bindings_runtime.cpp:1105-1117`、`tests/architecture/runtime_facade/test_runtime_facade_contract_boundaries.py` | `blocked-target` | 仍是 whole-shell read surface。`ObservationBatchPacket.task_orders` 公开存在时，不能称 TaskOrder shell retired。 |
| Runtime/world/batch escape hatches | `src/runtime/facade/runtime_facade.cpp:2498-2503`、`src/core/engine/world_batch_runtime.h:65-68`、`python/rl/runtime/world_batch_vec_env.py:302-306`、`tests/architecture/runtime_facade/test_scenario_setup_facade_boundary.py` | `blocked-target` | 只能作为 explicit compatibility/diagnostics 保留。受 public consumers 与 diagnostics paths 阻塞，不能删除。 |
| Default-factory legacy command projection | `src/components/command/default_factory_legacy_spawn_compat.h:36-54`、`src/components/command/default_factory_legacy_spawn_compat.h:101-121` | `delete-or-migrate-target` with blocker | 删除前必须迁到 typed control-state-only spawn。当前 helper 仍投影 `MovementCommand` 与 `LaggedCommand`。 |
| Python maintained path fallbacks | `python/rl/runtime/world_batch/adapter.py:118-141`、`python/rl/runtime/world_batch/adapter.py:773-887`、`python/rl/runtime/world_batch_vec_env.py:1261-1315` | 若隐藏 truth 则 `rollback-candidate` | 只有 C 证明 representation selection 是显式的才保留。静默 `hasattr` fallback 可能保留 dual truth。 |

WP23-A 退出：planning complete。不存在未命名的 "next step" 桶；每个审计 surface 都已经
归入 keep-after-audit、audit-before-keep、delete-or-migrate-target、blocked-target、
rollback-candidate 或 historical-only。

## 5.2 WP23-B Delete-Or-Block Table

本表是 WP23 唯一 active decision table，取代 WP22 queue continuation。

| Surface | 判定 | Owner | Replacement / exit condition | Validation / missing guard | Forced review trigger |
|---------|------|-------|------------------------------|----------------------------|-----------------------|
| WP22 queue entries | `blocked as historical-only` | WP23-F | 只归档或保留 frozen references。 | `rg` 必须证明 README 与 WP23 文本没有指向已删 sidecar 或 active WP22 queue dispatch。 | 任何未来派发请求直接引用 WP22 queue。 |
| TaskOrder maintained-batch path | `audit-before-keep`；可能变为 `rollback` 或 `blocked` | WP23-C | 只有成为唯一 maintained TaskOrder write/read path，或旧 whole-shell surfaces 明确变成 compatibility/blocked public API 时才保留。 | 需要 build 与 focused runtime/facade/binding/DTO tests；必须证明 `ObservationBatchPacket.task_orders` 与 Python fallback 不会带回 maintained whole-shell truth。 | WP23-C audit/design round 完成。 |
| `WorldTaskOrderAssignment.order` 与 `get/set_task_orders_batch` | 私有处 `migrate then delete`；公开处 `blocked public API` | WP23-C | maintained callers 使用 `TaskOrderMaintainedBatchContract`；旧 public API 仅显式 compatibility 或删除。 | 缺失 guard：旧 whole-shell getter/setter 仍绑定在 runtime/facade/Python。 | maintained contract 被接受，或 public consumer list 改变。 |
| `WorldLeaderIntentAssignment.intent` | `blocked` | TaskOrder 后的 WP23-C | 等 TaskOrder 判定完成后再设计同类路径。 | 缺少 maintained public write/read replacement。 | TaskOrder 得到 keep/rollback/blocked 判定。 |
| `WorldPilotReportAssignment.report` | `blocked` | TaskOrder 后的 WP23-C | 等 TaskOrder 判定完成后再设计同类路径。 | 缺少 maintained public write/read replacement。 | TaskOrder 得到 keep/rollback/blocked 判定。 |
| `ObservationBatchPacket.task_orders` | `blocked public API` | WP23-C / WP23-D | 替换为 maintained contract read，或显式标为 compatibility retained。 | 当前 packet 仍暴露 `std::vector<TaskOrder> task_orders`。 | TaskOrder maintained read path 被接受，或 packet API 改动。 |
| `RuntimeFacade::runtime()` | `blocked public API` | WP23-D | 所有 public consumers 有 facade-owned replacement 后才删除。 | 当前 guard 只局部化 consumers，不删除 API。 | 新 raw-runtime consumer 出现，或 replacement API 覆盖全部 consumers。 |
| `WorldBatchRuntime::world()` | `blocked public API` | WP23-D | raw-world adapter/diagnostics consumers 迁移后才删除。 | guard 将 `.world()` consumers 局部化到显式 allowlist。 | adapter 不再需要 raw-world compatibility handle。 |
| `vec_env.batch_runtime` | `blocked compatibility view` | WP23-D | 保持 explicit opt-in，或 public users 迁移后删除。 | runtime compatibility flag guard 已存在；public view 仍存在。 | public Python consumers 被移除，或 replacement facade APIs 落地。 |
| Default-factory `MovementCommand` / `LaggedCommand` projection | `migrate then delete`；当前 `blocked` | C/D ready 后的 WP23-E | spawn defaults 必须只 seed typed control-state，不再投影 behavior-bearing legacy mirrors。 | 现有 helper 仍 set projected `MovementCommand` / `LaggedCommand`。 | typed control-state replacement 覆盖剩余 command/link/factory consumers。 |
| Diagnostics legacy bindings and GPU/visual compatibility helpers | `blocked compatibility retained` | WP23-D / WP23-F | 只能带 guard label 作为 diagnostics/compatibility 保留，不得作为 retirement evidence。 | 必须保持在 maintained path allowlist 外。 | diagnostics path 变成 maintained dependency 或 guard 失败。 |

WP23-B 退出：planning complete。Implementation 现在只允许从本表选择有边界的
`WP23-C` / `WP23-D` 工作。如果任一项无法在单轮内完成，WP23 必须停为 `blocked`，
不得创建新 wave。

## 5.3 WP23-C TaskOrder Decision

审计日期：`2026-05-24`。

判定：`blocked`，不是 `keep`，也不是立即 rollback。

依据：

- maintained-batch path 已存在且有 guard value：
  `TaskOrderMaintainedBatchContract` 与
  `WorldTaskOrderMaintainedAssignment` 定义在
  `src/runtime/contracts/world_batch_contracts.h:563-628`；runtime 与 facade
  在 `src/core/engine/world_batch_runtime.cpp:738-849` 和
  `src/runtime/facade/runtime_facade.cpp:2649-2765` 暴露 maintained set/get API。
- maintained path 仍写回 compatibility shell：runtime 代码构造
  `TaskOrder compatibility_shell`，并在
  `src/core/engine/world_batch_runtime.cpp:746-761` 调用
  `world.set_task_order(...)`。
- 旧 whole-shell path 仍是 public 且 live：
  `WorldTaskOrderAssignment.order` 仍位于
  `src/runtime/contracts/world_batch_contracts.h:596-614`，同时
  `set_task_orders_batch` / `get_task_orders_batch` 仍通过 runtime、facade 与
  Python bindings 暴露在
  `src/core/engine/world_batch_runtime.cpp:766-857`、
  `src/runtime/facade/runtime_facade.cpp:2655-2768` 和
  `src/interfaces/python/bindings_runtime.cpp:1444-1457`。
- `ObservationBatchPacket` 仍在
  `src/runtime/facade/runtime_facade_types.h:295-310` 导出 whole-shell
  `std::vector<TaskOrder> task_orders`；`RuntimeFacade::build_observation_packet`
  在 `src/runtime/facade/runtime_facade.cpp:3029-3030` 通过
  `runtime_->get_task_orders_batch(...)` 填充它。
- Python 仍存在 fallback / feature-detection 分支，可以在 maintained
  assignments 与 whole-shell assignments 之间路由：
  `python/rl/runtime/world_batch/adapter.py:773-887` 与
  `python/rl/runtime/world_batch_vec_env.py:1261-1315`。
- 现有测试验证的是共存，而不是退场：
  `tests/world_batch/test_world_batch_runtime.py:921-964` 验证 maintained write
  后 legacy read，`tests/architecture/runtime_facade/test_runtime_facade_contract_boundaries.py`
  显式检查 maintained APIs 与 legacy shells 同时存在。

WP23-C 结果：

- 不接受 TaskOrder maintained-batch work 作为唯一 maintained representation。
- 不立即回滚它，因为 typed contract 是有用证据；当 public whole-shell exits
  被判定后，它仍可能成为 replacement shape。
- TaskOrder 标为 `blocked`，直到旧 public read/write surfaces 被删除、带 guard 标为
  compatibility，或被 maintained packet shape 替换。
- LeaderIntent 与 PilotReport 继续 blocked；TaskOrder public API decision 解决前，
  不启动同类 maintained-path 工作。

TaskOrder blocked-state contract：

| Surface | Owner | 当前删除不安全原因 | Replacement / deletion condition | Validation / missing guard | Forced review trigger |
|---------|-------|--------------------|----------------------------------|----------------------------|-----------------------|
| `TaskOrderMaintainedBatchContract` / `WorldTaskOrderMaintainedAssignment` | WP23-C / WP23-D | 是有用 replacement candidate，但仍通过 compatibility storage 投影，尚非唯一 truth。 | 只有旧 whole-shell APIs 被删除，或显式标为 compatibility 并加 guard 后才保留。 | 缺失 guard：不能证明 callers 无法把 maintained 与 whole-shell 两种 shape 都当作 maintained truth。 | WP23-D public API exit decision，或任何 TaskOrder implementation patch。 |
| `WorldTaskOrderAssignment.order` 与 `set/get_task_orders_batch` | WP23-D | Public runtime/facade/Python API 仍有 consumers 与 tests。 | 私有处删除；公开处只能作为 maintained path 外的显式 compatibility API。 | 缺失 public API deprecation/removal guard 与 consumer inventory。 | Public API inventory 改变，或 maintained contract packet replacement 落地。 |
| `ObservationBatchPacket.task_orders` | WP23-D | Public packet shape 导出 whole-shell `TaskOrder`。 | 替换为 maintained contract packet field，或标记为 retained compatibility export。 | 缺失 guard：阻止 observation packet 被引用为 maintained TaskOrder truth。 | Observation packet API 改动，或 facade-owned replacement 落地。 |
| Python `hasattr` maintained/legacy fallbacks | WP23-D / WP23-E | 可静默 fallback 到 whole-shell assignment，隐藏 representation drift。 | 使用显式 representation choice，或在 bindings baseline 固定后删除 fallback。 | 缺失测试：fallback 意外保留 dual truth 时必须失败。 | Binding baseline 改变，或 vector-env tasking path 改动。 |

WP23-C 退出：以 `blocked` 完成。这消耗 WP23-C 唯一 design/audit round。之后任何
TaskOrder 代码工作只能属于 `WP23-D` public API exit classification，或 owner 批准的
re-baseline，不得变成另一轮 WP23-C repair wave。

## 5.4 WP23-D Public API Exit Decision

审计日期：`2026-05-24`。

判定：`blocked public API`，本轮没有识别出 deletion-ready implementation surface。

依据：

- `RuntimeFacade::runtime()` 仍是 public compatibility escape hatch：
  它声明在 `src/runtime/facade/runtime_facade.h:53-56`，实现在
  `src/runtime/facade/runtime_facade.cpp:2498-2503`，并在
  `src/interfaces/python/bindings_runtime.cpp:1645` 绑定到 Python。
- `WorldBatchRuntime::world()` 仍是 raw batch runtime 上的 public API：
  `src/core/engine/world_batch_runtime.h:65-68` 将其标为 compatibility/diagnostics
  escape hatch。现有低层测试和 diagnostics 仍使用 raw worlds，例如
  `tests/world_batch/test_world_batch_runtime.py:355-408`，以及通过
  `facade.runtime().world(0)` 进入的 engagement diagnostics tests。
- `vec_env.batch_runtime` 尚未删除；它在
  `python/rl/runtime/world_batch_vec_env.py:302-306` 由显式
  `runtime_compatibility_enabled` opt-in gate 控制，由
  `python/rl/runtime/world_batch/compat.py:29-43` 的 `RuntimeCompatibilityView`
  支撑，并在 `tests/world_batch/test_world_batch_vec_env.py:669-704` 作为显式
  compatibility view 被测试。
- 当前 architecture guards 是局部化，不是删除：
  `tests/architecture/runtime_facade/test_scenario_setup_facade_boundary.py` 检查 `.batch_runtime`
  与 `RuntimeFacade.runtime()` consumers 留在显式 allowlist；
  `tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py:43-86` 在 replacement gates
  存在前保留 public compatibility surfaces。
- TaskOrder whole-shell public APIs 仍跨 C++ 与 Python bindings live：
  `set_task_orders_batch` / `get_task_orders_batch` 仍在
  `src/interfaces/python/bindings_runtime.cpp:1539-1582` 和
  `src/interfaces/python/bindings_runtime.cpp:1696-1735` 分别为
  `WorldBatchRuntime` 与 `RuntimeFacade` 绑定。
- GPU/visual compatibility overloads 仍在
  `src/interfaces/python/bindings_gpu.cpp:790-880` 接受 raw `WorldBatchRuntime&`
  参数，同时 facade overloads 也存在。因此 raw overloads 在 public callers 迁到
  facade overloads 前仍是 compatibility retained。

WP23-D 分类：

| Surface | 判定 | 原因 | Exit condition | Guard / validation |
|---------|------|------|----------------|--------------------|
| `RuntimeFacade::runtime()` | `blocked compatibility escape hatch` | Public Python binding 与 diagnostics consumers 仍存在。 | diagnostics 与 legacy adapters 都有 facade-owned replacements 后才删除。 | 保持 architecture guard，禁止 maintained-path consumers 落到 allowlists 外。 |
| `WorldBatchRuntime::world()` | `blocked diagnostics/raw-world escape hatch` | 低层 runtime tests、scenario-loader seams 与 diagnostics 仍需要 raw world access。 | spawn/setup/diagnostics helper APIs 覆盖这些 consumers 后才删除。 | 保持 `.world()` allowlist guard；replacement ready 后再补 deletion guard。 |
| `vec_env.batch_runtime` / `RuntimeCompatibilityView` | `blocked compatibility view` | 显式 opt-in compatibility contract 存在且有测试。 | Public callers 从 `batch_runtime` 迁到 facade/runtime adapter APIs 后才删除。 | 现有 `runtime_compatibility_enabled` gate 必须保留；其通过不等于 retirement evidence。 |
| TaskOrder whole-shell batch APIs | `blocked public tasking API` | WP23-C 已证明 whole-shell read/write 与 observation export 仍和 maintained contract 共存。 | public API inventory 与 replacement packet decision 完成后，删除或标为 compatibility。 | 缺失 guard：阻止 whole-shell APIs 被计为 maintained truth。 |
| `ObservationBatchPacket.task_orders` | `blocked public packet shape` | Public packet 仍导出 whole-shell `TaskOrder`。 | 替换为 maintained contract field，或显式标为 compatibility export。 | 缺失 DTO guard：区分 maintained tasking truth 与 compatibility export。 |
| Raw GPU/visual `WorldBatchRuntime&` overloads | `blocked diagnostics/compat overloads` | Raw overloads 与 facade overloads 为既有 callers 并存。 | callers 使用 facade overloads 且 diagnostics coverage 保留后才删除。 | 缺失 binding guard：拒绝新的 maintained consumers 使用 raw overloads。 |
| Diagnostics traces and diagnostics-only bindings | `compatibility retained` | diagnostics 本来就不是 maintained truth。 | 除非变成 maintained dependencies，否则带明确 `diagnostics_only` label 保留。 | 现有 diagnostics-only policy tests 仍有效。 |

WP23-D 退出：以 `blocked` 完成。它不解锁大范围删除。WP23-E 只允许候选
guard/label hardening 任务，用来让上述 blocked state 可执行；任何业务迁移或 API 删除
都需要 owner approval 或 re-baselined work package。

## 5.5 WP23-E Minimal Implementation Decision

判定：`skipped`。

原因：

- `WP23-C` 已将 TaskOrder 判定为 dual-representation public API 问题并 blocked。
- `WP23-D` 已 blocked public runtime/world/batch/diagnostics exits，且没有发现
  deletion-ready implementation surface。
- 现有 guards 已经局部化关键 escape hatches：
  `tests/architecture/runtime_facade/test_scenario_setup_facade_boundary.py` 覆盖 `.batch_runtime`
  与 `RuntimeFacade.runtime()` allowlists；
  `tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py:43-86` 将 public compatibility
  surfaces 绑定到 replacement gates。
- 现在补一个小型 guard-only patch 不能删除或迁移任何业务 surface，反而可能把
  `blocked` 变成另一个永久中间态。

WP23-E 退出：不运行 implementation batch。这是有意的 close-out control，不是漏项。
任何未来代码工作都必须作为新的 replacement-backed package 打开，并带明确 API ownership
与 deletion criteria。

## 5.6 WP23-F Close-Out

结果：`blocked`，这是 WP23 recovery 的正确结果。

收口证据：

- WP22 已冻结，只作历史 provenance；其 queues 不得派发。
- WP23 保持文档预算：只有本文和英文主文。
- 当前 WP22-era dirty work 被分类，而不是被整体接受。
- TaskOrder maintained-batch work 未被接受为 single maintained truth。
- Runtime/world/batch public escape hatches 被显式 blocked，而不是误标为 retired。
- C/D 揭示 blocked public API conditions 后，没有启动 subagent 或 implementation wave。

Blocked follow-up conditions：

| Follow-up surface | Required opening condition |
|-------------------|----------------------------|
| TaskOrder single representation | Owner 批准 public API migration：删除 whole-shell tasking APIs，或将其标为 compatibility-only 并加 failing guards。 |
| Observation packet tasking field | Owner 批准 maintained packet replacement，或明确 compatibility export policy。 |
| Runtime/world escape hatches | Facade-owned replacement APIs 覆盖 diagnostics、scenario-loader seams 与 low-level tests。 |
| `vec_env.batch_runtime` | Public callers 迁到 facade/runtime-adapter APIs，或接受文档化 compatibility deprecation plan。 |
| Raw GPU/visual runtime overloads | Maintained callers 使用 facade overloads，且 diagnostics parity 保持覆盖。 |

WP23-F 退出：完成。WP23 不是 legacy retirement pass；它是受控的 `blocked` recovery
closure，阻止 WP22 的 partial/quarantine evidence 被继续用作 acceptance。

## 6. TaskOrder 沉没成本防线

TaskOrder 是 WP23-C 风险最高的项目，因为当前工作树里已有 Hubble partial contract
和 Kepler interrupted wiring。

判定顺序：

1. 验证 maintained-batch path 是否真的替代 maintained whole-shell truth。
2. 如果是，只能在 guard 证明旧 whole-shell path 是 compatibility-only 或 blocked 时保留。
3. 如果不是，rollback 或标 blocked，不能无限 repair。
4. TaskOrder 得到 keep/rollback/blocked 判定前，不启动 LeaderIntent/PilotReport 实现。

WP23-C 的唯一一轮可以用于 audit/design，而不是代码。让 WP23-C 以 `blocked` 结束，
优于复刻 WP22 R2。

## 7. 派发规则

- 轻量 diagnostics/docs 任务：`gpt-5.4-mini`，`xhigh`。
- Runtime/facade/bindings/DTO/public API 任务：`gpt-5.4`，`high` 或 `xhigh`。
- `WP23-C` 与 `WP23-E`：`gpt-5.4`，`xhigh`。
- `WP23-A` 与 `WP23-B` 完成前不得派发 implementation。
- 不得仅为了结束 main thread turn 而关闭正常运行的 worker。
- 只有明确 user stop、request/transport failure、重复/错范围派发或 unsafe scope
  conflict 时才提前关闭。

必需 worker packet：

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 8. 验证基线

具体命令由改动文件决定，但 WP23 implementation 或 close-out 通常应选择相关子集：

```bash
git diff --check
cmake --build build-workshop --target ef_py -j4
python -m pytest -q tests/architecture/runtime_facade
python -m pytest -q tests/architecture/command_tasking/test_dto_domain_shell_guard.py
python -m pytest -q tests/architecture/structural_boundaries
python -m pytest -q tests/runtime/bindings/test_bindings_command_surface.py
python -m pytest -q tests/world_batch/test_world_batch_runtime.py
python -m pytest -q tests/world_batch/test_world_batch_vec_env.py
python -m pytest -q tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py
```

## 9. 下一步

WP23 已以 `blocked` 关闭。

下一步可执行动作：

1. 决定是否打开新的 replacement-backed package 来处理 TaskOrder / public API migration，
   或者在此停止 legacy-retirement work，回到 WP22/WP23 之外的产品或架构工作。
2. 不再派发 WP23 worker。任何新工作都需要 fresh scope、owner、deletion criteria 与
   validation gates。
