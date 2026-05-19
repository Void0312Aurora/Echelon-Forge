# WP6-B Parity Budget 注册表

状态：`2026-05-19` WP6-B parity budget 记录的 implementation-ready 注册表。

语言版本：

- 英文主文：[wp6_parity_budget_registry_20260519.md](wp6_parity_budget_registry_20260519.md)
- 中文辅文：`wp6_parity_budget_registry_20260519.zh.md`

输入：

- [WP6 后端配置文件策略](backend_profile_policy_wp6_20260519.zh.md)
- [WP6-A 后端配置文件分类分发单](wp6_backend_profile_taxonomy_cluster_20260519.zh.md)
- [WP6-B parity budget 分发单](wp6_parity_budget_cluster_20260519.zh.md)
- [WP2.5 调度语义冻结](scheduler_semantics_wp25_20260519.zh.md)
- [WP5 验证套件](validation_harness_wp5_20260519.zh.md)

规范术语：

- `MUST` 表示 WP6 维护文档与后续实现所要求的行为。
- `MUST NOT` 表示不能定义维护中的 parity 真值的行为。
- `SHOULD` 表示默认规则，偏离需要显式补充任务或审查说明。
- `MAY` 表示允许的兼容或 diagnostics 路径。

## 1. 目的

本注册表是 `WP6-B Parity Budget And Comparison Rules` 的实现准备产物。它把分发单里的模板落成命名 budget 记录，后续 backend profile metadata 可以通过 `parity_budget_ref` 引用这些记录。

本注册表刻意保持谨慎。`cpu_exact.reference` 是本注册表首个 revision 中唯一维护中的 exact 基线。GPU helper、GPU exact、resident-state 与 shadow-compare 条目在维护中 profile 显式声明 ownership、sync、parity 证据与 validation gate 前，都只是占位或 diagnostics 记录。

## 2. 注册表字段契约

每个注册表条目 MUST 携带以下字段：

| 字段 | 要求 |
|------|------|
| `budget_id` | budget 记录的稳定 id。 |
| `budget_version` | budget 记录的整数版本号。 |
| `backend_profile_id` | 拥有或将拥有该 budget 的 profile id。 |
| `profile_class` | `reference`、`accelerated_exact`、`resident_state`、`approximate` 或 `diagnostics_only` 之一。 |
| `comparison_reference` | 用于比较的语义锚点。 |
| `budget_scope` | 该 budget 覆盖的 clock domain、state shard、output family，以及 maintained / diagnostics 划分。 |
| `comparison_domains` | 各比较域的 exactness 与 tolerance 规则。 |
| `sync_barriers` | 锚定 replay 与比较的 barrier。 |
| `diagnostics_requirements` | 解释 mismatch 所需的结构化字段。 |
| `mismatch_policy` | 比较失败或占位条目被评估时的动作。 |
| `acceptance_gate` | 进入维护状态前所需的审查或测试门。 |
| `change_reason` | 该 budget revision 的简短原因。 |

注册表消费者 MUST NOT 因为一条记录存在就推断它是维护中状态。维护状态来自 `profile_class`、`acceptance_gate` 以及引用该记录的 profile metadata。

## 3. 比较域默认规则

除非某个条目进一步收窄比较域，否则以下默认规则适用于下方所有条目：

| 比较域 | 注册表规则 |
|--------|------------|
| `event_order` | exact-only identity 域。`timestamp`、`priority`、`event_id` 与 event-family membership MUST 匹配。不允许维护中的 tolerance。 |
| `snapshot_versions` | exact-only identity 域。导出的 snapshot identity、barrier id、barrier sequence、shard-version map 与 lineage MUST 匹配。内部版本号必须先归一化成导出的 `SnapshotVersion` 再比较。 |
| `numeric_state` | payload 比较域。任何 tolerance 都 MUST 写明 field family、comparator 和 threshold。未列出的字段默认 exact。 |
| `observation_export` | exact envelope 域加 payload 继承。schema、field set、visibility label、provenance 与 source snapshot reference 都是 exact；payload 值继承 `numeric_state`。 |
| `diagnostics_trace` | 结构化 ancestry 与 mismatch code 是 exact。可读 diagnostics prose、summary text 与 formatting 仅为 diagnostics-only，MUST NOT 参与维护真值。 |

