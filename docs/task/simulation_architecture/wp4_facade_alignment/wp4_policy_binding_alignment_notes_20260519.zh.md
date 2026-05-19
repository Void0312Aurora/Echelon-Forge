# WP4-D/E Policy、AgentRole 与 Python Mirror 对齐探查说明

状态：`2026-05-19` 探查说明。仅文档变更，不新增 C++ 或 Python runtime
surface。

语言：

- 英文主文：[wp4_policy_binding_alignment_notes_20260519.md](wp4_policy_binding_alignment_notes_20260519.md)
- 中文辅文：`wp4_policy_binding_alignment_notes_20260519.zh.md`

已阅读输入：

- [WP4-D/E policy binding cluster](wp4_policy_binding_cluster_20260519.zh.md)
- [WP4 facade alignment](facade_alignment_wp4_20260519.zh.md)
- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.zh.md)
- `python/rl/runtime/*`
- `python/rl/control/*`
- `gym_envs/*`
- `src/interfaces/python/bindings_runtime.cpp`

## 1. 分类词汇

| 状态 | WP4-D/E 含义 |
|------|--------------|
| `maintained` | 已通过 facade-shaped request/result surface，可在补齐 provenance 字段后作为维护路径。 |
| `compatibility_adapter` | 迁移期可用，但缺少 `AgentRole`、`source_id`、`effective_time`、`valid_until`、`merge_policy` 或 snapshot provenance 等字段。 |
| `diagnostics_only` | truth-derived、raw-runtime、oracle 或 privileged helper 路径，不得成为维护中的 policy input。 |

重要命名提醒：很多 Python adapter 把 `AgentObservation` 值命名为 `truth`。
如果它来自 `ObservationBatchPacket.agent_observations`，它不是自动等于 raw
`World Truth`，而是 facade 导出的 observation，只是命名有风险。如果它来自
直接 `sim.*` 或 raw runtime escape hatch，则属于 compatibility 或
diagnostics 边界。

## 2. AgentRole 五元素映射草案

架构中的五元素是 `role`、`authority_scope`、`information_state_source`、
`decision_model_ref`、`action_interface`。`wp4_policy_binding_cluster_20260519`
还建议补充稳定的 `role_id`、`role_type` 与 `maintained_status`。

| 当前 adapter role | role | authority_scope | information_state_source | decision_model_ref | action_interface | 状态 |
|-------------------|------|-----------------|--------------------------|--------------------|------------------|------|
| Single-agent Gym pilot | `ScenarioLoader.load_scenario()` 返回的 `agent_id`；隐式 `autopilot_controller` 或 `pilot` | 一个 `is_agent` entity | `get_agent_observation` 加 `get_instrument_state`；batch 路径优先是 `ObservationBatchPacket` | 外部 RL policy、scripted controller 或 Gym caller action | `PilotAction`，通过 `set_pilot_action` 或 `WorldPilotActionAssignment` | `compatibility_adapter` |
| Batch execution pilot | `WorldBatchVecEnv` handle 的 `world_index`、`entity_id` 与 loader state | 每个 world handle 一个 entity | 可用时通过 `ObservationBatchRequest` 读取 `RuntimeFacadeAdapter.read_truth_and_instruments()` | 外部 RL policy 或 `MultiTimescaleActionWrapper` | `WorldPilotActionAssignment` 经 `RuntimeFacadeAdapter.set_pilot_actions_batch()` | `compatibility_adapter`，补齐 intent metadata 后接近 maintained |
| Multi-agent roster slot | `MultiAgentControlSlot`：`world_index`、`entity_id`、`entity_name`、`roster_index`、`role_code`、`formation_role_id`、`policy_route` | Roster member entity 与可选 team/element metadata | 可用时通过 `MultiAgentWorldRuntimeView.export_packet()` 使用 `ObservationBatchRequest` | 每 slot 的 policy route 或 caller-provided multi-agent policy | 每 entity 一个 `WorldPilotActionAssignment` | `compatibility_adapter` |
| Leader 或 C2 role | leader phase bucket 加 task/order/intent state；隐式 `flight_lead` 或 `coordinator` | 受控 entity 或 roster 的 mission command、task order、leader intent、pilot report | cached execution observation、instrument state、task/order state，以及有时命名为 `truth` 的 ownship observation | `FrozenExecutionPolicyAdapter`、scripted C2 manager 或 teacher baseline | `WorldMissionCommandAssignment`、`WorldTaskOrderAssignment`、`WorldLeaderIntentAssignment`、`WorldPilotReportAssignment` | `compatibility_adapter` |
| Scripted cooperative director | world-level `ScriptedCooperativeCoordinationDirector` | formation offsets、leader/wingman role metadata、roster tasking fields | loader mission command、cooperative state 与 roster metadata | scripted coordination policy | vec env 刷新的 command-chain assignment objects | `compatibility_adapter` |
| Oracle 或 privileged helper | 尚无维护中的 role id | 未显式限制时是无界 authority | raw `sim`、raw runtime、cached `truth`、scenario internals、privileged diagnostics | test oracle、teacher、debug utility | 任意 direct mutation 或 hidden helper | 除非被显式包装和限权，否则为 `diagnostics_only` |

