# WP7-D Dispatch Sheet: Multi-Fidelity Entry Conditions

Status: `2026-05-19` planned WP7 architecture/design dispatch sheet.

Language:

- English canonical: `wp7_multifidelity_entry_conditions_cluster_20260519.md`
- Chinese companion:
  [wp7_multifidelity_entry_conditions_cluster_20260519.zh.md](wp7_multifidelity_entry_conditions_cluster_20260519.zh.md)
- Implementation-ready notes:
  [wp7_multifidelity_entry_conditions_notes_20260519.md](wp7_multifidelity_entry_conditions_notes_20260519.md)

Inputs:

- [WP7 backend capability materialization](backend_capability_materialization_wp7_20260519.md)
- [Temp-02 SCAL architecture vision review](../review/temp-02_review_20260519.md)
- [Temp-02 source note](../review/temp/temp-02.md)
- [architecture and performance research followup](../../plan/architecture/architecture_and_performance_research_followup.md)
- [WP6 backend profile policy](backend_profile_policy_wp6_20260519.md)
- [WP6-A backend profile registry](wp6_backend_profile_registry_20260519.md)
- [WP6-B parity budget registry](wp6_parity_budget_registry_20260519.md)
- [WP5 validation harness](validation_harness_wp5_20260519.md)

Naming boundary:

- Older source reviews used `WP7` as a historical alias for backend profile
  policy. That line is closed as `WP6`.
- This WP7-D sheet belongs to the new post-WP6 materialization line. It must
  not reopen the old alias or claim that backend profile policy is still WP7.

## 1. Purpose

WP7-D turns the deferred multi-fidelity idea into implementation-ready entry
conditions. It does not enable adaptive fidelity scheduling, reduced-fidelity
execution, learned model substitution, or new maintained backend support.

The task is to define how a future fidelity profile request cites:

1. the shared `P0-P10` semantic lifecycle,
2. accepted backend profile metadata,
3. parity or tolerance budget records,
4. model family and deferred `ModelProvider` boundaries,
5. WP5 validation gate evidence,
6. facade-visible evidence that proves what was requested and what was
   actually maintained.

## 2. Required Work Items

| Stream | Required output | Write scope | Budget |
|--------|-----------------|-------------|--------|
| `WP7-D1 Fidelity Profile Vocabulary` | Define `exact_evaluation`, `fast_training`, `sensor_heavy`, `weapon_effects_heavy`, `large_scale_swarm`, `single_platform_physics`, and similar labels as requests, not maintained support claims. | Docs. | High. |
| `WP7-D2 Backend Profile Binding Rule` | State how every fidelity profile request must bind backend profile ids, parity/tolerance budgets, model family scope, validation gate, and facade evidence. | Docs. | High. |
| `WP7-D3 ModelProvider Deferral Boundary` | Document which ModelProvider terms are vocabulary-only now and which require model interfaces, training provenance, and promotion evidence before use. | Docs. | Medium-high. |
| `WP7-D4 Adaptive Scheduling Entry Gate` | Define prerequisites before adaptive fidelity scheduling can enter active implementation work. | Docs and future test plan. | High. |

## 3. Fidelity Profile Vocabulary Rules

A fidelity profile is not a backend profile. A fidelity profile is a compilation
or configuration request that selects accepted model families, backend profiles,
comparison budgets, and validation gates for a scenario or experiment.

The label alone is never a support claim:

| Fidelity profile request | Request meaning | Forbidden implication |
|--------------------------|-----------------|-----------------------|
| `exact_evaluation` | Use maintained exact truth for evaluation and comparison. | Does not imply exact GPU or resident-state support. |
| `fast_training` | Prefer throughput-oriented paths for training experiments. | Does not make approximate or diagnostics output exact truth. |
| `sensor_heavy` | Emphasize sensor, track, data-link, observation, and information-state workloads. | Does not bypass observation envelope, visibility, or belief boundaries. |
| `weapon_effects_heavy` | Emphasize launch, munition, effect, damage, reward, and termination evidence. | Does not weaken event ancestry or damage/effect trace requirements. |
| `large_scale_swarm` | Request scale-oriented execution for many platforms or agents. | Does not weaken event order, snapshot provenance, or facade evidence. |
| `single_platform_physics` | Request focused physics/control evaluation for one platform or a narrow platform family. | Does not certify high-fidelity physics beyond the named model family and budget. |

