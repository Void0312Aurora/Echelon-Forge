# Naval Current Progress Tracking

Status: `2026-05-25` workspace sampling review with N4 bridge acceptance.

This is the active tracking entry for `docs/task/naval/` after the
`2026-05-17` naval progress checkpoint. It focuses on infrastructure, naval
domain behavior, and RL integration.

Current positioning:

- The minimal realistic naval screen/contact scenario is stable.
- The naval domain now has a runnable tactical-prototype skeleton.
- RL/tasking integration has profile, contract, and batch-sync plumbing.
- Dedicated naval training tasks, rewards, curriculum, and evaluation gates are
  still pending.

## Current Conclusion

The naval line has moved beyond the older checkpoint where gun and
`MissionCommand -> CIWS` paths were still red. Current focused validation shows:

- contact-report and closing-contact DDG/T-AKE screen scenarios are present;
- closest-approach, HVU blind-zone, shared-track, and report-chain contracts pass;
- screen-hold disturbance recovery and late-oscillation guards pass;
- the previous gun and `MissionCommand -> CIWS` red points now pass focused runtime tests;
- `tasking_profile: naval` reaches the Python RL tasking bridge and maintained
  TaskOrder/MissionCommand/LeaderIntent/PilotReport contract projections;
- world-batch and cooperative vec env command-chain sync project naval fields
  through maintained assignments rather than relying only on old whole-shell
  compatibility transport.
- the `ddg51_take1_screen_threat_roe_v1` N4 bridge is accepted as a pre-fire
  scenario expansion with maintained threat/ROE and assigned-target provenance.

The remaining risk is mostly not "does the chain exist?" but "how much of it is
still MVP or engineering approximation?"

## Realism Gradient

Naval-domain realism should be accepted by the complexity actually used by a
scenario, not by whether a named subsystem exists somewhere in the codebase.
The working rule is:

- simple cruise or station-keeping scenarios only need cruise/station-keeping
  realism;
- contact-report scenarios additionally need sensor, track-sharing, and report
  realism;
- fire-control scenarios must first satisfy weapon, authorization, damage, and
  termination critical points;
- unused domain capabilities may remain MVP, but they must not be used to claim
  realism for a more complex scenario.

Suggested critical points:

| Grade | Scenario entry | Minimum realism requirement | Current state |
| --- | --- | --- | --- |
| `N0` platform identity | static units, formation display, geometry only | real public platform identity, role, basic dimensions/speeds/sensor families, source labels for approximations | present |
| `N1` cruise/transit | ships move by heading/speed or hold simple station | speed limits, acceleration/deceleration, turn rate, low-speed steerage, maritime state, mass/stores that do not break runtime | MVP present; enough for simple cruise and station-keeping |
| `N2` contact/report | detect, share tracks, report contacts | radar horizon, sea-state loss, LOS, data-link throttling, track source, report semantics, HVU blind-zone gates | current screen/contact contracts pass |
| `N3` screen/C2 | escort, station hold, disturbance recovery | `TASK_SCREEN/TASK_SUPPORT`, naval roles, station radius/bearing, reference entity, recovery and oscillation guards | single DDG/HVU screen present; not full fleet C2 |
| `N4` threatened maneuver/ROE | threat approach, target priority, pre-fire authorization | ROE state, engagement authority, target assignment, threat priority, sensor quality affecting decisions | pre-fire bridge accepted for `ddg51_take1_screen_threat_roe_v1`; still not a complete tactical commander |
| `N5` weapons engagement | VLS, gun, CIWS, or missile engagement is a scenario objective | fire-control prerequisites, valid track, range/arcs/cooldown/inventory, launch event, rejection reason, hit/intercept evidence | minimal skeleton passes focused tests; scenario-level gates still needed for firefight tasks |
| `N6` hit/damage/termination | damage evolves or decides outcome | mission/mobility/sensor kill, continuing fire/flooding proxy, capability degradation, termination and reward binding | proxy present; not high-fidelity survivability |
| `N7` ASW/embarked air/logistics | sonar, submarine, helo, or UNREP is core gameplay | acoustic propagation, contact confidence, sortie/recovery constraints, UNREP windows and store transfer | token/MVP; good for chain validation, not high-fidelity core tasks |
| `N8` fleet/learned tactics | multi-ship, multi-role, long-horizon RL or operational C2 | multi-node comms, command relationships, cooperative tactics, adversary policy, curriculum/eval coverage | not started |

