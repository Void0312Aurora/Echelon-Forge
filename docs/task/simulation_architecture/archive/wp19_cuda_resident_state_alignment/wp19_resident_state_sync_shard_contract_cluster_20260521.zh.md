# WP19-D Resident-State Sync And Shard Contract

状态：`2026-05-21` preflight-only / pass。

语言版本：

- 英文主文：[wp19_resident_state_sync_shard_contract_cluster_20260521.md](wp19_resident_state_sync_shard_contract_cluster_20260521.md)
- 中文辅文：`wp19_resident_state_sync_shard_contract_cluster_20260521.zh.md`

输入：

- [WP19 主计划](cuda_resident_state_alignment_wp19_20260521.zh.md)
- [WP19-B device-resident output contract](wp19_device_resident_output_contract_cluster_20260521.zh.md)
- [WP19-C GPU helper diagnostics boundary](wp19_gpu_helper_diagnostics_boundary_cluster_20260521.zh.md)
- [WP6 resident-state 边界规则](../wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.zh.md)
- [仿真系统架构设计](../../../plan/architecture/simulation_system_architecture_design.zh.md)
- [WP2.5 scheduler semantics](../wp25_scheduler_semantics/scheduler_semantics_wp25_20260519.zh.md)
- `src/core/engine/world_batch_runtime.h`
- `src/core/engine/world_batch_runtime.cpp`
- `src/runtime/facade/runtime_facade.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/contracts/backend_profile_contracts.h`

## 目的

把 resident-state ownership 与 sync vocabulary 映射到当前 runtime evidence 上，使未来
device-resident paths 在拥有 maintained state 前先具备契约。

本轮 preflight 的结论刻意保守：

1. 当前 maintained truth 仍然是 host-owned；
2. 当前 resident-state profile 仍是 blocked candidate，不是 live maintained surface；
3. 当前 host-visible export barrier 仍是 `export` packet barrier 与 host-returned batch
   results，而不是 backend-owned resident commit。

## 范围

范围内：

- 为 physics、tasking、track、damage、observation export、episode/runtime metadata、
  helper diagnostics，以及相邻 runtime setup/control seam 命名 state-shard
  vocabulary；
- 定义 sync cadence、trigger、barrier、stale-read、conflict、quarantine 与
  reconstruction/export rules；
- 用 architecture tests 或 preflight notes 防止 unsynced backend-local state 变成
  maintained truth。

范围外：

- CUDA helper implementation；
- device output DTO field ownership，由 WP19-B 负责；
- capability support promotion。

## 任务项

| ID | 任务 | 验收 |
|----|------|------|
| `D1` | Shard vocabulary | Candidate state shards 已命名，并在可行处链接到现有 runtime/facade evidence。 |
| `D2` | Sync barrier contract | Host-visible sync/export barriers 与 stale-read behavior 明确。 |
| `D3` | Ownership labels | Host-owned、backend-owned、partial-sync、observation-only 与 export-only labels 已映射到 WP19 surfaces。 |
| `D4` | Guard coverage | 测试或具体测试计划防止 unsynced backend-local state 影响 committed host truth。 |

## Runtime Evidence Baseline