## 4. Binding Contract

Every fidelity profile request must bind all of the following before it can be
accepted by implementation planning:

1. `backend_profile_id`: from the accepted WP6/WP7 registry line; do not invent
   ids in WP7-D.
2. `parity_budget_ref` or explicit tolerance budget: from the WP6 parity budget
   registry or a future accepted registry revision.
3. `model_family_scope`: the lifecycle stages and domain model families covered
   by the request.
4. `validation_gate`: the WP5 evidence tier or future promotion gate that must
   pass before the request is trusted.
5. `facade_evidence`: request id, backend profile id, budget id/version,
   comparison reference, snapshot or barrier provenance, mismatch policy, and
   diagnostics label.

The first accepted exact baseline remains `cpu_exact.reference`. GPU helpers,
exact GPU candidates, resident-state candidates, and shadow-compare candidates
stay diagnostics-only or unmaintained until their own profile metadata, budget,
ownership/sync policy, and WP5 evidence are accepted.

## 5. ModelProvider Deferral Boundary

`ModelProvider` is vocabulary-only in WP7-D. The following terms may be used to
describe future architecture intent: analytical provider, table provider,
surrogate provider, learned provider, hybrid provider, and diagnostics provider.

They must not become runtime interfaces or maintained claims until a later work
package defines:

1. provider interface and lifecycle ownership,
2. model artifact identity and versioning,
3. training or calibration provenance,
4. input/output contract and information-state boundary,
5. parity or tolerance budget,
6. WP5-compatible validation and replay evidence,
7. facade-visible evidence that separates maintained truth from diagnostics.

## 6. Adaptive Scheduling Entry Gate

Adaptive fidelity scheduling remains out of scope for active WP7-D
implementation. It may enter a future task only after all prerequisites below
exist:

1. state shard versioning that can identify every shard affected by a fidelity
   switch,
2. replay evidence proving deterministic comparison across switch boundaries,
3. mismatch policy for exact, tolerated, candidate, and diagnostics results,
4. scheduling contract that names allowed switch points, barriers, and rollback
   behavior,
5. rollback or quarantine procedure for mismatched or untrusted outputs,
6. facade evidence that records requested fidelity, selected backend profile,
   selected model family, budget version, and switch ancestry.

## 7. Non-Goals

- Do not implement adaptive fidelity scheduling.
- Do not introduce learned model providers.
- Do not promote approximate outputs to exact truth.
- Do not create a separate reduced-fidelity semantic lifecycle.
- Do not bypass backend profile or parity budget registries.
- Do not add maintained exact GPU, resident-state, shadow, or multi-fidelity
  capability claims.

## 8. Acceptance Gates

This cluster is accepted when:

1. Fidelity profile labels are defined as requests, not support claims.
2. Every example fidelity profile states which backend profile, parity or
   tolerance budget, model family, validation gate, and facade evidence would be
   required before use.
3. `ModelProvider` work is clearly deferred and scoped.
4. Adaptive scheduling prerequisites are named and kept outside current WP7
   implementation until gates exist.
5. The cluster cites WP6 policy/registries and WP5 evidence requirements.
6. English and Chinese documents link to each other and keep the same section
   shape.

## 9. Validation Commands

```bash
git diff --check
rg -n "fidelity profile|exact_evaluation|fast_training|sensor_heavy|weapon_effects_heavy|large_scale_swarm|ModelProvider|adaptive|validation gate" docs/task/simulation_architecture/wp7_multifidelity*20260519*.md
```
