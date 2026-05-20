# WP14-E Capability Effects Materialization

Status: `2026-05-21` planned / second-wave materialization candidate. This
slice remains open/planned while B/C/D are not yet mergeable.

Language:

- English canonical: `wp14_capability_effects_materialization_cluster_20260521.md`
- Chinese companion:
  [wp14_capability_effects_materialization_cluster_20260521.zh.md](wp14_capability_effects_materialization_cluster_20260521.zh.md)

Inputs:

- [WP14 capability composition](capability_composition_wp14_20260521.md)
- [WP14-B content definition lowering](wp14_content_definition_lowering_cluster_20260521.md)
- [WP14-C spawn resolution bridge](wp14_spawn_resolution_bridge_cluster_20260521.md)
- Current `src/models/core/default_unit_factory.h`
- Current `src/components/*`

## 1. Purpose

`WP14-E` binds capability families to existing ECS/component materialization
evidence. It should explain what the factory already constructs and why an
unsupported capability effect is rejected.

## 2. Scope

In scope:

- mobility, sensing, communication, launcher, survivability, command, and
  doctrine materialization evidence where current components/factory logic
  already support it;
- unsupported-effect rejection reasons;
- tests proving capability effects do not change current platform behavior.

Out of scope:

- adding new tactical behavior;
- tuning weapons, sensors, flight dynamics, or mission logic;
- creating new platform families;
- changing backend/fidelity capability projection.

## 3. Candidate Implementation Seams

Inspect before editing:

- `src/models/core/default_unit_factory.h`
- `src/content/unit_definition.h`
- relevant `src/components/*`
- existing air/naval engagement and mission runtime tests.

Preferred approach:

- map capability family evidence to existing component creation paths;
- add diagnostics or helper evidence before changing materialization behavior;
- reject unsupported effect families rather than silently ignoring them;
- preserve existing platform fixtures.

Parallel rule:

- `WP14-E` may run beside `WP14-D` only when write scopes stay disjoint.
- It should wait for B/C semantics to stabilize before claiming coverage.
- Main-thread integration/gate stays in `WP14-F`.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Evidence first | Materialization evidence names existing component/factory effects. |
| No behavior drift | Existing platform behavior remains unchanged unless separately scoped. |
| Unsupported effects | Unsupported or undeclared capability effects fail closed. |
| Family separation | Capability families do not collapse into one flat type-name string. |

## 5. Acceptance Tests

Minimum tests:

- capability family evidence matches existing materialized components for
  representative air and naval fixtures;
- unsupported capability effects reject with stable reasons;
- existing engagement/facade export tests still pass;
- no new platform behavior is required for acceptance.

Suggested commands:

```powershell
git diff --check
cmake --build build-local-win -j4
python -m pytest -q tests\architecture\test_wp14_capability_effects_materialization.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\engagement\test_facade_engagement_export.py
python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn"
```

Minimum acceptance gates for this slice:

- `git diff --check` passes;
- `python -m pytest -q tests\architecture\test_wp14_capability_effects_materialization.py` passes;
- `.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\engagement\test_facade_engagement_export.py` passes;
- `python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn"` passes;
- the evidence stays on existing component/factory behavior only;
- no new tactical behavior, platform family, or backend semantics is introduced.

## 6. Handoff Contract

Return:

- factory/component files touched;
- capability families covered;
- unsupported-effect rejection reasons;
- compatibility tests run;
- exact commands and outcomes;
- residuals for future platform-family expansion.