| Evidence source | 当前事实 | WP19-D 含义 |
|-----------------|----------|-------------|
| `backend_profile_contracts.h` resident-state registry seed | `resident_state.unmaintained_candidate` 目前是 `profile_class: resident_state`、`sync_policy: undeclared_blocked`、`maintained_status: unmaintained_candidate`、`resident_state_supported: false`，且 `diagnostics_allowed: true`。 | 今天并不存在 maintained 的 backend-owned 或 partial-sync resident shard。Unsynced backend-local state 仍然只是 candidate-only。 |
| `RuntimeFacade::capabilities()` | `supports_resident_state` 被硬编码为 `false`，同时 facade 仍会导出 candidate id、parity-budget ref 与 rejection reason。 | Resident-state 在 public capability surface 上明确 fail-closed。 |
| `WorldBatchRuntime` batch mutators 与 readers | setup、tasking、mission-command、leader-intent、pilot-report、observation 与 execution-episode controller mirrors 都通过 host-visible batch calls 暴露。 | 当前 maintained truth 是经由 host-owned runtime/facade surface 暴露，而不是通过 device-owned resident commit 暴露。 |
| `ObservationBatchPacket` 与 `EngagementEventPacket` | host-visible export packet 都带有 `snapshot_version`、`barrier_id`、`source_time_s` 与 provenance labels。`EngagementEventPacket` 还带有 `barrier_sequence`、`barrier_detail`、maintained packet provenance 与 diagnostics-only diagnostics provenance。 | 当前 maintained export barrier 是 host-visible facade export packet envelope，不是 backend-owned resident barrier。 |
| `ExecutionBatchStepResult` | rewards、termination、status vectors、reward reports、step infos、controller-state-change flags 与内嵌 `observation_packet` 都以 host-side step product 返回。 | episode/runtime metadata 当前是 host-owned derived product，不能在没有契约的情况下悄悄转交给 unsynced backend-local state。 |
| `WorldBatchRuntime::get_*_candidate_ids_batch(..., use_gpu)` | GPU helper path 会返回 sensor/visual/comm broadphase candidate ids，但不会投射 capability support 或 maintained truth。 | 当前 helper/GPU state 只能算 export-only 或 diagnostics-only evidence。 |
| `RuntimeFacade.runtime()` 与现有 architecture guards | raw runtime escape hatch 已被标记为 compatibility/diagnostics-only，且已有架构测试阻止 facade 依赖 GPU helper implementation 或 probe-based capability projection。 | WP19-D 可以在不扩展 public truth path 的前提下，延续同样的 fail-closed resident-state sync boundary。 |

## Candidate Shard Inventory

下表把候选 resident-state shard 映射到当前 runtime evidence。
“Current label” 指的是今天最贴近实现事实的标签，不是 promotion 建议。

