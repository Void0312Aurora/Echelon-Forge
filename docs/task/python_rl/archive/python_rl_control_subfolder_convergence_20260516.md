<!-- Machine-translated draft generated on 2026-05-18 from docs/task/python_rl/python_rl_control_subfolder_convergence_20260516.zh.md. Review before treating this file as authoritative. -->

# python/rl control subdomain boxing convergence record

Status: `2026-05-16` First round completed
Scope: `mission_defs`, `scripted_*` controllers, `wrappers`

## 1. Goal

After completing the boxing of the `tasking` subdomain, continue processing another clearly systematic control semantics module group under the `python/rl` root directory:

- `mission_defs.py`
- `scripted_takeoff.py`
- `scripted_stable_flight.py`
- `scripted_landing.py`
- `wrappers.py`

This group of files jointly handles:

- Command codes and phase semantics definitions
- Takeoff / cruise / landing scripted controllers
- Multi-timescale action wrapping and scripted residual mixing

Therefore, it is more suitable as an independent `control` subdomain rather than continuing to be flat in the root directory.

## 2. Current Round Results

Migrated to:

- `python/rl/control/mission_defs.py`
- `python/rl/control/scripted_takeoff.py`
- `python/rl/control/scripted_stable_flight.py`
- `python/rl/control/scripted_landing.py`
- `python/rl/control/wrappers.py`
- `python/rl/control/__init__.py`

## 3. Compatibility Strategy (Historical)

Consistent with the `tasking` subdomain, this round briefly retained root-level shims:

- `python/rl/mission_defs.py`
- `python/rl/scripted_takeoff.py`
- `python/rl/scripted_stable_flight.py`
- `python/rl/scripted_landing.py`
- `python/rl/wrappers.py`

After the main chain, testing, and toolchain switch was completed on `2026-05-16`, these shims have been removed.

## 4. Main Chain Modules Switched to New Paths

This round has switched the following core modules to preferentially use `python.rl.control.*`:

- `gym_envs/leader_env.py`
- `gym_envs/scenario_loader.py`
- `python/rl/world_batch_vec_env.py`
- `python/rl/cooperative_world_batch_vec_env.py`
- `python/rl/runtime/single_world_batch_runtime.py`
- `python/rl/runtime/leader_world_batch_runtime.py`
- `python/rl/policy_algo/hmoe_routing.py`
- `python/rl/profile/air_profile.py`
- `python/rl/tasking/leader_tasking.py`
- `game/backend/app.py`

## 5. Current Boundaries

This round did not further process:

1. Further splitting within `control`, e.g., breaking `wrappers.py` into finer-grained components.
2. All old path imports in tooling / diagnostic scripts / historical tests.
3. Further boxing of `runtime`, `policy_algo`, `planning`, `support` subdomains.

## 6. Subsequent Suggestions

Suggested priorities for the next phase:

1. Box the `runtime` subdomain.
2. Box the `policy_algo` subdomain.
3. Keep `python.rl.control.*` as the only stable import surface; do not restore the root-level compatibility layer.