后续实现建议的最小 `AgentRole` schema：

```yaml
role:
  role_id: stable string or numeric id
  role_type: autopilot_controller | flight_lead | wingman | coordinator | human_operator | diagnostic_oracle
authority_scope:
  world_index: optional integer
  entity_ids: [entity ids]
  roster_scope: optional roster or team id
  allowed_families: [direct_control, mission_command, tasking, coordination, report]
information_state_source:
  kind: ObservationPacket | DecisionBelief | shared_tactical_picture | diagnostics_only_oracle
  consumed_snapshot_version: optional version
  view_spec_schema: optional ObservationViewSpec version
decision_model_ref:
  kind: learned_policy | scripted_controller | scripted_director | teacher_baseline | human | diagnostics_helper
  id: checkpoint path, controller class, manager name, or human source id
action_interface:
  kind: ActionIntentPacket | CoordinationIntentPacket | PilotActionAssignmentCompat | CommandChainAssignmentCompat
  merge_policy: last_write_wins | priority_override | reject_on_conflict | merge_by_field | append_only
maintained_status: maintained | compatibility_adapter | diagnostics_only
```

## 3. Action Intent 路径

| 路径 | 当前行为 | 缺少的 WP4 字段 | 状态 |
|------|----------|-----------------|------|
| `gym_envs/universal_env_parts/actions.py::build_pilot_action` | 把 Gym action array 转成 `ef_py.PilotAction`。 | `source_layer`、`source_id`、`input_snapshot_version`、`effective_time`、`valid_until`、`merge_policy`、`AgentRole`。 | `compatibility_adapter` |
| `gym_envs/universal_env.py::step` | 单 world 直接 `sim.set_pilot_action(...)`，再 `sim.step()`。 | facade-compatible request 边界和全部 intent metadata。 | `compatibility_adapter`，不应作为 WP4 maintained frontend path。 |
| `python/rl/runtime/world_batch_vec_env.py::step_wait` | 构造 `WorldPilotActionAssignment`，调用 `RuntimeFacadeAdapter.set_pilot_actions_batch(...)`。 | first-class `ActionIntentPacket` 与 `ActionHoldPolicy`。 | `compatibility_adapter`，是当前更接近维护面的迁移路径。 |
| `python/rl/runtime/single_world_batch_runtime.py::step` | 单环境 wrapper，复用 batch assignment 路径。 | 同 batch path。 | `compatibility_adapter` |
| `python/rl/runtime/leader_world_batch_runtime.py::step_indices` | leader execution handle 批量构造 `WorldPilotActionAssignment`。 | 同 batch path。 | `compatibility_adapter` |
| `python/rl/runtime/multi_agent_runtime.py::apply_actions` | per-roster-slot action dict 转成 `WorldPilotActionAssignment`。 | per-slot `AgentRole` 与 action timing/conflict metadata。 | `compatibility_adapter` |

