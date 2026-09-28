# Ground Damage Effects Route Repair Task Clusters

Status: `2026-09-22` finite task-cluster plan for
[Ground Damage Effects Route Repair README.md](README.md).

Parent subproject:
[Ground Damage Effects Route Repair](README.md).

## Boundary Decision

This package repairs one measured defect and nothing else: the effects translation unit
resolved a duplicate component id, so the ground damage effects route found no state and
fell through to the placeholder. It may change **where** the component id is resolved and
**how** it reaches the effects route. It may not change the component count, add a registry
row, introduce a name-based lookup from a model translation unit, or claim any ground
capability.

Two decisions are fixed here because they are the ones a later reader would reopen:

1. **Resolution happens in the composition path**, in the effects-provider construction
   lambda, on the world-scoped model instance. The authority is
   [modularization_plan.md](../../../../../architecture/work/issues/modularization_plan.md)
   — models do not own lifecycle, the engine owns composition — read with
   [runtime_composition_baseline.md](../../../../../architecture/standards/runtime_composition_baseline.md):
   the owner-derived registry owns component membership.
2. **No new component carries the id.** A world-scoped singleton would move the component
   census from 85 to 86 and force regeneration of the registry constant, both generated
   manifests, four fixtures and the closure hashes — the exact chain the
   [registry-sync slice](../../../../../architecture/work/issues/runtime_composition_registry_sync.md)
   has just finished repairing.

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `G1-A` | main thread | n/a | Freeze the §10 declaration set and the exact write set before any code moves. | this `README.md`, this cluster document | no code; no test marker change; no capability claim | `cmo_python tools/maintenance/document_link_audit.py` | Both documents name every write set, every validation command, and the declaration items the change touches | first; nothing may run before it | 1 | pass |
| `G1-B` | main thread | n/a | Resolve `GroundPlatformDamageState` once per world in the effects-provider construction lambda and carry it on the world-scoped model instance. | `src/runtime/providers/default_simulation_provider_catalog.cpp`, `src/core/interfaces/effects_model.h`, `src/models/weapons/default_effects_model.cpp` | no new registry row; no new component; no setter; no change to `make_default_effects_model`'s kernel-source exclusion | `cmo_python -m pytest -q tests/architecture/composition -p no:cacheprovider`; the component census still reads `85 / 2 / 34` | The id is resolved after component registration, once per world, and the census is unmoved | after `G1-A`; serial with `G1-C` | 2 | pass |
| `G1-C` | main thread | n/a | Consume the passed id in the routing detail and the ground domain header, and delete the diagnostic `id<T>()` call. | `src/models/weapons/detail/default_effects_domain_routing_detail.h`, `src/models/domains/ground/default_effects_ground_domain.h` | no predicate relaxation; no signature change downstream of the selection struct; no second lookup channel | `cmo_python -m pytest -q tests/architecture/structural_boundaries -p no:cacheprovider`; search proof that no `id<T>()` remains under `src/models/` | The effects TU no longer names a component type in order to resolve it, and the pinned separation strings survive | after `G1-B`; serial with `G1-D` | 2 | planned |
| `G1-D` | main thread | n/a | Remove the four `xfail(strict=True)` markers and re-pin the unmarked monotonicity node to a real assertion. | `tests/runtime/ground/test_ground_damage_response.py` | no marker deletion without the node passing; no test marker change before the route works | `cmo_python -m pytest -q tests/runtime/ground tests/architecture/ground -p no:cacheprovider` | Three nodes pass unmarked and the monotonicity node asserts rather than falling through. The fourth carried the reachability marker for a second expectation it bundles with reachability; its marker is replaced by `_MOBILITY_PROJECTION_OPEN`, which names that expectation. Measured outcome `2026-09-22`: `4 passed, 1 xfailed` — the remaining failure is the mobility projection, not reachability, and the pre-work wording "four nodes pass unmarked" is amended to this. The same file gained two nodes that pin the multi-world half of the acceptance gate, which the plan had left as a measurement to be taken rather than as a test. Outcome `2026-09-28`: the mobility expectation was withdrawn by owner decision rather than satisfied with a coefficient; the fourth node was split into its reachability assertions and `test_ground_route_does_not_degrade_mobility_for_any_warhead_family`, and the file reads `8 passed`. | after `G1-C`; serial with `G1-E` | 2 | pass |
| `G1-E` | main thread | n/a | Reconcile the declaration surfaces, record acceptance, and name the behaviour change with its flip set. | `docs/domains/ground/standards/specialization_baseline.md` (+ `.zh.md`), `docs/domains/ground/README.md` (+ `.zh.md`), `src/models/domains/ground/README.md` (**and its `.zh.md`**, whose pair is unregistered and therefore invisible to the bilingual audit), `src/systems/domains/ground/README.md`, `src/runtime/facade/README.md` (+ `.zh.md`), `docs/architecture/work/issues/modularization_plan.md`, `docs/systems/combat/reviews/ground_damage_reachability_20260921.md`, `docs/domains/ground/reviews/ground_systems_owner_admission_20260921/README.md` (+ `.zh.md`), this package's acceptance record. **Write set extended by the sweep, recorded rather than silent:** `src/systems/domains/README.md` (+ `.zh.md`), which carried the same claim and which the `G1-A` freeze missed | no capability promotion; no edit to `src/systems/combat/README.md`; no claim that the duplicate class is extinct; no rewriting of a recorded measurement — pre-repair readings stay and are marked as such | `cmo_python tools/maintenance/document_link_audit.py`; `cmo_python tools/maintenance/translate_docs_batch.py audit …`; `cmo_python -m pytest -q tests/architecture/governance -p no:cacheprovider` | Declaration items 1, 2, 4, 6, 9 and 10 reconciled, acceptance recorded, and the flip set stated. Outcome `2026-09-22`: link audit `198 / 1732 / 0`; bilingual audit `74 synced, 0 diverged` after refreshing the two registered pairs; governance at the branch baseline; flip set recorded in the package README | after `G1-D`; serial, never parallel | 1 | pass |

