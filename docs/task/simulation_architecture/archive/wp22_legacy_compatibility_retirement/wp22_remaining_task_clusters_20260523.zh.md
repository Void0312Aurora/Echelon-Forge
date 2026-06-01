# WP22 剩余任务簇

状态：frozen / 已由
[`WP23 Legacy Retirement Recovery And Reset`](../wp23_legacy_retirement_recovery/legacy_retirement_recovery_wp23_20260523.zh.md)
取代。本文档只作为历史证据，不得再作为 active residual queue，也不得授权新的 WP22
wave。

冻结前历史状态：`2026-05-23`，在 WP21/WP22 先前收尾口径被拒绝后重新基线化。
本文用于替代临时追加的“下一轮派发”，把剩余工作固定为有限 residual cluster。
`R1-B` 默认工厂 projection deletion 在 `R1-A` 之后仍然被阻塞，因此在下面的 residual R1 子切片完成前都必须继续推迟删除。
R3 已经被收束成有限 replacement cluster；这里只允许下面三个子切片派发，public escape-hatch deletion 仍然被阻断。
本文不声明 WP22 完成，也不让 `WP22-F` 获得验收资格。

`R2` 现在已经围绕已接受的 `MissionCommand` owner-slice migration pass 正式重切。
剩余的 R2 工作是有限且有源码事实支撑的：`TaskOrder`、`LeaderIntent`、
`PilotReport` 以及 world-batch assignment shell family。这个 packet 只用于文档
重切，不授权 implementation、`WP22-F`、`R4` 或 closure。

输入：

- [WP22 主计划](legacy_compatibility_retirement_wp22_20260522.zh.md)
- [WP22 事实台账](wp22_retirement_fact_ledger_cluster_20260522.zh.md)
- [WP22 派发队列](wp22_subagent_dispatch_queue_20260522.zh.md)
- [架构重构审计](../../../review/architecture_refactoring_audit_20260522.md)

## 当前阻塞事实

| 事实 | 当前状态 | 后果 |
|------|----------|------|
| `Command-link pending transport packet` | `scoped pass`；delayed movement delivery 现在由 typed state 拥有，pending action delivery 有显式 typed air-control overlay projection。 | 这只稳定 R0/R1-1；不删除 pending shells、`ActionCommand`、default-factory projections 或 public compatibility escape hatches。 |
| `MissionCommandControlState` | 只拥有 heading/speed/altitude target 与 lagged mirror，不拥有 throttle/brake/nose-wheel 或完整 action 语义。 | `MovementCommand`、`LaggedCommand`、`ActionCommand` 与 pending action transport 还不能删除。 |
| `default_factory_legacy_spawn_compat.h` | 仍投影行为相关的 `MovementCommand` / `LaggedCommand` mirror。 | `R1-B` 默认工厂 projection deletion 在 `R1-A` 之后仍然被阻塞；重复删除尝试只是 planning smell，不是新的派发目标。 |
| Aggregate DTO shells | `MissionCommand`、`TaskOrder`、`LeaderIntent`、`PilotReport` 只是被标记为 compatibility transport shell，尚未退场。 | `S-001/S-002/S-003` 需要迁移 maintained consumer 或强化 owner-slice 边界。 |
| `Exact-stage inventory` | `src/core/engine/exact_stage_inventory.cpp` 现在是受 guard 保护的 contract ledger，不再是 maintained-truth register。 | R1-3 是 scoped pass，但 ledger demotion 不授权 default-factory projection deletion。 |
| `Diagnostics/debug movement mirror bindings` | `src/interfaces/python/bindings_core.cpp` 仍暴露 quarantined 的 debug movement mirror helpers，包括 `debug_get_pending_movement_command`、`debug_get_pending_action_command`、`debug_get_legacy_movement_command` 与 `debug_set_legacy_movement_command`。 | R1-2 只接受为 hard quarantine/narrowing；diagnostics helpers 仍存在并保持 non-maintained surface。 |
| Public escape hatches | `RuntimeFacade::runtime()`、`WorldBatchRuntime::world()`、公开 `batch_runtime` / `vec_env.batch_runtime`、diagnostics bindings、显式 legacy mode 与 fallback cadence 仍是 compatibility/diagnostics surface，直到 replacement APIs 存在。 | `WP22-C/E/F` 在 maintained caller 被 guard 或迁移前不能关闭；这些 surface 只能 quarantine，不能删除。 |
| Structural debt | `runtime_facade.cpp`、`default_unit_factory.h`、`bindings_core.cpp` 与 `exact_stage_inventory.cpp` 仍是混合职责表面。 | 仍需要结构工作，但结构拆分本身不能被误当成 legacy 退场。 |