| Candidate shard | 当前 evidence / surface | Current label | 当前 cadence / trigger / barrier | 当前 stale-read / conflict 规则 |
|-----------------|-------------------------|---------------|----------------------------------|---------------------------------|
| `setup/static world config` | `BatchWorldSetupRequest`、`BatchWorldSetupResult`、`reset_batch`、`apply_world_setup_batch`，以及 `WorldBatchRuntime` 中的 terrain/wind/zone/spawn setup。 | `host-owned` | 只由 setup/reset 调用触发。语义上对齐 WP25 `setup/reset` 与 `input_injection`；当前没有 backend-owned resident barrier 暴露。 | setup state 只有在 host setup/reset 完成后才算 authoritative。未来 backend cache 可以镜像它，但在声明 reconstruction/export rule 之前不能成为 maintained truth。 |
| `tasking/command/control intent` | `set_pilot_actions_batch`、`set_mission_commands_batch`、`set_task_orders_batch`、`set_leader_intents_batch`、`set_pilot_reports_batch`，以及 `WorldBatchRuntime` / `RuntimeFacade` 的对应 getters。 | `host-owned` | 由显式 batch setter 在 `step_batch()` 或 `run_wp10_window()` 前触发。语义上可视为 WP25 `input_injection`；当前没有 same-window backend publish surface。 | host batch mutator 仍是唯一 authoritative writer。backend-local copy 在后续 profile 声明 per-field ownership 与 commit barrier 前，都只能算 stale 或 candidate mirror。 |
| `physics/world truth` | `SimulationKernel::step()` 通过 `step_batch()` / `step_worlds()` 调用，外加通过 observation 与 counterfactual snapshot 间接 host export。 | 当前是 `host-owned`；`backend-owned` 尚不可用 | 由 runtime step completion 触发。当前唯一 maintained read point 是 post-step host read 与后续 export packet。 | parallel worker completion order 不是 scheduler truth。未来 resident physics shard 必须在声明 barrier 上发布 committed host-visible reconstruction，之后才能影响 maintained state。 |
| `track/sensed observation state` | `get_agent_observations_batch`、`ObservationBatchPacket.agent_observations`、以及由 observation contacts 派生出的 `EngagementEventPacket.track_packets`。 | `observation-only` payload，外包在 `host-owned` export envelope 中 | 由显式 facade export 或 execution-step result 内嵌导出触发。public barrier 是 `export`。 | track/observation payload 只能通过带 snapshot/provenance 的 exported packet 供 maintained consumer 使用，不能直接改写 committed world/tasking/damage state。 |
| `engagement lifecycle` | `LaunchRequest`、`LaunchEvent`、`MunitionLifecyclePacket`，以及经由 `EngagementEventPacket` 导出的 recent engagement events。 | `host-owned` export | 由显式 engagement export 在 recent events 收集后触发。public barrier 是 `export`，packet envelope 上还带 `barrier_sequence` 与 `barrier_detail`。 | recent-event buffer 可以导出或比较，但 unsynced backend-local event order 不能定义 scheduler truth。 |
| `damage/effects` | `EffectsEvent`、`DamageReport`、recent engagement-event export，以及把 traces 连到 effects/damage ids 的 diagnostics ancestry。 | `host-owned` export，伴随 `export-only` diagnostics sidecar | 由显式 engagement export 在 host-visible recent events 可用后触发。public barrier 是 `export`。 | damage report 只有作为 exported host-visible product 时才是 maintained。backend-only effects accumulator 在具备 reconstruction 与 parity rule 前必须 quarantine 到 diagnostics。 |
| `observation export envelope` | `ObservationBatchPacket.snapshot_version`、`barrier_id`、`source_time_s`、`provenance`；`EngagementEventPacket.snapshot_version`、`barrier_id`、`barrier_sequence`、`barrier_detail`、`packet_provenance`、`diagnostics_provenance`。 | `host-owned` envelope，承载 `observation-only` 或 `export-only` payload | 由 facade export call 触发。public barrier 明确序列化为 `export`。 | 任何未来 backend-owned 或 partial-sync shard 都必须重建到这个 envelope，或重建到 WP19-B 的增量 DTO seam，之后 frontend 才能把它当成 maintained。 |
| `episode/runtime metadata` | `ExecutionEpisodeState`、rewards、`terminated`、`truncated`、status vectors、termination specs、reward reports、step infos、controller-state-change flags，以及 `ExecutionBatchStepResult` 中嵌套的 `ObservationBatchPacket`。 | `host-owned` | 由 `export_execution_episode_states()` 或 `step_execution_batch()` 触发。嵌套 observation packet 使用 `export`；其余仍是 host-returned step bundle，尚无 resident barrier id。 | controller mirror 只有在 primed 且 world/entity 匹配时才有效。backend-local controller copy 或 reward cache 在声明 ownership、barrier 与 replay rule 前都不能成为 maintained truth。 |
| `helper diagnostics / candidate broadphase exports` | `get_sensor_candidate_ids_batch`、`get_visual_candidate_ids_batch`、`get_comm_candidate_ids_batch`、GPU helper/probe outputs、diagnostics traces。 | `export-only` | 由显式 helper/query/export 调用触发。当前没有 maintained resident barrier。 | 这些输出可能 stale、approximate 或 backend-local。它们不能驱动 committed state、fallback 或 capability projection。 |
| `backend operational resident shards` | 目前只有被阻塞的 registry placeholder `resident_state.unmaintained_candidate`；还没有当前 facade DTO 或 host-visible resident commit packet。 | 仅是未来候选 `backend-owned` 或 `partial-sync` | trigger/barrier/cadence 当前均未声明，因此 blocked。 | 在 per-shard ownership、cadence、trigger、barrier、reconstruction、parity budget 与 validation evidence 被声明并接受前，禁止 promotion。 |

