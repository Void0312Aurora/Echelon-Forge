# WP22-D Command DTO 与 Legacy Surface 退场

状态：`2026-05-22` 源事实复核已完成，A-001 后续实现已落地，最新
default-factory seed narrowing 切片也已本地通过。Maintained typed setup
现在使用 maintained validator 加 batch-owned typed spawn helper；显式 legacy
compatibility setup 仍命名保留并与 maintained path 分离。`default_unit_factory.h`
已不再 direct include `legacy_command.h`；剩余 spawn-time command projection 隔离在
`default_factory_spawn_command_projection.h`，但这仍不是 typed control-state ownership。
更广义 command/DTO 退场仍开放。

WP22 的 2026-05-23 re-baseline 备注：`R1-B` 默认工厂 projection deletion 在 `R1-A`
之后仍然被阻塞。重复删除尝试只是 planning smell，不是新的派发目标。
有限 residual cluster 现在拆成 pending transport shell narrowing、debug/diagnostics
mirror retirement 与 exact-stage contract demotion/alignment；在这三个子切片完成前，
default-factory projection deletion 继续推迟。

Noether pass：allowlist 不是 closure evidence。剩余 seam 只有在同时具备
replacement、owner 与 failing guard 时才允许保持打开。
`control_input_resolution.h`、`command_link.h` 与 `operation_system.h`
仍是命名的 compatibility-owner seam；default-factory spawn seed 现在由
`default_factory_spawn_command_projection.h` 持有。该 helper 是显式 quarantine，
不是 typed control-state replacement。
第八轮 Harvey 切片只能验收为 `partial`：default factory 现在会先 seed typed
`MissionCommand` shell，再投影 compatibility state，但 `MovementCommand` /
`LaggedCommand` projection 仍承载行为语义，继续阻塞 `L-001b` 退场。

Guard wording checkpoint：
`control_input_resolution.h`、`command_link.h` 与 `operation_system.h` 仍是命名的
compatibility-owner seam；
`default_factory_spawn_command_projection.h` 持有剩余 spawn-time command mirror projection，直到 typed control-state replacement 落地前仍阻塞 closure；
`MissionCommand`、`TaskOrder`、`LeaderIntent` 与 `PilotReport` 现在已标为
compatibility transport shell，并带 owner-slice projection helper；这是 guarded
quarantine，不是 DTO retirement；
allowlist 不是 closure evidence；
每个开放 seam 仍需 replacement、owner 与 failing guard。

输入：

- [WP22 main plan](legacy_compatibility_retirement_wp22_20260522.zh.md)
- [WP22-A fact ledger](wp22_retirement_fact_ledger_cluster_20260522.zh.md)
- [WP22-C runtime escape-hatch closure](wp22_runtime_escape_hatch_closure_cluster_20260522.zh.md)

## 目的

退场仍然作为 maintained implementation surface 的 C++ legacy command fallback、
aggregate DTO shell 与 type-name setup compatibility。WP22-D 不允许把
compatibility preservation 当作 closure evidence。

## 源事实复核范围快照

