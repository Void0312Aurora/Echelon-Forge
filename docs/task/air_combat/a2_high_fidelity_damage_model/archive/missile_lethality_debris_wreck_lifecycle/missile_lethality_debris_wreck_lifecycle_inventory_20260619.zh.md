# MLF-8 残骸和碎片生命周期盘点

状态：`2026-06-19` P1 inventory pass。这是只读源码盘点，不验收任何 runtime
行为修改。

英文规范页：
[missile_lethality_debris_wreck_lifecycle_inventory_20260619.md](missile_lethality_debris_wreck_lifecycle_inventory_20260619.md)。

## 摘要

MLF-8 不需要再做一套飞机毁伤模型。MLF-6 已经写出脱落部件结构事实，MLF-7
已经把这些事实投影到飞机和平台后果状态。剩下的缺口更窄：当前 runtime 还没有
负责人写入链路关联的 `LifecycleTransitionEvent` 行，用来表达终端残骸或脱落部件碎片；
同时 reward/runtime consumer 还没有准备好安全接收 diagnostics-only 的 MLF-8 生命周期行。

## 盘点表

| 表面 | 当前 owner | 当前能力 | 可否复用到 MLF-8 | runtime 前缺口 / 守卫 |
| --- | --- | --- | --- | --- |
| 结构断裂状态 | [structural_failure.h](../../../../../../src/components/combat/structural_failure.h) | `StructuralBreakupState` 保存断裂阶段、激活断裂模式、激活结构组、脱落部件数量、机体解体和最后断裂事件 id。 | 可以。它是脱落部件生命周期事实的状态输入。 | 只有数量和结构组 mask，没有逐碎片质量、速度或世界身份。 |
| 结构断裂事件写入器 | [structural_failure_system.h](../../../../../../src/systems/combat/structural_failure_system.h) | 发出带 `break_mode`、`detached_part_ref`、`detached_part_count`、`airframe_breakup`、cause linkage 和 chain header 的 `StructuralBreakupEvent`。 | 可以。它是 MLF-8 碎片事实的父事件来源。 | MLF-8 不得把标签解释成校准碎片物理。 |
| 结构后果桥 | [structural_consequence_system.h](../../../../../../src/systems/combat/structural_consequence_system.h) | 通过维护中的 aircraft/platform damage state 处理 wing/tail/engine/fuselage/multi-axis 后果，并写 diagnostics-only `PlatformConsequenceEvent`。 | 可以。它证明飞机本体后果已经属于 MLF-7。 | MLF-8 不应复制后果逻辑。 |
| 生命周期事件契约 | [engagement_contracts.h](../../../../../../src/runtime/contracts/engagement_contracts.h) | 已定义 canonical `lifecycle` stage 和 `LifecycleTransitionEvent`，包含 from/to state、ground lifecycle、wreck entity、debris count、terminal flag 和 terminal projection id。 | 可以。这是最可能的基础事件形状。 | 目前只是 DTO，没有 recorder/write path 拥有它。 |
| 事件包存储 | [engagement_event_types.h](../../../../../../src/core/engine/engagement_event_types.h) | `RecentEngagementEvents` 已包含 `lifecycle_transition_events`。 | 可以。现有 packet 能承载 MLF-8 行。 | event store 还没有 lifecycle record API、cap 或排序路径。 |
| 事件记录接口 | [engagement_event_recorder.h](../../../../../../src/core/interfaces/engagement_event_recorder.h) | recorder 已负责 damage、component、structural 和 platform-consequence 事件写入。 | 部分可复用。已有模式可照着做。 | 没有 `EngagementLifecycleTransitionEventRecord` 和 `record_lifecycle_transition_event`。 |
| 事件存储实现 | [simulation_kernel_engagement_event_store.cpp](../../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp) | 已为 structural 和 platform consequence events 补 header、chain linkage。 | 部分可复用。可以沿用现有 helper 风格。 | 没有 lifecycle writer；sorted export 目前也不排序 lifecycle 行，因为还没有写入者。 |
| 地面撞击生命周期 | [logistics.h](../../../../../../src/components/systems/logistics.h)、[ground_contact_system.h](../../../../../../src/systems/physics/ground_contact_system.h) | `GroundImpactLifecycle` 区分 `None`、`LandedAirframe`、`CrashedWreck` 和 `DebrisFragmentResidue`；ground contact 记录撞击速度、下沉率和严重度。 | 可用于终端残骸事实。 | 它描述的是原实体地面状态，不是脱落碎片实体。 |
| Active-state API | [simulation_kernel_observation_api.cpp](../../../../../../src/core/engine/simulation_kernel_observation_api.cpp) | `is_unit_active()` 按 Flecs liveness 使用 `is_alive()`。 | 可以。它是终端退役后的活跃状态真相来源。 | MLF-8 不得让已死亡原实体因为残骸事实而看起来仍 active。 |
| 地面 debug API | [simulation_kernel_observation_api.cpp](../../../../../../src/core/engine/simulation_kernel_observation_api.cpp)、[bindings_core.cpp](../../../../../../src/interfaces/python/bindings_core.cpp) | `debug_get_ground_contact_state()` 向 Python 导出 lifecycle 和撞击字段。 | 可用于测试和诊断。 | 它是 debug state，不是事件链记录。 |
| Runtime facade | [runtime_facade_types.h](../../../../../../src/runtime/facade/runtime_facade_types.h)、[runtime_facade_packet.cpp](../../../../../../src/runtime/facade/runtime_facade_packet.cpp) | facade packet 已包含 lifecycle transition events，并为 header 和 `wreck_entity` 分配 world index。 | 可以。现有 facade path 可暴露 MLF-8 事实。 | 当前没有 producer 填这些行。 |
| Python 绑定 | [bindings_runtime.cpp](../../../../../../src/interfaces/python/bindings_runtime.cpp)、[bindings_core.cpp](../../../../../../src/interfaces/python/bindings_core.cpp) | `LifecycleTransitionEvent` 和 `lifecycle_transition_events` 已对 Python 公开。 | 可以。P4 可更多关注测试和诊断，而不是新绑定形状。 | 若 P2 将 `terminal` 和 `terminal_projection_id` 设为规范字段，需要扩展 shape tests。 |
| 结构诊断 | [structural_breakup_export.py](../../../../../../tools/diagnostics/structural_breakup_export.py) | 导出 structural breakup rows，并显式标记 wreck/debris lifecycle 为 false。 | 可作为上游结构来源。 | lifecycle 行成为 runtime facts 后，需要单独的 MLF-8 lifecycle export/probe。 |
| Reward 标准事实 | [air_combat.py](../../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py) | 会跳过 diagnostics-only `PlatformConsequenceEvent`，但会消费全部 `LifecycleTransitionEvent` 作为标准 damage facts 和 terminal-state facts。 | 在加守卫前不可直接复用。 | P2/P3 必须增加 diagnostics-only guard，或规定一种非 reward 的事件形状，才能发出 MLF-8 诊断。 |
| 地面 reward shaping | [air_combat.py](../../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py)、[test_air_combat_reward_surface.py](../../../../../../tests/runtime/air_combat/test_air_combat_reward_surface.py) | 直接 ground state 已可驱动 `ground_crashed_wreck` terminal state 和 reward shaping。 | 可作为现有行为证据。 | MLF-8 lifecycle facts 不得重复计分或静默新增 reward 权威。 |
| 既有 no-lifecycle 测试 | [test_continuous_rod_surface.py](../../../../../../tests/runtime/air_combat/test_continuous_rod_surface.py)、[test_warhead_component_event_surface.py](../../../../../../tests/runtime/air_combat/test_warhead_component_event_surface.py) | 早期 MLF 测试断言 lifecycle events 仍为空。 | 可作为非回归检查。 | P3 只有在 MLF-8 契约证据明确时，才能更新或保留这些期望。 |
| 外部 debris 证据 | [test_benchmark_evidence_admission.py](../../../../../../tests/architecture/damage_model/test_benchmark_evidence_admission.py) | TP-21 selected debris outputs 仍是 fail-closed / hash-gated。 | 只能作为边界证据。 | 没有后续证据门之前，不得把校准 debris output 放入 MLF-8。 |

