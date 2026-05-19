# Simulation Architecture

Status: active subproject opened on `2026-05-19`.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This subproject turns the strict simulation architecture baseline into scoped
work packages. It should be used before starting broad implementation across
weapons, naval runtime, sensor/track, command/tasking, facade, or backend
acceleration.

Architecture authority:

- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [system layering and engine encapsulation plan](../../plan/architecture/system_layering_and_engine_encapsulation_plan.md)
- [architecture and performance follow-up](../../plan/architecture/architecture_and_performance_research_followup.md)

## Current Position

The active design conclusion is:

1. The project should follow one canonical semantic lifecycle.
2. Real execution should use a multi-rate temporal DAG, with feedback crossing
   explicit state-store or event-queue boundaries.
3. Air, naval, weapon, and future domains should extend that lifecycle through
   stage-local model families and stage-node contracts.
4. Runtime facade and typed request/result contracts should become the long-term
   frontend dependency.
5. Policy computation and test/orchestration should be modeled as explicit
   producers and consumers of facade contracts, not as hidden owners of
   simulation state.
6. Local work on this machine should focus on build/import/smoke, architecture
   docs, contract design, and simulation assembly rather than RL training.

## Work Packages

| Work package | Status | Goal | Output |
|--------------|--------|------|--------|
| `WP0 Architecture Baseline` | complete | Make the semantic lifecycle, temporal DAG, and extension rules explicit | architecture design doc, task subproject entry |
| `WP1 Pipeline Inventory` | complete | Map current code, systems, models, and tests onto `P0-P10` and current coupling hotspots | [pipeline inventory](pipeline_inventory_wp1_20260519.md) |
| `WP2 Contract Freeze` | active | Identify packet families, stage-node contracts, and cross-layer policy/orchestration contracts that need explicit ownership | [contract freeze](contract_freeze_wp2_20260519.md) |
| `WP3 Engagement Pilot` | active | Use weapon/engagement as the first cross-domain validation slice | [engagement pilot task family](engagement_pilot_wp3_20260519.md) |
| `WP4 Facade Alignment` | planned | Ensure pilot behavior is reachable through facade-shaped APIs | facade request/result additions and adapter plan |
| `WP5 Validation Harness` | planned | Add smoke and architecture tests that prove the lifecycle is shared | focused tests and local Windows smoke commands |

## WP0 Scope

WP0 is documentation-only:

- add the strict architecture baseline,
- open this task subproject,
- update navigation entries,
- avoid code changes,
- avoid deciding exact field layouts before WP1/WP2 evidence is collected.

Exit criteria:

1. `docs/plan/architecture` has a clear architecture authority document.
2. `docs/task` has a simulation architecture entry.
3. The task entry explains why weapon work should be treated as a cross-domain
   engagement pilot with multiple clock domains, not a standalone vertical
   stack.

## WP1 Pipeline Inventory

WP1 should inspect the live code and produce a table that maps existing assets
onto the canonical semantic lifecycle:

- `P0 ContentCompile`
- `P1 WorldSetup`
- `P2 TaskingIntent`
- `P3 CommandDelivery`
- `P4 PlatformControl`
- `P5 PhysicsStep`
- `P6 SenseTrackLink`
- `P7 FireControlLaunch`
- `P8 MunitionLifecycle`
- `P9 EffectsDamage`
- `P10 ObservationExport`

Expected evidence:

- relevant `src/components/*` DTOs,
- `src/systems/*` stage behavior,
- `src/models/*` model implementations,
- `src/core/engine/*` orchestration surfaces,
- `src/runtime/facade/*` request/result coverage,
- Python adapter compatibility paths,
- tests that already enforce or violate the intended boundary,
- evidence of clock domains, event queues, state-store feedback, or current
  cross-stage coupling.

WP1 should not implement new code unless a small doc or test fixture is required
to complete the inventory.

## WP2 Contract Freeze

Input:

- [WP1 pipeline inventory](pipeline_inventory_wp1_20260519.md)

Output:

- [WP2 contract freeze](contract_freeze_wp2_20260519.md)

WP2 should turn the inventory into a scoped contract plan. It should decide:

1. which packet families already exist,
2. which are compatibility aggregations,
3. which need new facade-level request/result APIs,
4. which should stay component-only,
5. which stage nodes need explicit read/write sets, clock domains, latency
   policies, and sync policies,
6. which same-window DAG edges are data-derived versus cross-window feedback,
7. which state shards need versioning now or later for partial sync,
8. which event families need deterministic `(timestamp, priority, event_id)`
   ordering,
9. which clock domains can use default nested triggering and which need an
   explicit merge policy,
10. which Python calls need adapter compatibility,
11. which observation schemas are policy/test-owned `ObservationViewSpec`
    variants versus simulation-owned state exports,
12. how policy action cadence maps onto `P3/P4/P5` using `ActionIntentPacket`
    and `ActionHoldPolicy`,
13. how reward is split between simulation facts and experiment shaping using
    the fact/shaping criterion from the architecture baseline,
14. how `terminated` and `truncated` reasons are attributed to simulation,
    policy, or orchestration sources,
15. which side owns authoritative episode phase and which side only mirrors it
    for Gymnasium, batch, replay, or CI APIs,
16. how scripted, learned, and human coordination directors inject tasking or
    command intent without mutating raw ECS state,
17. which `merge_policy` each cross-layer producer uses,
18. which scheduling-window injection semantics each action or coordination
    path expects,
19. which observation schema changes are minor-compatible versus
    major-incompatible.

The expected output is a freeze document, not implementation.

Architecture closure note:

- The architecture framework is closed at the simulation/policy/orchestration
  layer boundary.
- Remaining `B`-level contract semantic details should patch the architecture
  baseline directly.
- `C`-level implementation alignment should be tracked as task plans.
- `D`-level internal design blanks, such as policy-layer internals or
  orchestration-layer internals, should become separate architecture docs and
  should not reopen the simulation-layer framework.

## WP3 Engagement Pilot

Output:

- [WP3 engagement pilot task family](engagement_pilot_wp3_20260519.md)

The first implementation pilot should be the engagement lifecycle because it
crosses the largest number of architecture boundaries and naturally uses
multiple clock domains:

`tasking -> command delivery -> sensor/track -> fire control -> launcher -> munition -> seeker/guidance/fuze -> effects -> damage -> observation`

The pilot must involve at least two platform families, such as:

- aircraft pylon launch,
- naval mount launch.

The pilot should avoid creating separate `air weapon` and `naval weapon`
runtime paths. Differences should appear in launcher, munition, seeker,
guidance, fuze, effects, doctrine families, and clock-domain policies.

The first implementation wave should be split into contract DTO scaffolding,
facade packet shells, Python binding exposure, air launch adapters, naval
launch adapters, munition/damage export, diagnostics trace, and a
stage-aligned non-RL smoke harness. Air and naval workers may run in parallel
only when they do not edit the same shared kernel file.

## Acceptance Gates

Every implementation task derived from this subproject should satisfy:

1. stage ownership is documented,
2. stage-node read/write sets and clock domains are documented,
3. feedback crosses state-store or event-queue boundaries,
4. facade or compatibility-adapter access is explicit,
5. CPU exact behavior remains the reference path,
6. cross-domain behavior uses the same lifecycle,
7. local smoke tests run without requiring RL dependencies,
8. diagnostics can explain command, launch, munition, effect, and damage events,
9. observation schema, action validity, reward composition,
   termination/truncation source, and episode lifecycle authority are assigned
   to explicit layers.

## Non-Goals

- Full RL training on the local Windows machine.
- Immediate exact GPU world-step replacement.
- Introducing Rust as a near-term backend.
- Rewriting all existing command/tasking DTOs before the contract freeze.
- Moving every existing file into new directories during WP0/WP1.
