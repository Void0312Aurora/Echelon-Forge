# WP24 Integration Assessment And Cleanup Close-Out

Status: closed on `2026-05-24`. Old public TaskOrder whole-shell compatibility
surfaces have been removed; observation and tasking export are split;
command-chain Python business writes now route through maintained
MissionCommand/LeaderIntent/PilotReport contracts; runtime-window, setup/step,
and legacy visual fallback boundaries fail closed by default.

Chinese companion:
[wp24_integration_assessment_and_next_dispatch_20260524.zh.md](wp24_integration_assessment_and_next_dispatch_20260524.zh.md)

## 1. Assessment

WP24-A through WP24-H established the maintained TaskOrder business path:

- `TaskOrderMaintainedBatchContract` covers the command-chain TaskOrder business
  slices used by current runtime paths.
- `WorldBatchRuntime` and `RuntimeFacade` expose maintained
  `set_task_orders_maintained_batch` and `get_task_orders_maintained_batch`.
- `TaskingBatchPacket.task_order_contracts` plus
  `TaskingBatchRequest.include_task_order_contracts` provide maintained tasking
  export, while `ObservationBatchPacket` stays observation-only.
- Python VecEnv, cooperative VecEnv, scenario-loader runtime proxy, and
  multi-agent observation consumers use maintained TaskOrder assignments and
  maintained observation contracts.

The earlier quarantine decision is superseded. This close-out patch deletes the
remaining public TaskOrder whole-shell compatibility surfaces instead of
accepting them as residuals.

After this assessment, a parallel subagent verification wave confirmed additional
facade/information-boundary leaks outside the retired TaskOrder public whole-shell
surface. The corrective package is tracked in
[WP24 Facade Boundary Closure Task Package](wp24_facade_boundary_closure_task_package_20260524.md).

The current implementation wave has closed the highest-risk command-chain leak:
runtime/facade/bindings expose maintained command-chain contracts, Python
scenario-loader and VecEnv paths write maintained assignments, and multi-agent
tasking reads use maintained mission-command contracts instead of whole-shell
fallbacks.

The follow-up hardening also closed two production-boundary leaks identified by
focused review: normal full-batch stepping now stays on facade `step_batch()`,
and runtime-window action injection requires explicit maintained
ObservationPacket/DecisionBelief provenance plus C++ authorization.
The final close-out hardens legacy visual fallback as compatibility-only, so
maintained visual export uses the facade-owned batch helper or fails closed.

## 2. Cleanup Result

Deleted surfaces:

- `WorldTaskOrderAssignment`;
- `WorldTaskOrderCompatibilityAssignment`;
- runtime/facade/binding `set_task_orders_batch` and `get_task_orders_batch`;
- runtime/facade/binding `set_task_orders_compatibility_batch` and
  `get_task_orders_compatibility_batch`;
- `ObservationBatchRequest.include_task_orders`;
- `ExecutionBatchStepRequest.include_task_orders`;
- `ObservationBatchPacket.task_orders`;
- `RuntimeFacadeAdapter.set_task_orders_batch`;
- `RuntimeFacadeAdapter.set_task_orders_batch_compatibility`;
- Python maintained-to-legacy reverse projection.

Retained implementation detail:

- `SimulationKernel::set_task_order/get_task_order` remain as ECS storage access
  beneath the maintained batch contract. They are not accepted as public
  maintained business APIs.

## 3. Updated Guards

The focused tests now assert the deletion state:

- runtime/facade/bindings expose maintained TaskOrder batch APIs only;
- DTOs expose `task_order_contracts`, not `task_orders`;
- tasking requests expose `include_task_order_contracts`, while observation and
  execution requests expose no tasking flags;
- Python adapters do not expose legacy TaskOrder batch writers;
- architecture tests fail if the deleted names return;
- Python command-chain business writers use `World*MaintainedAssignment` and
  `set_*_maintained_batch`, with guards against old whole-shell writer re-entry.
- maintained runtime-window action injection calls
  `authorize_maintained_action_intent()` and rejects compatibility/default
  provenance labels;
- maintained full-batch stepping does not use
  `facade.runtime_compatibility_quarantine().step_worlds()`;
- legacy visual fallback is compatibility-only and fails closed unless
  `runtime_compatibility_enabled=True` is explicit.

Residual raw runtime surfaces are not accepted on the default maintained
production path. `UniversalEnv` raw `SimulationKernel` ownership remains gated by
`runtime_compatibility_enabled=True`, rejected by default from `train.py`, and
guarded as compatibility quarantine.

## 4. Validation Plan

Focused validation for this cleanup:

```bash
git diff --check
python -m py_compile python/scenario/runtime/batch_apply.py python/scenario/runtime/world_setup_compat.py python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch/command_chain_cache.py python/rl/runtime/world_batch_vec_env.py python/rl/runtime/cooperative_world_batch_vec_env.py python/rl/runtime/multi_agent_runtime.py python/rl/runtime/agent_shim.py gym_envs/universal_env.py train.py
cmake --build build-workshop --target ef_py -j4
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/bindings/test_bindings_command_surface.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py
PYTHONPATH=build-workshop python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "task_order or command_chain"
PYTHONPATH=build-workshop python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "task_order or command_chain or observation or batch_runtime or visual"
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py -k "task_order or command_chain or observation or batch_runtime"
PYTHONPATH=build-workshop python -m pytest -q tests/architecture/runtime_facade/test_layering.py tests/architecture/test_wp22_dto_domain_shell_guard.py
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py
```

Full-suite validation remains outside this focused cleanup unless requested.
