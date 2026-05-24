# WP24 TaskOrder Maintained Business Migration

状态：`2026-05-24` 已关闭；public TaskOrder whole-shell compatibility surfaces
已删除，observation/tasking export 已拆分，command-chain Python business writes
已改用 maintained MissionCommand/LeaderIntent/PilotReport contracts，并且 legacy
visual fallback 已被 hard-gate 到显式 runtime compatibility opt-in 后面。

WP24 是
[`WP23 Legacy Retirement Recovery And Reset`](../wp23_legacy_retirement_recovery/legacy_retirement_recovery_wp23_20260523.zh.md)
以 `blocked` 关闭后打开的 replacement-backed TaskOrder 业务迁移包。它不是 WP23
continuation wave。WP24 的目标是把 maintained TaskOrder 业务流量迁到
`TaskOrderMaintainedBatchContract`，并从 runtime/facade/Python 业务面删除旧的
public whole-shell TaskOrder path。

最新集成记录：

- [WP24 集成验收评估与清理收口](wp24_integration_assessment_and_next_dispatch_20260524.zh.md)
- [WP24 Facade Boundary Closure Task Package](wp24_facade_boundary_closure_task_package_20260524.zh.md)

当前 close-out 状态：

- TaskOrder public whole-shell batch/facade/Python writer surfaces 已移除。
- `ObservationBatchPacket` 是纯 observation export；command/tasking reads 使用
  `TaskingBatchRequest` 与 `TaskingBatchPacket`。
- Python 里的 MissionCommand、LeaderIntent、PilotReport business writers 在跨越
  runtime/facade boundary 前，会先把 compatibility shell 投影成 maintained
  contract。
- Runtime-window action injection 现在要求显式 maintained
  ObservationPacket/DecisionBelief provenance，并经过 C++ action-intent
  authorization；正常 full-batch stepping 停留在 facade `step_batch()`。
- Raw `SimulationKernel` setup 只通过显式 compatibility quarantine path 保留；
  它不再是默认 training/runtime setup route。
- Legacy single-world visual fallback 是 compatibility-only；没有显式
  `runtime_compatibility_enabled=True` 时会 fail closed。

## 1. Maintained Target

已接受的 maintained path 是：

- 写入使用 `WorldTaskOrderMaintainedAssignment`；
- 读取与 observation export 使用 `TaskOrderMaintainedBatchContract`；
- facade observation packet 通过 `include_task_order_contracts` gate 暴露
  `task_order_contracts`；
- Python VecEnv、cooperative、scenario-loader 与 multi-agent observation 路径在缺少
  maintained TaskOrder batch binding 时 fail closed。

`SimulationKernel::set_task_order/get_task_order` 在本包中仍是实现存储细节，不是已接受的
public business API。

## 2. 已删除的兼容面

本轮 close-out patch 不再保留隔离区，而是删除此前的 public compatibility surface：

- `WorldTaskOrderAssignment` 与 `WorldTaskOrderCompatibilityAssignment`；
- runtime/facade/binding `set_task_orders_batch` 与 `get_task_orders_batch`；
- runtime/facade/binding `set_task_orders_compatibility_batch` 与
  `get_task_orders_compatibility_batch`；
- `ObservationBatchRequest.include_task_orders`；
- `ExecutionBatchStepRequest.include_task_orders`；
- `ObservationBatchPacket.task_orders`；
- `RuntimeFacadeAdapter.set_task_orders_batch`；
- `RuntimeFacadeAdapter.set_task_orders_batch_compatibility`；
- Python maintained-to-legacy reverse projection。

TaskOrder whole-shell 类型仍可作为 ECS storage 与 command-layer projection material
存在，但不再是 public batch/facade business transport。

## 3. 收口标准

WP24 只有在 TaskOrder deletion patch 与 facade boundary closure package 都通过
focused validation 后才能关闭。TaskOrder-specific closure standard 证明：

- maintained runtime/facade TaskOrder write/read roundtrip 保留 command-chain paths
  使用的业务字段；
- observation export 仍支持 maintained `task_order_contracts`；
- Python normal business paths 不暴露也不调用已删除的 legacy writer；
- architecture guards 会在已删除 public surfaces 重新出现时失败。

Boundary closure package 额外要求 pure observation packet、facade-owned
scenario setup、maintained command-chain contracts，以及 Python call site 显式
maintained provenance。其中 observation split、command-chain contracts、
provenance guard、runtime-window authorization、正常 facade-owned batch stepping
与 legacy visual fallback hard-gating 均已在本 close-out 中落地。

本 deletion patch 的 focused validation：

```bash
git diff --check
python -m py_compile python/scenario/runtime/batch_apply.py python/scenario/runtime/world_setup_compat.py python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch/command_chain_cache.py python/rl/runtime/world_batch_vec_env.py python/rl/runtime/cooperative_world_batch_vec_env.py python/rl/runtime/multi_agent_runtime.py python/rl/runtime/agent_shim.py gym_envs/universal_env.py train.py
cmake --build build-workshop --target ef_py -j4
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/bindings/test_bindings_command_surface.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py
PYTHONPATH=build-workshop python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "task_order or command_chain"
PYTHONPATH=build-workshop python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "task_order or command_chain or observation or batch_runtime or visual"
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py -k "task_order or command_chain or observation or batch_runtime"
PYTHONPATH=build-workshop python -m pytest -q tests/architecture/test_runtime_facade_layering.py tests/architecture/test_wp22_dto_domain_shell_guard.py
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py
```