## 4. 初始 Budget 注册表

### 4.1 `cpu_exact.reference`

```yaml
budget_id: parity_budget.cpu_exact.reference.v1
budget_version: 1
backend_profile_id: cpu_exact.reference
profile_class: reference
comparison_reference: self
budget_scope:
  maintained_status: maintained_exact_baseline
  clock_domains: [physics.fixed_tick, sensor.scan_slot]
  state_shards: [scheduler, physics, track, observation, engagement]
  output_families: [observation_packet, committed_snapshot, diagnostics_trace]
  diagnostics_only_surfaces: [human_readable_diagnostics_prose]
comparison_domains:
  event_order:
    mode: exact_identity
    key: [timestamp, priority, event_id]
    event_family_membership: exact
    allowed_drift: none
  snapshot_versions:
    mode: exact_identity
    identity: [world_id, global_version, barrier_id, barrier_sequence, shard_versions, lineage]
    normalization: exported_snapshot_version
    allowed_drift: none
  numeric_state:
    mode: exact
    tolerance_budget: []
    default_for_unlisted_fields: exact
  observation_export:
    envelope:
      mode: exact
      fields: [schema_version, field_set, visibility_label, provenance, source_snapshot_version]
    payload: inherit_numeric_state
  diagnostics_trace:
    structured:
      mode: exact
      fields: [source_request_id, event_id, source_snapshot_version, resulting_snapshot_version, mismatch_code]
    prose: diagnostics_only
sync_barriers: [input_injection, tick_commit, window_commit, export]
diagnostics_requirements:
  - backend_profile_id
  - budget_id
  - budget_version
  - comparison_reference
  - source_snapshot_version
  - resulting_snapshot_version
  - sync_barrier_id
  - mismatch_domain
  - mismatch_code
  - mismatch_summary
mismatch_policy:
  maintained_profile_result: fail
  diagnostics_result: report_only
  quarantine_required: true
acceptance_gate: maintained_cpu_reference_existing_wp6_baseline
change_reason: initial maintained exact reference budget
```

实现说明：这是本注册表中唯一可在没有后续 promotion review 的情况下作为维护中 exact truth 使用的条目。

### 4.2 `gpu_helpers.diagnostics_only`

```yaml
budget_id: parity_budget.gpu_helpers.diagnostics_only.v1
budget_version: 1
backend_profile_id: gpu_helpers.diagnostics_only
profile_class: diagnostics_only
comparison_reference: cpu_exact.reference
budget_scope:
  maintained_status: diagnostics_only_not_truth
  clock_domains: [declared_by_helper_export]
  state_shards: []
  output_families: [helper_metrics, helper_trace, probe_export]
  diagnostics_only_surfaces: [all_exported_surfaces]
comparison_domains:
  event_order:
    mode: exact_identity_if_replayed_against_reference
    key: [timestamp, priority, event_id]
    event_family_membership: exact
    allowed_drift: none
  snapshot_versions:
    mode: exact_identity_if_snapshot_link_is_reported
    identity: [source_snapshot_version, barrier_id, barrier_sequence]
    normalization: exported_snapshot_version
    allowed_drift: none
  numeric_state:
    mode: diagnostics_only
    tolerance_budget: []
    required_if_promoted: field_family_comparator_threshold
    default_for_unlisted_fields: exact
  observation_export:
    envelope:
      mode: exact_if_present
      fields: [schema_version, field_set, visibility_label, provenance, source_snapshot_version]
    payload: inherit_numeric_state
  diagnostics_trace:
    structured:
      mode: exact_if_present
      fields: [source_request_id, event_id, source_snapshot_version, mismatch_code]
    prose: diagnostics_only
sync_barriers: [export]
diagnostics_requirements:
  - backend_profile_id
  - budget_id
  - budget_version
  - comparison_reference
  - source_snapshot_version
  - export_barrier_id
  - helper_name
  - helper_build_or_feature_flag
  - diagnostics_label
  - mismatch_summary
mismatch_policy:
  maintained_profile_result: not_applicable
  diagnostics_result: report_only
  quarantine_required: false
acceptance_gate: not_eligible_for_maintained_truth_without_reclassification
change_reason: initial diagnostics-only placeholder for GPU helper exports
```