## Sync Cadence、Trigger 与 Barrier 规则

WP19-D 复用 WP25 的 barrier vocabulary，但当前 runtime 只把其中一部分作为 public data 暴露。

| Semantic barrier | 当前 runtime evidence | WP19-D 规则 |
|------------------|-----------------------|-------------|
| `input_injection` | 语义上由 step 前的 host batch setter 与 setup call 表示。 | 未来 resident-state profile 可以复用这个 barrier，但今天它仍是 host-owned，且没有 materialized resident packet barrier id。 |
| `stage_publish` | 当前没有任何 maintained public resident-state surface 暴露 same-window backend publish。 | today same-window backend visibility 不是 maintained claim。未来若要使用，必须按 shard 显式声明，并避免意外渗入 facade truth。 |
| `window_commit` | 语义上由 completed runtime step 与 controller step result 表示，但还没有为所有 result bundle 统一序列化成 packet barrier id。 | 未来 resident-state 或 partial-sync profile 必须指明哪些 shard 在此 commit，以及如何重建 snapshot identity。 |
| `export` | 在 `ObservationBatchPacket` 与 `EngagementEventPacket` 上被显式暴露。 | 这是当前唯一 public host-visible sync barrier，可用于 maintained observation/engagement export。 |
| `counterfactual_selected_slice` | 在 `RuntimeCounterfactualSnapshot` / `RuntimeWorldlineComparison` 上被显式暴露。 | 这是受限 comparison/export barrier，不是 resident-state ownership barrier。 |

默认 cadence 与 trigger 规则：

1. setup 与 static-world shard 只在 setup/reset path 同步；
2. tasking/control shard 只在显式 host batch mutation 后，随 runtime window 同步；
3. physics、engagement 与 damage shard 只有在 completed step 之后，再经由 export
   或 result reconstruction 才变成 host-visible；
4. observation 与 track shard 只有在显式 `export` barrier 上，才成为 maintained
   consumer input；
5. helper diagnostics 只在显式 export 或 query 时同步，并保持 non-authoritative。

## Ownership Label Mapping To WP19 Surfaces

| Ownership label | 当前可落到的 WP19 surface | 当前状态 |
|-----------------|----------------------------|----------|
| `host-owned` | `BatchWorldSetupRequest/Result`、batch mutator、host-returned execution-step bundle、`ObservationBatchPacket`、`EngagementEventPacket`、execution-episode controller mirror。 | 这是今天唯一的 maintained state path。 |
| `backend-owned` | 当前没有 maintained public surface。只有 blocked registry placeholder 与未来 additive DTO/export seam 属于候选。 | 不可用；仍被 `resident_state.unmaintained_candidate` 阻塞。 |
| `partial-sync` | 当前没有 maintained public surface。未来 profile 可以把选定 backend shard 同步进 host-visible packet 或 DTO。 | 不可用；若引入，必须声明 per-shard ownership、cadence、trigger、barrier、stale-state policy 与 mismatch policy。 |
| `observation-only` | `ObservationBatchPacket.agent_observations`、`EngagementEventPacket.track_packets`，以及任何未来仍受 observation envelope 约束的 device observation view。 | 仅作为 exported observation payload 可用，不构成 state ownership。 |
| `export-only` | diagnostics traces、helper candidate-id query、helper/probe output、mismatch evidence、shadow-style report。 | 今天可用，但不得影响 committed truth 或 support flags。 |

## Stale-Read、Conflict、Quarantine 与 Reconstruction 规则

1. 任何缺少声明式 host-visible reconstruction/export barrier 的 backend-local 或
   helper-local value，对 maintained use 来说都默认是 stale。