实现含义：本轮不要新增 public C++ binding。等 WP4-A 稳定名称后，先新增
Python adapter object，用 metadata 包装现有 `PilotAction` assignment，使其成为
`ActionIntentPacket` 等价路径，再考虑 binding 扩展。

## 4. Coordination Intent 路径

| 路径 | 当前行为 | 缺少的 WP4 字段 | 状态 |
|------|----------|-----------------|------|
| `gym_envs/leader_env_parts/bridges.py::LeaderCommandBridge` | 持有 `TaskOrder`、`LeaderIntent`、`PilotReport`，并可直接 sync 到 `loader.sim`。 | source identity、roster scope、update clock、merge policy、consumed observation version。 | `compatibility_adapter` |
| `gym_envs/leader_env_parts/decision_runtime/commands.py::apply_leader_command` | 把 leader action 解码成 mission command、task、leader intent 与 report state。 | `CoordinationIntentPacket` 边界、conflict policy 与 `AgentRole`。 | `compatibility_adapter` |
| `python/rl/runtime/world_batch_vec_env.py::_sync_command_chain_batch` | 通过 `RuntimeFacadeAdapter` 刷新 mission/task/leader/report assignments。 | intent packet metadata 与 deterministic merge contract。 | `compatibility_adapter`，是当前 batch bridge。 |
| `python/rl/runtime/cooperative_world_batch_vec_env.py::_sync_command_chain_batch` | cooperative worlds 和 roster slots 的同类 command-chain flush。 | per-role authority scope 与 merge policy。 | `compatibility_adapter` |
| `python/rl/runtime/world_batch/cooperative_director.py::ScriptedCooperativeCoordinationDirector` | scripted world-level director 在 batch sync 前修改 command-chain state。 | 显式 source layer/id、update clock 与 produced tasking fields。 | `compatibility_adapter` |

实现含义：当前 coordination 行为可以作为 `CoordinationIntentPacket` 的证据来源，
但还不是 packet 本身。应在 WP4-A 命名 maintained coordination surface 后再包装。

## 5. Observation 与 Belief 输入路径

| 路径 | 当前行为 | 状态 |
|------|----------|------|
| `RuntimeFacadeAdapter.export_observation_packet(...)` | 可用时走 `RuntimeFacade.export_observation_packet(...)`，否则用 batch getters 构造 `_ObservationPacketCompat`。 | facade 存在时为 `maintained`；fallback 是 `compatibility_adapter`。 |
| `RuntimeFacadeAdapter.read_truth_and_instruments(...)` | 构造 `ObservationBatchRequest`，返回 `packet.agent_observations` 与 `packet.instrument_states`。Legacy 命名把 observations 称为 `truth`。 | `maintained` surface，但有命名/provenance 缺口。 |
| `WorldBatchVecEnv._collect_observations(...)` | 读取 observation/instrument packet，缓存后构造 policy observation。 | 在记录 `ObservationViewSpec` 与 snapshot provenance 前为 `compatibility_adapter`。 |
| `gym_envs/universal_env_parts/observations.py::build_universal_observation` | 从 instrument state、agent observation、contacts、RWR、mission vector、可选 proprio 构造 policy observation dict。 | `compatibility_adapter`；显式 view spec 和 allowed fields 后可提升。 |
| `python/rl/runtime/world_batch/observation_batching.py::compute_execution_observation_batch` | 从缓存 instrument 与 agent observation 构造 compiled/batched observation。 | `compatibility_adapter`；需要 source packet/version metadata。 |
| `MultiAgentWorldRuntimeView.export_packet(...)` | 可用时使用 `ObservationBatchRequest`，否则退回 raw batch getters。 | 使用 facade request 时是 `maintained` surface；fallback 是 `compatibility_adapter`。 |
| `python/rl/control/*` scripted controllers | 只消费 `instruments`、`mission` 等 observation dict key；部分内部状态是隐式 belief。 | 输入 observation 维护时可视为 maintained；缺少 `DecisionBelief` metadata。 |
| `FrozenExecutionPolicyAdapter` | 冻结 SB3 policy 的 inference wrapper。 | decision model reference 已存在；`DecisionBelief` contract 缺失。 |

