# WP7-C 实现说明：Promotion Evidence Gates

状态：`2026-05-19`，WP7-C 第二波设计细化的实现级说明。

语言版本：

- 英文主文：[wp7_promotion_evidence_gates_notes_20260519.md](wp7_promotion_evidence_gates_notes_20260519.md)
- 中文辅文：`wp7_promotion_evidence_gates_notes_20260519.zh.md`
- 分发单：
  [wp7_promotion_evidence_gates_cluster_20260519.zh.md](wp7_promotion_evidence_gates_cluster_20260519.zh.md)

输入：

- [WP7 后端能力物化](backend_capability_materialization_wp7_20260519.zh.md)
- [WP7-A registry materialization](wp7_registry_materialization_cluster_20260519.zh.md)
- [WP7-A 实现说明](wp7_registry_materialization_notes_20260519.zh.md)
- [WP7-D multi-fidelity entry conditions](wp7_multifidelity_entry_conditions_cluster_20260519.zh.md)
- [WP7-D 实现说明](wp7_multifidelity_entry_conditions_notes_20260519.zh.md)
- [WP6 后端 profile registry](wp6_backend_profile_registry_20260519.zh.md)
- [WP6 parity budget registry](wp6_parity_budget_registry_20260519.zh.md)
- [WP6 resident-state 边界规则](wp6_resident_state_boundary_rules_20260519.zh.md)
- [WP5 验证套件](validation_harness_wp5_20260519.zh.md)

## 1. 运行规则

WP7-C 只定义 promotion gate 证据。它不晋级
`gpu_exact.unmaintained_candidate`、`resident_state.unmaintained_candidate`
或 `shadow_compare.unmaintained_candidate`。

candidate 只有在其 promotion gate 中的全部证据一起被接受后，才可以投影为
maintained capability：

1. 维护中的 backend profile registry revision；
2. 维护中的 parity budget revision；
3. ownership 与 sync contract；
4. event order 与 snapshot evidence；
5. mismatch 与 quarantine policy；
6. replay evidence；
7. facade/core layering evidence；
8. WP5 harness mapping；
9. 更新 capability projection rule 的 acceptance review。

Fail-closed 规则：如果任意必需项缺失、过期、仍为 candidate-only、
diagnostics-only 或不完整，capability projection 必须保持 false。runtime
code、GPU helper availability、deployment probe、更快执行路径或 fidelity
request label 都不能覆盖此规则。

## 2. Gate 记录形态

未来实现或 review checklist 应把每个 promotion gate 表示为包含以下字段的
记录：

```yaml
promotion_gate_id: exact_gpu_promotion_gate
candidate_profile_id: gpu_exact.unmaintained_candidate
required_profile_registry_revision:
  backend_profile_id: future-maintained-profile-id
  maintained_status: maintained
required_parity_budget_revision:
  budget_id: future-maintained-budget-id
  budget_version: incremented
ownership_sync_contract:
  host_state_owner: declared
  backend_state_owner: declared
  sync_policy: declared
event_snapshot_evidence:
  event_order: exact_or_budgeted_by_domain
  snapshot_versions: exact_or_reconstructed_at_declared_barriers
mismatch_quarantine_policy:
  mismatch_policy: fail_or_quarantine_for_maintained_result
  quarantine_required: true
replay_evidence:
  seeds_events_snapshots_barriers: present
facade_core_layering_evidence:
  maintained_facade_path: no_raw_core_bypass
wp5_harness_mapping:
  mandatory_tiers: []
  scope_condition_tiers: []
acceptance_review:
  required: true
capability_projection:
  remains_false_until_acceptance_review: true
```

这个形态是描述性约束，不是 runtime schema 承诺。字段名可以适配 WP7-A
materialization，但语义义务不能削弱。

## 3. Exact GPU Promotion Gate

`exact_gpu_promotion_gate` 适用于 `gpu_exact.unmaintained_candidate`。
promotion 意味着未来 accelerated exact profile 可以在声明 scope 内作为
maintained truth。仅证明 GPU kernel 可运行或 helper probe 可用并不充分。

