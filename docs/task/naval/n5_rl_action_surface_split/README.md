# N5 RL Action Surface Split

Status: `2026-05-26` implemented for the first maintained naval RL action and
observation surface slices. This is still an `N4` pre-fire training-entry
repair, not an `N5` weapon-engagement release.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- [N4 threat / ROE bridge](../n4_threat_roe_bridge/README.md)
- [N4 RL task surface preflight](../n4_threat_roe_bridge/naval_n4_rl_task_surface_preflight_20260525.md)
- [Common / air / naval split plan](../../common_air_naval/common_air_naval_modular_split_plan_20260515.md)
- [Naval standards](../../../standards/naval/README.md)
- [Air action contract](../../../standards/air/act.md)
- [Subagent usage policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Separate the naval RL control surface from the air takeoff training surface.

The N4 training entries were useful because they proved the scenario, reward,
and maintained world-batch runtime path. Formal training then showed a domain
mismatch: `action_mode=takeoff4` emits air-style `PilotAction`
stick/rudder/throttle values, and ship motion treats non-neutral rudder or
throttle as manual takeover. That bypasses the better naval station-hold
command path.

This project releases a bounded repair: a dedicated pre-fire naval action mode
that changes station-order intent through the naval task/command chain while
keeping the low-level pilot-action carrier neutral, plus a naval mission
observation mode that names station, contact, ROE, report-chain, and target
provenance fields directly.

## Output

- [N5 RL action surface split cluster](naval_n5_rl_action_surface_split_cluster_20260526.md)
- Maintained action mode: `naval_station3`
- Maintained observation mode: `naval_screen_station_v1`
- Active naval training-entry migration:
  `examples/config/training/active/naval/*.json`
- Focused runtime and training-entry tests.

## Scope

In scope:

- one dedicated naval RL action mode for station-order probing;
- one dedicated naval mission observation mode for station, contact, ROE,
  report-chain, and assigned-target fields;
- active N4 training-entry migration away from `takeoff4`;
- active N4 training-entry migration away from the air formation-role mission
  observation;
- world-batch pre-step command synchronization for the new action mode;
- focused tests proving no weapon release, no damage/kill reward, and no air
  takeoff action or air formation-role observation reuse in active naval
  entries.

Out of scope:

- weapon release, hit/intercept, damage, kill, or engagement reward;
- full naval helm/autopilot doctrine;
- cooperative naval multi-slot promotion;
- final naval packet ownership and cooperative observation schema;
- broad `MissionCommand` replacement with formal `CommandPacket`.

## Gate

This slice is mergeable when:

- active naval N4 configs use `action_mode=naval_station3`;
- zero naval action preserves the current station order;
- non-zero naval action updates station bearing/radius/speed intent through the
  naval task/command chain;
- active naval N4 configs use `mission_obs_mode=naval_screen_station_v1`;
- the policy mission vector exposes station error, screen separation, contact,
  support/report, ROE, and assigned-target fields;
- the ship pilot-action carrier stays neutral for the naval action mode;
- training bootstrap accepts the active entries;
- contract and reward tests remain pre-fire.

## Residuals

- Replace compatibility `MissionCommand` aggregation with narrower command and
  tasking packets once the architecture lane releases them.
- Promote cooperative naval slots only after non-agent roster accounting is
  accepted.
- Keep `naval_limited_engagement_v1` blocked behind a separate launch/reject
  package.
- Extend the first naval observation slice only when the scenario actually
  moves beyond screen-station and pre-fire contact/report behavior.
