# Naval Domain Surface Split Current Status

Status: `2026-06-12` P3/P4 maintenance refresh;
`P1-A/P1-B/P2-A/P3-A/P3-B/P4-A` accepted; inventory snapshot for
[Naval Domain Surface Split](README.md).

## Confirmed Implementation Facts

| Fact | Evidence | Status |
| --- | --- | --- |
| Active naval entries still point at `action_mode=naval_station3` and `mission_obs_mode=naval_screen_station_v1`. | `examples/config/training/active/naval/naval_contact_report_threat_roe_smoke_v1.json:37-45` and the sibling hold/recovery entries, plus the bootstrap guard in `python/training/bootstrap.py:212-223`. | accepted first slice |
| Naval tasking profile rejects non-naval action modes. | `gym_envs/universal_env_parts/naval_actions.py:28-36`. | accepted first slice |
| The active naval action exposes `_naval_station3_command_surface` while still flowing through a neutral `PilotAction` carrier for legacy assignment. | `gym_envs/universal_env_parts/actions.py`; `gym_envs/universal_env_parts/naval_actions.py`; `tests/runtime/naval/test_naval_station_policy_surface.py`. | command surface accepted; carrier compatibility adapter |
| `naval_screen_station_v1` is now formally bounded as a maintained Python adapter. | `python/mission_obs_taxonomy.py`; `gym_envs/scenario_loader/mission_observation.py`; `python/rl/runtime/world_batch/observation_batching.py`; `tests/runtime/mission/test_mission_obs_taxonomy.py`. | accepted maintained adapter |
| `MissionCommand` remains a flat compatibility shell. | `src/components/command/mission_command.h:11-18`; `src/runtime/contracts/world_batch_contracts.h:549-599`. | compatibility adapter |
| World-batch still exposes `WorldPilotActionAssignment`. | `src/runtime/contracts/world_batch_contracts.h:543-547`. | blocker |
| N4 contracts still forbid weapon/damage proof. | `tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json:1-64` and `tests/contracts/unit/naval/naval_screen_threat_roe_offstation_recovery.json:1-64`. | required boundary |
| `naval_station3` now has a `naval_station_command` action family, a maintained command-surface diagnostic, and a compatibility-only `PilotAction` transport adapter. | `gym_envs/universal_env_parts/naval_actions.py`; `python/rl/runtime/world_batch/adapter.py:341-408`; `tests/runtime/naval/test_naval_station_policy_surface.py`. | accepted second slice; action-side maintenance tightened |
| Active naval config now uses the domain-neutral `shaping_backend` alias and resolves it to canonical `flight_shaping_backend` env settings. | `python/env_config.py:60-76, 120-125`; `examples/config/training/active/naval/naval_contact_report_threat_roe_smoke_v1.json:43`; `tests/runtime/core/test_env_config.py:73-102`. | accepted second slice |
| Active naval eval now emits a `surface_gate` covering the action command surface, legacy transport adapter, and maintained naval observation adapter. | `tools/eval/naval_station_policy_eval.py`; `tests/eval/test_evaluation_cli_contracts.py`. | accepted integration gate |

## Residual Dependency Inventory

Accepted shared infrastructure here means generic runtime or reward plumbing that the naval path may reuse, but does not own. Compatibility adapters are still air-shaped or flat compatibility surfaces that remain in the path. Blockers are the pieces that still prevent a maintained naval packet boundary.