## Dispatch Rules

- Every worker packet maps to exactly one cluster above.
- `G1-B` through `G1-D` are serial. They change one behaviour across three layers, and a
  second writer in the same window makes every measurement unusable — this sequence has
  already paid for that lesson twice.
- The package's own `README.md`, this document's status cells, and the current-status and
  acceptance documents are updated by whichever cluster last changed the recorded state.
- Nothing under `src/` is edited by `G1-A` or by the documentation half of `G1-E`; the
  component census must be provably unmoved at every cluster boundary.
- If a cluster exceeds its round cap, stop and re-scope before adding a follow-up wave.
- Follow [Subagent Usage Policy](../../../../../engineering/automation/standards/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
```

## Validation Plan

Run at the Windows MSVC host unless a row says otherwise.

| Command | What it decides |
| --- | --- |
| `cmo_python -m pytest -q tests/runtime/ground tests/architecture/ground -p no:cacheprovider` | the route works: the reachability nodes pass unmarked, the split node pins the bootstrap mobility contract, and nothing else in the ground surface regressed. `test_repaired_route_holds_in_a_world_created_after_earlier_worlds` and `test_worlds_do_not_leak_ground_damage_into_each_other` carry the multi-world half of the acceptance gate |
| `cmo_python -m pytest -q tests/architecture/composition -p no:cacheprovider` | the component and system census is unmoved, and the executable graph hash is unchanged |
| `cmo_python -m pytest -q tests/architecture/structural_boundaries -p no:cacheprovider` | the pinned separation strings survive and no new edge was introduced |
| `cmo_python -m pytest -q tests/architecture/governance -p no:cacheprovider` | no new documentation or governance failure beyond the branch baseline |
| `cmo_python tools/maintenance/document_link_audit.py` | links resolve |
| `cmo_python tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/engineering/documentation/reference/bilingual_document_clusters.json` | the bilingual pairs touched by `G1-E` stay in step |

The branch baseline is governance `3 failed, 169 passed, 1 xfailed` with three named
pre-existing node ids; "no new failures" means that same set, not a green suite.

## Acceptance Criteria

- The three reachability-marked ground damage nodes pass without their markers. The
  fourth was amended twice. First it kept a `strict=True` marker for the mobility
  projection it also asserted. On `2026-09-28` that expectation was withdrawn and the node
  was split: the reachability assertions pass unmarked, and the mobility contract is pinned
  as `test_ground_route_does_not_degrade_mobility_for_any_warhead_family`.
- The current component census reads `85 components, 2 kernel systems, 35 resolved systems`
  and none of the gates asserting it changed.
- No `id<T>()` call remains under `src/models/`, verified by search.
- The composition-path resolution is demonstrated to follow component registration and to
  be per-world, and the multi-world behaviour is measured rather than assumed.
- The behaviour change is stated with its flip set, including that a ground-targeted
  structural hit may no longer destroy where it previously did through the placeholder.
- No page claims a ground capability, and no forbidden string reappears.

## Residual Map

- **No Ground hit degrades mobility, by decision.** With the route repaired, the ground
  consequence applies through `command_integrity` and `structural_integrity`, but
  `apply_default_effects_ground_chassis_consequence_blocks` degrades `mobility_integrity`
  and `track_integrity` only when the Ground spatial scales carry a blast or a mobility
  term. Those terms come from warhead mechanism load, and the effects model estimates that
  only for structured air targets, so they are zero on the Ground route for every warhead
  family. An earlier wording blamed "a pure structural hit"; independent review corrected it. The expectation was withdrawn
  on `2026-09-28` instead of inventing an uncalibrated coefficient. The behaviour is pinned
  by `test_ground_route_does_not_degrade_mobility_for_any_warhead_family`, and the
  component-attributed follow-up and its entry conditions are recorded in the
  [package README](README.md#decision-mobility-expectation-2026-09-28).
- **`105`'s creation site remains unobserved.** The repair removes the sites a duplicate
  could originate from in the effects unit; it does not prove that unit was the origin.
- **The duplicate class is not proven extinct.** A future `id<T>()` or typed read in that
  unit could reintroduce the identical defect, and the flecs consistency assert that would
  catch it is compiled out of this build.
- **If the multi-world measurement contradicts the premise**, the repair becomes
  `FLECS_CPP_NO_AUTO_REGISTRATION` plus registry-only registration, which is a different
  package with a different write set.
- `ground_p2_stage_node` and the `docs/task/ground/` archive-ledger registration stay
  separate, recorded on the [Ground owner README](../../../README.md).
