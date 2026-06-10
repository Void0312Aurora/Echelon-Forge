# Naval N4 RL Task Surface Preflight

Status: `2026-05-25` pass / accepted as a docs-only preflight surface.

Language:

- English canonical: `naval_n4_rl_task_surface_preflight_20260525.md`
- Chinese companion:
  [naval_n4_rl_task_surface_preflight_20260525.zh.md](naval_n4_rl_task_surface_preflight_20260525.zh.md)

Inputs:

- [N4 threat / ROE bridge task cluster](naval_n4_threat_roe_bridge_cluster_20260524.md)
- [N4 threat / ROE dispatch queue](naval_n4_threat_roe_dispatch_queue_20260524.md)
- [N4 integration acceptance](naval_n4_integration_acceptance_20260525.md)
- [Naval current progress](../naval_current_progress_20260524.md)

## Decision

The first naval RL curriculum after the screen/contact MVP should stay inside
the accepted `N3 -> N4` bridge. It should use the N4 threat/ROE state as
observable decision context, but it should not add a weapon-release action or
claim a learned engagement policy.

Recommended order:

1. `naval_contact_report_threat_roe_v1`: report and classify a closing surface
   contact while preserving valid threat/ROE provenance.
2. `naval_screen_station_hold_threat_aware_v1`: keep the DDG/T-AKE screen
   geometry stable while threat and ROE state are visible to the policy.
3. `naval_limited_engagement_v1`: defer until N5 launch/reject gates are
   accepted.

This preflight freezes the task surface only. It does not create trainer
configs, rewards in code, policy checkpoints, or evaluation dashboards.

## Realism Boundary

| Boundary | Included | Excluded |
| --- | --- | --- |
| `N1-N3` screen/contact | ownship station keeping, HVU protection, contact report, shared-track continuity | fleet-level C2 and multi-ship tactics |
| `N4` threat/ROE | threat state, ROE state, engagement authority, assigned-target provenance, track-source quality | launch-event success, hit/intercept result, damage outcome |
| `N5+` engagement/damage | read-only out-of-scope detection for safety termination | weapon-release action, damage reward, kill-based termination |

The task may observe `authorization_to_fire`, but an RL action must not fire in
the N4 curriculum. If a later environment exposes weapon controls, the N4 task
must mask them or terminate as an out-of-scope transition.

## Observation Surface

Minimum observation groups:

| Group | Fields |
| --- | --- |
| Screen geometry | DDG-HVU range, station radius error, station bearing error, relative bearing to HVU, ownship speed, ownship heading |
| Contact geometry | contact range, bearing, closure rate, local/shared track age, contact source, source confidence or quality |
| N4 state | `threat_state`, `roe_state`, `authorization_to_fire`, engagement authority holder/grantor ids |
| Target provenance | `assigned_target_id`, `assigned_target_track_id`, `assigned_target_source_id`, `assigned_target_snapshot_time_s`, assigned-target age |
| Report chain | last report age, report/track presence flags, command-chain active flag, facade/world-batch packet provenance |
| Safety flags | HVU blind-zone exposure, stale-track flag, unauthorized-fire event flag, N5/N6 transition flag |

Normalization rules:

- ids should be projected as presence, equality, or stable small-coded features
  unless a later model explicitly supports entity-id embeddings;
- track and target ages should be clipped to the contract window;
- source and state enums should use stable numeric codes from maintained
  command/tasking surfaces;
- unknown or absent provenance should be an explicit feature value, not
  silently folded into zero-confidence valid state.

## Action Surface

Allowed action families:

- hold current screen station;
- adjust desired station radius or bearing within accepted N3 limits;
- adjust speed or heading command within ship-motion bounds;
- report, classify, or request confirmation for the contact;
- acknowledge or request ROE state update;
- maintain assigned-target acknowledgement without creating a new target from
  static metadata.

Forbidden action families:

- weapon release;
- hit/kill/damage declaration;
- direct inventory edits;
- bypassing report or track provenance to set threat state;
- overwriting ROE state without an auditable scenario condition.

## Reward Surface

Reward candidates:

- positive reward for staying inside the screen station window;
- positive reward for timely contact report and shared-track continuity;
- positive reward when threat escalation is backed by fresh track provenance;
- small positive reward for stable ROE/authority consistency;
- penalty for false threat escalation;
- penalty for stale-track target assignment;
- penalty for HVU exposure or station loss;
- strong penalty or immediate failure for unauthorized fire attempts.

The reward must not use hit probability, intercept success, damage amount, or
kill state in N4.

## Termination Surface

Success candidates:

- contact exits the threat window after valid report, threat, and ROE handling;
- the episode reaches the planned horizon with station geometry inside the N3
  window and no N5/N6 transition;
- assigned-target provenance remains valid through the final decision window.

Failure candidates:

- HVU exposure exceeds the accepted N3 tolerance;
- threat/ROE state cannot be justified by valid track provenance;
- target assignment appears from static metadata alone;
- unauthorized fire is attempted or recorded;
- required weapon release, hit, damage, or kill state appears before the task is
  promoted to N5;
- timeout without contact report or threat-state resolution.

## Evaluation Gates

Before implementing a trainer, add deterministic gates for:

- observation schema includes all required N4 groups;
- action mask excludes weapon release in the N4 task;
- reward does not reference damage or kill state;
- seeded scenario rollouts preserve the N3 screen/contact contracts;
- assigned-target provenance cannot be missing when `threat_state` is elevated;
- stale track age is penalized or rejected;
- unauthorized fire is a failure signal, not a success path.

Suggested later validation commands:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/leader/test_tasking_profile_contracts.py tests/leader/test_command_field_projection_contracts.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "naval_owner_slice or task_order_naval or command_chain or mission_command"
```

## Acceptance

This preflight is accepted because it:

- names the first two N4-compatible RL task candidates;
- defines observation, action, reward, termination, and evaluation surfaces;
- consumes the accepted N4 threat/ROE fields;
- keeps weapon release, damage, and learned-policy claims out of scope.

The naval RL line is ready for a later implementation package, not for a
trained-policy claim.

## Residuals

- Create concrete trainer/eval config entrypoints only after owner approval.
- Add observation-schema tests before a policy loop is launched.
- Keep `naval_limited_engagement_v1` blocked behind N5 launch/reject gates.
