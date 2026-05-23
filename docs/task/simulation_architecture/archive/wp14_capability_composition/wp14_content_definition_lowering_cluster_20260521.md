# WP14-B Content Definition Lowering

Status: `2026-05-21` planned / first-wave implementation candidate. This slice
remains open/planned until B has implementation evidence; do not create an
acceptance review for WP14.

Language:

- English canonical: `wp14_content_definition_lowering_cluster_20260521.md`
- Chinese companion:
  [wp14_content_definition_lowering_cluster_20260521.zh.md](wp14_content_definition_lowering_cluster_20260521.zh.md)

Inputs:

- [WP14 capability composition](capability_composition_wp14_20260521.md)
- [WP14-A capability bundle contract](wp14_capability_bundle_contract_cluster_20260521.md)
- Current `src/content/unit_definition.h`
- Current `src/core/interfaces/unit_factory.h`
- Current `src/models/core/default_unit_factory.h`

## 1. Purpose

`WP14-B` defines the first deterministic lowering from a compatibility
`type_name` to a capability bundle template and resolved platform spawn plan.
It makes existing implicit factory composition visible without changing public
callers.

## 2. Scope

In scope:

- lower current `UnitDefinition` evidence into capability bundle templates;
- cover existing sensor refs, mounted sensors, loadouts, naval weapon systems,
  mobility hints, command/doctrine defaults, and survivability placeholders
  where present;
- return a resolved spawn plan that `WP14-C` can materialize;
- produce fail-closed reasons for unknown or incomplete templates.

Out of scope:

- changing Python public APIs;
- replacing every scenario/content JSON shape;
- editing kernel/facade setup bridges owned by `WP14-C`;
- adding new platform families or behavior models.

## 3. Candidate Implementation Seams

Inspect before editing:

- `src/content/unit_definition.h`
- `src/content/unit_catalog.*`
- `src/core/interfaces/unit_factory.h`
- `src/models/core/default_unit_factory.h`
- tests that spawn `Aircraft`, `F-16C_Block50`, ships, sensors, and naval
  weapon systems.

Preferred approach:

- keep `type_name` as the compatibility lookup key;
- add a small resolver/helper that returns capability bundle template evidence;
- do not require JSON migration in the first slice;
- preserve factory materialization behavior exactly.

Parallel rule:

- This slice may run beside `WP14-A` only if it does not edit shared contract
  names out from under A.
- It may not run in parallel with `WP14-C` on the same factory/kernel seam.
- Main-thread integration/gate ownership stays with `WP14-F`; subagents own
  only disjoint files or helper blocks.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Compatibility | Existing type names resolve without caller changes. |
| Explicit lowering | Sensor, launcher/loadout, command/doctrine, mobility, and survivability evidence is represented when current definitions contain it. |
| Determinism | Resolution order and evidence refs are stable. |
| Fail closed | Unknown or incomplete templates return inspectable rejection reasons. |

## 5. Acceptance Tests

Minimum tests:

- known aircraft and naval type names resolve to deterministic capability plans;
- sensor refs, mounted sensors, default loadouts, and naval weapon systems are
  represented as capability evidence where present;
- unknown type names reject with stable reasons;
- resolved-plan path preserves current factory materialization behavior.

Suggested commands:

```powershell
git diff --check
cmake --build build-local-win -j4
python -m pytest -q tests\architecture\test_wp14_content_definition_lowering.py
python -m pytest -q tests\architecture\test_wp14_platform_capability_contracts.py
python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn or world_setup"
```

Minimum acceptance gates for this slice:

- `git diff --check` passes with no new diff errors;
- `python -m pytest -q tests\architecture\test_wp14_content_definition_lowering.py` passes;
- `python -m pytest -q tests\architecture\test_wp14_platform_capability_contracts.py` passes;
- `python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn or world_setup"` passes;
- any supported `rg` audit used to justify new evidence coverage is recorded in the handoff;
- `spawn_unit(type_name)` behavior remains unchanged for existing callers.

## 6. Handoff Contract

Return:

- content/factory files touched;
- resolver/helper names;
- type names and capability families covered;
- tests added or updated;
- exact commands run and outcomes;
- blockers for `WP14-C` bridge or `WP14-E` materialization.
