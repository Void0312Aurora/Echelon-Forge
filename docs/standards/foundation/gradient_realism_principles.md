# Gradient Realism Principles

Language:
- English canonical: `foundation/gradient_realism_principles.md`
- Chinese companion: [gradient_realism_principles.zh.md](gradient_realism_principles.zh.md)

Status: `2026-05-24` authoritative foundation rule for multi-domain realism gating.

This document defines how the project treats domain realism as scenario
complexity increases. It is a standards-tree foundation document because the
rule applies across air, naval, ground, joint command, sensors, weapons, and
future domains.

The central rule is:

> A scenario may only claim the realism level whose required domain mechanisms
> are implemented, visible to the runtime contract, and covered by evidence.

This prevents a simple cruise-level model from being described as a credible
engagement model just because the scenario now contains weapons, opponents, or
more entities.

## Purpose

Gradient realism exists to keep three things aligned:

- scenario complexity
- implemented domain mechanisms
- claims made in documentation, training configs, evaluation reports, and task
  plans

As a scenario adds more tactical demands, the minimum realism gate rises. A
scenario that only asks an aircraft to cruise can accept a narrower flight model
than a scenario that asks an agent to fight through high angle-of-attack
maneuvering, sensor uncertainty, weapon release, and ROE constraints.

## Realism Is Not A Single Switch

The project does not use a single "realistic / unrealistic" label. Instead,
realism is scoped to the scenario layer being exercised.

Examples:

- A route-following scenario can be valid with route guidance, wind handling,
  stable speed/altitude behavior, and reward/termination sanity.
- A landing scenario needs additional runway, approach, gear, flare, and
  touchdown behavior before it can be called realistic enough for landing work.
- An engagement scenario needs additional sensor, track, weapon, ROE,
  damage/effects, and high-maneuver flight behavior before it can be treated as
  a credible combat-training scenario.

Passing a lower gate never implies that higher gates have passed.

## Gradient Levels

The following labels are shared project vocabulary. They are not exhaustive
physics requirements; they define the minimum claim boundary.

| Level | Scenario capability | Minimum realism gate |
| --- | --- | --- |
| `G0` | Static setup / entity presence | Units spawn with coherent identity, side, position, and basic state. |
| `G1` | Stable motion / cruise | Kinematics, speed/altitude/heading response, finite-state safety, and basic energy behavior are stable enough for route or cruise tasks. |
| `G2` | Route, weather, and formation tasks | Navigation, wind, route geometry, role/slot visibility, and multi-agent spacing semantics are represented at the task-observation boundary. |
| `G3` | Takeoff, landing, recovery, station, or terrain-constrained execution | The domain-specific surface or terrain constraints that define the task are represented and can terminate/reward the episode coherently. |
| `G4` | Sensor contact, reporting, and shared tactical picture | Agents no longer depend on hidden truth for the relevant task; contacts, tracks, classification, reporting, and data sharing have explicit visibility and quality semantics. |
| `G5` | Weapon release, ROE, and minimum engagement lifecycle | Weapon authorization, target assignment, launch constraints, ammunition/cooldown, guidance/effects events, and engagement termination are represented by maintained contracts. |
| `G6` | Credible adversarial combat or contested multi-domain behavior | High-maneuver platform behavior, sensor/track uncertainty, weapon envelopes, damage/effects, command authority, and reward/termination shaping are strong enough that policy success is not dominated by non-tactical artifacts. |
| `G7` | Advanced contested realism | Electronic warfare, deception, relay/latency constraints, authority transfer, multi-platform coordination, and domain-specific countermeasures are represented well enough for the scenario's stated claims. |

Projects may add domain-specific sub-gates under these labels, but they should
not redefine the labels locally.

## Claim Rules

1. A scenario's realism claim must name the highest gate it actually satisfies.
2. A training or evaluation result must not imply a higher gate than the
   scenario, runtime, and evidence support.
3. A feature being wired into the runtime is not enough to raise the gate. The
   feature must also affect observations, rewards, termination, diagnostics, or
   traceable runtime products in a maintained path.
4. Compatibility or diagnostics-only paths do not establish maintained realism
   unless the gate explicitly allows them.
5. A regression at a lower gate blocks claims at all higher gates that depend on
   it.

## Regression Rule

When infrastructure work changes runtime ownership, facade paths, batch paths,
observation provenance, action injection, or compatibility gates, realism must
be rechecked at the highest active scenario gate.

If a new failure mode appears after such work, it should be recorded as a
possible realism regression until isolated. This applies even if the functional
scenario still runs.

For example, if a `1v1` air-combat scenario still launches, detects targets, and
fires weapons but episodes become dominated by deep-stall termination, the
scenario remains functionally connected but must not be claimed as credible
combat realism until the flight-stability gate is restored.

## Cross-Domain Rule

A multi-domain scenario is limited by the weakest domain gate that materially
affects the task.

Examples:

- A naval air-defense scenario with credible ship motion but truth-leaking
  target classification is not a credible sensor/engagement scenario.
- A ground support scenario with plausible tasking but no terrain-masked
  sensing should not claim contested ground reconnaissance realism.
- An air-combat scenario with weapon launch and damage events but unstable
  high-angle-of-attack behavior should remain below credible combat realism.

## Evidence Expectations

Each gate should have evidence appropriate to its risk:

- `G0-G2`: focused runtime tests, shape/roundtrip tests, and finite-state smoke.
- `G3-G4`: scenario-specific termination/reward checks, observation visibility
  checks, and diagnostics for task-critical quantities.
- `G5-G6`: engagement lifecycle tests, authority/ROE checks, flight/sensor/weapon
  realism guards, and short policy or scripted-rollout diagnostics.
- `G7`: explicit contested-behavior tests with traceable jamming, deception,
  relay, authority-transfer, or coordination evidence.

The evidence only needs to cover the scenario's claim. It does not need to
implement unrelated high-fidelity behavior early.

## Documentation Rule

Task documents and README files should distinguish:

- functional progress: the scenario path runs or a feature is wired
- realism gate: the highest gradient level currently supported
- blocking realism regressions: lower-gate failures that prevent higher claims

This distinction is required for multi-domain simulation work. It keeps
incremental progress useful without overstating alignment with the real domain.