| 证据区域 | promotion 前必需证据 |
|----------|----------------------|
| Profile registry revision | 维护中的 backend profile row 替换或 supersede `gpu_exact.unmaintained_candidate`；它命名稳定 `backend_profile_id`、`profile_class: accelerated_exact`、维护中的 `comparison_reference`、`host_state_owner`、`backend_state_owner`、`sync_policy`、`state_scope`、`observability_scope`、`validation_gate`、`maintained_status` 与 source provenance。 |
| Parity budget revision | 维护中的 budget 替换 `parity_budget.gpu_exact.unmaintained_candidate.v1`，递增 `budget_version`，并保持 `event_order`、`snapshot_versions`、observation envelope 与 structured diagnostics ancestry exact。任何 numeric tolerance 都会使 `accelerated_exact` 失效并要求重新分类。 |
| Ownership and sync | proposal 命名 host 或 backend 对每个 state shard 的 owner，命名 input injection、tick commit、window commit、export 的 sync barrier，并声明 GPU completion order 永远不是 scheduler truth。 |
| Event order and snapshot evidence | evidence 必须证明 event family membership、timestamp/priority/event id ordering、导出的 `SnapshotVersion`、barrier id、barrier sequence、shard-version map 与 lineage 相对 `cpu_exact.reference` 完全一致。 |
| Mismatch and quarantine policy | maintained result mismatch 会使 gate 失败。candidate mismatch output 必须与 committed state 隔离，只能作为带标签 diagnostics 保留。mismatch summary 必须包含 domain、code、source snapshot、resulting snapshot 与 backend build/profile id。 |
| Replay evidence | replay 必须在 CPU reference 与 GPU candidate 路径上重建相同 facade request stream、deterministic seed、event log、barrier sequence、committed snapshot、observation export 与 diagnostics ancestry。 |
| Facade/core layering evidence | maintained access 必须经过 facade request/result contract。accelerated core 不能暴露 raw runtime mutation path、隐藏 fallback control flow 或 helper-only capability projection。 |
| WP5 harness mapping | mandatory tier：design、trace、boundary、replay/evidence。scope-conditioned tier：当 exact GPU scope 包含 observation、track、data-link、belief 或 policy-input surface 时，information/belief 为 mandatory。 |
| Acceptance review | review 必须在同一个 promotion packet 中接受 profile registry revision、parity budget revision、replay report、mismatch/quarantine policy、facade/core layering evidence 与 capability projection update。 |

Projection guard：`projection.exact_gpu_supported` 在 acceptance review 明确指向
maintained profile 与 maintained budget 前保持 false。`fast_training` 与
`large_scale_swarm` request 可以请求吞吐或规模，但不能绕过此 promotion gate。

## 4. Resident-State Promotion Gate

`resident_state_promotion_gate` 适用于
`resident_state.unmaintained_candidate`。promotion 意味着未来 profile 可以为命名
maintained state scope 声明 backend-resident ownership 或 synchronization。
unsynced backend-local state 仍是 diagnostics-only。

| 证据区域 | promotion 前必需证据 |
|----------|----------------------|
| Profile registry revision | 维护中的 resident-state profile row 替换或 supersede `resident_state.unmaintained_candidate`；它命名稳定 `backend_profile_id`、`profile_class: resident_state`、维护中的 `comparison_reference`、per-shard `host_state_owner`、per-shard `backend_state_owner`、接受的 `sync_policy`、`state_scope`、`observability_scope`、`validation_gate`、`maintained_status` 与 source provenance。 |
| Parity budget revision | 维护中的 budget 替换 `parity_budget.resident_state.unmaintained_candidate.v1`，递增 `budget_version`，并命名 maintained host-visible state、backend-resident operational state、comparison domain、sync barrier、diagnostics requirement、mismatch policy 与 acceptance gate。 |
| Ownership and sync | proposal 必须按 shard 选择 WP6-C1 接受的 `backend-owned`、`partial-sync` 或 `observation-only` 等 label；定义 cadence、trigger、barrier、stale-read policy、conflict resolution、reconstruction/export rule、rollback 或 fallback non-interference 与 quarantine behavior。 |
| Event order and snapshot evidence | evidence 必须证明 declared barrier 上的 scheduler event order，而不是 backend thread completion order。host-visible reconstruction 或 export 必须归一化为带 barrier id、barrier sequence、shard version 与 lineage 的导出 `SnapshotVersion`。 |
| Mismatch and quarantine policy | stale、conflicting、unsynced 或无法 reconstruction 的 state 会使 gate 失败，并从 maintained state 中 quarantine。diagnostics export 必须把 backend-local cache、device-resident working set、queue-local scratch state 与 speculative value 标为 diagnostics-only。 |
| Replay evidence | replay 必须为每个声明 shard 重建 pre-sync、sync 与 post-sync state，包括 owner map、source snapshot、resulting snapshot、barrier id、stale-state outcome、conflict outcome 与 diagnostics ancestry。 |
| Facade/core layering evidence | public maintained path 必须消费 facade export、reconstructed snapshot 或声明的 observation packet。policy、scheduler 或 engagement path 不得在接受的 facade contract 外读取 raw backend-resident truth。 |
| WP5 harness mapping | mandatory tier：design、boundary、replay/evidence。resident state 触及 command、launch、munition、effect、damage、reward、termination 或 scheduler trace 时，trace 为 mandatory。触及 observation、visibility、track、data-link、belief 或 decision input 时，information/belief 为 mandatory。 |
| Acceptance review | review 必须一起接受 ownership/sync map、resident-state boundary label、maintained budget、stale-state policy、mismatch/quarantine policy、replay report、facade/core layering evidence 与 capability projection update。 |

