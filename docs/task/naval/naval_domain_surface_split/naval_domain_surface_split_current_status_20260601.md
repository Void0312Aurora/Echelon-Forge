# Naval Domain Surface Split Current Status

Status: `2026-06-01`; `P1-A/P1-B/P2-A/P3-B` accepted;
inventory snapshot for [Naval Domain Surface Split](README.md).

## Confirmed Implementation Facts

| Fact | Evidence | Status |
| --- | --- | --- |
| Active naval entries still point at `action_mode=naval_station3` and `mission_obs_mode=naval_screen_station_v1`. | `examples/config/training/active/naval/naval_contact_report_threat_roe_smoke_v1.json:37-45` and the sibling hold/recovery entries, plus the bootstrap guard in `python/training/bootstrap.py:212-223`. | accepted first slice |
| Naval tasking profile rejects non-naval action modes. | `gym_envs/universal_env_parts/naval_actions.py:28-36`. | accepted first slice |
| The active naval action still flows through a neutral `PilotAction` carrier. | `gym_envs/universal_env_parts/actions.py:36-39`; `gym_envs/universal_env_parts/naval_actions.py:39-63`. | compatibility adapter |
| `naval_screen_station_v1` is present, but the naval mission vector is still Python-owned in batch observation. | `python/mission_obs_taxonomy.py:141-145`; `python/rl/runtime/world_batch/observation_batching.py:41-77`. | blocker |
| `MissionCommand` remains a flat compatibility shell. | `src/components/command/mission_command.h:11-18`; `src/runtime/contracts/world_batch_contracts.h:549-599`. | compatibility adapter |
| World-batch still exposes `WorldPilotActionAssignment`. | `src/runtime/contracts/world_batch_contracts.h:543-547`. | blocker |
| N4 contracts still forbid weapon/damage proof. | `tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json:1-64` and `tests/contracts/unit/naval/naval_screen_threat_roe_offstation_recovery.json:1-64`. | required boundary |
| `naval_station3` now has a `naval_station_command` action family and compatibility-only `PilotAction` transport adapter. | `gym_envs/universal_env_parts/naval_actions.py:23-65`; `python/rl/runtime/world_batch/adapter.py:341-408`; `tests/runtime/naval/test_naval_n4_reward_surface.py:36-56`. | accepted second slice |
| Active naval config now uses the domain-neutral `shaping_backend` alias and resolves it to canonical `flight_shaping_backend` env settings. | `python/env_config.py:60-76, 120-125`; `examples/config/training/active/naval/naval_contact_report_threat_roe_smoke_v1.json:43`; `tests/runtime/core/test_env_config.py:73-102`. | accepted second slice |

## Residual Dependency Inventory

Accepted shared infrastructure here means generic runtime or reward plumbing that the naval path may reuse, but does not own. Compatibility adapters are still air-shaped or flat compatibility surfaces that remain in the path. Blockers are the pieces that still prevent a maintained naval packet boundary.

| Surface | Evidence | Classification | Current readout |
| --- | --- | --- | --- |
| `PilotAction` carrier on the naval action path | `gym_envs/universal_env_parts/actions.py:36-39`; `gym_envs/universal_env_parts/naval_actions.py:39-63` | compatibility adapter | Naval station mode still emits a neutral `PilotAction`; the naval path does not yet own policy-visible action truth. |
| `MissionCommand` shell and world-batch projection | `src/components/command/mission_command.h:11-18`; `src/runtime/contracts/world_batch_contracts.h:563-599` | compatibility adapter | The shell is still `core + air + naval`, and the maintained batch projection still carries air recovery/takeoff/formation alongside naval slices. |
| `flight_shaping` runtime and backend selector | `python/env_config.py:99-149`; `gym_envs/scenario_loader/core.py:273-283`; `gym_envs/scenario_loader/step_evaluation.py:311-323`; `gym_envs/scenario_loader/execution_runtime/mainline.py:530-578`; `gym_envs/scenario_loader/reward_runtime/shaping_inputs.py:4-60, 174-213`; `src/core/mission/runtime/reward_runtime.cpp:208-471` | accepted shared infrastructure, with air-labeled selector as compatibility adapter | The reward math is shared runtime. The naval entry still names the backend through `flight_shaping_backend`, but naval profile gates domain flight-shaping off with `domain_flight_shaping_enabled = not naval_runtime_profile`. |
| runway / takeoff / formation fields | `src/components/command/air/mission_command_air.h:7-49`; `src/runtime/contracts/world_batch_contracts.h:563-599`; `gym_envs/scenario_loader/mission_observation.py:93-147` | compatibility adapter | These remain air-shaped command/observation fields on the shared shell; they are not naval policy truth. |
| gear / ILS / runway math | `gym_envs/scenario_loader/reward_runtime/shaping_inputs.py:4-60, 174-213`; `src/core/mission/runtime/reward_runtime.cpp:262-471` | accepted shared infrastructure | Generic safety and approach math still uses gear, runway, and ILS terms, but naval runtime treats it as shared support math rather than owned naval semantics. |
| Python-owned `naval_screen_station_v1` fallback | `python/mission_obs_taxonomy.py:141-145`; `python/rl/runtime/world_batch/observation_batching.py:41-50, 66-77` | blocker | The naval observation mode is still Python-owned and the batch path falls back to `basic`, so there is no maintained naval packet yet. |
| `WorldPilotActionAssignment` | `src/runtime/contracts/world_batch_contracts.h:543-547` | blocker | World-batch still exposes the old policy-action assignment contract, so naval-owned policy truth is not yet in place. |

## Readiness Matrix

| Surface | Current grade | Next required move |
| --- | --- | --- |
| Action | N4 pre-fire station-order probe with explicit compatibility adapter | continue retiring `PilotAction` carrier from the wider maintained path or keep it tested as compatibility-only |
| Command | shared shell with naval owner slice | add projection guards and narrow the command/action packet boundary |
| Observation | Python-owned naval vector | promote to a maintained packet or document the adapter as bounded and temporary |
| Config | active naval config uses naval modes and `shaping_backend` alias | keep legacy `flight_shaping_backend` compatible and preserve CLI/canonical override precedence |
| Eval | zero-action/offstation N4 gates | keep the gates while moving onto the new surface |
| Runtime math | shared `flight_shaping` terms | keep generic math shared, but do not relabel it as naval-owned behavior |

## Open Risks

- Keeping the neutral `PilotAction` carrier acceptable for too long can hide a real naval action-transport gap.
- Leaving `MissionCommand` as the main aggregation point makes N5 fire-control work likely to inherit air recovery, takeoff, formation, and altitude assumptions.
- The Python-owned observation fallback is useful for the first slice, but it should not become the permanent maintained naval packet.
- Renaming configuration without compatibility aliases would break air and existing training entries; the split must stay additive first.
- `flight_shaping` itself is shared runtime, but the air-labeled selector should still be retired from the naval-facing surface.

## Immediate Next Step

`P2-A` and `P3-B` are accepted. The next dispatch may choose either `P2-B`
command projection or `P3-A` observation packet; keep `P2-B` serial if it touches
`src/runtime/contracts/**`.
