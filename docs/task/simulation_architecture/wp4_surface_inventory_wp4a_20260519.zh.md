# WP4-A Surface Inventory 初稿

状态：`2026-05-19` 首轮 inventory 草案。

语言版本：

- 英文主文：[wp4_surface_inventory_wp4a_20260519.md](wp4_surface_inventory_wp4a_20260519.md)
- 中文辅文：`wp4_surface_inventory_wp4a_20260519.zh.md`

输入：

- [WP4-A facade surface inventory 分发单](wp4_surface_inventory_cluster_20260519.zh.md)
- [WP4 facade 对齐](facade_alignment_wp4_20260519.zh.md)
- [WP4 facade alignment plan review](../review/wp4_facade_alignment_plan_review_20260519.md)
- [Temp-02 SCAL architecture vision review](../review/temp-02_review_20260519.md)
- `src/runtime/facade/*` 中的当前 facade header，以及
  `src/interfaces/python/bindings_runtime.cpp` 中的 Python bindings

本草案仅限文档。不实现 facade method，不拆分 `RuntimeFacade`，也不添加 runtime scheduler/replay 行为。

## 1. 目的

WP4-A 在后续 WP4 worker 修改 facade、policy、binding、diagnostics 或 validation 代码前，先建立 surface 词汇。

本 inventory 有三个目标：

1. 将每个 surface 分类为 `maintained`、`compatibility_adapter`、
   `diagnostics_only` 或 `deferred`；
2. 为每个 surface 写出 WP4-A 分发单要求的 metadata；
3. 保留 Temp-02 的 information / agency / evidence 边界：
   `World Truth`、`ObservationPacket`、`DecisionBelief`、`AgentRole` 与
   `DiagnosticsTrace` 不能互相替代。

## 2. 分类规则

| 分类 | 含义 | 维护中 truth 状态 |
|------|------|-------------------|
| `maintained` | 后续实现可依赖的规范 surface 或 contract concept。 | 可按 owner 定义 facade、policy、replay 或 validation truth。 |
| `compatibility_adapter` | 现有或迁移期路径，可以保留，但不是推荐维护路径。 | 重新分类前不能成为 mainline path。 |
| `diagnostics_only` | Evidence、debug、oracle 或 inspection surface。 | 不能定义 scheduler truth、policy/training truth 或 world truth。 |
| `deferred` | 已命名但 WP4-A 暂不实现或提升的 surface candidate。 | 后续 WP4/WP5/backend 任务提升前没有维护行为。 |

Consumer group 使用 WP4-A 词汇：`frontend`、`policy`、`orchestration`、
`test`、`diagnostics`、`binding` 或 `backend`。

Information-state layer 使用 WP4-A 词汇：`WorldTruth`、`SensedState`、
`TrackState`、`SharedTacticalPicture`、`AgentObservation`、`DecisionBelief`
或 `not_applicable`。

## 3. Surface Inventory