当前没有 first-class `DecisionBelief` DTO 或 Python helper。belief-like state 存在于
model latent state、scripted-controller memory、teacher baseline、cached leader
window state 中。只有当它们派生自声明 observation 时才应标为 maintained；truth-derived
teacher 或 debug baseline 应标为 `diagnostics_only`。

## 6. World Truth 与 Oracle 风险表

| 路径 | 风险 | 必要标签 |
|------|------|----------|
| `RuntimeFacadeAdapter.world(...)`、`make_scenario_loader(...)` 与 `_compat_runtime = facade.runtime()` | 集中的 raw runtime escape hatch。迁移期可接受，但不得重新作为 maintained policy API 暴露。 | `compatibility_adapter` |
| `bindings_runtime.cpp` 暴露 `WorldBatchRuntime` 与 `RuntimeFacade.runtime()` | Python 仍可触达 raw batch runtime 与 world handles。 | `compatibility_adapter`；若作为 policy truth 使用则为 `diagnostics_only`。 |
| `gym_envs/universal_env.py` 直接 `sim.set_pilot_action`、`sim.step`、`sim.get_agent_observation`、visual observation calls | Legacy single-world env 绕过 facade-shaped request/result 流。 | `compatibility_adapter` |
| `build_universal_observation(...)` 使用名为 `truth` 的值和 `truth.x/y` 构造 ILS/mission observation | 可能是 facade-exported ownship observation，但 provenance 与 view-spec 权限不明确。 | `compatibility_adapter`；若 raw truth 或 hidden scenario metadata 被 policy 消费，则为 `diagnostics_only`。 |
| `gym_envs/scenario_loader/step_evaluation.py` 与 reward/runtime helpers 使用 `truth_*` 值 | 用于 simulation facts 和 reward reports 可以成立，但必须区分 fact/shaping ownership；作为 policy observation oracle 则不安全。 | reward/fact computation 为 `compatibility_adapter`；输入 maintained policy belief 时为 `diagnostics_only`。 |
| Leader/C2 helpers 使用 `truth_now` 计算 station metrics 或 report location | 可能是合法 ownship/report state，但当前缺少 source snapshot 与 role metadata。 | `compatibility_adapter` |
| 通过 raw world 或 runtime compatibility helper 调 visual observation | visual view 可以是合法 observation data，但当前绕过 `ObservationViewSpec` 命名。 | `compatibility_adapter`；privileged debug view 为 `diagnostics_only`。 |
| Scripted teachers、teacher baselines 与 oracle diagnostics | 可能使用受控 agent 不可见的信息。 | 除非证明输入来自 maintained observation，否则为 `diagnostics_only`。 |

## 7. Python Binding Mirror 状态

当前 bindings 已镜像稳定的 WP4 facade shells：

| C++ surface | Python mirror 状态 |
|-------------|--------------------|
| `RuntimeCapabilities`、`RuntimeBatchConfig`、`BatchResetRequest` | 已在 `bindings_runtime.cpp` 绑定。 |
| `BatchWorldSetupRequest` / `BatchWorldSetupResult` | 当前字段已绑定。 |
| `ObservationBatchRequest` / `ObservationBatchPacket` | include flags 与 packet vectors 已绑定。 |
| `EngagementBatchRequest` / `EngagementEventPacket` | track、launch、lifecycle、effects、damage、diagnostics vectors 已绑定。 |
| `ExecutionBatchStepRequest` / `ExecutionBatchStepResult` | step requests、rewards、termination/truncation、info、observation packet 已绑定。 |
| `RuntimeFacade` maintained methods | setup、reset、observation export、engagement export、execution step、batch helpers 已绑定。 |

