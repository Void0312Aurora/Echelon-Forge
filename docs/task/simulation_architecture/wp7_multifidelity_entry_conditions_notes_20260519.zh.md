# WP7-D 实施说明：Multi-Fidelity Entry Conditions

状态：`2026-05-19`，WP7-D 第一波设计细化的可实施说明。

语言版本：

- 英文主文：[wp7_multifidelity_entry_conditions_notes_20260519.md](wp7_multifidelity_entry_conditions_notes_20260519.md)
- 中文辅文：`wp7_multifidelity_entry_conditions_notes_20260519.zh.md`
- 分发单：
  [wp7_multifidelity_entry_conditions_cluster_20260519.zh.md](wp7_multifidelity_entry_conditions_cluster_20260519.zh.md)

## 1. 操作规则

WP7-D 只定义 request vocabulary 与 entry gate。fidelity profile request 可以请求某种执行形态，
但 maintained support 仍然只能来自：

1. 已验收的 backend profile metadata；
2. 已验收的 parity 或 tolerance budget；
3. 已验收的 validation gate evidence；
4. facade-visible projection，并且该 projection 必须保守报告 declared support。

因此 request label 必须作为 requested intent 存储和报告，而不是 capability truth。如果后续
runtime 不能用维护中 metadata 满足某个请求，结果必须根据 mismatch policy 被拒绝、降级为
diagnostics-only，或路由到维护中 baseline。

## 2. Request Vocabulary

| Request label | 允许用途 | 必需绑定 | 最小 facade evidence |
|---------------|----------|----------|----------------------|
| `exact_evaluation` | evaluation、benchmark、regression comparison、promotion review。 | `backend_profile_id=cpu_exact.reference`，除非后续 exact profile 被晋级；`parity_budget.cpu_exact.reference.v1`；exact model family scope；WP5 replay/evidence gate。 | request id、selected exact profile、budget id/version、comparison reference、snapshot version、event-order evidence、validation gate result。 |
| `fast_training` | training throughput experiment、curriculum sweep、diagnostics run。 | evaluation 必须有维护中 exact baseline；任何 approximate 或 diagnostics path 都必须携带 tolerance 或 diagnostics budget，且不得标记为 truth。 | request id、selected training profile、exact evaluation reference、tolerance/diagnostics label、mismatch policy、quarantine status。 |
| `sensor_heavy` | sensor scan、track、shared picture、observation、belief 与 information-state 压力场景。 | 覆盖 observation/track scope 的 backend profile；observation envelope budget；WP5 information/belief 与 replay gate。 | visibility label、source snapshot version、observation schema、track/observation provenance、selected backend profile、validation gate。 |
| `weapon_effects_heavy` | launch、munition、effect、damage、reward、termination 与 trace ancestry 压力场景。 | 覆盖 engagement/effect scope 的 backend profile；event-order 与 diagnostics trace budget；WP5 trace/replay gate。 | launch/event ancestry、damage/effect source ids、reward/termination provenance、mismatch domain、validation gate。 |
| `large_scale_swarm` | 面向大量平台或大量智能体的规模化运行。 | 覆盖 swarm 所用 scheduler、observation、engagement 与 snapshot scope 的 backend profile 与 budget。 | agent/platform count、shard-version map、barrier ids、selected profile、budget id/version、mismatch policy。 |
| `single_platform_physics` | 面向命名平台族的聚焦 physics/control 分析。 | 覆盖 physics/control scope 的 backend profile；exact 或显式 numeric tolerance budget；WP5 design/replay gate。 | platform/model family id、physics state shard versions、comparator/tolerance fields、selected profile、validation gate。 |

## 3. Binding Record Shape

未来实现应把 fidelity request 视为类似以下记录：

```yaml
fidelity_request_id: stable-request-id
fidelity_profile_request: exact_evaluation
backend_profile_id: cpu_exact.reference
parity_budget_ref: parity_budget.cpu_exact.reference.v1
model_family_scope:
  lifecycle_stages: [P0, P1, P2, P3, P4, P5, P6, P7, P8, P9, P10]
  families: [physics, sensor, engagement, observation]
validation_gate:
  wp5_tiers: [trace_conformance, replay_evidence_conformance]
facade_evidence:
  required_fields:
    - fidelity_request_id
    - fidelity_profile_request
    - selected_backend_profile_id
    - selected_budget_id
    - selected_budget_version
    - comparison_reference
    - source_snapshot_version
    - resulting_snapshot_version
    - sync_barrier_id
    - mismatch_policy
    - diagnostics_label
```

这个形状是描述性说明，不是 runtime schema 承诺。WP7-A 在 registry materialization
期间可以调整字段名，但必须保留相同的语义义务。

## 4. Backend、Budget、Model、Gate、Evidence 矩阵

