# Naval N5 RL Action Surface Split Cluster

Status: `2026-05-26` implemented and focused validation passed for the first
naval action-surface split. The same repair line now includes `N5-E`, the first
naval observation-surface split. Despite the `N5` folder name, this cluster
keeps the released behavior inside the accepted `N4_pre_fire_bridge` boundary;
it only unblocks later N5 work by removing air-action and air-observation
dependencies.

Cluster round cap:

- one implementation round plus at most one repair round.

## Boundary Decision

The following reuse is accepted:

- shared training bootstrap, PPO policy classes, world-batch runtime, compiled
  observation backend, reward plumbing, and facade-shaped synchronization;
- common tasking profile dispatch through `python.rl.tasking.bridge`;
- compatibility `MissionCommand` while the architecture lane still treats it as
  an aggregation point.

The following reuse is no longer accepted for active naval RL entries:

- air reduced takeoff action surfaces as naval task actions;
- initializing naval training around takeoff throttle bias;
- letting non-neutral stick/rudder/throttle bypass the naval station command
  path through ship manual takeover.
- air formation-role mission observations as active naval policy inputs.

## Task Cluster

| Stream | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Parallel / dependency | Round cap | Status |
|--------|-------|-------------------|------|-----------|-----------|------------|--------------|-----------------------|-----------|--------|
| `N5-A Evidence and boundary` | main-thread integration | current main thread | Record why the air `takeoff4` surface must be split from naval active RL while preserving shared infrastructure reuse. | `docs/task/naval/n5_rl_action_surface_split/**`, naval README index | broad naval doctrine, new scenario, weapon release | `git diff --check -- docs/task/naval` | docs name accepted reuse, rejected reuse, and residuals | serial before implementation | 1 + 1 repair | implemented |
| `N5-B Naval station action mode` | main-thread integration | current main thread | Add `naval_station3`: bearing delta, radius delta, speed bias mapped to naval station-order intent. | `gym_envs/universal_env_parts/**`, `gym_envs/universal_env.py`, `python/rl/runtime/world_batch_vec_env.py`, `python/env_config.py`, `python/training/cli.py`, `train.py`, maintained eval/benchmark CLIs | weapon switches, damage, full helm/autopilot, cooperative promotion | env-config pytest, runtime naval pytest | zero action remains neutral; non-zero action changes naval task/command intent; pilot action remains neutral | depends on N5-A | 1 + 1 repair | implemented |
| `N5-C Active entry migration` | main-thread integration | current main thread | Move active N4 naval training configs from `takeoff4` to `naval_station3`. | `examples/config/training/active/naval/**`, training entry tests | new trained-policy claim, larger curriculum | training-entry pytest, bootstrap `--test_only` gate | active entries no longer use air takeoff action mode and still stay pre-fire | depends on N5-B | 1 + 1 repair | implemented |
| `N5-D Focused acceptance` | main-thread integration | current main thread | Prove the first split did not reopen N4 engagement/damage semantics. | tests and validation notes in this doc | broad regression suite, formal training claim | focused pytest plus naval contract runner | focused tests pass; residuals remain explicit | after N5-B/C | 1 + 1 repair | passed |
| `N5-E Naval observation mode` | main-thread integration | current main thread | Add `naval_screen_station_v1` so active naval RL receives station/contact/ROE/report fields instead of air formation-role fields. | `python/mission_obs_taxonomy.py`, `gym_envs/scenario_loader/mission_observation.py`, `python/rl/runtime/world_batch/**`, active naval configs/docs, mission/naval/training tests | weapon release, damage/kill observation, cooperative packet schema | taxonomy pytest, runtime naval pytest, training-entry pytest | active entries use the naval mode; world-batch keeps C++ mission batching on a safe fallback while replacing the policy mission vector with naval fields | after N5-D and before new formal training | 1 + 1 repair | implemented |

No subagents were dispatched for this implementation round. The cluster is
still finite and policy-compatible; future delegated work should map to one of
the residual clusters below before dispatch.

## Implemented Slice

`naval_station3` action vector:

- `0`: station bearing delta, normalized `[-1, 1]`, mapped to `+/-25 deg`;
- `1`: station radius delta, normalized `[-1, 1]`, mapped to `+/-1800 m`;
- `2`: station speed bias, normalized `[-1, 1]`, mapped to `+/-1.25 m/s`
  within the task speed band when present.

Runtime behavior:

- `WorldBatchVecEnv` applies the naval station action to loader-owned naval
  task/mission intent before stepping the batch world.