| Surface | classification | consumer_group | request/result DTO | source_layer | snapshot_semantics | scheduler_dependency | information_state_layer | compatibility_rule | deprecation_rule | validation_gate |
|---------|----------------|----------------|--------------------|--------------|--------------------|----------------------|-------------------------|--------------------|------------------|-----------------|
| `BatchWorldSetupRequest` / `BatchWorldSetupResult`；`BatchResetRequest` | `maintained` | frontend、test、orchestration、binding | request: `BatchWorldSetupRequest` 或 `BatchResetRequest`；result: `BatchWorldSetupResult` 或 reset side effect | facade 加 simulation setup | setup/reset commit 创建或重置 `setup` shard，并建立初始 `SnapshotVersion` ancestry | `state_shard_version`、`barrier_visibility`、`replay_metadata` | `WorldTruth` | 通过 raw runtime 做 legacy setup 只允许作为 compatibility diagnostics | 当 facade setup 覆盖当前 tests 与 bindings 后，移除 raw setup 依赖 | facade setup/reset tests 加 architecture raw-runtime layering gate |
| `ObservationViewSpec` | `maintained` | policy、test、binding | request: 当前 C++ facade 中无；result/concept: `ObservationViewSpec` | policy/test 拥有 schema；facade 拥有 export binding | 命名 schema version、required fields、optional fields、include flags、source snapshot requirement、encoding/normalization owner | `state_shard_version`、`barrier_visibility`、`replay_metadata` | `AgentObservation` | Python 直接组装 observation 在能命名等价 view spec 和 source snapshot 前为 compatibility | 当 `ObservationBatchRequest` 或 adapter metadata 携带 view-spec parity 后，废弃直接组装 | WP5 information/belief leakage gate 与 observation schema compatibility gate |
| `ObservationPacket` / `ObservationBatchRequest` / `ObservationBatchPacket` | `maintained` | frontend、policy、test、binding | request: `ObservationBatchRequest`；result: `ObservationBatchPacket` | facade 对 simulation state 的 export | runtime metadata 可用后，必须命名 committed source `SnapshotVersion`、source time、export barrier 与 observation packet version | `state_shard_version`、`barrier_visibility`、`replay_metadata` | `AgentObservation` | `get_agent_observations_batch` 等 direct getter 在绕过 packet provenance 时是 compatibility helper | 当 packet export 携带所需 provenance 且测试改用 packet path 后，收窄 direct getter | facade observation tests 加 WP5 information/belief leakage gate |
| `DecisionBelief` | `maintained` | policy、orchestration、test | request: consumed `ObservationPacket` 或 memory/estimator input；result/concept: `DecisionBelief` | policy/agent side | 必须声明 consumed observation packet id、observation snapshot version、memory/estimator state、model reference 与 uncertainty/confidence shape | `replay_metadata`、`state_shard_version`、`barrier_visibility` | `DecisionBelief` | truth-derived oracle belief 是 `diagnostics_only`，且必须携带 oracle label | belief metadata 可用后，维护中的 adapter 废弃 oracle fallback | WP5 information/belief leakage gate，用于区分 declared belief 与 `WorldTruth` |
| `EngagementBatchRequest` / `EngagementEventPacket` | `maintained` | frontend、test、diagnostics、binding | request: `EngagementBatchRequest`；result: `EngagementEventPacket` | facade 对 engagement evidence 的 export | track、launch、lifecycle、effects、damage 与 diagnostics payload 必须保留 world-safe refs 与 event/report ancestry | `event_order`、`state_shard_version`、`barrier_visibility`、`replay_metadata` | `TrackState` | 未使用 packet slot 只有在记录为 compatibility gap 时才可保留为 placeholder | 当 WP4-B/WP5 trace gate 文档化 producer coverage 后，移除 placeholder ambiguity | engagement facade tests 与 trace conformance tests |
| `ExecutionBatchStepRequest` / `ExecutionBatchStepResult` | `maintained` | frontend、policy、orchestration、test、binding | request: `ExecutionBatchStepRequest`；result: `ExecutionBatchStepResult` | facade execution step over compiled runtime products | step result 应携带 observation snapshot、reward fact/shaping ancestry、termination source 与 mirrored status provenance | `barrier_visibility`、`clock_domain`、`state_shard_version`、`replay_metadata` | `AgentObservation` | Python step assembly fallback 在 facade result 携带所有 ownership metadata 前是 compatibility | reward、termination、observation 与 lifecycle provenance 可通过 facade 看到后，废弃 fallback | facade step tests 加 WP4-C lifecycle alignment gates |
| `ActionIntentPacket` / `ActionHoldPolicy` | `deferred` | policy、orchestration、test | request: future `ActionIntentPacket`；result: accepted/rejected intent 或 translated command/control packet | policy/orchestration 经由 facade-compatible adapter | 需要 `source_id`、`input_snapshot_version`、`effective_time`、`valid_until`、`merge_policy` 与 hold/expiry metadata | `clock_domain`、`barrier_visibility`、`replay_metadata`、`event_order` | `DecisionBelief` | 当前 direct action assignment path 是 compatibility adapter，不能视为 maintained policy truth | WP4-D 定义 adapter path，且 WP5 能测试 cadence/replay metadata 后再提升 | WP4-D action bridge 加 WP5 boundary/replay gates |
| `CoordinationIntentPacket` | `deferred` | policy、orchestration、frontend、test | request: future `CoordinationIntentPacket`；result: accepted/rejected tasking 或 coordination report | policy/orchestration/human producer 经由 facade-compatible adapter | 需要 source type/id、roster、target refs、update clock、`effective_time`、`merge_policy`、produced tasking fields | `event_order`、`barrier_visibility`、`clock_domain`、`replay_metadata` | `SharedTacticalPicture` | 当前 cooperative director write 在穿过声明过的 facade-compatible injection path 前为 compatibility | WP4-D 定义 coordination adapter 且 raw tasking write 不再是 mainline 后提升 | WP4-D coordination bridge 与 architecture raw-mutation gate |
| `AgentRole` | `deferred` | policy、orchestration、test、binding | request: WP4-A 中无；result/concept: `AgentRole` | policy/agent boundary | 维护使用前必须命名 role id/type、authority scope、information-state source、decision model reference 与 action interface | `replay_metadata`，发出 action 时还依赖 `clock_domain` | `DecisionBelief` | ad hoc policy identity 在映射到 `AgentRole` 前是 compatibility | WP4-D contract sketch 把当前 adapter 连接到 role metadata 后提升 | WP4-D AgentRole gate 与 WP5 information/agency gate |
| `RewardSpec` / `RewardReport` | `maintained` | policy、test、orchestration、binding | request: reward spec 可来自外部/config；result: `ExecutionBatchStepResult` 中 reward 字段与 future `RewardReport` | split simulation facts and policy/test shaping | fact term 必须命名 source `SnapshotVersion`；shaping term 必须命名 owner/source，以及适用时的 consumed observation/belief | `state_shard_version`、`barrier_visibility`、`replay_metadata` | `not_applicable` | Python reward fallback 在标记 fact/shaping ownership 与 source version 时保留 compatibility | WP4-C 暴露 fact/shaping attribution 后，废弃未标记 fallback | WP4-C reward attribution tests |
| `TerminationSpec` / `EpisodeStatus` | `maintained` | frontend、policy、orchestration、test、binding | request: 存在时为 orchestration truncation/reset request；result: `ExecutionBatchStepResult` 中 termination/status 字段与 future `EpisodeStatus` | simulation 拥有 semantic termination；orchestration 拥有 truncation | terminated/truncated reason 必须携带 reason source、source time、snapshot version 与 mirrored phase status | `state_shard_version`、`barrier_visibility`、`replay_metadata` | `not_applicable` | Gymnasium-style adapter mirror 在保留 authoritative source 前为 compatibility | facade lifecycle source 明确后，废弃 private adapter phase machine | WP4-C termination/lifecycle tests |
| `EpisodeLifecycleContract` | `maintained` | frontend、policy、orchestration、test、binding | request: reset/step lifecycle requests；result: phase、step count、reset transition id、mirrored status | compiled runtime/facade authority with adapter mirrors | facade state 是权威；adapter 可以 mirror phase，但不能推进私有 truth | `barrier_visibility`、`replay_metadata` | `not_applicable` | adapter-local lifecycle state 只是 compatibility mirror | facade phase 覆盖 use case 后，移除权威 adapter phase mutation | architecture lifecycle authority gate 与 WP4-C tests |
| `DiagnosticsTrace` | `diagnostics_only` | diagnostics、test、frontend、binding | request: 当前 piggyback on `EngagementBatchRequest`；result: `EngagementEventPacket` 内的 `DiagnosticsTrace` | core/engine evidence exported through facade | trace 在可用时连接 request、event、report、snapshot/export version 与 observation packet version | `event_order`、`state_shard_version`、`barrier_visibility`、`replay_metadata` | `not_applicable` | WP4 可保持 trace piggyback on engagement export；WP4-A 不要求 dedicated diagnostics facade | 当 WP5 trace conformance 需要跨 surface query 时，提升为 dedicated diagnostics query/export surface | WP5 trace and replay/evidence conformance gates |
| Direct observation getters: `get_agent_observations_batch`、`get_instrument_states_batch`、`get_mission_commands_batch`、`get_task_orders_batch`、`get_leader_intents_batch`、`get_pilot_reports_batch` | `compatibility_adapter` | frontend、test、binding | request: `WorldEntityRef` list；result: per-field vectors | facade helper over simulation state | 可能缺少统一 packet provenance 与 view-spec schema metadata | `state_shard_version`、`barrier_visibility` | varies；通常是 `AgentObservation` 或 `not_applicable` | 在 tests 与 bindings 迁移到 `ObservationBatchPacket` 前允许存在 | packet path 具备 parity 与 provenance 后，收窄或标记为 diagnostics | facade observation parity tests |
| `RuntimeFacade::runtime()` / raw `WorldBatchRuntime` | `compatibility_adapter` | test、diagnostics、backend | request: raw runtime access；result: raw runtime handle | facade escape hatch to simulation internals | 不是 facade snapshot contract | 对 maintained truth 为 none；可为 diagnostics 检查 scheduler artifacts | `WorldTruth` | 只允许 legacy tests、迁移期 debugging 与 low-level capability verification 使用 | 从 maintained frontend path 中移除；仅保留显式 diagnostics/legacy 用途 | `tests/architecture/test_runtime_facade_layering.py` |
| `RuntimeCapabilities` / backend capability query | `deferred` | backend、frontend、diagnostics、test | request: `capabilities()`；result: `RuntimeCapabilities` | facade/backend capability boundary | 当前 struct 记录 capability flags，但不定义 backend profile parity 或 resident-state semantics | future `clock_domain`、`state_shard_version`、`replay_metadata`、parity budget | `not_applicable` | 现有 empty/simple query 可文档化，但不能暗示 backend parity | parity budget 与 device-resident state policy 完成后，在 backend profile work 中提升 | deferred backend profile validation；非 WP4-A implementation |
| `ef_py` mirror | `maintained` | binding、policy、test、frontend | request/result: mirrors stable C++ facade DTOs | Python binding adapter | 必须保留 DTO name 与 field semantics；没有独立 snapshot truth | 与被 mirror 的 surface 相同 | 与被 mirror 的 surface 相同 | 绕过 facade DTO 的 Python helper 是 compatibility-only | binding mirror 覆盖稳定 DTO 后，移除 helper-only maintained docs | binding field-presence tests 与 raw-runtime exposure checks |

