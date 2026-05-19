# WP4-B + WP4-C Dispatch Sheet: Engagement, Step, And Lifecycle Alignment

Status: `2026-05-19` dispatch sheet; starts after WP4-A publishes the initial
surface vocabulary.

Language:

- English canonical: `wp4_engagement_step_cluster_20260519.md`
- Chinese companion: [wp4_engagement_step_cluster_20260519.zh.md](wp4_engagement_step_cluster_20260519.zh.md)

Inputs:

- [WP4 facade alignment](facade_alignment_wp4_20260519.md)
- [WP4-A surface inventory cluster](wp4_surface_inventory_cluster_20260519.md)
- [WP3 engagement pilot acceptance review](../review/wp3_engagement_pilot_acceptance_review_20260519.md)
- [WP2.5 scheduler semantics freeze](scheduler_semantics_wp25_20260519.md)
- Current `src/runtime/facade/*`, `tests/runtime/facade/`, and
  `tests/runtime/engagement/`

## 1. Purpose

This sheet groups the WP4 implementation-facing facade work that is closest to
the accepted WP3 pilot:

- `WP4-B Engagement Alignment`
- `WP4-C Step And Lifecycle Alignment`

The cluster should stabilize maintained facade outputs without inventing new
engagement, guidance, effects, damage, reward, or termination semantics.

## 2. Dispatch Deliverables

| Stream | Required output | Primary write scope | Reasoning budget |
|--------|-----------------|---------------------|------------------|
| `WP4-B1 Engagement Producer Coverage` | Document and, where needed, test which event families populate engagement export slots. | `docs/task/simulation_architecture`, `tests/runtime/engagement/`. | Medium. |
| `WP4-B2 World-Safe Engagement Export` | Verify multi-world export preserves or retags `world_index` consistently and avoids raw runtime as maintained path. | `src/runtime/facade/runtime_facade.cpp`, engagement tests. | Medium. |
| `WP4-B3 Diagnostics Piggyback Boundary` | Ensure diagnostics piggybacking on engagement export is explicit until a dedicated diagnostics surface exists. | facade docs/tests; avoid broad runtime changes. | Medium-high. |
| `WP4-C1 Step Result Ownership` | Align execution-step result shape with reward, termination, observation snapshot, and episode phase ownership. | `src/runtime/facade/*`, `tests/runtime/facade/`. | High if DTO shape changes. |
| `WP4-C2 Reward Fact/Shaping Attribution` | Document or test fact vs shaping attribution on maintained step results. | facade docs/tests; Python adapter evidence if needed. | High. |
| `WP4-C3 Termination/Truncation Attribution` | Document or test reason-source separation and mirrored phase behavior. | facade docs/tests; adapter tests if needed. | Medium-high. |

## 3. Write-Scope Rules

1. This cluster MAY edit `src/runtime/facade/runtime_facade.cpp` and facade
   tests.
2. This cluster SHOULD avoid `src/interfaces/python/bindings_runtime.cpp`
   unless WP4-E has agreed signatures are stable.
3. This cluster MUST NOT edit policy/orchestration adapters except for narrow
   evidence notes or tests that do not conflict with WP4-D.
4. This cluster MUST NOT edit `simulation_kernel_weapon_api.cpp` unless a
   compatibility adapter cannot be expressed any other way; such work must be
   serialized through the integration owner.
5. If WP4-A has not frozen a surface name, this cluster SHOULD write a
   documentation note or skipped/pending test rather than inventing a new name.

## 4. Engagement Alignment Rules

WP4-B MUST preserve these accepted WP3 properties:

1. Engagement export is facade-first.
2. Multi-world export remains world-safe.
3. Recent-event retagging must not create ambiguous `world_index` ancestry.
4. Event-family coverage must be explicit for track, launch, effects, damage,
   and diagnostics slots.
5. Empty or placeholder slots are allowed only when documented as
   compatibility placeholders or deferred producers.
6. Diagnostics data that rides inside engagement export MUST be labeled as
   engagement evidence or diagnostics piggyback, not a full diagnostics
   logging framework.

## 5. Step And Lifecycle Alignment Rules

WP4-C MUST preserve these architecture boundaries:

1. `ExecutionBatchStepResult` reports step result state through facade-shaped
   data, not hidden mirrors.
2. Reward output distinguishes simulation facts from shaping/composition where
   current data allows it.
3. `terminated` and `truncated` remain separate, with reason-source attribution
   when available.
4. Episode phase authority remains compiled/facade-owned; Gymnasium or Python
   adapters mirror and request transitions only.
5. Observation snapshots returned by step results must name source time or
   snapshot provenance when current DTOs can carry it.

## 6. Validation Targets

Recommended focused commands:

```powershell
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\engagement\test_facade_engagement_export.py tests\runtime\facade\test_runtime_facade.py
```

If local artifacts are stale, rebuild `ef_core` and `ef_py` before running the
focused tests.

## 7. Exit Criteria

This cluster exits when:

1. Engagement facade export has explicit producer coverage for current slots.
2. Multi-world engagement export remains world-safe.
3. Step results document reward, termination, truncation, observation, and
   episode lifecycle ownership.
4. Diagnostics piggybacking is explicit and ready for WP5 evidence validation.
5. Any unimplemented surface is marked deferred or pending WP4-A/WP4-E, not
   silently hidden behind raw runtime access.
