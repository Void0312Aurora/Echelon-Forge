<!-- Machine-translated draft generated on 2026-05-18 from docs/task/python_rl/python_rl_policy_algo_subfolder_convergence_20260516.zh.md. Review before treating this file as authoritative. -->

# python/rl policy_algo subdomain convergence record

Status: `2026-05-16` First round completed
Scope: `policies`, `hmoe_routing`, `ppo_adaptive_kl`, `device_dict_rollout_buffer`

## 1. Objective

After the first two phases (`tasking`, `control`, `runtime`), continue to collect policy and training algorithm related modules.

These files collectively assume:
- Policy network definition
- HMoE semantic routing
- PPO training variants
- Device-dedicated rollout buffer

They are semantically consistent, with clear call boundaries, making them more suitable as low-risk convergence targets for the next round than continuing to directly split `world_batch_vec_env.py`.

## 2. Results of this round

Migrated to:
- `python/rl/policy_algo/policies.py`
- `python/rl/policy_algo/hmoe_routing.py`
- `python/rl/policy_algo/ppo_adaptive_kl.py`
- `python/rl/policy_algo/device_dict_rollout_buffer.py`
- `python/rl/policy_algo/__init__.py`

## 3. Compatibility strategy (historical)

This round temporarily retained root-level shims:
- `python/rl/policies.py`
- `python/rl/hmoe_routing.py`
- `python/rl/ppo_adaptive_kl.py`
- `python/rl/device_dict_rollout_buffer.py`

Unlike `tasking` / `control`, this round did not add these modules to the pre-registered alias list in `python/rl/__init__.py`, but instead continued to use a shim approach that resolves upon module import, consistent with `runtime`.

After completing the main chain and test switch on `2026-05-16`, these shims were deleted.

## 4. Main chain modules switched to new paths

This round has switched:
- `gym_envs/leader_env.py`
- `python/rl/support/nonfinite_probe.py`
- `tools/eval/sb3_eval_base.py`
- `python/testing/scenario_contract_runner.py`
- `tools/diagnostics/trace_training_nonfinite_source.py`
- `tools/diagnostics/cooperative_trajectory_base.py`
- `tools/diagnostics/flight_trajectory_diagnostics.py --mode takeoff_to_landing`

## 5. Verification

This round's verification covered:
- `tests/policy/test_routing_contracts.py`
- `tests/policy/test_execution_policy_surface.py`
- `tests/policy/test_policy_bootstrap_initialization.py`
- `tests/world_batch/test_world_batch_vec_env.py`

Additionally confirmed that the new path sub-package can stably export key interfaces; root-level shims were removed in the final stage.

## 6. Current boundaries

This round did not process:
- `nonfinite_probe.py`
- `coarse_route_propagator.py`
- `shared_memory_vec_env.py`
- `world_batch_vec_env.py`
- `cooperative_world_batch_vec_env.py`

These files remain the main heavy items in the `python/rl` root directory.

## 7. Subsequent suggestions

Suggested priorities for the next phase:

1. Lightweight collection of `support` / `planning`
   - `nonfinite_probe.py`
   - `coarse_route_propagator.py`

2. Third phase of `runtime`
   - `shared_memory_vec_env.py`

3. Finally assess whether to proceed with:
   - `world_batch_vec_env.py`
   - `cooperative_world_batch_vec_env.py`

This will continue to smoothly reduce the complexity of the root directory without prematurely entering the largest coupling surface.