## 4. Information-State 边界

`ObservationViewSpec` 是维护中的 policy/test-owned surface concept。它拥有 schema version、required fields、optional fields、feature encoding、normalization、masking、stacking 与 checkpoint compatibility behavior。它不拥有权威仿真状态。

`ObservationPacket` 是 facade-exported data product。当前 C++ DTO 是
`ObservationBatchPacket`。只有当它从声明过的 source snapshot、barrier 与 view specification 采样时，才是维护中的 observation。它不是 belief state，也不能在声明 view 外静默包含 `WorldTruth` 字段。

`DecisionBelief` 是 policy/agent-side belief layer。维护中的
`DecisionBelief` 必须命名它消费的 `ObservationPacket` version、memory/estimator state、model reference 与 uncertainty/confidence shape。Truth-derived oracle belief 是 `diagnostics_only`。

`AgentRole` 是 agency boundary：role + authority + information-state source + decision model + action interface。WP4-A 记录名称与边界，但 WP4-D 拥有 contract sketch 与 adapter mapping。

`DiagnosticsTrace` 是 evidence boundary。它可以引用 truth、event、report、
snapshot 与 export 来解释发生了什么，但不能成为 policy observation 或 maintained scheduler truth。在 WP4-A 中，它保持为 `diagnostics_only` surface，并 piggyback on engagement export，直到后续 diagnostics facade 被提升。