- The maintained command-chain synchronization then projects the updated
  station order into the runtime.
- The low-level `PilotAction` sent for this action mode is neutral:
  rudder/stick-roll `0.0`, throttle `0.5`, weapon triggers off.
- The legacy `takeoff4` path remains available for focused low-level ship
  manual-takeover diagnostics, but active naval training entries no longer use
  it.

`naval_screen_station_v1` mission observation vector:

- station/order: command code, target heading/speed, station radius/bearing,
  station error, normalized station error, screen separation and separation
  error;
- geometry: own/support-relative x/y and desired relative x/y;
- contact/report: target-contact present, support-track present, report-chain
  seen;
- authority/provenance: ROE state, authorization-to-fire, assigned target id
  and source id;
- role: self role, relative slot, and reference relative slot.

Runtime behavior:

- Active naval configs now request `mission_obs_mode=naval_screen_station_v1`.
- The mode is Python-owned for the first slice. World-batch still uses the
  compiled observation backend for instruments, contacts, and RWR, but it feeds
  the compiled mission-observation batcher a safe `basic` fallback and then
  replaces the policy-facing mission vector with the naval vector.
- This avoids passing a new mode code to the legacy C++ mission-observation
  surface before the packet/ownership split is ready.

## Verification

Validation commands for this slice:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/core/test_env_config.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/mission/test_mission_obs_taxonomy.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/naval/test_naval_n4_reward_surface.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_naval_active_training_entries.py tests/training/test_naval_n4_closure_gate.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
git diff --check -- docs/task/naval examples/config/training/active/naval gym_envs/scenario_loader gym_envs/universal_env.py gym_envs/universal_env_parts python/env_config.py python/mission_obs_taxonomy.py python/training/cli.py python/rl/runtime/world_batch python/rl/runtime/world_batch_vec_env.py python/rl/runtime/cooperative_world_batch_vec_env.py train.py tools/eval tools/diagnostics/benchmarks/world_batch_vec_env.py tests/runtime/core/test_env_config.py tests/runtime/mission/test_mission_obs_taxonomy.py tests/runtime/naval/test_naval_n4_reward_surface.py tests/training/test_naval_active_training_entries.py tests/training/test_naval_n4_closure_gate.py
```

Focused results:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/core/test_env_config.py
# 8 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/mission/test_mission_obs_taxonomy.py
# 3 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/naval/test_naval_n4_reward_surface.py
# 7 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_naval_active_training_entries.py tests/training/test_naval_n4_closure_gate.py
# 7 passed, 6 subtests passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
# PASS: naval screen threat/ROE pre-fire contract passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/core/test_env_config.py tests/runtime/mission/test_mission_obs_taxonomy.py tests/runtime/naval/test_naval_n4_reward_surface.py tests/training/test_naval_active_training_entries.py tests/training/test_naval_n4_closure_gate.py
# 25 passed, 6 subtests passed

git diff --check -- docs/task/naval examples/config/training/active/naval gym_envs/scenario_loader gym_envs/universal_env.py gym_envs/universal_env_parts python/env_config.py python/mission_obs_taxonomy.py python/training/cli.py python/rl/runtime/world_batch python/rl/runtime/world_batch_vec_env.py python/rl/runtime/cooperative_world_batch_vec_env.py train.py tools/eval tools/diagnostics/benchmarks/world_batch_vec_env.py tests/runtime/core/test_env_config.py tests/runtime/mission/test_mission_obs_taxonomy.py tests/runtime/naval/test_naval_n4_reward_surface.py tests/training/test_naval_active_training_entries.py tests/training/test_naval_n4_closure_gate.py
# passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json --output_base /tmp/cmo_naval_n5_smoke --run_name naval_station3_smoke
# completed 512 timesteps with action_mode=naval_station3 and saved final_model

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json --output_base /tmp/cmo_naval_n5e_obs_smoke --run_name naval_screen_station_v1_smoke
# completed 512 timesteps with action_mode=naval_station3, mission_obs_mode=naval_screen_station_v1, and saved final_model
```

## Residual Clusters

Future `N5-F` packet split:

- replace compatibility `MissionCommand` station-order aggregation with
  narrower command/tasking packets after the architecture lane releases that
  surface.

Future `N5-G` cooperative promotion:

- handle non-agent support ship roster accounting before promoting active
  naval entries to cooperative execution.

Future `N5-H` training evidence:

- run formal training only after the action and observation surfaces are both
  accepted, and report learned behavior as evidence rather than as a config
  bootstrap claim.
