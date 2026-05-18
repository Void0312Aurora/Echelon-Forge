# python/rl 根级 shim 调用点收敛记录

状态：`2026-05-16` 第二轮已完成并关闭
范围：`python/rl` 根级旧路径调用点的主链收敛

## 1. 目标

在已经把 `python/rl/__init__.py` 的预注册 alias 改为显式 root shim 之后，继续降低项目内部对旧根路径的依赖。

这一轮的目标是先完成调用点收敛，再删除 shim：

1. 主链内部调用
   应优先切到真实子域路径。

2. 收尾验证调用
   在删除前完成迁移与聚焦验证，不再长期保留 shim 覆盖。

## 2. 本轮原则

本轮采用：

- 主链与维护中的工具链尽量切到子域路径
- 测试与工具链也切到真实子域路径
- `scenario_contract_runner` 的 patch 契约同步切到新路径

这样既能压缩真实运行链对 shim 的依赖，又能在删除前完成闭环验证。

## 3. 本轮已切换

### tasking

- `gym_envs/scenario_loader.py`
- `gym_envs/leader_env.py`

已从：

- `python.rl.tasking_bridge`

切到：

- `python.rl.tasking.bridge`

### control

已切换到 `python.rl.control.*` 的文件包括：

- `tools/eval/task_eval_driver.py`
- `tools/eval/eval_sb3.py`
- `tools/diagnostics/diagnose_takeoff_to_landing_trajectory.py`
- `tools/diagnostics/analyze_cooperative_observation_scales.py`
- `tools/diagnostics/diagnose_runway_drift_sweep.py`
- `tools/diagnostics/trace_training_nonfinite_source.py`
- `tools/diagnostics/cooperative_trajectory_base.py`
- `tools/diagnostics/benchmarks/coarse_route_segments.py`
- `python/testing/scenario_contract_runner.py` 中普通 scripted controller 导入点

### policy_algo

已切换到 `python.rl.policy_algo.*` 的文件包括：

- `tools/diagnostics/benchmarks/coarse_route_segments.py`
- `tools/diagnostics/benchmarks/policy_observation_bridge.py`

## 4. 删除前的最后收口点

删除前，旧根路径主要集中在测试与少量兼容验证点：

- `tests/runtime/*`
- `tests/leader/*`
- `tests/hmoe/*`
- `tests/world_batch/*`
- `python/testing/scenario_contract_runner.py` 中直接 patch `python.rl.wrappers` 的两处契约逻辑

这些点现已完成迁移，不再保留旧路径入口。

## 5. 验证

本轮已验证：

- `tests/runtime/mission/test_leader_tasking_runtime.py`
- `tests/leader/test_common_core_semantics.py`
- `tests/runtime/multi_agent/test_multi_agent_benchmark.py`
- `tests/runtime/navigation/test_coarse_route_propagator.py`
- `tests/test_cuda_import_order.py`

以及后续一轮聚焦验证：

- `tests/leader/test_task_order_randomization.py`

均通过。

## 6. 结论

当前可以认为：

1. `python/rl` 根级 shim 已经不再是主链依赖
2. 测试与工具链也已完成切换
3. 根级 shim 已可安全删除，并已在本轮后续收尾中移除

## 7. 后续建议

下一步建议：

1. 保持新子域路径为唯一受支持入口。
2. 对历史/分析文档中的旧根路径引用做渐进式清理。
3. 把后续结构收敛重点放回重模块拆分，而不是继续维护兼容层。