| ID | 已核验 live fact | Source anchors | Retirement mode | Implementation dependency |
|----|------------------|----------------|-----------------|---------------------------|
| `L-001` | `legacy_command.h` 仍是 maintained surface。直接 include allowlist 已缩窄，但这并不是 closure evidence：`control_input_resolution.h`、`command_link.h` 与 `operation_system.h` 仍是命名的 compatibility-owner seam，且 maintained path 仍读取 `MovementCommand` 或 `ActionCommand`。 | `src/components/command/air/control_input_resolution.h:5`; `src/components/command/command_link.h:3`; `src/systems/core/operation_system.h:8`; `src/systems/naval/embarked_air_ops_system.h:11`; `src/systems/combat/damage_system.h:9`; `src/systems/physics/ground_contact_system.h:177`; `src/systems/physics/force_system.h:75-78`; `src/systems/physics/instrument_system.h:182-183`; `src/systems/physics/propulsion_system.h:40-47`; `src/systems/systems/logistics_system.h:90-94` | `migrate` | 可立即启动 maintained caller 迁移与 guard；在这些系统仍以 legacy command 为 truth 前，不得宣称已退场。 |
| `L-001a` | `control_input_resolution.h` 只是 partial bridge。它集中了一部分 fallback 检查，但 propulsion、force、instrument、ground-contact 仍自带 legacy-resolution 行为。 | `src/components/command/air/control_input_resolution.h:17-48`; `src/systems/physics/propulsion_system.h:40-47`; `src/systems/physics/ground_contact_system.h:177`; `src/systems/physics/force_system.h:75-78`; `src/systems/physics/instrument_system.h:182-183` | `quarantine` | 可与 `L-001` 并行；在单一 bridge 完成前，不得删除各系统 fallback。 |
| `L-001b` | Aircraft spawn command mirror projection 现在已隔离到 `default_factory_spawn_command_projection.h` 的 `SpawnCommandProjectionControlStateSeed`；`default_unit_factory.h` 只调用命名 helper，且已不再 direct include `legacy_command.h`。这还不是 typed control-state/default initialization replacement。 | `src/components/command/default_factory_spawn_command_projection.h`; `src/models/core/default_unit_factory.h`; `tests/architecture/platform_spawn/test_default_factory_spawn_command_projection.py`; `tests/architecture/compatibility_quarantine/test_guard_enforcement.py` | `quarantine / scoped pass` | 更广义 `default_unit_factory.h` 拆分必须与 `WP22-E` 协调；不得把 helper seam 当成 typed control-state replacement。 |
| `L-001c` | 第八轮 typed seed reduction 在 flight-model spawn 时加入 typed `MissionCommand` shell，并从 `MissionCommandCore` 投影剩余 command projection。它减少了重复 `ActionCommand` seeding，但没有退场 legacy control-state projection。 | `src/models/core/default_unit_factory.h`; `src/components/command/default_factory_spawn_command_projection.h`; `tests/architecture/platform_spawn/test_default_factory_spawn_command_projection.py`; `tests/runtime/mission/test_mission_command_split_semantics.py`; `tests/runtime/naval/test_naval_legacy_movement_debug.py` | `partial / blocker evidence` | 下一步 implementation 必须盘点并替换 spawn-time `MovementCommand` / `LaggedCommand` control path，而不是扩大 projection helper。 |
| `L-001d` | `R1-B` default-factory projection deletion 在 `R1-A` 之后仍然被阻塞。残余 blocker 现在是一个有限 cluster，而不是单一 helper seam：pending transport shell narrowing、debug/diagnostics mirror retirement 与 exact-stage contract demotion/alignment 必须先完成。 | `docs/task/simulation_architecture/archive/wp22_legacy_compatibility_retirement/wp22_remaining_task_clusters_20260523.md`; `src/components/command/default_factory_spawn_command_projection.h`; `src/interfaces/python/bindings_core.cpp`; `src/core/engine/exact_stage_inventory.cpp` | `blocked / residual cluster` | 在 finite R1 residual cluster 返回完整 packet 之前，不要再派发另一次 default-factory deletion attempt。 |
| `A-001` | Maintained typed setup 现在消费 `validate_maintained_typed_platform_spawn_request(...)`，并通过 `WorldBatchRuntime::spawn_typed_platform_unit(...)` materialize，不再重建 `WorldSpawnRequest`。显式 legacy compatibility typed setup 仍命名分离保留。 | `src/runtime/facade/runtime_facade.cpp`; `src/core/engine/world_batch_runtime.cpp`; `src/core/engine/world_batch_runtime.h`; `src/interfaces/python/bindings_runtime.cpp`; `tests/architecture/platform_spawn/test_boundary_guards.py`; `tests/runtime/facade/test_runtime_facade.py` | `scoped pass` | 保持 guard，防止 maintained typed setup 重新引入 `compatibility_type_name_materialization` 或 legacy request-shape rematerialization。 |
| `S-001` | aggregate DTO shell 仍 live，但现在明确是 compatibility transport shell。`MissionCommand`、`TaskOrder`、`LeaderIntent`、`PilotReport` 仍继承 cross-domain air/naval slice；owner-slice projection helper 与 world-batch assignment wrapper guard 已明确其 transport role。 | `src/components/command/mission_command.h`; `src/components/tasking/task_order.h`; `src/components/tasking/leader_intent.h`; `src/components/tasking/pilot_report.h`; `src/runtime/contracts/world_batch_contracts.h`; `tests/architecture/command_tasking/test_dto_domain_shell_guard.py` | `migrate / guarded quarantine` | 下一步 implementation 必须把 maintained consumer 迁向 domain owner slice 或 variant DTO；若同一 header 正在结构拆分，需与 `WP22-E` 协调。 |
| `S-002` | air recovery/takeoff 与 formation 字段在三个 DTO stage 中重复出现，flat-shell truth 仍横跨 command、tasking、leader layer。 | `src/components/command/air/mission_command_air.h:18-31`; `src/components/tasking/air/task_order_air.h:68-108`; `src/components/tasking/air/leader_intent_air.h:137-163` | `migrate` | 可与 `S-001` 并行；去重 field ownership 时不得静默改变 semantics。 |
| `S-003` | naval lifecycle data 在 aggregate DTO 间仍然非对称。`MissionCommandNaval` 携带 stationing/helo-launch 字段，而 tasking/intent/report 仍分别保留 warfare-role 与 OTC 字段。 | `src/components/command/naval/mission_command_naval.h:42-50`; `src/components/tasking/naval/task_order_naval.h:115-119`; `src/components/tasking/naval/leader_intent_naval.h:169-172`; `src/components/tasking/naval/pilot_report_naval.h:184-186` | `migrate` | 可立即启动，但凡改变 runtime mission-command mapping，都需在触碰 inline combat ordering 时与 `WP22-E` 协调。 |

