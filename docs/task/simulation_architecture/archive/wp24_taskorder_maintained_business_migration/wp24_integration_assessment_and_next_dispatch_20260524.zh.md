# WP24 集成评估与清理收口

状态：`2026-05-24` 已关闭。旧 public TaskOrder whole-shell compatibility
surfaces 已删除；observation 与 tasking export 已拆分；command-chain Python
business writes 已通过 maintained MissionCommand/LeaderIntent/PilotReport
contracts 路由；runtime-window、setup/step 与 legacy visual fallback 边界默认
fail closed。

英文主文：
[wp24_integration_assessment_and_next_dispatch_20260524.md](wp24_integration_assessment_and_next_dispatch_20260524.md)

## 1. 验收评估

WP24-A 到 WP24-H 已建立 maintained TaskOrder business path：

- `TaskOrderMaintainedBatchContract` 覆盖当前 runtime paths 使用的 command-chain
  TaskOrder 业务 slices。
- `WorldBatchRuntime` 与 `RuntimeFacade` 暴露 maintained
  `set_task_orders_maintained_batch` 与 `get_task_orders_maintained_batch`。
- `TaskingBatchPacket.task_order_contracts` 与
  `TaskingBatchRequest.include_task_order_contracts` 提供 maintained tasking
  export；`ObservationBatchPacket` 保持 observation-only。
- Python VecEnv、cooperative VecEnv、scenario-loader runtime proxy 与 multi-agent
  observation consumers 使用 maintained TaskOrder assignments 和 maintained
  observation contracts。

此前的 quarantine 决策已被本轮清理取代。本 close-out patch 删除 remaining public
TaskOrder whole-shell compatibility surfaces，不再把它们作为 residual 接受。

在本 assessment 之后，并行 subagent 核验确认 TaskOrder public whole-shell
surface 之外仍存在 facade / information-boundary 泄漏。整改任务包记录在
[WP24 Facade Boundary Closure Task Package](wp24_facade_boundary_closure_task_package_20260524.zh.md)。

当前 implementation wave 已关闭最高风险的 command-chain 泄漏：runtime/facade/
bindings 暴露 maintained command-chain contracts，Python scenario-loader 与 VecEnv
路径写入 maintained assignments，multi-agent tasking reads 使用 maintained
mission-command contracts，不再回落 whole-shell fallback。

Focused review 后的补刀也关闭了两个 production-boundary leaks：正常 full-batch
stepping 现在停留在 facade `step_batch()`，runtime-window action injection 要求显式
maintained ObservationPacket/DecisionBelief provenance，并经过 C++ authorization。
最终收口还把 legacy visual fallback harden 成 compatibility-only，因此 maintained
visual export 要么使用 facade-owned batch helper，要么 fail closed。

## 2. 清理结果

已删除 surfaces：

- `WorldTaskOrderAssignment`；
- `WorldTaskOrderCompatibilityAssignment`；
- runtime/facade/binding `set_task_orders_batch` 与 `get_task_orders_batch`；
- runtime/facade/binding `set_task_orders_compatibility_batch` 与
  `get_task_orders_compatibility_batch`；
- `ObservationBatchRequest.include_task_orders`；
- `ExecutionBatchStepRequest.include_task_orders`；
- `ObservationBatchPacket.task_orders`；
- `RuntimeFacadeAdapter.set_task_orders_batch`；
- `RuntimeFacadeAdapter.set_task_orders_batch_compatibility`；
- Python maintained-to-legacy reverse projection。

保留的实现细节：

- `SimulationKernel::set_task_order/get_task_order` 仍作为 maintained batch contract
  下方的 ECS storage access。它们不是已接受的 public maintained business APIs。

## 3. 更新后的 Guard

focused tests 现在断言 deletion state：

- runtime/facade/bindings 只暴露 maintained TaskOrder batch APIs；
- DTO 暴露 `task_order_contracts`，不暴露 `task_orders`；
- tasking request 暴露 `include_task_order_contracts`；observation 与
  execution requests 不暴露 tasking flags；
- Python adapters 不暴露 legacy TaskOrder batch writers；
- architecture tests 会在已删除名称回归时失败；
- Python command-chain business writers 使用 `World*MaintainedAssignment` 与
  `set_*_maintained_batch`，并 guard 旧 whole-shell writer 回流。
- maintained runtime-window action injection 调用
  `authorize_maintained_action_intent()`，并拒绝 compatibility/default provenance
  labels；
- maintained full-batch stepping 不再使用
  `facade.runtime_compatibility_quarantine().step_worlds()`；
- legacy visual fallback 是 compatibility-only，没有显式
  `runtime_compatibility_enabled=True` 时会 fail closed。

默认 maintained production path 不再接受 residual raw runtime surface。
`UniversalEnv` raw `SimulationKernel` ownership 仍被
`runtime_compatibility_enabled=True` gate，`train.py` 默认拒绝进入，并由 guard 约束为
compatibility quarantine。

## 4. 验证计划

本轮 cleanup 的 focused validation：

```bash
git diff --check
python -m py_compile python/scenario/runtime/batch_apply.py python/scenario/runtime/world_setup_compat.py python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch/command_chain_cache.py python/rl/runtime/world_batch_vec_env.py python/rl/runtime/cooperative_world_batch_vec_env.py python/rl/runtime/multi_agent_runtime.py python/rl/runtime/agent_shim.py gym_envs/universal_env.py train.py
cmake --build build-workshop --target ef_py -j4
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/bindings/test_bindings_command_surface.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py
PYTHONPATH=build-workshop python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "task_order or command_chain"
PYTHONPATH=build-workshop python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "task_order or command_chain or observation or batch_runtime or visual"
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py -k "task_order or command_chain or observation or batch_runtime"
PYTHONPATH=build-workshop python -m pytest -q tests/architecture/runtime_facade tests/architecture/command_tasking/test_dto_domain_shell_guard.py
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py
```

除非另行要求，完整测试套件不纳入本 focused cleanup。