| Request label | Backend profile 规则 | Parity/tolerance budget 规则 | Model family 规则 | Validation gate 规则 | Facade-visible evidence 规则 |
|---------------|----------------------|------------------------------|-------------------|----------------------|------------------------------|
| `exact_evaluation` | 在另一个 exact profile 晋级前，使用 `cpu_exact.reference`。 | 使用 `parity_budget.cpu_exact.reference.v1` 的 exact domains；除非未来 exact profile 明确声明，否则没有 numeric tolerance。 | 影响维护中输出的所有 family 必须位于 exact lifecycle path 内。 | WP5 replay/evidence，加上相关 trace、boundary 与 information gate。 | 必须暴露 exact profile 和 budget id、event order、snapshot identity 与 structured diagnostics ancestry。 |
| `fast_training` | evaluation 使用维护中 exact；speed path 只能在标记后使用 diagnostics/candidate path。 | approximate output 需要显式 tolerance；diagnostics output 使用 report-only budget。 | training model family 必须说明它是否输入 policy、reward 或 diagnostics。 | evaluation 使用 exact gate；training-only diagnostics 可使用 report-only gate。 | 必须暴露 training output 不是 exact truth，并命名 exact comparison reference。 |
| `sensor_heavy` | 必须绑定 observation/track backend profile scope；resident-state candidate 仍未维护。 | observation envelope 必须 exact；payload tolerance 必须按字段声明。 | sensor、track、data-link、observation、belief family 必须命名 visibility boundary。 | WP5 information/belief leakage 与 replay gate。 | 必须暴露 visibility label、source snapshot、observation schema 与 diagnostics label。 |
| `weapon_effects_heavy` | 必须绑定 engagement/effect backend profile scope。 | event order 与 diagnostics trace ancestry 保持 exact；numeric effect tolerance 必须命名。 | weapon、effect、damage、reward、termination family 必须命名 source event ancestry。 | WP5 trace conformance 与 replay gate。 | 必须暴露 launch id、munition/effect id、damage ancestry、reward/termination provenance。 |
| `large_scale_swarm` | 必须绑定 scheduler、observation、engagement scope 中使用的每个 backend profile。 | scale 不会在没有命名 budget 时放松 event order 或 snapshot identity。 | agent/platform model family 必须标明读写哪些 state shard。 | WP5 design、boundary、trace 与 replay gate。 | 必须暴露 shard-version map、barrier sequence、selected profile 与 quarantine status。 |
| `single_platform_physics` | 必须绑定 physics/control backend profile scope。 | numeric tolerance 需要 field family、comparator、threshold 与 reference。 | platform family、control law 与 physics model family 必须命名。 | WP5 design/replay gate，加上未来可能的 physics model certification gate。 | 必须暴露 platform id、model family id、state shard versions、comparator 与 validation gate。 |

## 5. ModelProvider 边界

WP7-D 可以使用以下 vocabulary：

| Term | WP7-D 状态 | maintained use 前置条件 |
|------|------------|--------------------------|
| Analytical provider | 仅 vocabulary。 | interface、parameters、domain validity、parity budget、replay evidence。 |
| Table provider | 仅 vocabulary。 | table identity、version、interpolation rule、provenance、tolerance budget。 |
| Surrogate provider | 仅 vocabulary。 | training/calibration data、domain limits、uncertainty reporting、tolerance budget。 |
| Learned provider | 仅 vocabulary。 | training pipeline、artifact identity、evaluation split、safety envelope、validation evidence。 |
| Hybrid provider | 仅 vocabulary。 | ownership split、switch policy、mismatch policy、rollback/quarantine evidence。 |
| Diagnostics provider | 仅 vocabulary。 | diagnostics labeling、non-interference rule、export-only evidence。 |

任何 `ModelProvider` 术语都不得暗示 maintained support，除非 provider 已绑定 backend metadata、
model artifact identity、budget、validation gate 与 facade evidence。

## 6. Adaptive Fidelity Scheduling 进入门槛

adaptive scheduling 不能作为 runtime work 启动，直到未来任务能够证明：

1. state shard versioning 覆盖每个可切换 shard，包括 host 与可能的 backend-resident ownership。
2. replay evidence 可以用 exact barrier identity 重建 pre-switch、switch 与 post-switch snapshot。
3. mismatch policy 按 profile class 定义 `fail`、`report_only`、`quarantine` 与 `rollback` 结果。
4. scheduling contract 命名允许的 switch point、禁止切换的 lifecycle stage、barrier requirement，以及每个点的 committed state owner。
5. rollback/quarantine 可以防止 candidate 或 approximate output 污染 maintained state。
6. facade evidence 记录 requested fidelity、selected backend profile、model family、budget version、switch reason 与 switch ancestry。

在六项全部存在前，`adaptive` 与 `adaptive fidelity scheduling` 都只是计划术语。

## 7. Future Test Hooks

第一波设计不要求 runtime test。如果 WP7-D 后续新增 architecture test，应优先做 doc/schema
检查，断言：

1. request label 不会被 projection 成 maintained capability flag；
2. 每个 request record 都有 backend、budget、model、validation gate 与 facade evidence 字段；
3. `ModelProvider` entry 在缺少 model/training evidence 时保持 deferred；
4. adaptive scheduling entry 在缺少 state shard versioning、replay evidence、mismatch policy、
   scheduling contract 与 quarantine rule 时 fail closed。

## 8. 未解决风险

1. WP7-A 可能重命名 registry field shape；WP7-D 应适配命名，但不得放松绑定义务。
2. 未来 approximate profile 必须先拥有显式 tolerance budget，才能用于 diagnostics 或 training-only
   experiment 之外的场景。
3. learned 或 surrogate provider 容易混淆 truth 与 diagnostics；晋级前必须具备 facade-visible labeling。
