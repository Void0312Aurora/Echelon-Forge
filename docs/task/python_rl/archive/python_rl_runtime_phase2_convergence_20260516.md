<!-- Machine-translated draft generated on 2026-05-18 from docs/task/python_rl/python_rl_runtime_phase2_convergence_20260516.zh.md. Review before treating this file as authoritative. -->

# python/rl runtime Subdomain Phase 2 Consolidation Record

Status: `2026-05-16` Phase 2 completed  
Scope: `single_world_batch_runtime`, `leader_world_batch_runtime`, `leader_batched_vec_env`

## 1. Objective

After completing the support layer boxing in Phase 1 of runtime, continue to incorporate the second cluster of files that are directly related to the leader/execution runtime chain but are still significantly smaller than `world_batch_vec_env.py` / `cooperative_world_batch_vec_env.py`:

- `single_world_batch_runtime.py`
- `leader_world_batch_runtime.py`
- `leader_batched_vec_env.py`

This cluster collectively handles:

- Single-world execution runtime bridging
- Multi-leader shared execution runtime grouping
- Leader batched vector environment batch inference on frozen execution policies

## 2. Current Result

Migrated to:

- `python/rl/runtime/single_world_batch_runtime.py`
- `python/rl/runtime/leader_world_batch_runtime.py`
- `python/rl/runtime/leader_batched_vec_env.py`

Legacy root-level lazy shims were preserved simultaneously:

- `python/rl/single_world_batch_runtime.py`
- `python/rl/leader_world_batch_runtime.py`
- `python/rl/leader_batched_vec_env.py`

## 3. Compatibility Strategy (Historical)

This phase continued the lazy shim strategy from runtime Phase 1, rather than performing package initialization pre‑registration in `python/rl/__init__.py`.

The reason remains unchanged:

- Runtime‑related modules come into contact with `gym_envs.*` earlier.
- `gym_envs` and `python.rl.*` have cross‑references during initialization.

Therefore, the safer approach remains:

1. Move the subdomain real implementation into `python/rl/runtime/`.
2. Keep a shim with the same name at the old root path temporarily.
3. Have the main‑chain code switch to the new path first.

After call‑site consolidation completed on `2026-05-16`, the above shims were removed.

## 4. Main‑Chain Modules Already Switched to the New Path

Switched in this phase:

- `gym_envs/leader_env.py`
- `python/rl/support/multi_agent_benchmark.py`
- Internal reference to `leader_world_batch_runtime` inside `python/rl/runtime/leader_batched_vec_env.py`

## 5. Current Boundary

Still not migrated in this phase:

- `world_batch_vec_env.py`
- `cooperative_world_batch_vec_env.py`
- `shared_memory_vec_env.py`

These three remain the heaviest and most tightly coupled files in the runtime subdomain.

## 6. Verification

Verification in this phase covered:

- `tests/runtime/multi_agent/test_multi_agent_runtime.py`
- `tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py`
- `tests/world_batch/test_world_batch_vec_env.py`
- `tests/test_cuda_import_order.py`

And confirmed:

- The new subpackage entrypoints work correctly.
- After deleting the root‑level shims, focused tests and import smoke tests still pass.

## 7. Follow‑up Suggestions

Two options for the next phase:

1. **Continue with runtime Phase 3**  
   Start handling `shared_memory_vec_env.py`, then evaluate whether to move to `world_batch_vec_env.py`.

2. **Shift to the `policy_algo` subdomain**  
   Incorporate:
   - `policies.py`
   - `hmoe_routing.py`
   - `ppo_adaptive_kl.py`
   - `device_dict_rollout_buffer.py`

If the goal is to reduce the complexity of the `python/rl` root directory as quickly as possible, `policy_algo` would be a more stable choice than directly tackling `world_batch_vec_env.py`.