## P1 已接受结论

1. MLF-8 首版应是很薄的生命周期事件层，不是新的毁伤或气动模型。
2. `LifecycleTransitionEvent` 是最合适的初始载体，但缺 runtime writer 和链路策略。
3. 脱落部件事实应消费 `StructuralBreakupEvent.detached_part_ref` 和
   `detached_part_count`；基础切片不创建一等 ECS 实体。
4. 终端残骸事实应消费原实体 ground lifecycle 和 active-state 语义；不得替代原实体
   liveness 规则。
5. reward 路径是 runtime 前最主要的守卫：当前 lifecycle events 还不会按
   `diagnostics_only` 被过滤。

## P2 契约输入

P2 必须决定：

- 基础 MLF-8 是否只使用 `LifecycleTransitionEvent`；
- 脱落部件写一条聚合记录，还是按 detached part 写多条记录；
- 如何设置 `consumer_visibility`，让 diagnostics-only 行不进入 reward；
- lifecycle rows 如何链回 `StructuralBreakupEvent` 和/或 `PlatformConsequenceEvent`；
- 没有结构断裂的终端地面撞击是否属于 MLF-8；
- 哪些测试证明无 reward leakage 和无误报。

## Runtime 阻塞项

- 增加或明确拒绝 lifecycle event recorder API。
- 若验收 writer，则补 event-store cap/sort/header completion。
- diagnostics-only lifecycle facts 发出前，必须先补 reward non-leakage 行为。
- 增加 no-breakup、detached-part、terminal wreck、diagnostics-only filtering 和
  active-state 语义聚焦测试。
