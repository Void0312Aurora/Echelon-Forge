# Naval Domain Surface Split

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/naval_domain_surface_split/README.md`
Owner: `domains/naval`
Last verified: `2026-09-23`

Status: `2026-09-23` active; the bounded N4 closure is **accepted**. `P2-B` command
projection landed as `NavalCommandIntent` with a single maintained write seam, and the
split branch now has an executable native projection regression test. N5/N6 remain
separate blocked work.
See the [`P5-A` closure record](naval_domain_surface_split_p5_closure_20260922.md).

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- [Naval owner README](../../../README.md)
- [Naval progress snapshot](../../../reviews/naval_progress_snapshot_20260527.md)
- [N4 threat / ROE bridge](../../../reviews/n4_threat_roe_bridge_20260525/README.md)
- [N5 RL action surface split](../../../reviews/n5_rl_action_surface_split_20260527/README.md)
- [Domain owner index](../../../../README.md)
- [Command boundary README](../../../../../../src/components/command/README.md)
- [Naval standards](../../../README.md)
- [Subproject creation standard](../../../../../engineering/automation/rules/subproject_creation_standard.md)

## Purpose

This subproject continues the naval-domain separation after the first N4
training-entry repair. The previous slice removed direct active-entry reuse of
`takeoff4` and air formation-role mission observations. It did not remove every
air-first compatibility carrier from the maintained naval runtime path.

The goal here is to turn that remaining compatibility into explicit adapter
surface and introduce naval-owned command, action, observation, and configuration
surfaces before any N5 weapon-engagement or N6 damage claim is opened.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Active N4 action mode | accepted first slice; `2026-06-12` command-surface tightened | `naval_station3` in `gym_envs/universal_env_parts/naval_actions.py` | `_naval_station3_command_surface` is the station-order truth; neutral `PilotAction` remains legacy transport |
| Active N4 mission observation | accepted maintained adapter | `naval_screen_station_v1` in `python/mission_obs_taxonomy.py` and `gym_envs/scenario_loader/mission_observation.py` | policy vector is produced by `naval_screen_station_v1_maintained_adapter`; compiled batch input still falls back to `basic` |
| Command shell | compatibility-active | `MissionCommand = core + air + naval` in `src/components/command/mission_command.h` | flat shell still carries air owner slices and target-altitude naming |
| Naval command projection | landed (`P2-B`, bounded) | `NavalCommandIntent` in `src/components/domains/naval/command/mission_command_naval.h`; projection `mission_command_naval_intent(owner_slice, core)`; single write seam `set_mission_command_naval_projection` | station/motion and embarked-air systems consume the projected component; the weapon-release compatibility reader still consumes the flat shell and is not an N5 closure |
| World-batch policy action | compatibility-active | `WorldPilotActionAssignment` in `src/runtime/contracts/world_batch_contracts.h` | no naval-owned action assignment packet yet |
| N5/N6 claims | held | N4 contracts forbid weapon inventory, health, and damage deltas | this subproject does not release weapon or damage authority |
| Naval tasking token mapping | focused bilingual guard refreshed | `tests/architecture/command_tasking/test_naval_tasking_standard_guard.py` cross-checks English/Chinese standard tokens, the C++ enum, and the Python profile | contract-only evidence; it is a terminology guard and does not bound naval observation, which `tests/runtime/naval/test_naval_station_policy_surface.py` does |
| Naval reward surface | declared terms reported at zero | `DECLARED_NAVAL_TERMS` in `gym_envs/scenario_loader/reward_runtime/naval.py`; `tools/eval/naval_station_policy_eval.py` requires those names | repaired `2026-09-22`: the surface is observed as a key set and a zero-valued declared term was being dropped, which had one naval surface test red on `main` |

## Scope

In scope:

- inventory air-first compatibility that still sits on the active naval path;
- define a naval-owned action or intent transport to replace policy-visible
  dependence on `PilotAction` for maintained naval entries;
- narrow `MissionCommand` use so naval station, ROE, target assignment, and
  later fire-control intent move through explicit maintained owner slices;
- promote `naval_screen_station_v1` from Python-owned replacement toward a
  maintained naval observation packet;
- rename or wrap air-labeled environment knobs such as `flight_shaping_backend`
  where they block naval runtime ownership;
- add tests and docs that keep N4 pre-fire gates green while refusing N5/N6
  overclaims.

Out of scope:

- weapon release success, hit/intercept, damage, kill, or engagement reward;
- full naval helm doctrine, ship autopilot, or fleet C2;
- formal learned-policy acceptance;
- removing every historical compatibility shell in one pass;
- broad rewrites of mature air takeoff, cruise, landing, or cooperative
  execution behavior.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze scope, inputs, write sets, and forbidden claims. | user request plus current N4/N5 evidence | subproject files and parent README links exist | active |
| `P1 Inventory` | Map all active naval air-first dependencies. | P0 scaffold | current-status inventory names code owners and risk level | accepted |
| `P2 Command/Action Split` | Introduce naval-owned command and action transport seams. | P1 inventory accepted | active naval policy path no longer depends on `PilotAction` semantics | accepted: action command surface bounded, and `P2-B` command projection landed as `NavalCommandIntent` |
| `P3 Observation/Config Split` | Promote naval observation and neutralize blocking env names. | P2 packet boundary accepted | `naval_screen_station_v1` has maintained packet gate and config aliases | accepted |
| `P4 Integration Gates` | Wire training/eval/contracts to the new surfaces. | P2/P3 implementation slices | focused tests and scenario contracts pass without N5/N6 claims | accepted |
| `P5 Closure` | Sync acceptance, current progress, and archive boundaries. | P4 validation | acceptance record marks the split accepted or held | accepted for the bounded N4 surface; N5/N6 and carrier cleanup remain deferred |

## Task Clusters

- Task cluster plan:
  [naval_domain_surface_split_task_clusters_20260601.md](naval_domain_surface_split_task_clusters_20260601.md)
- Current status:
  [naval_domain_surface_split_current_status_20260601.md](naval_domain_surface_split_current_status_20260601.md)
- Dispatch queue:
  [naval_domain_surface_split_dispatch_queue_20260601.md](naval_domain_surface_split_dispatch_queue_20260601.md)
- `P2-B` closure:
  [naval_domain_surface_split_p2b_command_projection_20260921.md](naval_domain_surface_split_p2b_command_projection_20260921.md)
- `P5-A` closure decision:
  [naval_domain_surface_split_p5_closure_20260922.md](naval_domain_surface_split_p5_closure_20260922.md)
- Acceptance gate:
  [naval_domain_surface_split_acceptance_20260601.md](naval_domain_surface_split_acceptance_20260601.md)

## Outputs And Evidence

Expected outputs:

- naval action/intent packet or equivalent maintained adapter boundary;
- command-chain tests proving naval fields survive without relying on air owner
  slices for semantics;
- observation tests proving naval policy inputs are not air formation/takeoff
  vectors with renamed fields;
- active naval training-entry checks that reject air action and air observation
  fallback;
- eval JSON surface gates proving active entries run on the maintained action
  command surface and naval observation adapter;
- updated docs that keep `naval_limited_engagement_v1` blocked until a separate
  N5 launch/reject package exists.

## Acceptance Gate

This subproject can be marked accepted only when:

- active maintained naval entries have a naval-owned action/intent transport, or
  the remaining `PilotAction` use is explicitly compatibility-only with a
  maintained command surface as policy truth;
- `MissionCommand` compatibility shell use is bounded behind maintained
  projection tests for shared core and naval owner slices;
- naval policy observation does not rely on air takeoff, air formation, runway,
  gear, or ILS fields as policy-visible semantics;
- config and CLI names no longer force naval paths to advertise air
  `flight_shaping` ownership where the behavior is domain-neutral;
- N4 pre-fire scenario contracts and active training-entry tests still pass;
- N5 weapon release and N6 damage authority remain refused unless a separate
  accepted package opens them.

## Residuals And Next Steps

- The first implementation slice should be an inventory and guard pass, not a
  broad refactor.
- Command/action packet work should be split before observation packet work if
  write sets overlap.
- `naval_limited_engagement_v1` remains a separate future N5 package.
- Formal naval policy training remains after transport, observation, reward, and
  eval gates are accepted.
- The command projection is exercised by the native C++ regression test; direct Python
  binding remains intentionally absent. The remaining follow-on is transport/carrier
  cleanup, not a missing projection execution gate.

## Evidence Lifecycle

Accepted or superseded records move to owner-local `docs/domains/naval/reviews/`;
they do not remain under the retired task root.
