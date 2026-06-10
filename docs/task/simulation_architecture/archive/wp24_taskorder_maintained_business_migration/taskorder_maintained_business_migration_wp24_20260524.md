# WP24 TaskOrder Maintained Business Migration

Status: closed on `2026-05-24`; public TaskOrder whole-shell compatibility
surfaces have been deleted, observation/tasking export is split, command-chain
Python business writes now use maintained MissionCommand/LeaderIntent/
PilotReport contracts, and legacy visual fallback is hard-gated behind explicit
runtime compatibility opt-in.

WP24 is the replacement-backed TaskOrder business migration package opened after
[`WP23 Legacy Retirement Recovery And Reset`](../wp23_legacy_retirement_recovery/legacy_retirement_recovery_wp23_20260523.md)
closed as `blocked`. It is not a WP23 continuation wave. WP24's purpose is to
move maintained TaskOrder business traffic onto `TaskOrderMaintainedBatchContract`
and remove the old public whole-shell TaskOrder path from runtime/facade/Python
business surfaces.

Latest integration records:

- [WP24 Integration Assessment And Next Dispatch](wp24_integration_assessment_and_next_dispatch_20260524.md)
- [WP24 Facade Boundary Closure Task Package](wp24_facade_boundary_closure_task_package_20260524.md)

Current close-out state:

- TaskOrder public whole-shell batch/facade/Python writer surfaces are removed.
- `ObservationBatchPacket` is pure observation export; command/tasking reads use
  `TaskingBatchRequest` and `TaskingBatchPacket`.
- MissionCommand, LeaderIntent, and PilotReport business writers in Python now
  project compatibility shells into maintained contracts before crossing the
  runtime/facade boundary.
- Runtime-window action injection now requires explicit maintained
  ObservationPacket/DecisionBelief provenance and C++ action-intent
  authorization; normal full-batch stepping stays on facade `step_batch()`.
- Raw `SimulationKernel` setup remains available only through explicit
  compatibility quarantine paths; it is no longer the default training/runtime
  setup route.
- Legacy single-world visual fallback is compatibility-only and fails closed
  unless `runtime_compatibility_enabled=True` is explicit.

## 1. Maintained Target

The accepted maintained path is:

- writes use `WorldTaskOrderMaintainedAssignment`;
- tasking reads use `TaskingBatchRequest` and `TaskingBatchPacket` with
  `task_order_contracts` gated by `include_task_order_contracts`;
- observation export remains pure agent-observation and instrument-state data;
- Python VecEnv, cooperative, scenario-loader, and multi-agent observation paths
  fail closed if the maintained TaskOrder batch binding is unavailable.

`SimulationKernel::set_task_order/get_task_order` remain implementation storage
details for this package. They are not accepted public business APIs.

## 2. Deleted Compatibility Surface

This close-out patch removes the previous quarantine zone instead of carrying it
forward:

- `WorldTaskOrderAssignment` and `WorldTaskOrderCompatibilityAssignment`;
- runtime/facade/binding `set_task_orders_batch` and `get_task_orders_batch`;
- runtime/facade/binding `set_task_orders_compatibility_batch` and
  `get_task_orders_compatibility_batch`;
- `ObservationBatchRequest.include_task_orders`;
- `ExecutionBatchStepRequest.include_task_orders`;
- `ObservationBatchPacket.task_orders`;
- `RuntimeFacadeAdapter.set_task_orders_batch`;
- `RuntimeFacadeAdapter.set_task_orders_batch_compatibility`;
- Python maintained-to-legacy reverse projection.

The remaining TaskOrder whole-shell type may still exist as ECS storage and
command-layer projection material, but it is no longer a public batch/facade
business transport.

## 3. Closure Standard

WP24 can close only after the TaskOrder deletion patch and the facade boundary
closure package both pass focused validation. The TaskOrder-specific closure
standard proves:

- maintained runtime/facade TaskOrder write/read roundtrips preserve the business
  fields used by command-chain paths;
- tasking export supports maintained `task_order_contracts`;
- Python normal business paths do not expose or call the removed legacy writer;
- architecture guards fail if the deleted public surfaces reappear.

The boundary closure package adds mandatory acceptance for pure observation
packets, facade-owned scenario setup, maintained command-chain contracts, and
explicit maintained provenance at Python call sites. Observation split,
command-chain contracts, provenance guards, runtime-window authorization, normal
facade-owned batch stepping, and legacy visual fallback hard-gating are
implemented for the close-out.

Focused validation for this deletion patch:

```bash
git diff --check
python -m py_compile python/scenario/runtime/batch_apply.py python/scenario/runtime/world_setup_compat.py python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch/command_chain_cache.py python/rl/runtime/world_batch_vec_env.py python/rl/runtime/cooperative_world_batch_vec_env.py python/rl/runtime/multi_agent_runtime.py python/rl/runtime/agent_shim.py gym_envs/universal_env.py train.py
cmake --build build-workshop --target ef_py -j4
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/bindings/test_bindings_command_surface.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py
PYTHONPATH=build-workshop python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "task_order or command_chain"
PYTHONPATH=build-workshop python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "task_order or command_chain or observation or batch_runtime or visual"
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py -k "task_order or command_chain or observation or batch_runtime"
PYTHONPATH=build-workshop python -m pytest -q tests/architecture/runtime_facade/test_layering.py tests/architecture/command_tasking/test_dto_domain_shell_guard.py
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py
```