2. `RuntimeFacade.runtime()` 与 direct `WorldBatchRuntime` escape hatch 仍然只属于
   compatibility/diagnostics-only；它们不是 resident-state commit path。
3. 每个 maintained profile 中，一个 shard 只能有一个 authoritative owner。除非未来
   profile 精确声明 partial-sync split 与 conflict rule，否则禁止同一 committed field
   同时由 host/backend 混合主导。
4. parallel worker completion order，以及任何未来 GPU queue completion order，都不是
   scheduler truth。可接受的顺序仍以 WP25 barrier/order model 加 exported snapshot
   identity 为准。
5. unsynced backend-local state 必须 quarantine 到 `diagnostics-only`、
   `observation-only` 或 `export-only` surface。它不得更新 committed host state、改变
   fallback control flow，也不能单独满足 parity。
6. 从 backend-owned 或 partial-sync shard 重建出来的结果，必须终止在 host-visible
   packet 或 DTO 中，并携带 snapshot identity、barrier identity、source time、
   provenance 与 mismatch handling。
7. observation-only shard 可以导出 payload，但不得改写 committed world truth、
   scheduler order、tasking state 或 damage state。
8. episode/runtime metadata 在未来 resident-state profile 声明 controller state、
   reward state 与 termination state 如何同步、版本化并通过 replay validation 之前，
   仍保持 host-owned。

## Guard Coverage

当前守卫姿态：

- 现有 `tests/architecture/runtime_facade/test_layering.py` 已经阻止 facade 耦合 GPU
  helper implementation，且阻止 probe-driven capability promotion；
- WP19-D 应把 resident-state sync preflight 保持在同一条 fail-closed 路线上：
  blocked resident-state candidate、`supports_resident_state == false`，以及
  host-visible export barrier 继续保持显式。

本流可安全追加的 architecture guard：

- 断言 resident-state registry entry 仍然保持
  `undeclared_blocked` + `unmaintained_candidate` +
  `resident_state_supported: false`；
- 断言 public facade capability surface 继续 fail-closed，同时
  observation/engagement export packet envelope 继续使用显式 host-visible `export`
  barrier 与 maintained/diagnostics provenance label。

## Future Maintained Resident-State Promotion 的 Residuals

本流并不构成 capability promotion 依据。主要 residuals 如下：

1. facade DTO 还没有 public per-shard resident `SnapshotVersion.shard_versions`
   contract；
2. 对大多数 runtime product 来说，`input_injection` 与 `window_commit` 仍主要是
   semantic barrier，而不是 fully serialized host-visible packet metadata；
3. 目前没有任何 maintained DTO 承载 backend-owned 或 partial-sync reconstruction
   result；
4. backend profile contract 中还没有 machine-readable、per-shard 的 conflict
   resolution、mismatch quarantine 与 stale-state policy；
5. 还没有 replay/validation evidence 证明 backend-owned resident shard 能在不违反
   WP6/WP25 规则的前提下重建 host-visible truth；
6. helper/GPU export 仍然只是有价值的 evidence，但不能仅凭本次 preflight 就被提升到
   `observation-only` 或 `export-only` 以外的语义。

## 建议验证

```bash
git diff --check
python -m pytest -q tests/architecture/runtime_facade/test_layering.py
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP19 --summary
```

## 交付

返回：

- sync/shard inventory 与 ownership-label mapping；
- 任何新增的 architecture guard coverage；
- 指向 WP19-B / WP19-E 的 blocker 或 residual；
- 明确说明 WP19-D 当前以 `preflight-only` 关闭，而不是 maintained resident-state
  promotion。

## Closure Outcome

WP19-D 在 WP19 范围内以 preflight-only sync/shard contract 通过验收。当前
maintained truth 仍是 host-owned，resident-state 仍是 blocked candidate；任何未来晋级
仍需要 per-shard ownership、cadence、barrier、reconstruction、parity-budget、
conflict、quarantine 与 replay evidence。
