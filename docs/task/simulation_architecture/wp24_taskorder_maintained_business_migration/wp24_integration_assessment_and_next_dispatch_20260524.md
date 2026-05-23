# WP24 Integration Assessment And Cleanup Close-Out

Status: `2026-05-24` cleanup close-out in progress; old public TaskOrder
whole-shell compatibility surfaces have been removed from code and tests are
being revalidated.

Chinese companion:
[wp24_integration_assessment_and_next_dispatch_20260524.zh.md](wp24_integration_assessment_and_next_dispatch_20260524.zh.md)

## 1. Assessment

WP24-A through WP24-H established the maintained TaskOrder business path:

- `TaskOrderMaintainedBatchContract` covers the command-chain TaskOrder business
  slices used by current runtime paths.
- `WorldBatchRuntime` and `RuntimeFacade` expose maintained
  `set_task_orders_maintained_batch` and `get_task_orders_maintained_batch`.
- `ObservationBatchPacket.task_order_contracts` plus
  `include_task_order_contracts` provide maintained observation export.
- Python VecEnv, cooperative VecEnv, scenario-loader runtime proxy, and
  multi-agent observation consumers use maintained TaskOrder assignments and
  maintained observation contracts.

The earlier quarantine decision is superseded. This close-out patch deletes the
remaining public TaskOrder whole-shell compatibility surfaces instead of
accepting them as residuals.

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
- observation and execution requests expose `include_task_order_contracts`, not
  `include_task_orders`;
- Python adapters do not expose legacy TaskOrder batch writers;
- architecture tests fail if the deleted names return.

## 4. Validation Plan

Focused validation for this cleanup:

```bash
git diff --check
python -m py_compile python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch_vec_env.py python/rl/runtime/cooperative_world_batch_vec_env.py python/rl/runtime/multi_agent_runtime.py train.py
cmake --build build-workshop --target ef_py -j4
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/bindings/test_bindings_command_surface.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py
PYTHONPATH=build-workshop python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "task_order or command_chain"
PYTHONPATH=build-workshop python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "task_order or command_chain or observation or batch_runtime"
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py -k "task_order or command_chain or observation or batch_runtime"
PYTHONPATH=build-workshop python -m pytest -q tests/architecture/test_runtime_facade_layering.py tests/architecture/test_wp22_dto_domain_shell_guard.py
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py
```

Full-suite validation remains outside this focused cleanup unless requested.