## 5. RuntimeFacade 拆分阈值

WP4-A 记录以下治理规则，但不实施拆分：

```text
If RuntimeFacade exceeds 40 maintained public methods, plan a split into
RuntimeSessionFacade, WorldSetupFacade, ExecutionStepFacade,
ObservationFacade, EngagementFacade, DiagnosticsFacade, and
BackendCapabilityFacade.
```

该阈值是规划触发器，不要求自动重构，也不把 compatibility-only helper 与 maintained request/result surface 等价计数。拆分提案应先分类哪些方法是 maintained、compatibility-only、diagnostics-only 或 deferred。

## 6. 验收门槛

WP4-A inventory 在满足以下条件时可用：

1. WP4-A 分发单列出的每个 surface 都已有分类；
2. 每行都声明 consumer group、request/result DTO、source layer、
   snapshot semantics、scheduler dependency、information-state layer、
   compatibility rule、deprecation rule 与 validation gate；
3. `ObservationViewSpec`、`ObservationPacket`、`DecisionBelief`、
   `AgentRole` 与 `DiagnosticsTrace` 有显式边界；
4. compatibility 与 diagnostics path 不会被误认为 maintained
   policy/training truth；
5. 后续 WP4-B/C/D/E worker 可以引用这些 surface name，而不需要新增词汇。

## 7. 未决问题

1. `ObservationViewSpec` 是否应在 WP4 成为显式 C++ DTO，还是在 WP5 validation 需要 runtime metadata 前保持为 policy/test-owned 文档概念？
2. `DiagnosticsTrace` 是否应在 WP4 获得 dedicated facade query/export，还是 engagement-piggyback 路径足够支撑到 WP5 trace conformance？
3. `RuntimeCapabilities` 是否应在 WP5 前提升，还是继续推迟到 backend profile / parity-budget 工作？
4. `RuntimeFacade` split threshold 的基线方法数应如何计算：只算 maintained request/result methods，还是算除 constructor/accessor 外的全部 public methods？