bindings 同时仍暴露 compatibility surfaces：

| Surface | 状态 |
|---------|------|
| `WorldBatchRuntime` | compatibility-only。 |
| `WorldBatchRuntime.world(...)` | compatibility/diagnostics escape hatch。 |
| `RuntimeFacade.runtime()` | compatibility/diagnostics escape hatch。 |
| raw candidate-id 与 visual helpers | 在 `ObservationViewSpec` 拥有语义前属于 compatibility。 |

以下内容应等 WP4-A 稳定名称和字段后再绑定：

- `ObservationViewSpec`，
- `DecisionBelief`，
- `AgentRole`，
- `ActionIntentPacket`，
- `ActionHoldPolicy`，
- `CoordinationIntentPacket`，
- request metadata fields：`source_layer`、`source_id`、
  `input_snapshot_version`、`effective_time`、`valid_until`、`merge_policy`。

## 8. 后续实现建议

1. `WP4-D1 AgentRole adapter sketch`：新增 Python 侧文档或 dataclass 草案，
   把 `ScenarioLoader` agent id 与 roster slot 映射到 `AgentRole`；不要在
   WP4-A surface 名称稳定前公开绑定。
2. `WP4-D2 ActionIntent shim`：建立窄 Python compatibility shim，用 source id、
   effective time、validity、merge policy 和 role metadata 包装 `PilotAction` /
   `WorldPilotActionAssignment`。
3. `WP4-D3 CoordinationIntent shim`：把 leader command-chain assignments 包装为
   packet-equivalent object，补 source、roster scope、update clock 与 merge policy。
4. `WP4-D4 Observation provenance pass`：重命名或标注 Python 中把
   `AgentObservation` 称为 `truth` 的变量；等 facade 暴露 snapshot metadata 后记录
   source packet/version。
5. `WP4-D5 Oracle audit tests`：增加 architecture tests，禁止 maintained policy
   path 在注册 compatibility adapter 外调用 raw `RuntimeFacade.runtime()`、
   `WorldBatchRuntime.world(...)` 或直接 `sim.get_agent_observation(...)`。
6. `WP4-E1 Binding mirror after WP4-A`：只绑定稳定 DTO 名称并加 field-presence
   tests；`WorldBatchRuntime` 与 `RuntimeFacade.runtime()` 继续文档化为
   compatibility-only。
7. `WP7.5 训练路径 facade 桥接`：在维护中的 facade request / observation surface
   稳定后，把 `WorldBatchVecEnv` 主线 batch stepping 与维护中的 observation read
   从 `_compat_runtime` 迁到 `RuntimeFacade.step_execution_batch()` 加
   `RuntimeFacade.export_observation_packet()`；该桥接工作应放在已验收 `WP4`
   之外单独推进。

## 9. 开放问题

1. `AgentObservation` 中 ownship `x/y/z` 这类字段是否默认属于 maintained policy
   observation，还是只有 `ObservationViewSpec` 显式允许 ownship truth-state
   projection 时才允许？
2. WP2.5 shard/version 语义实现后，Python `ObservationBatchPacket` 的
   `SnapshotVersion` 由哪个对象拥有？
3. Visual observation 应作为 `ObservationViewSpec` 字段族，还是单独 observation
   export surface？
4. Leader teacher baseline 应建模为 `diagnostics_only` 的 `DecisionBelief`，
   还是建模为限权的 orchestration-layer supervisor？
5. `RuntimeFacadeAdapter.world(...)` 是否继续可调用，还是 WP4 后移入显式命名的
   diagnostics 方法？