实现说明：该记录可以支持 diagnostics 报告。它 MUST NOT 用来声明 exact GPU execution、resident state 或 shadow comparison。

### 4.3 `gpu_exact.unmaintained_candidate`

```yaml
budget_id: parity_budget.gpu_exact.unmaintained_candidate.v1
budget_version: 1
backend_profile_id: gpu_exact.unmaintained_candidate
profile_class: accelerated_exact
comparison_reference: cpu_exact.reference
budget_scope:
  maintained_status: unmaintained_candidate
  clock_domains: [physics.fixed_tick, sensor.scan_slot]
  state_shards: [scheduler, physics, track, observation, engagement]
  output_families: [observation_packet, committed_snapshot, diagnostics_trace]
  diagnostics_only_surfaces: [accelerator_kernel_notes, human_readable_diagnostics_prose]
comparison_domains:
  event_order:
    mode: exact_identity_required_for_promotion
    key: [timestamp, priority, event_id]
    event_family_membership: exact
    allowed_drift: none
  snapshot_versions:
    mode: exact_identity_required_for_promotion
    identity: [world_id, global_version, barrier_id, barrier_sequence, shard_versions, lineage]
    normalization: exported_snapshot_version
    allowed_drift: none
  numeric_state:
    mode: exact_required_for_accelerated_exact
    tolerance_budget: []
    default_for_unlisted_fields: exact
  observation_export:
    envelope:
      mode: exact_required_for_promotion
      fields: [schema_version, field_set, visibility_label, provenance, source_snapshot_version]
    payload: inherit_numeric_state
  diagnostics_trace:
    structured:
      mode: exact_required_for_promotion
      fields: [source_request_id, event_id, source_snapshot_version, resulting_snapshot_version, mismatch_code]
    prose: diagnostics_only
sync_barriers: [input_injection, tick_commit, window_commit, export]
diagnostics_requirements:
  - backend_profile_id
  - budget_id
  - budget_version
  - comparison_reference
  - source_snapshot_version
  - resulting_snapshot_version
  - sync_barrier_id
  - accelerator_backend_id
  - accelerator_build_or_feature_flag
  - mismatch_domain
  - mismatch_code
  - mismatch_summary
mismatch_policy:
  maintained_profile_result: not_accepted
  candidate_result: fail_and_remain_unmaintained
  diagnostics_result: report_only
  quarantine_required: true
acceptance_gate: future_wp6_accelerated_exact_promotion_review_with_replay_evidence
change_reason: initial unmaintained candidate budget; no exact GPU acceptance claimed
```

实现说明：如果任何 numeric tolerance 变成必需，该候选项 MUST 从 `accelerated_exact` 重新分类出去。

### 4.4 `resident_state.unmaintained_candidate`