The current naval scenarios mainly sit at `N1-N3`:

- `ddg51_take1_screen_contact_report_v1` is primarily an `N2` contact/report
  realism gate.
- `ddg51_take1_screen_closing_contact_v1` adds contact closure and `N3`
  screen-geometry stability.
- `ddg51_take1_screen_threat_roe_v1` is accepted as an `N4` pre-fire bridge:
  threat/ROE state and assigned-target provenance are observable, but weapon
  release and damage are not acceptance proof.
- Weapons, CIWS, damage, ASW, embarked air, and UNREP have runtime tests, but
  they are currently infrastructure and local chain evidence. They do not by
  themselves promote the current screen/contact scenarios into firefight or full
  naval-combat scenarios.

Future scenarios should declare which grade they enter and turn that grade's
critical points into tests or contracts. For example:

- `naval_screen_station_hold` should gate mostly `N1-N3`;
- `naval_contact_report` must gate `N2` sensor/shared-track/report behavior;
- `naval_surface_engagement` must first add `N4-N6` scenario-level ROE,
  fire-control, launch-event, damage, and termination gates.

## Infrastructure

Scenarios:

- [ddg51_take1_screen_contact_report_v1.json](../../../scenarios/naval/ddg51_take1_screen_contact_report_v1.json)
- [ddg51_take1_screen_closing_contact_v1.json](../../../scenarios/naval/ddg51_take1_screen_closing_contact_v1.json)
- [ddg51_take1_screen_threat_roe_v1.json](../../../scenarios/naval/ddg51_take1_screen_threat_roe_v1.json)

Contracts:

- [naval_screen_contact_report_geometry.json](../../../tests/contracts/unit/naval/naval_screen_contact_report_geometry.json)
- [naval_screen_closing_contact_geometry.json](../../../tests/contracts/unit/naval/naval_screen_closing_contact_geometry.json)
- [naval_screen_threat_roe_geometry.json](../../../tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json)
- [scenario_loader_naval_common_core_semantics.json](../../../tests/contracts/unit/naval/scenario_loader_naval_common_core_semantics.json)

Runtime surfaces now include ship/submarine platform components, ship and
submarine motion systems, embarked-air token ops, naval command/task-order
extension slices, structured naval weapon mounts, a mission-command weapon
release system, and abstract UNREP/logistics state.

The important infrastructure change is that naval fields are no longer just
JSON metadata. They are exercised through ECS components, systems, Python
bindings, runtime tests, contracts, and world-batch maintained projections.

## Domain State

Implemented MVP behavior includes:

- ship acceleration, deceleration, turn-rate limits, low-speed steerage, sea
  state, wave heading/period, maritime environment override, roll/pitch proxy,
  and added resistance;
- surface-radar horizon, sea-state loss, ducting approximation, ESM
  bearing-only contacts, sonar/acoustic MVP, source-preserving tracks, and
  less-flooded data-link sharing;
- `TASK_SCREEN` / `TASK_SUPPORT`, naval role defaults, station type defaults,
  station-keeping, screen-hold recovery, and oscillation guards;
- structured `VLS / gun / CIWS` mounts, minimal VLS-SAM launch, gun direct fire,
  simplified CIWS intercept, mission-command-driven CIWS, launch adapter
  request/event shape, intermediate damage states, and ongoing damage proxy;
- abstract naval stores, UNREP window/connect/transfer/complete state, and
  token-level embarked helo launch/recover/relay behavior.

Boundaries:

- This is not full fleet C2.
- Weapon and damage chains are engineering approximations, not complete naval
  fire-control, ballistics, channels, EW, compartment, stability, flooding, or
  damage-control models.
- ESM, sonar, UNREP, and embarked air are MVP/token-level surfaces.

## RL Integration

Existing RL/tasking integration:

- [naval_profile.py](../../../python/rl/profile/naval_profile.py) owns naval
  defaults and `build_kernel_mission_command()`;
- [naval_adapter.py](../../../python/rl/tasking/naval_adapter.py) exposes the
  profile through the tasking bridge;
- [bridge.py](../../../python/rl/tasking/bridge.py) resolves
  `tasking_profile: naval` and `ServiceProfile.Navy`;