## R2 残余 owner-slice targets

已接受的 `MissionCommand` owner-slice migration pass 不在这里重开。R2 的
剩余项是有限且有源码依据的；下面这些才是下一批可以讨论的 owner-slice
targets，在 guard 通过前都继续保持 compatibility 显式。

| Target | 有源码依据的 owner slices / guards | 仍然 live 的内容 | 硬停条件 |
|--------|-------------------------------------|------------------|----------|
| `TaskOrder` | `TaskOrderCore`、`TaskOrderAir`、`TaskOrderNaval`；`src/components/tasking/task_order.h` 仍是 flat compatibility/transport shell。 | maintained caller 仍可直接到达 umbrella shell，而不是 owner-slice projection。 | 如果 packet 需要发明新的 DTO shape，或把 shell 扩宽到现有 source slices 之外，就必须停为 `blocked`。 |
| `LeaderIntent` | `LeaderIntentCore`、`LeaderIntentAir`、`LeaderIntentNaval`；`src/components/tasking/leader_intent.h` 仍是 flat compatibility/transport shell。 | maintained caller 仍可直接到达 umbrella shell，而不是 owner-slice projection。 | 如果任何 maintained caller 仍需要 flat-shell truth，而又不能用显式 compatibility projection 表达，就必须停为 `blocked`。 |
| `PilotReport` | `PilotReportCore`、`PilotReportAir`、`PilotReportNaval`；`src/components/tasking/pilot_report.h` 仍是 flat compatibility/transport shell。 | maintained caller 仍可直接到达 umbrella shell，而不是 owner-slice projection。 | 如果 packet 想把 transport 责任搬进一个新的 maintained DTO，而不是使用现有 owner slices，就必须停为 `blocked`。 |
| world-batch assignment shells | `WorldMissionCommandAssignment`、`WorldTaskOrderAssignment`、`WorldLeaderIntentAssignment`、`WorldPilotReportAssignment`，以及 `world_batch_assignment_compatibility_shell(...)`。 | 这些 wrapper 仍然 live，且 source 中已有 `shell_type` marker 与 guard helper。 | 如果改动会把这些 wrapper 变成 first-class maintained truth，或移除它们明确的 transport-only contract，就必须停为 `partial` 或 `blocked`。 |

硬停条件：

- 如果源码仍显示某条 maintained path 上存在 flat-shell truth，或者 packet
  必须发明新的 DTO shape / 扩宽现有 compatibility shell，就返回
  `blocked`。
- 如果只能让一部分 maintained consumer 迁移，而 flat shell 仍必须为其余
  consumer 保持 live，或者 packet 只能证明 guard narrowing 而不是 retirement，
  就返回 `partial`。
- 如果下一步会触碰 public escape hatch，例如 `RuntimeFacade::runtime()`、
  `WorldBatchRuntime::world()`、公开 `batch_runtime` / `vec_env.batch_runtime`
  或 diagnostics bindings，就必须立即停手；这些不属于 R2。
- 无论哪种情况，都不要从这个 packet 授权 implementation、`WP22-F`、`R4`
  或 closure。

## 有限 residual cluster 计划