```yaml
budget_id: parity_budget.resident_state.unmaintained_candidate.v1
budget_version: 1
backend_profile_id: resident_state.unmaintained_candidate
profile_class: resident_state
comparison_reference: cpu_exact.reference
budget_scope:
  maintained_status: unmaintained_candidate
  clock_domains: [physics.fixed_tick, sensor.scan_slot]
  host_visible_maintained_state: [committed_snapshot, observation_packet, diagnostics_trace_structured]
  backend_resident_operational_state: [backend_local_cache, device_resident_working_set]
  state_shards: [observation, physics_or_track_if_declared_by_future_profile]
  output_families: [observation_packet, committed_snapshot, diagnostics_trace]
  diagnostics_only_surfaces: [unsynced_backend_local_state, human_readable_diagnostics_prose]
comparison_domains:
  event_order:
    mode: exact_identity_required_at_declared_barriers
    key: [timestamp, priority, event_id]
    event_family_membership: exact
    allowed_drift: none
  snapshot_versions:
    mode: exact_identity_required_for_host_visible_exports
    identity: [world_id, global_version, barrier_id, barrier_sequence, shard_versions, lineage]
    normalization: exported_snapshot_version
    allowed_drift: none
  numeric_state:
    mode: exact_by_default_with_explicit_future_tolerance_only
    tolerance_budget: []
    required_if_toleranced: [field_family, comparator, threshold]
    default_for_unlisted_fields: exact
  observation_export:
    envelope:
      mode: exact_for_host_visible_exports
      fields: [schema_version, field_set, visibility_label, provenance, source_snapshot_version]
    payload: inherit_numeric_state
  diagnostics_trace:
    structured:
      mode: exact_for_host_visible_exports
      fields: [source_request_id, event_id, source_snapshot_version, resulting_snapshot_version, mismatch_code]
    prose: diagnostics_only
sync_barriers: [input_injection, partial_sync_commit, window_commit, export]
diagnostics_requirements:
  - backend_profile_id
  - budget_id
  - budget_version
  - comparison_reference
  - source_snapshot_version
  - resulting_snapshot_version
  - sync_barrier_id
  - host_state_owner
  - backend_state_owner
  - sync_policy
  - resident_state_scope
  - mismatch_domain
  - mismatch_code
  - mismatch_summary
mismatch_policy:
  maintained_profile_result: not_accepted
  candidate_result: fail_and_remain_unmaintained
  diagnostics_result: report_only
  quarantine_required: true
acceptance_gate: future_wp6_resident_state_promotion_review_with_ownership_sync_and_replay_evidence
change_reason: initial unmaintained resident-state candidate budget; host/backend split not yet accepted as maintained
```

实现说明：未同步的 backend-local state 只属于 diagnostics-only，除非后续 profile 声明 ownership、sync cadence 与 parity 证据。

### 4.5 `shadow_compare.unmaintained_candidate`

```yaml
budget_id: parity_budget.shadow_compare.unmaintained_candidate.v1
budget_version: 1
backend_profile_id: shadow_compare.unmaintained_candidate
profile_class: diagnostics_only
comparison_reference: cpu_exact.reference
budget_scope:
  maintained_status: unmaintained_candidate
  clock_domains: [reference_clock_only]
  state_shards: []
  output_families: [shadow_report, mismatch_report, diagnostics_trace]
  diagnostics_only_surfaces: [shadow_report, mismatch_report, human_readable_diagnostics_prose]
comparison_domains:
  event_order:
    mode: exact_identity_for_reference_stream
    key: [timestamp, priority, event_id]
    event_family_membership: exact
    allowed_drift: none
  snapshot_versions:
    mode: exact_identity_for_reference_links
    identity: [source_snapshot_version, barrier_id, barrier_sequence]
    normalization: exported_snapshot_version
    allowed_drift: none
  numeric_state:
    mode: diagnostics_only_until_promoted
    tolerance_budget: []
    required_if_promoted: [field_family, comparator, threshold]
    default_for_unlisted_fields: exact
  observation_export:
    envelope:
      mode: exact_if_exported
      fields: [schema_version, field_set, visibility_label, provenance, source_snapshot_version]
    payload: inherit_numeric_state
  diagnostics_trace:
    structured:
      mode: exact_for_shadow_report_ancestry
      fields: [source_request_id, event_id, source_snapshot_version, mismatch_code]
    prose: diagnostics_only
sync_barriers: [reference_export, shadow_report_export]
diagnostics_requirements:
  - backend_profile_id
  - budget_id
  - budget_version
  - comparison_reference
  - source_snapshot_version
  - shadow_run_id
  - compared_profile_id
  - sync_barrier_id
  - mismatch_domain
  - mismatch_code
  - mismatch_summary
mismatch_policy:
  maintained_profile_result: not_applicable
  candidate_result: report_only_and_remain_unmaintained
  diagnostics_result: report_only
  quarantine_required: false
acceptance_gate: future_wp6_shadow_compare_review_before_any_maintained_claim
change_reason: initial unmaintained shadow-compare placeholder; no shadow capability acceptance claimed
```