Projection guard：`projection.resident_state_supported` 在 acceptance review 明确指向
maintained resident-state profile 与 maintained budget 前保持 false。
`sensor_heavy`、`fast_training` 与 `large_scale_swarm` request 可以压测类似
resident 的 workload，但不能绕过此 promotion gate。

## 5. Shadow Compare Promotion Gate

`shadow_compare_promotion_gate` 适用于
`shadow_compare.unmaintained_candidate`。promotion 不表示 shadow output 可以静默
影响 committed state。任何 maintained shadow profile 都必须先定义它是
non-mutating diagnostics、maintained comparison service，还是单独 review 过的
control path。

| 证据区域 | promotion 前必需证据 |
|----------|----------------------|
| Profile registry revision | 维护中或明确 diagnostics-only 的 shadow profile row 替换或 supersede `shadow_compare.unmaintained_candidate`；它命名稳定 `backend_profile_id`、profile class、comparison reference、non-interference contract、observability scope、validation gate、maintained status 与 source provenance。 |
| Parity budget revision | 维护中的 budget 或接受的 diagnostics budget 替换 `parity_budget.shadow_compare.unmaintained_candidate.v1`，递增 `budget_version`，并命名 compared profile id、reference stream identity、shadow run id、comparison domain、diagnostics requirement、mismatch policy 与 acceptance gate。 |
| Ownership and sync | proposal 必须证明 host reference path 拥有 committed state。除非 later maintained profile 明确声明单独 non-mutating 或 mutating control path 并通过 review，否则 shadow output 只能是 export-only。 |
| Event order and snapshot evidence | evidence 必须把 shadow report 关联到 reference event id、source snapshot version、barrier id、barrier sequence、compared profile id 与 shadow run id。report timing 不得重排或影响 maintained reference stream。 |
| Mismatch and quarantine policy | 除非未来 maintained control path 被接受，shadow mismatch 只能 report-only。任何可能影响 fallback、scheduling、policy input 或 committed state 的 mismatch 都必须触发 quarantine 并使 promotion 失败。 |
| Replay evidence | replay 必须在不要求 shadow path mutate committed state 的前提下，重现 reference stream、shadow input capture、shadow output report、mismatch code 与 diagnostics ancestry。 |
| Facade/core layering evidence | shadow result 必须通过 facade evidence 作为 diagnostics 或已 review 的 comparison output 暴露。core shadow helper 不得绕过 facade label、mutate raw runtime state 或因 availability 切换 capability projection。 |
| WP5 harness mapping | mandatory tier：design、boundary、replay/evidence。shadow report 比较 command、launch、effect、damage、reward、termination 或 event ancestry 时，trace 为 mandatory。比较 observation、visibility、track、belief 或 policy-input surface 时，information/belief 为 mandatory。 |
| Acceptance review | review 必须一起接受 non-interference proof、diagnostics separation、maintained 或 diagnostics budget classification、mismatch/quarantine policy、replay report、facade/core layering evidence 与 capability projection update。 |

Projection guard：`projection.shadow_supported` 保持 false，除非 acceptance review 明确
接受 maintained shadow capability。`weapon_effects_heavy` 或 `sensor_heavy`
request 可以请求额外 comparison diagnostics，但不能绕过此 promotion gate，也不能让
shadow output 影响 committed state。

## 6. WP5 Harness Mapping

下表是 WP5 映射的最低要求。mandatory 表示该 gate 的每个 promotion proposal 都必须
通过该 tier。scope-conditioned 表示当 candidate 触及列出的 domain 时，该 tier 变为
mandatory。

| Gate | Design | Trace | Boundary | Information/belief | Replay/evidence |
|------|--------|-------|----------|--------------------|-----------------|
| `exact_gpu_promotion_gate` | Mandatory：profile、budget、lifecycle 与 capability projection artifact 匹配 WP6/WP7-A 字段。 | Mandatory：event id、event family membership 与 diagnostics ancestry 在声明 domain 内匹配 CPU reference。 | Mandatory：maintained path 使用 facade contract，且没有 raw core bypass。 | Scope-conditioned：observation、track、visibility、belief、data-link 或 policy-input scope 中 mandatory。 | Mandatory：deterministic seed、event order、snapshot version、barrier、facade export 与 diagnostics 可相对 `cpu_exact.reference` replay。 |
| `resident_state_promotion_gate` | Mandatory：ownership map、sync policy、resident boundary label 与 state scope 已文档化且可机器检查。 | Scope-conditioned：scheduler、command、launch、munition、effect、damage、reward 或 termination scope 中 mandatory。 | Mandatory：host/backend boundary、reconstruction/export 与 facade-only maintained access 被 enforced。 | Scope-conditioned：observation、visibility、track、data-link、belief 或 decision-input scope 中 mandatory。 | Mandatory：pre-sync、sync、post-sync、stale-state、conflict、barrier、snapshot 与 quarantine evidence 可 replay。 |
| `shadow_compare_promotion_gate` | Mandatory：non-interference、diagnostics separation、budget classification 与 projection rule 已文档化。 | Scope-conditioned：event、engagement、reward、termination 或 trace ancestry comparison 中 mandatory。 | Mandatory：shadow output 不能 mutate committed state，也不能绕过 facade diagnostics label。 | Scope-conditioned：observation、visibility、track、belief 或 policy-input comparison 中 mandatory。 | Mandatory：reference stream、shadow capture、report export、mismatch code 与 diagnostics ancestry 可 replay。 |

