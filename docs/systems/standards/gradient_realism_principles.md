# Gradient Realism Principles

Language:
- English canonical: `gradient_realism_principles.md`
- Chinese companion: [gradient_realism_principles.zh.md](gradient_realism_principles.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/systems/standards/gradient_realism_principles.md`
Owner: `systems/realism-governance`
Last verified: `2026-08-08`

Status: maintained cross-domain system-realism gate.

This document defines how the project treats domain realism as scenario
complexity increases. It is a cross-domain systems standard because the rule
gates claims against implemented mechanisms, runtime visibility, and evidence
across domains. The G0-G7 vocabulary is a policy and evidence scale; it does
not mean every level is implemented or enforced by every repository lane.

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

## Simplified-But-Credible Modeling Rule

The project's default target is not research-grade, engineering-grade, or
full-physics exactness. For most runtime, scenario, and RL workloads, the
correct target is:

> a simplified model that remains as realistic as practical while staying
> implementable, maintainable, and verifiable.

The simplification here is relative to research-grade or engineering-grade
models, not relative to game-like or toy abstractions. In other words, the
project does not require default implementation of highly detailed models whose
data support is weak and whose implementation cost is disproportionate, but it
also must not reduce a claimed tactical-realism problem into little more than a
functional wiring exercise for the sake of trainability.

An acceptable simplified model should preserve at least the following:

- causal structure: critical state, action, and event relationships remain
  intact
- relative ordering: better/worse, stronger/weaker, nearer/farther consequence
  directions remain broadly aligned with real tactical expectations
- consequence chains: the observation changes, constraints, risks, windows,
  damage, failure modes, or authority logic that the task actually depends on
  leave visible runtime effects
- verifiable boundaries: the claimed precision level matches available data,
  test evidence, and implementation strength

An unacceptable pseudo-high-fidelity model often shows one or more of these
signs:

- numerically finer output without source support or reasonable calibration
- many parameters while the key causal direction is still wrong, causing policy
  learning to optimize simulator artifacts instead of tactics
- dense local detail while the consequence chain that matters to the task is
  still missing

The target, then, is neither "make everything engineering-grade by default" nor
"turn it into game rules for convenience," but a tactically credible simplified
model between those extremes that can support both reasoning and RL learning.

This rule is cross-domain. It applies not only to lethality models, but also to
flight dynamics, sensing, weapon guidance, electronic warfare, air/ground/naval
platform behavior, command chains, logistics constraints, and future domains.

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