实现说明：shadow comparison 可以解释差异，但该占位条目不会让 shadow output 成为维护中的真值来源。

## 5. Promotion 与 Revision 规则

1. 当 `comparison_domains`、`sync_barriers`、`diagnostics_requirements`、`mismatch_policy` 或 `acceptance_gate` 变化时，新条目或修订条目 MUST 增加 `budget_version`。
2. 从 `unmaintained_candidate` 提升到维护中使用，MUST 引用 replay 证据、ownership metadata、sync policy 和 validation 结果。
3. 提升到 `accelerated_exact` 时，MUST 保持 `event_order`、`snapshot_versions`、维护中的 `numeric_state`、observation envelope 与结构化 diagnostics ancestry 为 exact。
4. 提升到 `resident_state` 时，MUST 先识别 `host_visible_maintained_state`、`backend_resident_operational_state`、权威 owner 与 sync cadence，然后任何 capability flag 才能变成 true。
5. 任何允许 tolerance 的 numeric 字段，MUST 按 field family、comparator 与 threshold 列出。类似“足够接近”的 prose 不是 budget。
6. 只有当结构化 diagnostics 字段保持 exact 且 prose 被标注为 diagnostics-only 时，diagnostics prose 才可以在不导致维护 parity 失败的情况下变化。

## 6. 非目标

- 实现 runtime comparator 或 replay 代码。
- 创建 WP6-A 负责的 backend profile registry。
- 把 GPU exact、resident-state 或 shadow-compare 行为提升到维护状态。
- 编辑 `RuntimeCapabilities`、测试或 runtime backend 代码。
- 更新 README 或 index 发布页。

## 7. 退出标准

当以下条件满足时，本注册表可以交付 WP6-B：

1. 每个条目都包含 `budget_id`、`budget_version`、`backend_profile_id`、`profile_class`、`comparison_reference`、`budget_scope`、`comparison_domains`、`sync_barriers`、`diagnostics_requirements`、`mismatch_policy`、`acceptance_gate` 与 `change_reason`。
2. `cpu_exact.reference` 是唯一维护中的 exact 基线。
3. GPU helper、GPU exact、resident-state 与 shadow-compare 条目在后续 promotion 前都标为 diagnostics-only 或 unmaintained candidate。
4. `event_order` 与 `snapshot_versions` 是 exact-only identity 域。
5. Numeric tolerance 需要显式 field family、comparator 与 threshold。
6. Observation envelope 是 exact，observation payload 继承 `numeric_state`。
7. Diagnostics prose 被排除在维护真值之外。
8. 中文辅文具有相同的章节顺序与互链关系。

## 8. 验证命令

```bash
git diff --check
rg -n "budget_id|budget_version|backend_profile_id|profile_class|comparison_reference|budget_scope|comparison_domains|sync_barriers|diagnostics_requirements|mismatch_policy|acceptance_gate|change_reason" docs/task/simulation_architecture/wp6_parity_budget_registry_20260519*.md
rg -n "event_order|snapshot_versions|numeric_state|observation_export|diagnostics_trace|cpu_exact\\.reference|gpu_helpers\\.diagnostics_only|gpu_exact\\.unmaintained_candidate|resident_state\\.unmaintained_candidate|shadow_compare\\.unmaintained_candidate" docs/task/simulation_architecture/wp6_parity_budget_registry_20260519*.md
```
