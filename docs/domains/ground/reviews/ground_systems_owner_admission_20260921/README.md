# Ground Systems Owner Admission

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/reviews/ground_systems_owner_admission_20260921/README.md`
Owner: `domains/ground`
Last verified: `2026-09-22`

Status: `2026-09-21` accepted. Round 10 authorised the closure. Scope and boundary are
frozen. The declaration cluster is closed, the `DM-G1` cause is located, and the systems
owner is admitted with its guards updated. The
[acceptance record](ground_systems_owner_admission_acceptance_20260921.md) carries the
gate outcomes, and the
[Review Log](ground_systems_owner_admission_current_status_20260921.md) records which round
authorised which status change.

Lifecycle note `2026-09-22`: this packet is an accepted review record retained as
provenance. The `DM-G1` residual it recorded is discharged by the
[Ground Damage Effects Route Repair](../../work/active/ground_damage_effects_route_repair/README.md)
package, which landed on that date: the effects route resolves its component id once per
world in the composition path and is reachable. Where this packet, the review log, the
acceptance record, or the cluster plan says the effects route is unreachable, that is the
state **as of the review**, and the pre-repair measurement is preserved deliberately. The
capability refusal this packet made is unchanged and still governs; the repair claims no
Ground capability from reachability either.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- [Ground owner README](../../README.md)
- [Ground specialization baseline](../../standards/specialization_baseline.md)
- [Ground minimal task structure](../../standards/minimal_task_structure.md)
- [Ground defect inventory](../../reviews/ground_domain_defect_inventory_20260522.md)
- [Modularization plan — Ground System Gap](../../../../architecture/work/issues/modularization_plan.md)
- [DM-G1 ground damage reachability diagnosis](../../../../systems/combat/reviews/ground_damage_reachability_20260921.md)
- [Domain systems boundary](../../../../../src/systems/domains/README.md)
- [Combat systems boundary](../../../../../src/systems/combat/README.md)
- [Subproject creation standard](../../../../engineering/automation/rules/subproject_creation_standard.md)

## Purpose

The registry carries two rows labelled `domain = ground`: a shared ground-contact
primitive at stage 10 and the ground damage response at stage 30. The damage
response is the one that landed as a Ground-owned mechanism, and until this
package it lived in `src/systems/combat/`, whose own boundary README lists "ground
fires, ground damage, or land-domain combat runtime ownership" as prohibited. The
modularization plan described it as a no-op include/register shell and recorded
that no Ground systems owner existed, and the ground specialization baseline
called it a placeholder route. Three maintained descriptions and one directory
boundary disagreed with the shipped code, and the domain had no work package to
reconcile them.

This subproject admits `src/systems/domains/ground/` as the Ground per-tick
systems owner, moves the damage system into it, and reconciles the declarations
that currently contradict it. The modularization plan already names the
conditions for admitting that owner; its absence was an accepted architecture
state, and this package is the work surface that asks to change it.

The package also diagnoses — but does not fix — the `DM-G1` reachability defect,
so the new owner inherits a measured status line instead of an assumption.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Ground damage mechanism | implemented; effects route unreachable **as of this review** (reachable since `2026-09-22`) | `src/systems/domains/ground/damage_system_ground.h`; `builtin.system.ground_damage` at stage 30 in `src/core/engine/system_contribution_registry.cpp`; [DM-G1 diagnosis](../../../../systems/combat/reviews/ground_damage_reachability_20260921.md) | proves no ground combat capability either way; the per-tick system matches, and at review time a single hit routed through the placeholder fallback |
| Systems owner directory | admitted (`GA-B`) | `src/systems/domains/ground/` exists and owns the damage system; the governance guard now asserts the directory instead of its absence | the directory owns one system, not a ground runtime |
| Directory boundary | resolved (`GA-B`) | `src/systems/combat/README.md` Prohibited section, unedited | relocating the file made the prohibition true again, which is why the prohibition was not the thing to change |
| Ground specialization baseline | reconciled and promoted (`GA-A` → `pass` at `f3f85859`; page closed at `0fec39bb` after `2d0addf7`) | [specialization_baseline.md](../../standards/specialization_baseline.md) separates ownership, registration, and reachability status; no placeholder-route prose remains | ground damage stays refused as a capability after this package; the section is now "Registered And Reachable, But Not A Capability" |
| Modularization plan | updated (`GA-C`) | the plan now records `ground` among the admitted systems owners and describes the damage response rather than a no-op shell | the plan is architecture-owned; this package proposed the text, it does not own it |
| P2 stage node | held | the stage node registry carries five nodes and none for `P2 TaskingIntent` | out of scope here; needs its own package |
| Ground work package | this package | the [Ground owner README](../../README.md) owns the authorization window; this row does not restate it | first authorized Ground package |

## Scope

In scope:

- admit `src/systems/domains/ground/` with the boundary README that the
  `src/systems/domains/` root requires of its children;
- move `damage_system_ground.h` into it and update the include in
  `src/core/engine/system_contribution_registry.cpp`, keeping the registered
  contribution id and stage unchanged;
- update the `src/systems/domains/` README (EN/ZH), which had explained why no
  Ground owner existed;
- reconcile the Ground specialization baseline and the Ground owner README with
  the code, keeping the capability itself refused;
- propose the modularization-plan text change to the architecture owner;
- update the governance guard that had asserted the directory is absent;
- diagnose `DM-G1` with probe instrumentation only.

Out of scope:

- Ground movement, route following, terrain, sensing, fires, logistics, or
  observation export;
- any Ground combat capability claim — the effects route stays unreachable until a
  separate fix package closes it (discharged `2026-09-22`: the
  [repair package](../../work/active/ground_damage_effects_route_repair/README.md) closed it,
  and the capability refusal is the part that survives);
- the `DM-G1` fix itself;
- the P2 stage node and any facade-visibility promotion;
- editing `src/systems/combat/README.md`;
- new test files;
- broad rewrites of shared combat, effects, or physics code.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze scope, write sets, and forbidden claims. | this request plus the conflicting descriptions | package README and parent README link exist | accepted (round 10) |
| `P1 Evidence` | Enumerate every locked string, guard, fixture, and registration row the move touches. | `P0` | the cluster plan names each write set and validation command | accepted (round 10) |
| `P2 Declaration Reconciliation` | Reconcile the Ground-owned pages with the code. | `P1` | no Ground-owned page describes the mechanism as a placeholder | accepted (round 3) |
| `P3 Owner Admission` | Create the directory, move the system, update the registry include and the governance guard. | `P2` | directory exists, composition validates, guard updated | accepted (via round 5's `GA-B` authorisation) |
| `P4 Validation` | Run composition, Ground, and governance gates. | `P3` | named commands pass without new failures | accepted (via round 5's `GA-C` authorisation) |
| `P5 Closure` | Write acceptance, current status, and owner index updates. | `P4` | package accepted, or explicitly held with a named blocker | accepted (round 10) |

## Task Clusters

- Task cluster plan:
  [ground_systems_owner_admission_task_clusters_20260921.md](ground_systems_owner_admission_task_clusters_20260921.md)
- Current status:
  [ground_systems_owner_admission_current_status_20260921.md](ground_systems_owner_admission_current_status_20260921.md)

## Outputs And Evidence

- `src/systems/domains/ground/README.md` plus the relocated damage system;
- an unchanged registered contribution (`builtin.system.ground_damage`, stage 30)
  with an updated include path;
- reconciled Ground declarations that separate ownership from capability;
- an updated governance guard and modularization-plan proposal;
- a `DM-G1` measurement that either names a bounded cause or records that the
  cause lies in the kernel assembly path;
- validation output for the composition contract, the Ground suites, and the
  governance guard suite.

## Acceptance Gate

This subproject can be marked accepted only when:

- `src/systems/domains/ground/` exists and owns the damage system that was
  previously filed under `src/systems/combat/`;
- the default composition still validates with the same component and system
  contribution counts, and the registered ground contribution keeps its id and
  stage;
- no maintained page describes the ground damage route as a placeholder, and no
  maintained page claims it works;
- the `src/systems/combat/` boundary README is true again without being edited;
- the governance guard reflects the admitted owner instead of asserting absence;
- `DM-G1` has a recorded measurement, and a fix exists only if it came with its
  own package;
- the Ground suites and the architecture suites pass with no new failures.

## Residuals And Next Steps

- `DM-G1` remained open at review time with a located cause, narrower than first
  reported: the factory and registration units resolve `GroundPlatformDamageState` to
  component `94`, the effects unit resolved a duplicate `105`, and only the effects route
  was therefore unreachable. The per-tick system matches and was unaffected. The
  measurement and the corrections it forced are in the
  [DM-G1 diagnosis](../../../../systems/combat/reviews/ground_damage_reachability_20260921.md).
  **Discharged `2026-09-22` by the
  [repair package](../../work/active/ground_damage_effects_route_repair/README.md)**, which is
  the separate package this residual asked for. What it leaves open is the mobility
  projection expectation that still carries one `xfail(strict=True)`, and the duplicate's
  creation site, which remained unobserved.
- The four `xfail(strict=True)` nodes were not CI smoke material, and the unmarked
  monotonicity test in the same file could pass through the placeholder fallback; both were
  evidence-honesty items for the fix package. **Addressed `2026-09-22`**: three markers are
  removed and their nodes pass, the monotonicity node is re-pinned, and the fourth node's
  remaining marker names the mobility expectation rather than reachability.
- The P2 stage node was a separate package on the tasking side; the Ground
  surface's only claimed stage had no registered node.
- The retired `docs/task/ground/` records still have no retrieval address in the
  archive ledger; that belongs to the documentation governance owner.
- The bilingual registry's `last_verified` is a hash-baseline refresh date that
  the tool stamps, not a copy of a page header, and no gate compares the two. A
  review measured a header/stamp difference in 42 of the 148 registered files, so
  aligning the pairs this package touched does not fix the class; that belongs to
  documentation governance.
- Movement, terrain, sensing, and fires stay held until their own packages name
  the declarations the architecture standard requires.

## Archive

Accepted or superseded records move to `docs/domains/ground/reviews/`; they do
not remain under a retired task root. This package must not stay under
`work/active/` once it is accepted and its lasting facts have been promoted to
the Ground standards. **Satisfied**: it was accepted at review round 10 and now lives at
`docs/domains/ground/reviews/ground_systems_owner_admission_20260921/`.
