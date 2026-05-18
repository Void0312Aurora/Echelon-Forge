<!-- Machine-translated draft generated on 2026-05-18 from docs/task/python_rl/python_rl_runtime_subfolder_convergence_20260516.zh.md. Review before treating this file as authoritative. -->

# python/rl runtime Subdomain Phase 1 Convergence Record

Status: `2026-05-16` Phase 1 completed  
Scope: `execution_runtime`, `leader_window_runtime`, `multi_agent_runtime`

## 1. Goal

After completing the `tasking` and `control` subdomains, continue processing the most intensive `runtime` related modules under the `python/rl` root.

However, the overall size of `runtime` is significantly larger than the previous two groups, especially:

- `world_batch_vec_env.py`
- `cooperative_world_batch_vec_env.py`

These two have long dependency chains, high coupling, and a large scope of changes, making them unsuitable for migration in the same round along with all supporting modules.

Therefore, this phase only processes the supporting layers in `runtime` with clearer boundaries:

- `execution_runtime.py`
- `leader_window_runtime.py`
- `multi_agent_runtime.py`

## 2. Current Round Results

Migrated to:

- `python/rl/runtime/execution_runtime.py`
- `python/rl/runtime/leader_window_runtime.py`
- `python/rl/runtime/multi_agent_runtime.py`
- `python/rl/runtime/__init__.py`

## 3. Compatibility Strategy (Historical)

Unlike `tasking` / `control`, this round did not place these three old modules into `python/rl/__init__.py` for pre-registration aliases during package initialization.

Reason:

- `multi_agent_runtime` depends on `gym_envs.universal_env`
- `universal_env` in turn references `scenario_loader`
- `scenario_loader` imports `python.rl.*` during initialization

If `runtime.multi_agent_runtime` were forcibly imported early in `python/rl/__init__.py`, it would introduce a real circular import.

Therefore, this round adopted a deferred shim approach:

- `python/rl/execution_runtime.py`
- `python/rl/leader_window_runtime.py`
- `python/rl/multi_agent_runtime.py`

After the main branch and tests switched over on `2026-05-16`, these shims were deleted; the risk of circular imports during initialization was controlled through explicit subdomain import conventions.

## 4. Main Branch Modules That Have Switched to the New Path

Switched in this round:

- `gym_envs/leader_env.py`
- `python/rl/runtime/single_world_batch_runtime.py`
- `python/rl/runtime/leader_world_batch_runtime.py`
- `python/rl/cooperative_world_batch_vec_env.py`
- `python/rl/runtime/leader_batched_vec_env.py`

## 5. Current Boundary

This round explicitly did not migrate:

- `world_batch_vec_env.py`
- `cooperative_world_batch_vec_env.py`
- `single_world_batch_runtime.py`
- `leader_world_batch_runtime.py`
- `shared_memory_vec_env.py`
- `leader_batched_vec_env.py`

Explanation:

- These files still belong to the runtime semantic domain;
- However, they will be further split by dependency clusters in subsequent phases, rather than being moved all at once in this round.

## 6. Follow-up Suggestions

The next phase is recommended to choose one of two paths:

1. Continue with `runtime` Phase 2  
   First migrate `single_world_batch_runtime.py`, `leader_world_batch_runtime.py`, `leader_batched_vec_env.py`

2. Switch to the `policy_algo` subdomain  
   First migrate `policies.py`, `hmoe_routing.py`, `ppo_adaptive_kl.py`, `device_dict_rollout_buffer.py`

If continuing with `runtime`, it is still recommended to avoid directly migrating the heaviest `world_batch_vec_env.py` / `cooperative_world_batch_vec_env.py` at the start.
