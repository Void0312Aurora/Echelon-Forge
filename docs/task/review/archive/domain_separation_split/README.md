# Domain Separation Split

Status: `2026-06-10` archived accepted integration surface for the direct Air / Naval / Ground domain split; old domain-split compatibility entry points are retired rather than retained.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- [Review task area](../../README.md)
- [Domain Separation Audit 2026-06-09](../../domain_separation_audit_20260609.md)
- [Subproject creation standard](../../../../agent/rules/subproject_creation_standard.md)
- [Document authority map](../../../../agent/rules/document_authority_map.md)
- [Standards overview](../../../../standards/README.md)
- [Source layer map](../../../../manual/reference/src_layer_map.md)

## Purpose

This subproject turns the 2026-06-09 domain-separation audit into a durable
execution surface for the large split. The work is not gated on making one
domain a demonstration template first. It directly separates ownership across
`components/`, `systems/`, and `models/` so that Air, Naval, Ground, and common
surfaces stop sharing misleading generic files.

The subproject exists because the required work spans component schemas, ECS
systems, model routing, retired public paths, tests, and documentation. It must
therefore be split into finite clusters with explicit write sets and acceptance
gates.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Audit baseline | active input | [domain_separation_audit_20260609.md](../../domain_separation_audit_20260609.md) | Audit facts are an input, not implementation proof. |
| Air system ownership | pass | `src/systems/domains/air/`, `src/components/domains/air/platform/`; retired old physics/tuning paths | Runtime/tuning owners are split; generic physics/logistics read propulsion metrics through `components/physics/propulsion_readouts.h` rather than Air system helpers. |
| Combat damage components | pass | `src/components/combat/{common,air,naval,ground}/damage_*.h`; retired `src/components/combat/damage.h` | Consumers include owner headers directly; Ground damage remains an ownership shell, not a full runtime claim. |
| Combat damage systems | pass | `src/systems/combat/damage_system_{common,air,naval,ground}.h`; retired `src/systems/combat/damage_system.h` | Kernel registration calls common, air, naval, and ground system registrars directly; Ground damage system remains a no-op placeholder. |
| Weapon components | pass | `src/components/combat/{common,air,naval,ground}/weapon_*.h`; retired `src/components/combat/weapon.h` | Consumers include owner headers directly; Ground weapon remains an ownership shell. |
| Platform systems | pass | `src/systems/domains/naval/naval_logistics_system.h`, `src/systems/systems/logistics_system.h`, `src/components/physics/propulsion_readouts.h` | Naval underway resupply is extracted; Air propulsion readouts are no longer exposed through Air system helpers. |
| Model layer | pass | `src/models/weapons/detail/default_effects_domain_routing_detail.inc`, `src/models/domains/air/default_effects_air_domain.h`, `src/models/domains/naval/naval_sensor_maritime_adapter.h` | Effects and sensor ship-specific ownership now route through domain helpers; Naval/Ground effects remain placeholders. |
| Architecture guards | pass | `tests/architecture/structural_boundaries/test_structural_guardrails.py`, `tests/architecture/compatibility_quarantine/test_guard_enforcement.py` | Focused retired-path guard, full structural-boundary guard, and compatibility quarantine pass. |

## Scope

In scope:

- Retire `components/combat/damage.h` after moving common, air, naval, and
  ground-owned damage types into owner headers without claiming full new domain
  fidelity.
- Retire `src/systems/combat/damage_system.h` after moving common routing plus
  air/naval/ground update paths into owner system headers.
- Retire `components/combat/weapon.h` after moving common, air, naval, and
  ground-owned weapon types into owner headers.
- Move air-only runtime systems and tuning to `systems/domains/air` and
  `components/air`, then delete the old `physics` include paths once consumers
  use the owner paths directly.
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
- Removing unrelated historical compatibility surfaces outside this audit
  package.
- Archiving or rewriting unrelated review/task records.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze authority, non-goals, and task clusters. | Audit exists. | README, status, queue, and cluster plan exist. | pass |
| `P1 Components` | Split damage and weapon component ownership. | P0 files exist. | Common/air/naval/ground headers compile and old public aggregate headers are gone. | pass |
| `P2 Systems` | Split ECS system ownership. | P1 component surfaces compile. | Damage, air, naval logistics, and propulsion readout ownership are separated without old public wrappers. | pass |
| `P3 Models` | Route default effects and sensor behavior by domain ownership. | P1/P2 surfaces exist. | Generic model files stop depending directly on domain-only structs except through routers/adapters. | pass |
| `P4 Validation` | Add and run build, runtime, and architecture guards. | Implementation clusters land. | Focused checks pass; residual risks are recorded. | pass |
| `P5 Closure` | Sync docs, indexes, and retired-path notes. | P4 evidence exists. | Acceptance file is updated without overclaiming whole-domain maturity. | pass |

## Task Clusters

- Task cluster plan: [domain_separation_split_task_clusters_20260609.md](domain_separation_split_task_clusters_20260609.md)
- Current status: [domain_separation_split_current_status_20260609.md](domain_separation_split_current_status_20260609.md)
- Dispatch queue: [domain_separation_split_dispatch_queue_20260609.md](domain_separation_split_dispatch_queue_20260609.md)
- Acceptance gate: [domain_separation_split_acceptance_20260609.md](domain_separation_split_acceptance_20260609.md)

## Outputs And Evidence

- Domain-owned component headers under `src/components/domains/air/platform/`,
  `src/components/combat/{common,air,naval,ground}/` or the closest approved
  local convention.
- Domain-owned systems under `src/systems/domains/air/`, `src/systems/combat/`,
  `src/systems/domains/naval/`, and future `src/systems/domains/ground/` only where ownership is
  real.
- Domain routing/adapters under `src/models/domains/air/`, `src/models/domains/naval/`,
  `src/models/domains/ground/`, and common model helpers.
- Retired public include paths recorded in the guard and acceptance evidence.
- Architecture tests that fail when air/naval/ground-only types drift back into
  generic files.
- Focused build/runtime validation evidence.

## Acceptance Gate

This subproject can be marked accepted only when:

- The mixed `damage.h`, `damage_system.h`, and `weapon.h` ownership hotspots are
  retired as public entry points, and consumers use common/domain owner headers
  directly.
- Generic `systems/physics`, `systems/systems`, and `models/systems` files no
  longer own domain-only Air/Naval/Ground logic except through named adapters.
- Existing public behavior compiles and passes the focused runtime/architecture
  gates listed in the acceptance document.
- New Ground-owned shells are documented as ownership placeholders unless they
  have executable runtime and tests.
- Review, manual, and source README indexes reflect the new ownership without
  claiming full domain maturity.

## Follow-Up Boundaries

- Calibration and realism upgrades remain separate from ownership splitting.
- No domain-split compatibility wrapper is intentionally retained after this
  cleanup; unrelated legacy compatibility surfaces remain outside this package.
- Full Ground runtime maturity requires later movement/sensing/fires/damage
  implementation packages.
- If model routing reveals behavior drift, pause and record the first failing
  stage before adding new mechanics.

## Archive

This accepted subproject is archived under [review archive](../README.md).
Superseded local dispatch packets, worker reports, and closeout notes remain
tracked through [archive/README.md](archive/README.md) if future local records
are added.
