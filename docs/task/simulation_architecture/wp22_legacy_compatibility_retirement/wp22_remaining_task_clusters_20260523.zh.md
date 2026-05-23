# WP22 剩余任务簇

状态：`2026-05-23`，在 WP21/WP22 先前收尾口径被拒绝后重新基线化。
本文用于替代临时追加的“下一轮派发”，把剩余工作固定为有限 residual cluster。
`R1-B` 默认工厂 projection deletion 在 `R1-A` 之后仍然被阻塞，因此在下面的 residual R1 子切片完成前都必须继续推迟删除。
R3 仍然必须先重新划分，再允许任何进一步 implementation 或 closure 派发。
本文不声明 WP22 完成，也不让 `WP22-F` 获得验收资格。

输入：

- [WP22 主计划](legacy_compatibility_retirement_wp22_20260522.zh.md)
- [WP22 事实台账](wp22_retirement_fact_ledger_cluster_20260522.zh.md)
- [WP22 派发队列](wp22_subagent_dispatch_queue_20260522.zh.md)
- [架构重构审计](../../review/architecture_refactoring_audit_20260522.md)

## 当前阻塞事实

| 事实 | 当前状态 | 后果 |
|------|----------|------|
| `Epicurus command-link packet` | `partial`；当前工作区仍需要修复和验证。此前架构 guard 在 `deliver_pending_command(cmd[i], pending[i], current_time);` 上失败，runtime link QoS 也存在 `current_control_state_active` 预期过时或行为变化问题。 | 在该稳定门返回完整 packet 前，不能推进 closure 或更大的 command projection 删除。 |
| `MissionCommandControlState` | 只拥有 heading/speed/altitude target 与 lagged mirror，不拥有 throttle/brake/nose-wheel 或完整 action 语义。 | `MovementCommand`、`LaggedCommand`、`ActionCommand` 与 pending action transport 还不能删除。 |
| `default_factory_legacy_spawn_compat.h` | 仍投影行为相关的 `MovementCommand` / `LaggedCommand` mirror。 | `R1-B` 默认工厂 projection deletion 在 `R1-A` 之后仍然被阻塞；重复删除尝试只是 planning smell，不是新的派发目标。 |
| Aggregate DTO shells | `MissionCommand`、`TaskOrder`、`LeaderIntent`、`PilotReport` 只是被标记为 compatibility transport shell，尚未退场。 | `S-001/S-002/S-003` 需要迁移 maintained consumer 或强化 owner-slice 边界。 |
| `Exact-stage inventory` | `src/core/engine/exact_stage_inventory.cpp` 仍然声明 `CommandLinkMovement`、`CommandLinkAction`、`CommandLinkMission`、`ActionMapping`、`CommandLag`、`FlightControl`、`ComputeForces`、`GroundContact`、`UpdateInstruments` 与 `FuelConsumption` 的 exact-stage contract。 | exact-stage contract 的 demotion/alignment 必须先完成，然后才能重新讨论 default-factory projection deletion。 |
| `Diagnostics/debug movement mirror bindings` | `src/interfaces/python/bindings_core.cpp` 仍暴露 quarantined 的 debug movement mirror helpers，包括 `debug_get_pending_movement_command`、`debug_get_pending_action_command`、`debug_get_legacy_movement_command` 与 `debug_set_legacy_movement_command`。 | debug/diagnostics mirror retirement 是 residual R1 cluster 的一部分。 |
| Public escape hatches | `RuntimeFacade::runtime()`、`WorldBatchRuntime::world()`、公开 `batch_runtime` / `vec_env.batch_runtime`、diagnostics bindings、显式 legacy mode 与 fallback cadence 仍是 compatibility/diagnostics surface，直到 replacement APIs 存在。 | `WP22-C/E/F` 在 maintained caller 被 guard 或迁移前不能关闭。 |
| Structural debt | `runtime_facade.cpp`、`default_unit_factory.h`、`bindings_core.cpp` 与 `exact_stage_inventory.cpp` 仍是混合职责表面。 | 仍需要结构工作，但结构拆分本身不能被误当成 legacy 退场。 |

## 有限 residual cluster 计划

