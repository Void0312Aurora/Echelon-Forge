# WP24 TaskOrder Maintained Business Migration

状态：`2026-05-24` 正在 close-out；本轮 cleanup patch 已删除 public TaskOrder
whole-shell compatibility surfaces，focused validation 待运行。

WP24 是
[`WP23 Legacy Retirement Recovery And Reset`](../wp23_legacy_retirement_recovery/legacy_retirement_recovery_wp23_20260523.zh.md)
以 `blocked` 关闭后打开的 replacement-backed TaskOrder 业务迁移包。它不是 WP23
continuation wave。WP24 的目标是把 maintained TaskOrder 业务流量迁到
`TaskOrderMaintainedBatchContract`，并从 runtime/facade/Python 业务面删除旧的
public whole-shell TaskOrder path。

最新集成记录：
[WP24 集成验收评估与下一轮分发](wp24_integration_assessment_and_next_dispatch_20260524.zh.md)。

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

WP24 可以在 focused validation 证明以下事实后关闭：

- maintained runtime/facade TaskOrder write/read roundtrip 保留 command-chain paths
  使用的业务字段；
- observation export 仍支持 maintained `task_order_contracts`；
- Python normal business paths 不暴露也不调用已删除的 legacy writer；
- architecture guards 会在已删除 public surfaces 重新出现时失败。

本 deletion patch 的 focused validation：

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