| 任务簇 | 状态 | 范围 | 退出门 |
|--------|------|------|--------|
| `WP22-R0 Current Partial Stabilization` | scoped pass accepted | 完成 Epicurus 遗留的 command-link pending transport narrowing。movement delivery 由 typed state 拥有，action pending transport 维持 quarantine。 | focused runtime link/mission 测试通过，architecture command guards 通过，`ef_py` 构建通过，`git diff --check` 干净。 |
| `WP22-R1 Finite Residual Cluster` | `R1-1`、`R1-2`、`R1-3` scoped pass；deletion 仍被阻塞 | 把剩余的 R1 工作收敛成三个有限子切片：pending transport shell narrowing、debug/diagnostics mirror retirement、exact-stage contract demotion/alignment。默认工厂 projection deletion 继续推迟，直到 live mirror consumers 被证明可替换。 | `R1-B` 默认工厂 projection deletion 继续推迟；重复删除尝试只是 planning smell，不是新的派发目标。 |
| `WP22-R2 DTO Domain-Shell Retirement` | scoped `MissionCommand` pass；R2 的 finite residual list 仅限 `TaskOrder`、`LeaderIntent`、`PilotReport` 与 world-batch assignment shells；继续 implementation 前必须正式重切边界 | 将 maintained consumer 从聚合 command/tasking shell 迁移到 owner-slice 或 domain-specific DTO。compatibility transport shell 必须保持显式。 | DTO-shell guard 证明 maintained logic 使用 owner slice 或显式 projection，而不是 flat aggregate truth。 |
| `WP22-R3 Adapter Raw-World Replacement Re-scope` | `R3-1`、`R3-2`、`R3-3` scoped stable；不再派发 R3 implementation | 在任何 public escape-hatch 删除之前，先用 facade-owned request/result APIs 替换 maintained adapter raw-world methods。公开 runtime/world/batch access 与 diagnostics bindings 在 replacement APIs 存在前保持 compatibility-only。 | R3 已无有限 implementation dispatch 处于开放状态，但 public escape-hatch deletion 仍被阻断，且这不是 closure evidence。 |
| `WP22-R4 Structural Decomposition And Acceptance Prep` | 依赖门控 | R0-R3 ownership 稳定后再拆剩余大型表面，并运行 closure audit。 | 无未归属 default legacy path 后，才允许起草 closure audit 与 acceptance。 |

当前 `R2` 备注（`2026-05-23`）：`TaskOrder` shared-core guard 切片、
Python command-chain `LeaderIntent` / `PilotReport` projection 切片，以及
Python binding owner-slice exposure 切片都只接受为 `partial` evidence。
Peirce 已经把 Python command-chain snapshot path 移到 bound `LeaderIntent`
/ `PilotReport` owner-slice helpers 上，Nash 也对 `TaskOrder` command-chain
snapshot 完成同类切换，改为消费 bound `task_order_shared_core`、
`task_order_air_owner_slice` 与 `task_order_naval_owner_slice` helper views。
Feynman 已解除 `TaskOrder` Python binding visibility blocker，Kierkegaard
则确认剩余 R2 路径不再是 snapshot visibility，而是
`WorldTaskOrderAssignment`、`WorldLeaderIntentAssignment`、
`WorldPilotReportAssignment`、vec-env assignment writes，以及更广义
batch/facade/public binding APIs 中仍 live 的 whole-shell transport。
Beauvoir 的 readiness preflight 未发现可授权 closure 的 stale docs。Cicero
随后把 Python assignment writes 收口到命名 compatibility transport helpers，
Boyle 则确认现有 `TaskOrderCore` / `TaskOrderAir` / `TaskOrderNaval`
owner-slice projections 本身并不是可替代 public batch write/read contract。
Hubble 已经定义 guard-first 的 `TaskOrderMaintainedBatchContract` 与
`WorldTaskOrderMaintainedAssignment`；因此下一步 R2 串行工作是把这个
maintained contract 接入 runtime/facade/binding/Python write/read APIs，同时让旧
shell APIs 保持显式 compatibility-only surface。这不解锁 R4、`WP22-F`、DTO shell
retirement 或 public escape-hatch deletion。

硬上限：

- R0 repair 已完成，不要重新派发。
- R1 仅限下面三个 scoped-pass 子切片，不要再发明新的 R1 派发。
- R3 已限制为下面三个有限 replacement 子切片；三个子切片均为 scoped pass，这里不再允许继续派发 R3 implementation。
- R2 implementation 仅限下面已由源码支撑的 assignment transport 与
  batch/facade whole-shell seams；下一串行切片是 `TaskOrder` maintained
  runtime/facade/binding API wiring。除非验证回退，否则不要重开 owner-slice binding、
  command-chain snapshot 或 direct shell deletion 工作。
- R4/WP22-F 是串行 closure；只要 R2 residual owner-slice work、public
  compatibility escape hatches、default-factory projection 与 structural/binding
  debt 仍开放，就不可派发。

## R1 Residual Sub-slices