| 任务簇 | 状态 | 范围 | 退出门 |
|--------|------|------|--------|
| `WP22-R0 Current Partial Stabilization` | ready，必须先做 | 完成 Epicurus 遗留的 command-link pending transport narrowing。movement delivery 由 typed state 拥有，action pending transport 维持 quarantine。 | focused runtime link/mission 测试通过，architecture command guards 通过，`ef_py` 构建通过，`git diff --check` 干净。 |
| `WP22-R1 Finite Residual Cluster` | R0 后排队；`R1-B` 在 `R1-A` 之后仍被阻塞 | 把剩余的 R1 工作收敛成三个有限子切片：pending transport shell narrowing、debug/diagnostics mirror retirement、exact-stage contract demotion/alignment。默认工厂 projection deletion 继续推迟，直到这三个子切片都返回完整 packet。 | `R1-B` 默认工厂 projection deletion 继续推迟；重复删除尝试只是 planning smell，不是新的派发目标。 |
| `WP22-R2 DTO Domain-Shell Retirement` | 可并行；在再做临时追加实现前需要重切边界 | 将 maintained consumer 从聚合 command/tasking shell 迁移到 owner-slice 或 domain-specific DTO。compatibility transport shell 必须保持显式。 | DTO-shell guard 证明 maintained logic 使用 owner slice 或显式 projection，而不是 flat aggregate truth。 |
| `WP22-R3 Adapter Raw-World Replacement Re-scope` | 需先重划边界，才能继续 implementation 或 closure 派发 | 在任何 public escape-hatch 删除之前，先用 facade-owned request/result APIs 替换 maintained adapter raw-world methods。公开 runtime/world/batch access 与 diagnostics bindings 在 replacement APIs 存在前保持 compatibility-only。 | 下方三个有限 sub-slice 都必须返回 complete packet；只有这样，public escape-hatch deletion 才能进入考虑。 |
| `WP22-R4 Structural Decomposition And Acceptance Prep` | 依赖门控 | R0-R3 ownership 稳定后再拆剩余大型表面，并运行 closure audit。 | 无未归属 default legacy path 后，才允许起草 closure audit 与 acceptance。 |

硬上限：

- R0 最多一轮 repair。
- R1 仅限下面三个命名子切片，不要再发明新的 R1 派发。
- R3 必须先重划为下面的有限 replacement 任务簇，然后才可以继续任何 implementation 或 closure 派发。
- R2 已达到实现上限；在正式重切边界前，不再派发临时追加实现。
- R4/WP22-F 是串行 closure，R0-R3 未返回完整 packet 前不可派发。

## R1 Residual Sub-slices

| 子切片 | 范围 | 退出门 |
|-------|------|--------|
| `R1-1 Pending transport shell narrowing` | 收窄 `PendingMovementCommand` 与 `PendingActionCommand`，让 maintained delivery 只消费 typed payload，并把 legacy transport shell 限定为 diagnostics-only 或从 maintained path 删除。 | pending movement/action transport 不再充当 maintained command truth。 |
| `R1-2 Debug/diagnostics mirror retirement` | 退场或强 quarantine `bindings_core.cpp` 里的 debug movement mirror bindings，包括 legacy movement getter/setter 与 pending transport debug view。 | diagnostics access 是显式的，不会让 maintained caller 绕过 typed state。 |
| `R1-3 Exact-stage contract demotion/alignment` | 将 exact-stage inventory 从 maintained implementation truth 降级为受 guard 保护的 contract ledger，使其与 typed ownership、bridge compatibility projections 以及剩余的 optional operation/command-link mirror signatures 对齐。 | `exact_stage_inventory.cpp` 不再阻塞 residual R1 cluster 或 default-factory projection deletion。 |

## R3 Replacement Sub-slices

| 子切片 | 范围 | 退出门 |
|-------|------|--------|
| `R3-1 Scenario-loader construction` | 把 scenario-loader construction 从 raw-world 调用迁移到 facade-owned request/result 输入。 | scenario-loader construction 不再需要新的 maintained raw-world access。 |
| `R3-2 World layout/time-step access` | 用 facade-owned request/result APIs 暴露 world layout 与 time-step 读取，替代 raw adapter methods。 | layout/time-step 数据通过 replacement API 读取，而不是通过新的 maintained raw-world call site。 |
| `R3-3 Visual compatibility export/candidate helpers` | 将 visual compatibility export 与 candidate helper assembly 收拢到 facade-owned path。 | visual helper assembly 不再依赖新的 maintained raw-world access。 |

## 第一批派发

| 派发 | 任务簇 | 模型 / 思考预算 | 写入范围 | 为什么可并行 |
|------|--------|-----------------|----------|--------------|
| `WP22-R0-A command-link stabilization` | R0 | `gpt-5.4`, xhigh | `src/components/command/command_link.h`、`src/systems/systems/command_link_system.h`、`src/core/engine/simulation_kernel_command_api.cpp`、`tests/runtime/link/test_command_link_qos.py`、`tests/architecture/test_wp9_guard_enforcement.py` | 独占当前 partial packet，不触碰 DTO、runtime facade、binding 或 factory 文件。 |
| `WP22-R2-A DTO owner-slice migration` | R2 | `gpt-5.4`, high | command/tasking DTO headers 与 `tests/architecture/test_wp22_dto_domain_shell_guard.py`；不编辑 runtime facade 或 command-link | 与 R0 command-link 修复相互独立。 |
| `WP22-R3-A adapter raw-world replacement re-scope` | R3 | `gpt-5.4-mini`, xhigh | 仅 docs 与 queue 同步；不改代码 | 重新对齐有限 replacement 任务簇，保持 public escape hatches 仍为 compatibility-only，并在未来 implementation 派发前保持双语状态一致。 |

## 暂缓派发

| 派发 | 依赖 | 原因 |
|------|------|------|
| `WP22-R1-B default-factory projection deletion` | `R1-1`、`R1-2` 与 `R1-3` 全部完成 | `R1-B` 在 `R1-A` 后仍然被阻塞；重复删除尝试只是 planning smell，不是已就绪的证据。 |
| `WP22-R4-A closure preflight` | R0-R3 complete | 现在运行 closure 只会重复得到 “not eligible”。 |

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