- [observations.py](../../../gym_envs/leader_env_parts/decision_runtime/observations.py)
  consumes profile-specific task observation codes;
- [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py) and
  [cooperative_world_batch_vec_env.py](../../../python/rl/runtime/cooperative_world_batch_vec_env.py)
  project command-chain state through maintained assignments;
- [command_chain_cache.py](../../../python/rl/runtime/world_batch/command_chain_cache.py)
  covers naval owner-slice snapshots and maintained contract projection.

Current limitation: naval RL has integration plumbing, not a full dedicated
training product. It should not yet be described as a learned naval screen,
engagement, ASW, or UNREP policy.

N4 RL preflight is now recorded under
[naval_n4_rl_task_surface_preflight_20260525.md](n4_threat_roe_bridge/naval_n4_rl_task_surface_preflight_20260525.md).
The accepted next RL-compatible task candidates are:

- `naval_contact_report_threat_roe_v1`;
- `naval_screen_station_hold_threat_aware_v1`.

Both now have active smoke/probe entrypoints under
[examples/config/training/active/naval](../../../examples/config/training/active/naval/README.md).
These entries are implementation gates, not trained-policy evidence: they pair
the accepted N4 scenario with the maintained world-batch training path, use a
temporary no-release action surface, and keep weapon release, damage rewards,
kill rewards, and learned-policy claims out of scope. `naval_limited_engagement_v1`
remains blocked behind N5 launch/reject and non-damage gates.

## Validation

Sampling time: `2026-05-24 21:24 CST`.

Passed:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/naval/test_naval_ship_database.py tests/runtime/naval/test_naval_screen_scenario.py tests/runtime/naval/test_naval_sensor_realism_runtime.py tests/runtime/naval/test_naval_asw_helo_runtime.py tests/runtime/engagement/test_naval_launch_adapter.py tests/leader/test_naval_profile_semantics.py tests/leader/test_naval_contract_fields.py
# 49 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_contact_report_geometry.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_closing_contact_geometry.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/scenario_loader_naval_common_core_semantics.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "naval or task_order or command_chain"
# 5 passed, 22 deselected

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "naval_owner_slice or task_order_naval or command_chain"
# 5 passed, 54 deselected

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/mission/test_mission_command_naval_fields_roundtrip.py tests/runtime/mission/test_naval_mission_command_mapping.py tests/runtime/mission/test_ship_mission_command_authority.py
# 12 passed
```

N4 bridge acceptance:

- [N4 RL task surface preflight](n4_threat_roe_bridge/naval_n4_rl_task_surface_preflight_20260525.md)
- [N4 integration acceptance](n4_threat_roe_bridge/naval_n4_integration_acceptance_20260525.md)

Docs validation:

```bash
git diff --check -- docs/task/naval
# passed
```

N4 active training-entry gate:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_naval_active_training_entries.py
# 4 passed, 4 subtests passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json --train_config examples/config/training/active/naval/naval_contact_report_threat_roe_smoke_v1.json --output_base /tmp/cmo-naval-train.<tmp> --run_name naval_contact_report_threat_roe_smoke_v1
# Training Complete.

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json --output_base /tmp/cmo-naval-train.<tmp> --run_name naval_screen_station_hold_threat_aware_smoke_v1
# Training Complete.

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
# PASS
```

## Next Focus

Recommended next steps:

1. Turn the accepted N4 RL preflight into a concrete implementation package for
   `naval_contact_report_threat_roe_v1` or
   `naval_screen_station_hold_threat_aware_v1`.
2. Continue moving loader-owned raw simulation compatibility seams toward
   facade-owned maintained command-chain surfaces.
3. Add facade or world-batch acceptance around naval mission-command weapons,
   screen-hold, and `tasking_profile: naval`.
4. Keep `naval_limited_engagement_v1` blocked until a separate N5 package
   defines launch/reject, range/arc/cooldown/inventory, action masking, and
   non-damage acceptance gates.
5. Strengthen maritime-state field tests, sensor/LOS coupling, and naval weapon
   command stability before expanding into larger fleet combat.
6. Replace the temporary N4 no-release execution probe with a dedicated naval
   observation/action/reward/eval package before any learned-policy or
   cooperative naval training claim.