promotion packet 应包含 WP5 evidence index，列出每个 mandatory 与
scope-conditioned tier 对应的具体 test name、doc check、fixture、replay artifact
或 review exhibit。缺少 scope analysis 本身就是 gate 不完整，因此 capability
projection 保持 false。

## 7. Fidelity Request 不可绕过规则

WP7-D request label 是 intent，不是 support claim。必须遵守以下绑定：

| Fidelity request | Gate interaction |
|------------------|------------------|
| `fast_training` | 只有在标记为 training-only/report-only 时，才可以使用 diagnostics 或 candidate path。没有相关 promotion gate 与 acceptance review，不能声称 exact GPU、resident-state 或 shadow support。 |
| `sensor_heavy` | 必须遵守 observation envelope、visibility、track、belief 与 information-state evidence。没有相关 promotion gate，不能把 resident-state 或 shadow diagnostics 当作 maintained observation truth。 |
| `weapon_effects_heavy` | 必须保持 launch、munition、effect、damage、reward、termination、event ancestry、mismatch、quarantine 与 replay evidence。不能弱化 exact event order 或 shadow non-interference。 |
| `large_scale_swarm` | 可以请求 scale-oriented scheduling，但 scale 不放松 snapshot identity、shard-version evidence、quarantine 或 capability projection gate。 |
| `exact_evaluation` | 使用 `cpu_exact.reference`，除非未来 exact profile 已通过其 promotion gate 与 acceptance review。 |

如果 request 无法绑定到 maintained profile 与 maintained budget，则必须按 mismatch policy
reject、路由到 `cpu_exact.reference`，或报告为 diagnostics-only。它不得把 maintained
capability projection 设为 true。

## 8. 未来测试计划

本 WP7-C 设计波次不需要 runtime code 或 pytest。若后续变更新增测试，应先作为
architecture-doc 或 registry-seed check，断言：

1. 每个 candidate 都有命名 promotion gate；
2. 每个 promotion gate 都引用 profile revision、budget revision、ownership/sync、
   event/snapshot evidence、mismatch/quarantine、replay、facade/core layering、
   WP5 mapping 与 acceptance review；
3. 当前所有 candidate capability projection 保持 false；
4. WP7-D request label 不能晋级 candidate；
5. 中英文 WP7-C 文档保持互链和章节顺序对齐。

建议未来 target：

```text
tests/architecture/test_wp7_promotion_evidence_gates_docs.py
```

该测试应只检查文档或未来 registry seed artifact。它不能依赖 runtime GPU helper
behavior、resident-state runtime code 或 shadow execution。

## 9. Acceptance Checklist

WP7-C 只有在以下条件满足时才可进入 integration：

1. `exact_gpu_promotion_gate`、`resident_state_promotion_gate` 与
   `shadow_compare_promotion_gate` 已文档化。
2. 每个 gate 都列出 profile registry revision、parity budget revision、
   ownership/sync、event order/snapshot evidence、mismatch/quarantine policy、
   replay evidence、facade/core layering evidence、WP5 harness mapping 与
   acceptance review requirement。
3. WP5 mapping 为 design、trace、boundary、information/belief 与
   replay/evidence 命名 mandatory 与 scope-conditioned tier。
4. WP7-D request label 被明确禁止绕过 promotion gate。
5. gate 不完整时 capability projection 保持 false。
6. 没有语言声称今天已有 maintained exact GPU、resident-state 或 shadow compare
   support。

## 10. 验证命令

```bash
git diff --check
rg -n "gpu_exact\\.unmaintained_candidate|resident_state\\.unmaintained_candidate|shadow_compare\\.unmaintained_candidate|promotion gate|WP5|replay|mismatch|quarantine|acceptance review|capability projection" docs/task/simulation_architecture/wp7_promotion_evidence_gates*20260519*.md
```