| 子切片 | 范围 | 退出门 |
|-------|------|--------|
| `R1-1 Pending transport shell narrowing` | `scoped pass`：已收窄 `PendingMovementCommand` 与 `PendingActionCommand`，让 maintained delayed movement delivery 消费 typed payload，action pending delivery 具备显式 typed overlay projection。 | pending movement 不再充当 maintained command truth；action pending shell 仍是 quarantined compatibility transport。 |
| `R1-2 Debug/diagnostics mirror retirement` | `scoped pass`：`bindings_core.cpp` 里的 debug movement mirror bindings 已 hard-quarantine 为 diagnostics-only 或 legacy override surface，包括 legacy movement getter/setter 与 pending transport debug view。 | diagnostics access 是显式的，不会让 maintained caller 绕过 typed state。 |
| `R1-3 Exact-stage contract demotion/alignment` | `scoped pass`：将 exact-stage inventory 从 maintained implementation truth 降级为受 guard 保护的 contract ledger，使其与 typed ownership、diagnostics shells、bridge compatibility projections 以及剩余的 optional operation/command-link mirror signatures 对齐。 | `exact_stage_inventory.cpp` 不再作为 maintained-truth register；它只保留为受 guard 保护的 contract evidence，而 `R1-B` 仍然被阻塞。 |

## R3 Replacement Sub-slices

| 子切片 | 范围 | 退出门 |
|-------|------|--------|
| `R3-1 Scenario-loader construction` | `scoped pass`：`python/rl/runtime/world_batch/adapter.py` 里的 loader construction 路径现在使用命名 runtime-world-layout request/result seam，不再新增 maintained raw-world construction call site。 | scenario-loader construction 不再需要新的 maintained raw-world call site。 | `RuntimeFacade::runtime()`、`WorldBatchRuntime::world()`、`vec_env.batch_runtime` 继续是 quarantine-only；不能进入 deletion-ready。 |
| `R3-2 World layout/time-step access` | `scoped pass`：`python/rl/runtime/world_batch/adapter.py::world()` 现在返回受控 proxy 用于 layout/time-step read，`get_time_step()` 优先走 facade/runtime helper，并在 raw-world compatibility 前使用 adapter-owned fallback。 | layout/time-step 数据通过 replacement seam 读取，而不是通过新的 maintained raw-world call site。 | `WorldBatchRuntime::world()`、显式 `legacy` mode、diagnostics bindings 与 raw-world compatibility forwarding 继续是 quarantine-only。 |
| `R3-3 Visual compatibility export/candidate helpers` | `scoped pass`：facade-owned visual candidate assembly 现在经由命名 compatibility helpers，GPU wrappers 也保持 facade-owned 与 compatibility-runtime path 显式分离。 | visual helper assembly 不再依赖新的 maintained raw-world access。 | `RuntimeFacade::runtime()`、`WorldBatchRuntime::world()`、`vec_env.batch_runtime` 与 diagnostics bindings 继续是 quarantine-only。 |

当前 `R3` 备注（`2026-05-23`）：`R3-1`、`R3-2`、`R3-3` 均为 scoped pass。公开 `RuntimeFacade::runtime()`、`WorldBatchRuntime::world()`、`vec_env.batch_runtime`、显式 `legacy` mode、diagnostics bindings 与 raw-world compatibility forwarding 仍是 quarantine-only blocker，因此这不代表 public escape-hatch deletion-ready 或 WP22 closure evidence。

## 第一批派发