## 可复现命令

以下命令用于本次 source pass，任何实现 worker 在宣称 retirement 进展前都应重跑。

```bash
git diff --check
rg -n "legacy_command\\.h|MovementCommand|ActionCommand|LaggedCommand" src tests
rg -n "WorldSpawnRequest|TypedPlatformSpawnRequest|spawn_unit\\(|typed_platform_spawn_requests|type_name_projection_preserved" src tests
rg -n "struct .*: .*Air, .*Naval|struct World(MissionCommand|TaskOrder|LeaderIntent|PilotReport)Assignment|recovery_base_id|takeoff_procedure_id|warfare_role_code|officer_in_tactical_command|reference_entity_id|launch_helo|recover_helo" src/components src/runtime tests
```

本次执行结果：

- `git diff --check`：没有 whitespace 或 conflict-marker 输出。
- legacy command `rg`：确认 direct system include、factory spawn seeding、
  command-API seeding，以及 live debug/binding exposure。
- legacy direct-include allowlist：已缩到
  `control_input_resolution.h`、`command_link.h`、
  `default_factory_spawn_command_projection.h`、`operation_system.h` 与兼容 umbrella
  `physics/action.h`，但它仍是 blocker register，而不是 closure proof。
- typed spawn 聚焦验证：maintained typed setup 使用 maintained validator 和
  batch-owned typed spawn helper；显式 legacy compatibility typed setup 保留命名 compatibility bridge。
- 第八轮本地复核：default-factory/WP9 guards、mission/naval focused tests 与 WP22
  聚焦 architecture sweep 通过；但由于 projection helper 仍投影
  `MovementCommand` / `LaggedCommand`，该结果仍只能记为 `partial`。
- aggregate DTO `rg`：确认 composite air/naval struct 与 world-batch aggregate
  assignment wrapper 仍然 live。

## 并行与依赖规则

| 工作分片 | 派发姿态 | 规则 |
|----------|----------|------|
| `L-001`、`L-001a`、`S-001`、`S-002`、`S-003` | `可立即启动但需协调` | 可先做 consumer inventory、bridge consolidation、DTO guard authoring 与 migration seam。此分片不得翻转 maintained public setup ownership。 |
| `L-001b` | `需与 WP22-E 协调` | 与 structural decomposition 共享 `default_unit_factory.h` 与 spawn-init ownership。同一时间只能有一个 worker 编辑 spawn/legacy-command initialization range。 |
| `A-001` | `scoped pass / guard follow-up` | Maintained typed setup 在该 facade path 已是一线；保持显式 compatibility setup 分离并加 guard。 |
| 触及 mission/tasking DTO 文件的 header decomposition | `需与 WP22-E 协调` | 若 `WP22-E` 正在拆 `world_batch_contracts.h` 或 DTO header，`WP22-D` 必须避免同时改动相同行区间的 ownership。 |
| runtime-facade public setup semantics | `等待 WP22-C` | 不得与 `WP22-C` 并行修改 `runtime_facade.cpp:261-504`。 |

## Fail / Pass Gate

在实现 claim 后，只要仍满足以下任一条件，就必须判失败：

- maintained system 仍在 single bridge 之外自行从 `MovementCommand` 或
  `ActionCommand` fallback 解析 command truth；
- 已缩窄的 direct-include allowlist 被当作 closure evidence，而不是带
  replacement、owner 与 failing guard 的 blocker register；
- aircraft/default spawn 仍以 legacy command state 作为 maintained control
  truth，且没有 replacement seam；
- maintained `TypedPlatformSpawnRequest` 再次要求
  `type_name_projection_preserved = true`，或通过 legacy request-shape bridge materialize；
- aggregate DTO shell 仍是 maintained logic 的 unguarded domain truth。

只有以下全部被 source-backed 证明时才可判通过：

- maintained command resolution 流经单一 typed 或 bridge-owned compatibility seam；
- 新的 maintained caller 无法在 explicit compatibility allowlist 之外 include
  或依赖 `legacy_command.h`；
- 剩余 allowlist entry 已被收敛成 owner-bound compatibility seam，而不是
  开放式 residual；
