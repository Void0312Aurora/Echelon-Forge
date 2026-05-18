<!-- Machine-translated draft generated on 2026-05-18 from docs/task/python_rl/python_rl_tasking_domain_convergence_20260515.zh.md. Review before treating this file as authoritative. -->

# python/rl Tasking Subdomain Convergence Analysis and Phase 1 Implementation Freeze

Status: `2026-05-16` – Phase 1 implementation completed and now in post-root-level shim cleanup state  
Scope: Modules in `python/rl` directly related to the `tasking` subdomain, and their external entry points in `gym_envs/` and `python/testing/`

## 1. Objectives

This round does not directly refactor all of `python/rl`; instead it first completes the Phase 1 convergence of the `tasking` subdomain:

1. Freeze the subdomain division of `python/rl`.
2. Clarify the single external entry point strategy for the `tasking` subdomain.
3. Based on real call chains, assess the redundancy and retention rationale for `tasking_bridge.py`, `tasking_air_adapter.py`, `common_core_profile.py`, and `leader_tasking.py`.
4. Complete minimal code implementation to eliminate the “bridge and adapter directly mixed” state.

## 2. Freeze of `python/rl` Subdomains

It is currently recommended to freeze `python/rl` into the following subdomains:

- `runtime`
  - `world_batch_vec_env.py`
  - `cooperative_world_batch_vec_env.py`
  - `execution_runtime.py`
  - `single_world_batch_runtime.py`
  - `leader_world_batch_runtime.py`
  - `leader_window_runtime.py`
  - `leader_batched_vec_env.py`
  - `shared_memory_vec_env.py`
  - `multi_agent_runtime.py`
- `tasking`
  - `leader_tasking.py`
  - `bridge.py`
  - `air_adapter.py`
  - `common_core_profile.py`
  - `profile/air_profile.py`
  - `profile/common_core_base.py`
  - `profile/common_core_defaults.py`
- `control`
  - `wrappers.py`
  - `scripted_takeoff.py`
  - `scripted_stable_flight.py`
  - `scripted_landing.py`
  - `mission_defs.py`
- `policy_algo`
  - `policies.py`
  - `hmoe_routing.py`
  - `ppo_adaptive_kl.py`
  - `device_dict_rollout_buffer.py`
- `planning`
  - `coarse_route_propagator.py`
- `support`
  - `nonfinite_probe.py`
  - `multi_agent_benchmark.py`
  - `sb3_vec_env_compat.py`

This document only advances the `tasking` subdomain.

## 3. Current Call Chain Status of `tasking`

Confirmed main call relationships:

- `gym_envs/scenario_loader.py`
  - Uses `python.rl.tasking.bridge`
    - `build_kernel_mission_command`
    - `make_rule_based_leader_phase_manager`
    - `normalize_task_order_spec`
- `python/testing/scenario_contract_runner.py`
  - Uses `python.rl.tasking.bridge`
    - `normalize_task_order_spec`
    - `build_kernel_mission_command`
    - `make_rule_based_leader_phase_manager`
- `gym_envs/leader_env.py`
  - Previously used both
    - `python.rl.tasking.bridge`
    - `python.rl.tasking.air_adapter.ScriptedC2TaskManager`
- `python/rl/world_batch_vec_env.py`
  - Now directly uses `python.rl.tasking.leader_tasking.build_kernel_mission_command`
- `python/rl/cooperative_world_batch_vec_env.py`
  - Now directly uses `python.rl.tasking.leader_tasking.build_kernel_mission_command`
  - And `_apply_task_order_overrides`

Therefore, before this round of implementation, the `tasking` subdomain had three entry points:

1. `tasking.bridge`
2. `tasking.air_adapter`
3. `tasking.leader_tasking`

This makes it difficult for callers to determine which is the stable API.

## 4. Assessment of Key Modules

### 4.1 `tasking_bridge.py`

Assessment:

- Not dead code.
- Not a purely redundant layer that can be deleted yet.
- Currently plays the role of a “profile dispatch seam”, but implementation is still single profile (`air`).

Conclusion:

- Retain.
- Promote to the single external entry point for the `tasking` subdomain.

### 4.2 `tasking_air_adapter.py`

Assessment:

- Essentially an aggregation re‑export layer for the air profile.
- The biggest current problem is not that the file exists, but that external callers still import it directly.

Conclusion:

- Temporarily retain as the default air profile carrier behind `tasking_bridge`.
- No longer allow `gym_envs/`, `tools/`, `tests/` to treat it as an external entry point directly.

### 4.3 `common_core_profile.py`

Assessment:

- More like a common‑core compatibility facade.
- Contains both genuine common‑core defaults/spec helpers and many forwarding functions to `profile/air_profile.py`.

Conclusion:

- Keep it for now.
- Further distinction is needed in later phases:
  - real common‑core mutations/defaults
  - semantic inference provided solely for the air combat profile

### 4.4 `leader_tasking.py`

Assessment:

- Not a pure task manager.
- Currently carries:
  - `RuleBasedLeaderPhaseManager`
  - `ScriptedC2TaskManager`
  - `build_kernel_mission_command`
  - some air profile proxy and override logic

Conclusion:

- One of the core implementation files of the `tasking` subdomain, not redundant.
- But its responsibility is too large; later it should be split further into “phase manager / c2 task manager / mission command bridge / profile helper”.

## 5. Phase 1 Freeze Strategy

This phase only does the following convergence, no behavioral rewrites:

1. `tasking_bridge` becomes the single external entry point.
2. `gym_envs/leader_env.py` no longer directly imports `tasking_air_adapter.py`.
3. `tasking_air_adapter.py` retreats to being the default air adapter behind the bridge.
4. `leader_tasking.py` and `common_core_profile.py` are not heavily restructured for now.

This phase explicitly does not:

- Delete `tasking_air_adapter.py`
- Rewrite the internal structure of `leader_tasking.py`
- Immediately switch `world_batch_vec_env.py` / `cooperative_world_batch_vec_env.py` to using bridge
- Introduce a second real tasking profile

## 6. Implementation in This Round

Completed:

1. `python/rl/tasking/bridge.py`
   - Added `scripted_c2_task_manager_class(loader=None)` to obtain the default profile’s `ScriptedC2TaskManager` class through the bridge.
2. `gym_envs/leader_env.py`
   - Removed direct import of `python.rl.tasking.air_adapter.ScriptedC2TaskManager`.
   - Changed to obtain the default class binding via `python.rl.tasking.bridge.scripted_c2_task_manager_class()`.

After this:

- The external semantic entry point of `leader_env` is completely consolidated through the bridge.
- `tasking_air_adapter` is no longer exposed to the `gym_envs` call surface.
- The runtime behavior of `ScriptedC2TaskManager` remains unchanged.

## 7. Recommendations for Subsequent Phases

### Phase 2

- Converge the direct profile helper calls from `world_batch_vec_env.py` and `cooperative_world_batch_vec_env.py` to `leader_tasking`.
- Aim to have the runtime layer also obtain profile‑related capabilities through the bridge as much as possible.

### Phase 3

- Restructure `leader_tasking.py`
  - phase manager
  - scripted c2 manager
  - mission command builder
  - task‑order override helper

### Phase 4

- Determine which functions in `common_core_profile.py` should be moved directly into `profile/common_core_defaults.py`, which should remain as a facade, and which should be removed.

## 8. Current Risks

- `tasking_bridge.py` still dispatches only to the air profile; hence “multi‑profile” is only a seam, not a full capability.
- `leader_tasking.py` is still directly depended on by the runtime layer, so the internal structure of the subdomain is not yet truly thinned.
- `tasking_air_adapter.py` will still appear in documentation and old plans; later documentation needs to be gradually updated to refer to it as an “internal air adapter” rather than an external entry point.