| 派发 | 任务簇 | 模型 / 思考预算 | 写入范围 | 为什么可并行 |
|------|--------|-----------------|----------|--------------|
| `WP22-R0-A command-link stabilization` | R0 | `gpt-5.4`, xhigh | `src/components/command/command_link.h`、`src/systems/systems/command_link_system.h`、`src/core/engine/simulation_kernel_command_api.cpp`、`tests/runtime/link/test_command_link_qos.py`、`tests/architecture/test_wp9_guard_enforcement.py` | 独占当前 partial packet，不触碰 DTO、runtime facade、binding 或 factory 文件。 |
| `WP22-R2-A DTO owner-slice re-scope` | R2 | `gpt-5.4-mini`, xhigh | 仅 docs 与 queue 同步；不改代码。 | 把已接受的 `MissionCommand` pass 重切为有限 residual list：`TaskOrder`、`LeaderIntent`、`PilotReport` 与 world-batch assignment shells；继续保持 implementation、`WP22-F`、`R4` 和 closure 在 scope 外。 |
| `WP22-R2-B Python binding owner-slice exposure` | R2 | `gpt-5.4`, xhigh | `src/interfaces/python/bindings_command.cpp`、focused binding/DTO guard tests，以及最小 Python visibility tests | 将现有 `LeaderIntent` / `PilotReport` owner-slice types 与 projection helpers 暴露到 Python；不能发明新 DTO shape，不能扩宽 compatibility shells；如果 whole-shell transport 仍是必需路径，则返回 `partial` 或 `blocked`。 |
| `WP22-R2-C Python command-chain bound owner-slice consumption` | R2 | `gpt-5.4`, xhigh | `python/rl/runtime/world_batch/command_chain_cache.py`、focused world-batch/cooperative command-chain tests，以及必要时最小 binding-surface assertions | 尽可能把手工维护的 `LeaderIntent` / `PilotReport` owner-slice snapshots 改为从 bound owner-slice helper views 取值；assignment wrappers 保持 transport-only，如果 whole-shell transport 仍 live，则返回 `partial`。 |
| `WP22-R2-D TaskOrder Python owner-slice exposure` | R2 | `gpt-5.4`, xhigh | `src/interfaces/python/bindings_command.cpp`、binding/DTO guard tests，以及最小 TaskOrder command-chain visibility tests | 将现有 `TaskOrderCore` / `TaskOrderAir` / `TaskOrderNaval` owner slices 与 projection helpers 暴露到 Python；不能发明 DTO shape，不能扩宽 compatibility shells；如果 whole-shell transport 仍 live，则返回 `partial`。 |
| `WP22-R2-E residual whole-shell fact check` | R2 | `gpt-5.4-mini`, xhigh | 只读源码检查 | 给出 Peirce 后 `TaskOrder`、`LeaderIntent`、`PilotReport` 与 assignment-wrapper 剩余 whole-shell paths 的精确 anchors，并区分 compatibility-only transport 与 maintained truth。 |
| `WP22-R2-F TaskOrder command-chain bound owner-slice consumption` | R2 | `gpt-5.4`, xhigh | `python/rl/runtime/world_batch/command_chain_cache.py`、focused world-batch/cooperative command-chain tests，以及最小 TaskOrder snapshot assertions | 将 whole-shell `TaskOrder` command-chain snapshot 替换为从 bound `ef_py.task_order_*` owner-slice helper views 取值；`WorldTaskOrderAssignment` 保持 transport-only，只要 transport wrappers 仍 live 就返回 `partial`。 |
| `WP22-R3-A adapter raw-world replacement re-scope` | R3 | `gpt-5.4-mini`, xhigh | 仅 docs 与 queue 同步；不改代码 | 重新对齐有限 replacement 任务簇，使未来 implementation 只能针对 `R3-1` scenario-loader construction、`R3-2` world layout/time-step access 或 `R3-3` visual compatibility export/candidate helpers；`RuntimeFacade::runtime()`、`WorldBatchRuntime::world()`、`vec_env.batch_runtime` 与 diagnostics bindings 继续 quarantine-only。 |

## 暂缓派发

| 派发 | 依赖 | 原因 |
|------|------|------|
| `WP22-R1-B default-factory projection deletion` | `R1-1`、`R1-2` 与 `R1-3` 全部完成 | `R1-B` 在 `R1-A` 后仍然被阻塞；重复删除尝试只是 planning smell，不是已就绪的证据。 |
| `WP22-R4-A closure preflight` | R2 residual work、public compatibility escape hatches、default-factory projection 与 structural/binding debt 均已解决 | 现在运行 closure 只会重复得到 “not eligible”。 |

## Worker Packet 要求

每个 worker 必须返回：

- `status`：`pass`、`partial`、`blocked` 或 `failed`。
- `touched files`：精确文件列表。
- `commands/outcomes`：运行过的命令和结果。
- `remaining paths`：仍然 live 的 legacy、compatibility、diagnostics 或 transport shell。
- `integration notes`：行为风险和主线程必须复验的文件。

规则：

- worker 并不独占代码库，不能 revert 无关改动。
- 线程关闭、超时、中断只是 transport event，不是证据。
- `partial` 永远不能解锁下游 closure。
- 任何 worker 都不能宣称 WP22 完成、`R1-B` 已解阻塞，或 `WP22-F` eligible。
