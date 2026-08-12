# Weapons and Engagement Rules Roadmap

Language:
- English canonical: `weapons_engagement.md`
- Chinese companion: not maintained (English-only work surface).

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/systems/weapons/work/issues/weapons_engagement.md`
Owner: `systems/weapons`
Last verified: `not established`
Content status: not reverified during the 2026-08-07 ownership migration.

This document records the planning goals for missiles and engagement rules as a
reference for later iterations.

## Current Simplified Model
- Missiles use pursuit guidance with fixed speed and fixed turn rate.
- Hit detection is based on a distance threshold and damage value.
- Target state is represented only by HP.

## Core Capabilities Still Needed

### Launch Envelope
- Establish launch conditions from range, energy, and target-relative motion.
- Basic conditions: distance, line-of-sight angle, target angular rate, and
  remaining missile energy.
- Envelope progression: simple geometric threshold -> energy threshold ->
  maneuver threshold.

### Seeker Constraints
- Field-of-view (FOV) limit and boresight off-axis limit.
- Lock range / lock-on time.
- Break-lock conditions: excessive off-axis angle, obscuration, insufficient
  signal-to-noise ratio.

### Guidance Delay and Response
- Guidance lag: delay from command to control response in the processing /
  execution chain.
- Target-data delay: latency from sensor measurement to missile guidance (track
  age).
- Guidance update period: synchronized with seeker scan timing.

### Guidance Model Upgrades
- Simple pursuit -> proportional navigation (PN) or augmented proportional
  navigation (APN).
- Couple guidance commands to maneuver capability limits (max G / turn-rate
  constraints).
- Terminal guidance logic (late-stage weighting or mode switching).

### Hit and Effect Layers
- Hit result levels:
  - `Hit`
  - `Kill`
  - `MissionKill`
  - `MobilityKill`
  - `SensorKill`
- Failure levels:
  - `Seeker Lost`
  - `Burnout`
  - `Over-G`
  - `Self-Destruct`

## Suggested Data Structures
- `MissileModel`: propulsion, drag, max G, burn time, guidance delay.
- `SeekerModel`: FOV, lock range, lock-on time, scan period, SNR threshold.
- `EngagementRules`: launch-envelope parameters, hit-decision policy, and
  failure-decision policy.

## Logging and Evaluation
- Record each launch: launch conditions, lock time, break-lock reason, and hit
  result.
- Metrics: launch success rate, lock retention time, probability of hit, and
  mission-kill rate.

## Stepwise Rollout Plan
1) First add guidance delay and seeker FOV / lock-range checks. (Implemented)
2) Add PN guidance and G-limit constraints. (PN implemented; G-limits still to
   be integrated)
3) Add layered hit outcomes and update the effects model.
4) Build launch-envelope estimation and support rule configuration in
   scenarios.

## Current Implementation Summary
- Guidance delay and update period: missiles begin guidance after
  `guidance_delay_s`, and guidance updates run on
  `guidance_update_period_s`.
- Seeker constraints: FOV and `seeker_lock_range` act as lock conditions.
- Guidance model: 2D PN (proportional navigation) controlled by `nav_gain`.
