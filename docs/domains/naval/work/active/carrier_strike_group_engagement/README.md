# Carrier Strike Group Engagement

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/carrier_strike_group_engagement/README.md`
Owner: `domains/naval`
Last verified: `2026-09-28`

Status: `2026-09-28` planning. Scope, stage ladder, and finite task clusters are
drafted; `P0 Boundary` is active and no implementation cluster has started.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- [Naval owner README](../../../README.md)
- [Naval Minimal Task Structure](../../../standards/minimal_task_structure.md)
- [Naval Observation Contract](../../../standards/observation_contract.md)
- [Naval Domain Surface Split](../naval_domain_surface_split/README.md) — accepted
  bounded N4 package; its maintained surfaces are this package's starting point
- [Navy service profile](../../../../joint/service_profiles/standards/navy_profile.md)
- [Joint Command and Modeling Baseline](../../../../joint/standards/command_and_modeling_baseline.md)
- [Joint Command-Link and Reporting Baseline](../../../../joint/standards/command_link_and_reporting_baseline.md)
- [Air owner README](../../../../air/README.md)
- [Gradient Realism Principles](../../../../../systems/standards/gradient_realism_principles.md)
- [Subproject Creation Standard](../../../../../engineering/automation/rules/subproject_creation_standard.md)
- Unmerged equipment research catalog on `origin/codex/database-scaffold`
  (`database/research/equipment/catalog/**`), used as a parameter source only

## Purpose

This package builds a named, doctrinally complete engagement between two carrier
strike groups — a U.S. Navy `Gerald R. Ford`-class CSG and a PLA Navy
`Fujian`-class carrier group — and uses that scenario as the organizing target
for the naval infrastructure the repository still lacks.

The work is scenario-driven. It grows one runnable scenario ladder from static
order-of-battle presence to a full two-sided engagement. Each stage adds only
the infrastructure that stage needs, runs on its own, and is accepted against
the realism gate it claims. Every stage also ships a symmetric-mirror variant, in
which both sides field the same platform set, so mechanism defects can be
isolated before asymmetric named-platform effects are interpreted.

The first delivery is a scripted two-sided simulation. Learned policies are out
of scope, but every stage must leave the observation, action, and
termination-event boundaries that a later reinforcement-learning package would
consume.

This package replaces the historical `N0`-`N8` naval ladder as the forward plan
for naval combat capability. The earlier ladder, recorded in the
[naval progress snapshot](../../../reviews/naval_progress_snapshot_20260527.md),
remains dated provenance and is not extended.

## Current State

Measured on `work/naval-mechanisms` at `5fa7fc9e` on `2026-09-28`. The
[current status](carrier_strike_group_engagement_current_status_20260928.md)
records the full inventory.

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Naval platforms | bounded content | `examples/config/database/ships/units/*.json` (DDG-51 Flight I, ASW-helo DDG, Kilo MVP, Red surface placeholder, T-AKE) | no carrier, cruiser, Type 055/052D, SSN, or Chinese replenishment unit exists |
| Ship / submarine motion | kinematic | `src/systems/domains/naval/ship_motion_system.h`, `submarine_motion_system.h` | rate-limited speed/heading/depth; no hydrodynamics, turning circle, route following, or damage coupling |
| Command projection | accepted | `NavalCommandIntent` (`src/components/domains/naval/command/mission_command_naval.h`) | one screen station per ship; no multi-ship formation or group command hierarchy |
| Surface sensing | bounded | radar with sea clutter, ducting, and a horizon proxy (`src/models/domains/naval/naval_sensor_maritime_adapter.h`) | flat world; no geodetic frame |
| Undersea sensing | passive only | `src/systems/systems/sonar_system.h`, `src/models/systems/default_acoustic_model.cpp` | reads true positions of every Ship/Submarine; no active sonar, propagation profile, towed array, or sonobuoy |
| Naval weapons | bounded | `src/components/domains/naval/combat/weapon_naval.h`; `naval_mission_weapon_release_system.h` | gun and CIWS resolve as one hit roll; VLS only via the pilot-action path; no anti-ship missile, ship SAM family, or torpedo |
| Naval damage | synthetic | `DM-N1` profile in `src/components/domains/naval/combat/damage_naval.h`; `src/systems/combat/damage_system_naval.h` | compartment effects seed only on hitbox hits; ship motion ignores the damage state |
| Carrier aviation | absent | none | no catapult, arresting gear, deck/hangar capacity, sortie generation, or carrier landing |
| Air combat substrate | maintained on `main`; scripted stack unmerged | air combat scenarios; `origin/codex/scripted-stack-*` | reused, not re-owned; no carrier-based aircraft unit exists |
| Learned naval policy | absent | three smoke entries under `examples/config/training/active/naval/` | no checkpoint or training result |

## Scope

In scope:

- named platform units, each with source provenance, for both carrier groups:
  carriers, cruisers and destroyers, attack submarines, replenishment ships,
  carrier aircraft, embarked helicopters, and their weapons and sensors;
- the naval, carrier-aviation, undersea, and cross-cutting mechanisms each stage
  names in the phase plan, including command hierarchy, data links, electronic
  warfare, emission control, logistics, damage control, and outcome
  adjudication;
- one scenario ladder `CSG-S0`..`CSG-S6`, each stage in named and
  symmetric-mirror variants, with scenario contracts and tests;
- a measured throughput record (entities × fixed step × wall-clock) at every
  stage, run on HEI when the local host cannot complete it;
- reserved observation, action, and termination-event boundaries at every stage;
- replay and visualization of each stage scenario.

Out of scope:

- learned-policy training or any claim of learned-policy quality;
- land-based strike or support aircraft, space assets, and theater-level joint
  forces beyond the two groups; land-based bombers, long-range anti-ship
  ballistic missiles, and shore batteries are excluded from the first ladder;
- real-world operational assessment. Named platforms with sourced parameters do
  not make any scenario outcome a prediction about real forces;
- classified or non-public performance data; public sources only, with
  uncertainty recorded;
- changing Joint common-core semantics or Air-domain ownership; carrier aviation
  consumes Air mechanisms through their maintained owner surfaces.

## Phase Plan

The main ladder carries the air, surface, and strike path. An undersea track runs
in parallel because its write sets are largely disjoint; it must join before
`CSG-S6`. Each stage's claim ceiling uses the shared `G0`-`G7` labels.

| Phase | Stage scenario | Infrastructure added | Claim ceiling | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | none | package scope, stage ladder, claim ceilings, parameter-provenance policy | docs only | active |
| `CSG-S0` | both groups spawn statically with full order of battle | named units and loadouts; parameter provenance; geodetic frame and earth curvature; scenario schema for group composition | `G0` | planned |
| `CSG-S1` | both groups transit in formation | group formation and screen geometry; route following; ship turning and speed response; damage-to-mobility coupling; replenishment scheduling; fuel and endurance | `G1`-`G2` | planned |
| `CSG-S2` | deck cycle: launch waves, CAP, recovery | catapult and arresting-gear cycle; deck, elevator, and hangar capacity; sortie generation; recovery pattern and carrier landing; aircraft fuel and aerial refuelling; embarked helicopters | `G3` | planned |
| `CSG-S3` | mutual search and tactical picture | AEW aircraft; data-link track sharing with latency and capacity; ESM and emission control; target identification; removal of truth reads in naval sensing | `G4` | planned |
| `CSG-S4` | one-way strike against a defending group | anti-ship missiles; layered ship air defense and fire-control channels; soft-kill decoys and jamming; leaker damage through compartments; damage control and capability loss | `G5` | planned |
| `CSG-S5` | two-sided air-sea battle | fighter escort and intercept; stand-off jamming; strike planning and target assignment across the group; weapon and magazine depletion | `G6` | planned |
| `CSG-S6` | full engagement, named and mirror | undersea track joined; outcome and termination adjudication; whole-engagement replay; reserved RL boundaries frozen | `G6`, selected `G7` items | planned |
| `CSG-U1` | submarines transit and hold depth | submarine depth, speed, and self-noise coupling; quiet running | `G1`-`G2` | planned |
| `CSG-U2` | undersea search | propagation model; active sonar; towed array; dipping sonar and sonobuoys; submarine truth-read removal | `G4` | planned |
| `CSG-U3` | torpedo engagement | heavyweight and lightweight torpedoes; guidance, run, and fuze; torpedo countermeasures; below-waterline damage; submarine-launched anti-ship missiles through the `CSG-S4` path | `G5` | planned |
| `P5 Closure` | none | acceptance, indexes, archive | docs only | planned |

Dependencies: `CSG-S(n)` requires `CSG-S(n-1)` accepted. `CSG-U1` requires
`CSG-S0`; `CSG-U2` requires `CSG-U1` and `CSG-S3`; `CSG-U3` requires `CSG-U2`
and `CSG-S4`. `CSG-S6` requires `CSG-S5` and `CSG-U3`.

### Cross-Cutting Mechanism Register

Mechanisms that span several stages. Each has one introducing stage; later
stages must keep it in use rather than bypass it.

| Mechanism | Introduced | Consumed by | Notes |
| --- | --- | --- | --- |
| Geodetic frame and earth curvature | `CSG-S0` | every later stage | radar horizon, missile range, and data-link reach all depend on it |
| Environment: sea state, wind, day/night | `CSG-S1` | `S2` deck limits, `S3` sensing, `U2` acoustics | sea state already reduces ship speed |
| Group command hierarchy and authority | `CSG-S1` | `S3` reporting, `S5` target assignment | uses Joint command relationships; no new common-core fields |
| Fuel, endurance, and replenishment | `CSG-S1` (ships), `CSG-S2` (aircraft) | `S5` sortie planning | |
| Magazines, reload, and depletion | `CSG-S4` | `S5`, `S6` | VLS cells do not reload at sea |
| Data-link latency and capacity | `CSG-S3` | `S4` cueing, `S5` | cooperative engagement is a later `G7` item |
| Identification and classification | `CSG-S3` | `S4`, `S5`, `U2` | ties ROE to identity confidence |
| Electronic warfare and emission control | `CSG-S3` (ESM, EMCON) | `S4` soft-kill, `S5` stand-off jamming | |
| Damage control and capability degradation | `CSG-S4` | `S5`, `S6`, `U3` | includes loss of flight-deck capacity |
| Search and rescue of downed aircrew | `CSG-S5` | `S6` | scripted recovery only; no ground combat |
| Outcome adjudication and termination | `CSG-S6` | RL follow-on package | mission-kill and loss thresholds are declared, not tuned |
| Replay, visualization, throughput record | `CSG-S0` | every stage | |

## Task Clusters

- Task-cluster plan:
  [carrier_strike_group_engagement_task_clusters_20260928.md](carrier_strike_group_engagement_task_clusters_20260928.md)
- Current status:
  [carrier_strike_group_engagement_current_status_20260928.md](carrier_strike_group_engagement_current_status_20260928.md)
- Dispatch queue:
  [carrier_strike_group_engagement_dispatch_queue_20260928.md](carrier_strike_group_engagement_dispatch_queue_20260928.md)
- Acceptance gate:
  [carrier_strike_group_engagement_acceptance_20260928.md](carrier_strike_group_engagement_acceptance_20260928.md)

## Outputs And Evidence

Each accepted stage must leave:

- scenario files under `scenarios/naval/csg/` in named and mirror variants;
- scenario contracts under `tests/contracts/unit/naval/csg/`;
- focused native and Python tests for every mechanism the stage added;
- a throughput record: entity count, fixed step, simulated duration, wall-clock
  time, host;
- a replay artifact and a visualization profile;
- a stage acceptance record in this directory naming its claim ceiling and
  residuals.

Platform content must leave a provenance record for every parameter: source ID,
source tier, and uncertainty. The equipment research catalog is the first
source; public-web research fills gaps and is recorded the same way.

## Acceptance Gate

The package can be marked accepted only when:

- `CSG-S0`..`CSG-S6` and `CSG-U1`..`CSG-U3` each have a stage acceptance record;
- the named and mirror `CSG-S6` scenarios run to adjudicated termination on the
  maintained runtime, with replay;
- every stage's claim ceiling is met by maintained runtime evidence, not
  diagnostics-only paths (Claim Rule 3 of the gradient realism principles);
- no naval sensing path used by the scenarios reads another entity's true state
  where the stage claims `G4` or higher;
- the reserved RL observation, action, and termination-event boundaries are
  documented and exercised by a scripted controller;
- every named-platform parameter has a provenance record;
- no document or result claims learned-policy quality or real-world operational
  prediction.

## Residuals And Next Steps

- `P0 Boundary` needs owner review of this README, the task clusters, and the
  acceptance gate.
- `CSG-S0` is the first implementation stage. Its geodetic-frame cluster touches
  shared runtime surfaces, so it runs serially.
- The throughput record at `CSG-S1`/`CSG-S2` decides whether uniform
  high-fidelity stepping holds for the full order of battle. Mixed step rates
  need a separate decision; this package does not assume them.

## Archive

Stage acceptance records move to `docs/domains/naval/reviews/` once accepted.
Lasting facts, such as platform provenance rules or the group-formation contract,
are promoted to naval standards or references. Superseded planning records go to
`archive/` under the repository lifecycle policy.