| Surface | Evidence | Classification | Current readout |
| --- | --- | --- | --- |
| `PilotAction` carrier on the naval action path | `gym_envs/universal_env_parts/actions.py`; `gym_envs/universal_env_parts/naval_actions.py`; `tests/runtime/naval/test_naval_station_policy_surface.py` | bounded compatibility adapter | Naval station mode now records policy-visible station-command truth in `_naval_station3_command_surface`; the neutral `PilotAction` remains only as the legacy assignment carrier until `WorldPilotActionAssignment` is replaced or wrapped. |
| `MissionCommand` shell and world-batch projection | `src/components/command/mission_command.h:11-18`; `src/runtime/contracts/world_batch_contracts.h:563-599` | compatibility adapter | The shell is still `core + air + naval`, and the maintained batch projection still carries air recovery/takeoff/formation alongside naval slices. |
| `flight_shaping` runtime and backend selector | `python/env_config.py:99-149`; `gym_envs/scenario_loader/core.py:273-283`; `gym_envs/scenario_loader/step_evaluation.py:311-323`; `gym_envs/scenario_loader/execution_runtime/mainline.py:530-578`; `gym_envs/scenario_loader/reward_runtime/shaping_inputs.py:4-60, 174-213`; `src/core/mission/runtime/reward_runtime.cpp:208-471` | accepted shared infrastructure, with air-labeled selector as compatibility adapter | The reward math is shared runtime. The naval entry still names the backend through `flight_shaping_backend`, but naval profile gates domain flight-shaping off with `domain_flight_shaping_enabled = not naval_runtime_profile`. |
| runway / takeoff / formation fields | `src/components/command/air/mission_command_air.h:7-49`; `src/runtime/contracts/world_batch_contracts.h:563-599`; `gym_envs/scenario_loader/mission_observation.py:93-147` | compatibility adapter | These remain air-shaped command/observation fields on the shared shell; they are not naval policy truth. |
| gear / ILS / runway math | `gym_envs/scenario_loader/reward_runtime/shaping_inputs.py:4-60, 174-213`; `src/core/mission/runtime/reward_runtime.cpp:262-471` | accepted shared infrastructure | Generic safety and approach math still uses gear, runway, and ILS terms, but naval runtime treats it as shared support math rather than owned naval semantics. |
| `naval_screen_station_v1` observation adapter | `python/mission_obs_taxonomy.py`; `gym_envs/scenario_loader/mission_observation.py`; `python/rl/runtime/world_batch/observation_batching.py`; `tests/runtime/naval/test_naval_station_policy_surface.py` | accepted bounded adapter | The policy-visible vector is generated by `naval_screen_station_v1_maintained_adapter`; compiled batch input still uses `basic` as a bounded fallback and is not the policy truth. |
| `WorldPilotActionAssignment` | `src/runtime/contracts/world_batch_contracts.h:543-547` | blocker | World-batch still exposes the old policy-action assignment contract, so naval-owned policy truth is not yet in place. |

## Readiness Matrix

| Surface | Current grade | Next required move |
| --- | --- | --- |
| Action | N4 pre-fire station-order command surface with explicit legacy carrier | continue retiring `PilotAction` carrier from the wider maintained path or keep it tested as compatibility-only |
| Command | shared shell with naval owner slice | add projection guards and narrow the command/action packet boundary |
| Observation | bounded maintained naval adapter | optional later C++ packet promotion; keep adapter diagnostics tested |
| Config | active naval config uses naval modes and `shaping_backend` alias | keep legacy `flight_shaping_backend` compatible and preserve CLI/canonical override precedence |
| Eval | zero-action/offstation N4 gates | keep the gates while moving onto the new surface |
| Runtime math | shared `flight_shaping` terms | keep generic math shared, but do not relabel it as naval-owned behavior |

## Open Risks

- Dropping the `_naval_station3_command_surface` checks would let the neutral `PilotAction` carrier hide a real naval action-transport gap again.
- Leaving `MissionCommand` as the main aggregation point makes N5 fire-control work likely to inherit air recovery, takeoff, formation, and altitude assumptions.
- The maintained Python observation adapter is now bounded and tested, but a future C++ packet can still replace it if batch/device ownership requires it.
- Renaming configuration without compatibility aliases would break air and existing training entries; the split must stay additive first.
- `flight_shaping` itself is shared runtime, but the air-labeled selector should still be retired from the naval-facing surface.

## Immediate Next Step

`P3-A` and `P4-A` are now accepted for the bounded observation adapter and
active/eval integration gates. The next dispatch is `P2-B` command projection;
keep it serial if it touches `src/runtime/contracts/**`.
