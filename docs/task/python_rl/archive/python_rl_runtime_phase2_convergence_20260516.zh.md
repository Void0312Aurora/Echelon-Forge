# python/rl runtime 子域第二阶段收敛记录

状态：`2026-05-16` 第二阶段已完成
范围：`single_world_batch_runtime`、`leader_world_batch_runtime`、`leader_batched_vec_env`

## 1. 目标

在 runtime 第一阶段完成支撑层入箱后，继续收纳与 leader/execution 运行链直接相关、但仍明显小于 `world_batch_vec_env.py` / `cooperative_world_batch_vec_env.py` 的第二簇文件：

- `single_world_batch_runtime.py`
- `leader_world_batch_runtime.py`
- `leader_batched_vec_env.py`

这一簇共同承担：

- 单 world 执行运行时桥接
- 多 leader 共享执行运行时分组
- leader 批量向量环境对 frozen execution policy 的批处理推理

## 2. 本轮结果

已迁移到：

- `python/rl/runtime/single_world_batch_runtime.py`
- `python/rl/runtime/leader_world_batch_runtime.py`
- `python/rl/runtime/leader_batched_vec_env.py`

当时同步保留过根级延迟 shim：

- `python/rl/single_world_batch_runtime.py`
- `python/rl/leader_world_batch_runtime.py`
- `python/rl/leader_batched_vec_env.py`

## 3. 兼容策略（历史）

本阶段继续沿用 runtime 第一阶段的延迟 shim 策略，而不是在 `python/rl/__init__.py` 做包初始化预注册。

原因不变：

- runtime 相关模块会较早接触 `gym_envs.*`
- `gym_envs` 与 `python.rl.*` 存在初始化期的相互引用

因此更安全的方式仍然是：

1. 子域真实实现迁入 `python/rl/runtime/`
2. 旧根路径短期保留同名 shim
3. 主链代码优先切到新路径

在 `2026-05-16` 完成调用点收敛后，上述 shim 已删除。

## 4. 已切换到新路径的主链模块

本轮已切换：

- `gym_envs/leader_env.py`
- `python/rl/support/multi_agent_benchmark.py`
- `python/rl/runtime/leader_batched_vec_env.py` 内部对 `leader_world_batch_runtime` 的引用

## 5. 当前边界

本轮仍未迁移：

- `world_batch_vec_env.py`
- `cooperative_world_batch_vec_env.py`
- `shared_memory_vec_env.py`

这三者仍然是 runtime 子域中最重、耦合最深的一批。

## 6. 验证

本轮验证覆盖了：

- `tests/runtime/multi_agent/test_multi_agent_runtime.py`
- `tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py`
- `tests/world_batch/test_world_batch_vec_env.py`
- `tests/test_cuda_import_order.py`

并确认：

- 新子包入口正常工作
- 删除根级 shim 后，聚焦测试与导入烟测仍保持通过

## 7. 后续建议

下一阶段建议二选一：

1. 继续 runtime 第三阶段
   开始处理 `shared_memory_vec_env.py`，然后再评估是否进入 `world_batch_vec_env.py`

2. 转向 `policy_algo` 子域
   收纳：
   - `policies.py`
   - `hmoe_routing.py`
   - `ppo_adaptive_kl.py`
   - `device_dict_rollout_buffer.py`

如果目标是尽快降低 `python/rl` 根目录复杂度，`policy_algo` 会比直接硬拆 `world_batch_vec_env.py` 更稳。