- typed setup 不再依赖 legacy `type_name` materialization 作为 maintained path；
- mission/tasking DTO ownership 已按 domain 划分或被 guard，flat-shell truth
  不再是 first-class。

## Noether Guard Register

| Gate | 当前事实 | 为什么仍阻塞 |
|------|----------|---------------|
| `G-101` | `control_input_resolution.h`、`command_link.h` 与 `operation_system.h` 仍显式持有 `legacy_command.h` seam | allowlist 已很窄，但它标记的是 live compatibility ownership，不是可接受收尾。 |
| `G-102` | `default_factory_spawn_command_projection.h` 持有命名 `SpawnCommandProjectionControlStateSeed` seam，`default_unit_factory.h` 只通过窄 helper 调用 | 这是显式 quarantine，不是 typed control-state replacement。 |
| `G-103` | Maintained typed setup 使用 `validate_maintained_typed_platform_spawn_request(...)` 与 `WorldBatchRuntime::spawn_typed_platform_unit(...)` | 保持正向 guard，防止 maintained legacy rematerialization 回归。 |
| `G-104` | Flight-model spawn 现在先 seed typed `MissionCommand` shell，再投影 compatibility state | 这是进展，但 `MovementCommand` / `LaggedCommand` 仍承载行为性 spawn control state，closure 前必须替换。 |

## Return Packet

- `status`：本次 source-verification 与 document-refresh 为 `pass`；
  implementation retirement 本身仍然 mixed 且 dependency-gated。
- `touched files`：
  `docs/task/simulation_architecture/archive/wp22_legacy_compatibility_retirement/wp22_command_dto_legacy_surface_retirement_cluster_20260522.md`，
  `docs/task/simulation_architecture/archive/wp22_legacy_compatibility_retirement/wp22_command_dto_legacy_surface_retirement_cluster_20260522.zh.md`
- `commands run`：
  `git diff --check`；
  `rg -n "legacy_command\\.h|MovementCommand|ActionCommand|LaggedCommand" src tests`；
  `rg -n "WorldSpawnRequest|TypedPlatformSpawnRequest|spawn_unit\\(|typed_platform_spawn_requests|type_name_projection_preserved" src tests`；
  `rg -n "struct .*: .*Air, .*Naval|struct World(MissionCommand|TaskOrder|LeaderIntent|PilotReport)Assignment|recovery_base_id|takeoff_procedure_id|warfare_role_code|officer_in_tactical_command|reference_entity_id|launch_helo|recover_helo" src/components src/runtime tests`
- `remaining blockers`：
  `L-001b` 在 typed control-state/default initialization replacement 前仍是
  `default_factory_spawn_command_projection.h` 中的 command projection seam；
  aggregate DTO shell 仍承载 cross-domain truth。
- `integration notes`：
  `WP22-D` 现在可以启动 legacy-command consumer migration、single-bridge
  consolidation 与 DTO guard authoring。
  Maintained typed setup 在 runtime-facade path 已 first-class；不得把它折回显式 legacy compatibility setup。
  任何 `default_unit_factory.h`、`default_factory_spawn_command_projection.h` 或共享
  DTO-header 工作，都必须与 `WP22-E` 串行协调。
- `WP22-D implementation dispatch allowed?`：`yes`，但只限
  `L-001`、`L-001a`、`S-001`、`S-002`、`S-003`。
  `A-001` 是 scoped pass；只剩 regression guard follow-up，而更广义 DTO
  与 default-factory 工作仍开放。

## 第一轮实现快照

| 字段 | 值 |
|------|----|
| `status` | `blocked` |
| `commands run` | `git diff --check` -> 通过；focused typed setup/facade tests 现在通过；legacy-command scans 仍显示更广义 consumer/DTO 工作。 |
| `remaining blockers` | 更广泛的 `ActionCommand` consumers 仍然存在；`default_factory_spawn_command_projection.h` 保留命名 command projection seam；aggregate DTO shell 仍承载 cross-domain truth。 |
| `integration notes` | 保持 single-bridge migration 打开，保留 A-001 正向 guard，不要把缩窄后的 allowlist 当作 closure evidence。 |

## Verification Notes

- 本文档只记录 source-backed retirement fact；本次没有进行 implementation 改动。
- 本次没有运行 `pytest`，因为任务范围是事实复核与 cluster 文档补强，而不是
  runtime behavior 改动。
- 本说明仍然开放：`WP22-F` 仍然 not eligible，且 `R1-B` deletion 在有限 residual
  cluster 完成前仍然被阻塞。
- 不得把这个 packet 翻译成 acceptance 语言。已核验结果是：上述 legacy surface
  仍然 live，仍需退场。
