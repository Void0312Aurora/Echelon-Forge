<!-- Machine-translated draft generated on 2026-05-18 from docs/task/python_rl/python_rl_root_shim_callsite_convergence_20260516.zh.md. Review before treating this file as authoritative. -->

# python/rl Root-Level Shim Call Point Convergence Record

Status: `2026-05-16` Round 2 completed and closed  
Scope: Main chain convergence of root-level legacy path call points in `python/rl`

## 1. Goal

After the pre-registered aliases in `python/rl/__init__.py` have been changed to explicit root shims, continue to reduce the project's internal dependency on the old root path.

The objective of this round is to complete call point convergence first, then remove the shims:

1. Internal call points on the main chain  
   These should be switched to the real subdomain path first.

2. Closing verification calls  
   Complete migration and focused verification before removal, without retaining shim coverage for the long term.

## 2. Principles for This Round

This round adopts:

- Main chain and maintained toolchains are switched to the subdomain path as much as possible
- Tests and toolchains are also switched to the real subdomain path
- The patch contracts in `scenario_contract_runner` are also switched to the new path

This compresses the dependency on shims in the actual runtime chain while completing closed-loop verification before removal.

## 3. Switches Completed in This Round

### tasking

- `gym_envs/scenario_loader.py`
- `gym_envs/leader_env.py`

Changed from:

- `python.rl.tasking_bridge`

To:

- `python.rl.tasking.bridge`

### control

Files that have been switched to `python.rl.control.*` include:

- `tools/eval/task_eval_driver.py`
- `tools/eval/eval_sb3.py`
- `tools/diagnostics/diagnose_takeoff_to_landing_trajectory.py`
- `tools/diagnostics/analyze_cooperative_observation_scales.py`
- `tools/diagnostics/diagnose_runway_drift_sweep.py`
- `tools/diagnostics/trace_training_nonfinite_source.py`
- `tools/diagnostics/cooperative_trajectory_base.py`
- `tools/diagnostics/benchmarks/coarse_route_segments.py`
- Import point for the common scripted controller in `python/testing/scenario_contract_runner.py`

### policy_algo

Files that have been switched to `python.rl.policy_algo.*` include:

- `tools/diagnostics/benchmarks/coarse_route_segments.py`
- `tools/diagnostics/benchmarks/policy_observation_bridge.py`

## 4. Final Closing Points Before Removal

Before removal, the old root paths were mainly concentrated in tests and a small number of compatibility verification points:

- `tests/runtime/*`
- `tests/leader/*`
- `tests/hmoe/*`
- `tests/world_batch/*`
- Two contract logic points that directly patch `python.rl.wrappers` in `python/testing/scenario_contract_runner.py`

These points have now been migrated, and no old-path entry points remain.

## 5. Verification

This round has verified:

- `tests/runtime/mission/test_leader_tasking_runtime.py`
- `tests/leader/test_common_core_semantics.py`
- `tests/runtime/multi_agent/test_multi_agent_benchmark.py`
- `tests/runtime/navigation/test_coarse_route_propagator.py`
- `tests/test_cuda_import_order.py`

And subsequent focused verification:

- `tests/leader/test_task_order_randomization.py`

All passed.

## 6. Conclusion

It can now be considered that:

1. The `python/rl` root-level shim is no longer a dependency of the main chain
2. Tests and toolchains have also completed the switch
3. The root-level shim can be safely removed, and it has been removed in the subsequent closing steps of this round

## 7. Follow-up Suggestions

Next steps:

1. Keep the new subdomain path as the only supported entry point.
2. Perform a gradual cleanup of legacy root-path references in historical/analysis documents.
3. Focus subsequent structural convergence on re-module splitting rather than continuing to maintain a compatibility layer.
