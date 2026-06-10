# WP14-A Capability Bundle Contract

Status: `2026-05-21` planned / first-wave dispatch candidate.

Language:

- English canonical: `wp14_capability_bundle_contract_cluster_20260521.md`
- Chinese companion:
  [wp14_capability_bundle_contract_cluster_20260521.zh.md](wp14_capability_bundle_contract_cluster_20260521.zh.md)

Inputs:

- [WP14 capability composition](capability_composition_wp14_20260521.md)
- [Simulation system architecture design](../../../plan/architecture/simulation_system_architecture_design.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.md)
- Current `src/runtime/contracts/*`
- Current `src/runtime/facade/runtime_facade_types.h`

## 1. Purpose

`WP14-A` creates the platform capability vocabulary that later streams consume.
It must define `Capability`, `CapabilityBundle`, and resolved-plan evidence as
platform setup concepts, not as backend/fidelity `RuntimeCapabilities`.

## 2. Scope

In scope:

- capability family vocabulary for mobility, sensing, communication, launching,
  survivability, command, and doctrine;
- typed bundle/template/request/evidence structs or schema;
- naming separation between platform capabilities and backend runtime
  capabilities;
- architecture tests proving required fields and family labels.

Out of scope:

- content/factory lowering implementation owned by `WP14-B`;
- kernel/world-batch bridge owned by `WP14-C`;
- public `spawn_platform` API promotion;
- backend/fidelity capability projection.

## 3. Candidate Implementation Seams

Inspect before editing:

- `src/runtime/contracts/world_batch_contracts.h`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/contracts/backend_profile_contracts.h`
- `src/runtime/contracts/fidelity_profile_contracts.h`
- `tests/architecture/runtime_facade`

Preferred approach:

- add a new platform-focused contract header rather than extending
  `RuntimeCapabilities`;
- keep capability family labels stable and string-testable;
- include enough evidence fields for B/C to report how a `type_name` resolved;
- reject blank family/id/evidence fields in focused tests.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Naming separation | Platform capability vocabulary does not reuse backend/fidelity capability projection fields. |
| Required fields | Capability entries carry family, id, source/template, materialization target, and evidence refs. |
| Deterministic shape | Bundle ordering and resolved-plan evidence are stable enough for tests. |
| Fail-closed validation | Missing family, id, or evidence rejects the contract fixture. |

## 5. Acceptance Tests

Minimum tests:

- architecture test enumerates supported capability families;
- contract validation rejects missing family/id/source/evidence fields;
- test asserts no `RuntimeCapabilities` platform-family fields were added;
- bundle/resolved-plan fixture has deterministic ordering and evidence refs.

Suggested commands:

```powershell
git diff --check
cmake --build build-local-win -j4
python -m pytest -q tests\architecture\test_wp14_capability_bundle_contracts.py
python -m pytest -q tests\architecture\test_runtime_facade_layering.py
```

## 6. Handoff Contract

Return:

- contract files touched;
- capability family vocabulary;
- validation helper names;
- tests added or updated;
- exact commands run and outcomes;
- blockers for `WP14-B`, `WP14-C`, or `WP14-D`.
