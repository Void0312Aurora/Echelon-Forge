# Domain Separation Split

Status: `2026-06-10` active integration surface for the direct Air / Naval / Ground domain split; implementation clusters have landed, but overall subproject is not accepted.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- [Review task area](../README.md)
- [Domain Separation Audit 2026-06-09](../domain_separation_audit_20260609.md)
- [Subproject creation standard](../../../agent/rules/subproject_creation_standard.md)
- [Document authority map](../../../agent/rules/document_authority_map.md)
- [Standards overview](../../../standards/README.md)
- [Source layer map](../../../manual/src_layer_map.md)

## Purpose

This subproject turns the 2026-06-09 domain-separation audit into a durable
execution surface for the large split. The work is not gated on making one
domain a demonstration template first. It directly separates ownership across
`components/`, `systems/`, and `models/` so that Air, Naval, Ground, and common
surfaces stop sharing misleading generic files.

The subproject exists because the required work spans component schemas, ECS
systems, model routing, compatibility wrappers, tests, and documentation. It
must therefore be split into finite clusters with explicit write sets and
acceptance gates.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Audit baseline | active input | [domain_separation_audit_20260609.md](../domain_separation_audit_20260609.md) | Audit facts are an input, not implementation proof. |
| Air system ownership | partial candidate | `src/systems/air/`, `src/components/air/` in current worktree | Directory ownership does not finish combat/model split. |
| Combat damage components | held | `src/components/combat/damage.h` | Air/Naval/Common remain mixed; Ground damage is absent. |
| Combat damage systems | held | `src/systems/combat/damage_system.h` | Air/Naval/Common ECS logic remains mixed. |
| Weapon components | held | `src/components/combat/weapon.h` | Naval weapon types remain in the generic file; Ground is absent. |
| Platform systems | partial | `src/systems/naval/naval_logistics_system.h`, `src/systems/systems/logistics_system.h` | Naval underway resupply is extracted; Air propulsion helper residual still needs adapter or retention decision. |
| Model layer | pass | `src/models/weapons/detail/default_effects_domain_routing_detail.inc`, `src/models/air/default_effects_air_domain.h`, `src/models/naval/naval_sensor_maritime_adapter.h` | Effects and sensor ship-specific ownership now route through domain helpers; Naval/Ground effects remain placeholders. |
| Architecture guards | partial | `tests/architecture/structural_boundaries/test_structural_guardrails.py` | Focused domain split guard passes; broader existing architecture gates still fail on unrelated baselines. |

## Scope

In scope:

- Split `components/combat/damage.h` into common, air, naval, and ground-owned
  headers without claiming full new domain fidelity.
- Split `src/systems/combat/damage_system.h` into common routing plus
  air/naval/ground domain-owned update paths.
- Split `components/combat/weapon.h` into common, air, naval, and ground-owned
  headers.
- Move air-only runtime systems and tuning to `systems/air` and
  `components/air`, then reduce old `physics` paths to declared compatibility
  wrappers.
- Extract naval-specific logistics and sensor dependencies out of generic
  platform/model files.
- Introduce model-layer domain routing for effects/sensor behavior with explicit
  common, air, naval, and ground ownership boundaries.
- Add architecture guards and focused runtime/build validation for the split.

Out of scope:

- Treating Naval as a required exemplar domain before the rest of the split.
- Claiming complete Ground movement, sensing, fires, or damage runtime merely
  because owner directories or skeletal structs exist.
- Rebalancing weapon lethality, flight dynamics, naval survivability, or training
  behavior unless required to preserve existing behavior through the split.
- Removing public compatibility wrappers before their replacement includes and
  tests are in place.
- Archiving or rewriting unrelated review/task records.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze authority, non-goals, and task clusters. | Audit exists. | README, status, queue, and cluster plan exist. | pass |
| `P1 Components` | Split damage and weapon component ownership. | P0 files exist. | Common/air/naval/ground headers compile with compatibility wrappers. | pass |
| `P2 Systems` | Split ECS system ownership. | P1 component surfaces compile. | Damage, air, naval logistics, and generic system registration are separated. | partial |
| `P3 Models` | Route default effects and sensor behavior by domain ownership. | P1/P2 surfaces exist. | Generic model files stop depending directly on domain-only structs except through routers/adapters. | pass |
| `P4 Validation` | Add and run build, runtime, and architecture guards. | Implementation clusters land. | Focused checks pass; residual risks are recorded. | partial |
| `P5 Closure` | Sync docs, indexes, and compatibility-deprecation notes. | P4 evidence exists. | Acceptance file is updated without overclaiming whole-domain maturity. | partial |

## Task Clusters

- Task cluster plan: [domain_separation_split_task_clusters_20260609.md](domain_separation_split_task_clusters_20260609.md)
- Current status: [domain_separation_split_current_status_20260609.md](domain_separation_split_current_status_20260609.md)
- Dispatch queue: [domain_separation_split_dispatch_queue_20260609.md](domain_separation_split_dispatch_queue_20260609.md)
- Acceptance gate: [domain_separation_split_acceptance_20260609.md](domain_separation_split_acceptance_20260609.md)

## Outputs And Evidence

- Domain-owned component headers under `src/components/air/`,
  `src/components/combat/{common,air,naval,ground}/` or the closest approved
  local convention.
- Domain-owned systems under `src/systems/air/`, `src/systems/combat/`,
  `src/systems/naval/`, and future `src/systems/ground/` only where ownership is
  real.
- Domain routing/adapters under `src/models/air/`, `src/models/naval/`,
  `src/models/ground/`, and common model helpers.
- Compatibility wrappers with explicit migration notes.
- Architecture tests that fail when air/naval/ground-only types drift back into
  generic files.
- Focused build/runtime validation evidence.

## Acceptance Gate

This subproject can be marked accepted only when:

- The mixed `damage.h`, `damage_system.h`, and `weapon.h` ownership hotspots are
  split or reduced to explicitly common compatibility wrappers.
- Generic `systems/physics`, `systems/systems`, and `models/systems` files no
  longer own domain-only Air/Naval/Ground logic except through named adapters.
- Existing public behavior compiles and passes the focused runtime/architecture
  gates listed in the acceptance document.
- New Ground-owned shells are documented as ownership placeholders unless they
  have executable runtime and tests.
- Review, manual, and source README indexes reflect the new ownership without
  claiming full domain maturity.

## Residuals And Next Steps

- Calibration and realism upgrades remain separate from ownership splitting.
- Any compatibility wrapper left after acceptance must have a documented
  deprecation or retention reason.
- Full Ground runtime maturity requires later movement/sensing/fires/damage
  implementation packages.
- If model routing reveals behavior drift, pause and record the first failing
  stage before adding new mechanics.

## Archive

Superseded dispatch packets, worker reports, and closeout notes move to
[archive/README.md](archive/README.md) only after a replacement current-status
or acceptance surface exists.
