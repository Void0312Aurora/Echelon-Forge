# Ground Damage Effects Route Repair

Status: `2026-09-28` active. Route repaired, measured, and reconciled across its
declaration surfaces. The mobility-projection expectation that held acceptance was
decided on `2026-09-28`: withdrawn as an uncalibrated expectation, pinned as the current
bootstrap contract, and carried forward as a registered follow-up (see
[Decision: mobility expectation](#decision-mobility-expectation-2026-09-28)). What remains
before `P5` is independent review of that decision.

Language:
- English canonical: `README.md`
- Chinese companion: not required yet; high-churn implementation slice.

Document kind: `task`
Lifecycle: `active`
Canonical: `docs/domains/ground/work/active/ground_damage_effects_route_repair/README.md`
Owner: `domains/ground`
Last verified: `2026-09-28`

Inputs:

- [Ground owner README](../../../README.md) — the residual this package discharges
- [Ground specialization baseline](../../../standards/specialization_baseline.md) — the
  registered-but-unreachable statement this repair changed
- [DM-G1 diagnosis](../../../../../systems/combat/reviews/ground_damage_reachability_20260921.md)
  — the measurement the fix rests on
- [Simulation System Architecture Design](../../../../../architecture/standards/simulation_system_architecture_design.md)
  §4 laws, §6.1, §10 domain extension model
- [Modularization Plan](../../../../../architecture/work/issues/modularization_plan.md)
  — the ownership boundaries and the admission declaration list
- [Runtime Composition Baseline](../../../../../architecture/standards/runtime_composition_baseline.md)
- [Ground Systems Owner Admission](../../../reviews/ground_systems_owner_admission_20260921/README.md)
  — the accepted record that requires this fix to have its own package

## Purpose

The ground damage response is registered and its per-tick half runs:
`GroundDamageStateUpdate` matches spawned ground entities and advances
`GroundPlatformDamageState`. Its **effects half was unreachable**. The effects translation
unit resolved a duplicate component id — `105` where the factory and registration units
resolve `94` — so at routing time it found no state and a hit fell through to the legacy
placeholder path.

This package repaired that: the component is resolved **once, in the composition path**,
and the resolved id is passed down to the effects route. It exists as its own package
because the accepted admission record requires it — "a fix exists only if it came with its
own package" — and because the repair changes runtime behaviour, which that record refused
to take on the admission's authority.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Per-tick ground damage | reachable | `GroundDamageStateUpdate` matches spawned ground entities; registered as `builtin.system.ground_damage`, domain `ground`, stage 30, [`system_contribution_registry.cpp`](../../../../../../src/core/engine/system_contribution_registry.cpp) | proves the system runs, not that damage lands |
| Effects route | reachable, measured `2026-09-22` | the warn-level probe prints `GROUND SELECT entity=582 key_type=11 state=1 hitbox=1 sys=1 platform=1` where it printed `state=0` before; `test_ground_damage_response.py` reports `4 passed, 1 xfailed` where it reported `1 passed, 4 xfailed` | measured for the hit this test exercises; the duplicate's creation site was never observed, so "only the effects route was affected" holds for the routes measured |
| Component identity minting | composition-owned | `register_component<T>` is `ecs.component<T>()` from the admitted rows, and it runs before model realization | the repair must not move identity derivation into `src/models/**` |
| Duplicate-id detection | absent in this build | flecs's `ECS_INCONSISTENT_COMPONENT_ID` assert is compiled out: `Release` plus `NDEBUG` means no `FLECS_DEBUG` and no `FLECS_KEEP_ASSERT` | the 94/105 split is a **silent** failure class here, not a loud one |
| Ground damage test markers | none held | three reachability markers removed and their nodes pass; the fourth node was split on `2026-09-28` into its reachability assertions and `test_ground_route_does_not_degrade_mobility_for_any_warhead_family` in [`test_ground_damage_response.py`](../../../../../../tests/runtime/ground/test_ground_damage_response.py), `8 passed` | the split node pins the current mobility contract (no warhead family reaches the chassis mobility branches, because Ground mechanism-load estimation is not admitted); it is not a claim that ground movement is immune to damage |

## Scope

In scope:

- resolve `GroundPlatformDamageState` once per world in the effects-provider construction
  lambda and carry the id on the world-scoped model instance;
- consume that id in the effects routing detail and in the ground domain header, replacing
  the typed reads;
- delete the diagnostic `id<T>()` call at
  [`default_effects_domain_routing_detail.h`](../../../../../../src/models/weapons/detail/default_effects_domain_routing_detail.h),
  which is the only `id<T>()` in all of `src/` and the one live creation-site candidate for
  the duplicate;
- remove the four `xfail(strict=True)` markers and re-pin the unmarked monotonicity node
  (outcome: three markers removed and their nodes pass; the fourth was first re-marked
  because it bundled a mobility expectation with its reachability assertions, then split
  on `2026-09-28` once that expectation was withdrawn — the accounting is `G1-D`'s, and it
  is three-plus-one, not four);
- reconcile the pages that state the effects route is unreachable.

Out of scope, and refused:

- **any new component or registry row.** Carrying the id in a new world-scoped component
  would move the component count from 85 to 86 and force regeneration of the registry
  constant, both generated manifests, four fixtures and the closure hashes. This package
  changes no count.
- **any name-based lookup from a model translation unit.** It would put identity derivation
  back in `src/models/**`, create a second gate-free membership channel, and rest correctness
  on a string that two components already share in a build where the duplicate-id assert is
  compiled out.
- **any claim that ground damage is a capability.** Removing the placeholder fallback for
  the measured routes does not make movement, terrain, sensing, fires, logistics or
  observation export real.
- **new model-replacement setters**, and any edit that would admit `make_default_effects_model`
  into the kernel source; both are pinned by existing guards.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze scope, write set, and the §10 declaration set. | this request plus the diagnosis | README and cluster plan name every write set and validation command | active |
| `P1 Evidence` | Confirm the resolution point and the id's lifetime before writing code. | `P0` | the composition step is located, its ordering against model realization is demonstrated, and the multi-world stability question is answered by measurement | active |
| `P2 Implementation` | Resolve once in composition and consume the id in the effects route. | `P1` | the duplicate-resolving call is gone and the route reads the passed id | accepted |
| `P3 Integration` | Wire the tests and the declaration surfaces. | `P2` | four `xfail` markers removed, the monotonicity node re-pinned, and the §10 items 1, 2, 4, 6, 9, 10 reconciled | met `2026-09-28` — three markers removed and the route proven; the fourth node was split so its reachability assertions pass unmarked and its withdrawn mobility expectation is pinned as the bootstrap contract. The declaration reconciliation is done: §10 items 1 and 2 in the Ground specialization baseline, item 4 in `src/models/domains/ground/README.md`, item 6 in `src/runtime/facade/README.md`, items 9 and 10 in the same baseline's verification anchors and the unchanged Python-caller surface |
| `P4 Validation` | Run the gates and record outcomes. | `P3` | named commands show no failures beyond the branch baseline, and the behaviour change is stated with its flip set | met `2026-09-28` — the gates are run and the flip set is recorded below. The smoke suite ran as `ef_test` 174/174 and CTest 14/14. The only failures beyond the base set are the two Air realism nodes recorded as known exposures of the entity-id seed defect |
| `P5 Closure` | Write acceptance and sync indexes. | `P4` | package accepted, or explicitly held with a named blocker | held — the mobility decision is recorded below; closure waits on an independent review of that decision and of the split node |

## Task Clusters

- Task cluster plan:
  [ground_damage_effects_route_repair_task_clusters_20260922.md](ground_damage_effects_route_repair_task_clusters_20260922.md)

## Outputs And Evidence

- a resolved-once component id flowing composition to model, with the effects TU no longer
  naming a component type to resolve it;
- `GroundPlatformDamageState` reachable on the effects route for the measured hit;
- four `xfail(strict=True)` nodes freed: three markers removed and their nodes pass, and the
  unmarked monotonicity node re-pinned to a real assertion; the fourth node's reachability
  assertions now run on their own, and its mobility expectation became the separate
  bootstrap-contract node described in the decision below;
- reconciled statements in the Ground specialization baseline, the owner pages, the
  modularization plan, the DM-G1 diagnosis and the accepted admission record;
- validation output for the ground suites, the composition contracts and the governance
  guards;
- the multi-world measurement, reported with the per-world vectors, and pinned as two nodes
  in [`test_ground_damage_response.py`](../../../../../../tests/runtime/ground/test_ground_damage_response.py)
  so the property is re-checked rather than measured once.

### Review Record

Round 1, independent, on `671d08de`: **no blocking finding**, four follow-up suggestions.
It reproduced the fix rather than reading it — it traced registration before composition,
read the pinned flecs source to confirm `s_id` is process-global and first-wins with the
consistency assert compiled out, verified the artifact postdates every changed source,
reproduced `23 passed, 1 xfailed`, `4 passed, 1 xfailed`, and the `state=1` probe line, and
settled the contested question by **unmarking the fourth node and running it**: the sole
failure is the mobility assertion, with every reachability assertion passing.

| Follow-up | Disposition |
| --- | --- |
| Take the id from the admitted registry instead of the process-global type cache, so the ordering guarantee is structural rather than incidental | **Held, not discharged.** Correct and out of this repair's bound: it changes the resolution site into the registry row, needs its own acceptance and its own measurement, and this repair's subject was removing the duplicate resolution. It is the strongest candidate for the next package. |
| The diagnosis page and five other pages still asserted unreachability | **Addressed** in the reconciliation recorded above, with the recorded measurements kept and marked pre-repair. |
| The scope line said "remove the four markers" while the outcome is three-plus-one | **Addressed**: the scope entry now carries the outcome inline. |
| The composition figure `72 passed, 1 skipped` is host-dependent; three of those are missing-prerequisite skips elsewhere | **Addressed**: the gate row now names the host, the prerequisites, and the independently measured `69 passed, 4 skipped`, and states that the census is the host-independent part. |

## Acceptance Gate

This subproject can be marked accepted only when:

- the effects route reaches `GroundPlatformDamageState` for the hit the existing test
  exercises, demonstrated by the four previously-`xfail` nodes' reachability assertions
  passing without markers. *Amended `2026-09-28`:* the fourth node also asserted a mobility
  expectation. That assertion was withdrawn by owner decision rather than made to pass, and
  it now lives in a separate node that pins the current contract. The gate is met for
  reachability only; it does not claim that the withdrawn expectation passed;
- no component or system contribution count changed: the executable graph census stays
  `85 components, 2 kernel systems, 35 resolved systems`, and the four gates that assert it
  are untouched;
- the effects translation unit no longer contains an `id<T>()` call, verified by search
  rather than by reading;
- the composition-path resolution is shown to happen after component registration and once
  per world, and the multi-world behaviour is **measured**, not assumed — `s_id` is
  process-global per type and this repository runs many worlds per process;
- the behaviour change is stated with its flip set: a ground-targeted structural hit that
  previously destroyed through the placeholder path may no longer destroy;
- no page claims ground damage is a capability;
- the gates report no failures beyond the branch baseline, which is governance
  `3 failed, 169 passed, 1 xfailed` with the same three node ids.

Gate status, first measured `2026-09-22`. Rows dated `2026-09-28` were re-decided or re-measured on that date. Every status is measured against the items above rather than asserted:

| Gate item | Status | Measurement |
| --- | --- | --- |
| route reaches the component | met `2026-09-28` | the route reaches it — `state=1` at the probe and three nodes freed. The fourth node bundled a mobility expectation with its reachability assertions (pre-decision reading: `4 passed, 1 xfailed`); after the mobility decision it was split, its reachability assertions pass unmarked, and the file reads `8 passed` |
| census unmoved | met | composition contracts `72 passed, 1 skipped` on the author's Windows MSVC host, which carries `g++` and Cordis/Node; an independent review measured the same suite as `69 passed, 4 skipped` on a host without those prerequisites, so the three extra skips are missing-prerequisite bail-outs rather than passes. The census itself is host-independent: `85 / 2 / 35` (85 components, 2 kernel systems, 35 resolved systems), counted from `EF_DEFAULT_COMPONENT_CONTRIBUTIONS` and pinned at `system_contribution_registry.cpp` and in `runtime_composition_evidence_contract.py`. An earlier revision of this row said `85 / 2 / 34`, a typo against the pin |
| no `id<T>()` in the effects unit | met | search over `src/models/` returns no `id<T>()` call |
| composition-owned, per-world resolution | met, measured | five sequential kernels in one process each printed `GROUND SELECT … state=1`, produced the identical post-hit vector `[0.8167, 1.0000, 0.9010, 0.8680]`, and the last was created after the earlier four were destroyed. Pinned as `test_repaired_route_holds_in_a_world_created_after_earlier_worlds` and `test_worlds_do_not_leak_ground_damage_into_each_other` | the measurement covers many worlds in one process; it does not prove the numeric id is the same value in each world, which no surface reports |
| flip set stated | met | below |
| no capability claim | met | the declaration surfaces were reconciled in `G1-E` and each one keeps the refusal: the baseline's "Registered And Reachable, But Not A Capability", the owner page's "remain held as capabilities", the facade's declared visibility of none |
| no new gate failure | met | governance `3 failed, 169 passed, 1 xfailed`, same three node ids; structural boundaries `2 failed, 14 passed`, pre-existing |

### Behaviour Change And Flip Set

One measured behaviour changed, and this is the set of statements that flips with it:

- **Before.** A ground-targeted structural hit failed the ground selection predicate, fell
  through to `GroundPlaceholder`, and that fallback's shared finalize destroyed the element:
  `[0.0, 0.0, 0.0, 0.0]`, position zeroed, `SPLASH! Target … Destroyed.`
- **After.** The same hit is selected by the ground route and applies ground consequences.
  One 120-damage structural hit leaves the element alive at
  `[0.8167, 1.0000, 0.9010, 0.8680]`.
- **What flips.** Any test, scenario, fixture, or expectation that relied on a single
  ground-targeted structural hit destroying a ground element no longer holds. The four
  `xfail` nodes were the repository's explicit record of the old behaviour. Three now pass
  unmarked. The fourth's marker was first renamed to the expectation it actually asserted;
  on `2026-09-28` that expectation was withdrawn and the node split (see the mobility
  decision below).
- **What does not flip.** No capability claim, no component or system count, no facade
  surface, no registry row, and no Python caller compatibility. The mechanism was already
  registered; only its reachability changed.
- **Not claimed.** That the duplicate component id class is extinct: the assert that would
  catch it is compiled out of this build, and the creation site of `105` was never observed.

## Decision: Mobility Expectation (2026-09-28)

**Cause, corrected by independent review.** The first version of this decision blamed the
hit: "a pure structural hit carries neither a blast nor a mobility scale". That was wrong.
The Ground route never estimates warhead mechanism load at all. In the effects model the
direct-hit and spatial-projection mechanism-load paths are gated on
`structured_air_target`, and a Ground target receives the default `WarheadEffectProfile{}`.
The blast and mobility spatial scales that
`apply_default_effects_ground_chassis_consequence_blocks` gates on are therefore always
zero on the Ground route, **whatever the warhead family**. Measured on `2026-09-28`: blast,
blast-fragmentation, fragmentation and continuous-rod profiled hits all leave the element at
`[0.8167, 1.0, 0.9010, 0.8680]`, with mobility still `1.0` after 60 ticks. The chassis
mobility and track branches are implemented but unreachable, the same defect class as
`DM-G1`. The per-tick `ongoing_structural_damage` term in the Ground damage system is never
raised anywhere in `src/`, so it cannot move mobility later either.

**Decision.** The expectation that a hit degrades Ground mobility is **withdrawn**, not
satisfied. The node that bundled it with reachability is split: its reachability
assertions stand alone, and `test_ground_route_does_not_degrade_mobility_for_any_warhead_family`
pins the current contract across the four warhead families (mobility stays `1.0` while
mission and survivability degrade).

**Why not make the branches reachable now.** There are two candidates:

- Admit mechanism-load estimation for Ground targets. That would route uncalibrated **air**
  warhead physics (armor scale, orientation weighting, spatial sampling) into Ground
  consequences, with no Ground vulnerability profile behind it.
- Add a structural-to-mobility term. That would be an invented coefficient.

Either would read as Ground damage fidelity, which this package and the Ground
specialization baseline both refuse to claim. Pinning the true behaviour keeps the gap
visible, and the replacement has to change the node deliberately.

**What is not claimed.** That Ground movement is immune to damage. The pinned node describes
the uncalibrated bootstrap route, not the world.

**Registered follow-up: component-attributed Ground mobility consequence.** Mobility loss
should come from damage to named mobility components (running gear, drivetrain, crew
casualties for dismounts), not from a scalar term on the chassis block. Entry conditions,
all required:

1. Ground mechanism-load estimation is admitted: the effects model's air-only
   mechanism-load gate is widened to Ground targets through a Ground-owned evidence path,
   not by reusing air vulnerability. Without this, the chassis branches stay unreachable and
   conditions 2–5 cannot produce any mobility loss.
2. Authored Ground hitboxes replace the provisional whole-body extent synthesized at spawn.
3. The Ground route has a vulnerability/evidence profile with provenance, analogous to the
   air vulnerability evidence gate.
4. Something consumes mobility: Ground movement does not read `mobility_capability` today,
   so the package must also define how mobility loss changes movement (speed cap,
   immobilisation) and what the training observation exposes.
5. An owner-accepted expectation matrix replaces the pinned node.

## Residuals And Next Steps

- **Known exposure, not owned here: entity-id-keyed stochastic draws.** Admitting
  `GroundPlatformDamageState` (together with the other components on this branch) shifts
  every Flecs entity id by 2. Every seed that mixes raw ids therefore moves. Two Air
  realism nodes flip for that reason alone:
  `test_phase2_fire_suppression_integrity_reduces_fire_cascade_growth` fails, and
  `test_shot_effect_record_links_fuze_geometry_warhead_part_entry_and_consequence_hook`
  XPASSes its strict marker. The same flips reproduce on the base build by spawning
  unrelated units first, or by running a second episode after `reset(seed)` on one kernel.
  The root fix is a stable per-world entity serial, owned by
  [Stable Entity Identity For Stochastic Draws](../../../../../architecture/work/issues/stable_entity_identity_for_stochastic_draws.md).
  Both nodes are left unmarked here on purpose: re-marking them would hide the defect
  instead of fixing it.

- **No Ground hit degrades mobility, by decision.** The cause is that Ground mechanism-load estimation is not admitted. See
  [Decision: Mobility Expectation](#decision-mobility-expectation-2026-09-28). The pinned node
  is `test_ground_route_does_not_degrade_mobility_for_any_warhead_family`; the component-attributed
  follow-up and its entry conditions replace it.
- The **creation site of component `105` is still unobserved.** This repair eliminates the
  only `id<T>()` in `src/` and the effects TU's typed reads, which removes the sites a
  duplicate could originate from in that unit. It does not prove the duplicate was created
  there, and it does not prove the class extinct.
- If the multi-world measurement contradicts the premise, the repair is not this one: the
  candidate becomes `FLECS_CPP_NO_AUTO_REGISTRATION` plus registry-only registration.
- `ground_p2_stage_node` and the `docs/task/ground/` archive-ledger registration remain
  separate packages, recorded on the [Ground owner README](../../../README.md).

## Archive

Promote lasting facts to the Ground standards and the owner pages, retain the accepted
decisions under `docs/domains/ground/reviews/`, and retire this packet from `work/active/`
once accepted.
