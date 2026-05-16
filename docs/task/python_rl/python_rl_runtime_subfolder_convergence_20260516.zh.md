# python/rl runtime 子域第一阶段收敛记录

状态：`2026-05-16` 第一阶段已完成
范围：`execution_runtime`、`leader_window_runtime`、`multi_agent_runtime`

## 1. 目标

在 `tasking` 与 `control` 子域完成入箱后，继续处理 `python/rl` 根目录中最密集的 `runtime` 相关模块。

但 `runtime` 的整体体量明显大于前两组，尤其：

- `world_batch_vec_env.py`
- `cooperative_world_batch_vec_env.py`

这两者依赖链长、耦合高、改动面大，不适合在同一轮里和全部支撑模块一起迁移。

因此本阶段只处理 `runtime` 中边界较清晰的支撑层：

- `execution_runtime.py`
- `leader_window_runtime.py`
- `multi_agent_runtime.py`

## 2. 本轮结果

已迁移到：

- `python/rl/runtime/execution_runtime.py`
- `python/rl/runtime/leader_window_runtime.py`
- `python/rl/runtime/multi_agent_runtime.py`
- `python/rl/runtime/__init__.py`

## 3. 兼容策略（历史）

与 `tasking` / `control` 不同，本轮没有把这三个旧模块放进 `python/rl/__init__.py` 中做包初始化阶段的预注册别名。

原因：

- `multi_agent_runtime` 会依赖 `gym_envs.universal_env`
- `universal_env` 又会回引 `scenario_loader`
- `scenario_loader` 在初始化时会导入 `python.rl.*`

如果在 `python/rl/__init__.py` 中提前强行导入 `runtime.multi_agent_runtime`，会引入真实循环导入。

因此本轮曾改为延迟 shim 方案：

- `python/rl/execution_runtime.py`
- `python/rl/leader_window_runtime.py`
- `python/rl/multi_agent_runtime.py`

在 `2026-05-16` 主链与测试完成切换后，这些 shim 已删除；初始化期循环依赖风险则通过显式子域导入规约控制。

## 4. 已切换到新路径的主链模块

本轮已切换：

- `gym_envs/leader_env.py`
- `python/rl/runtime/single_world_batch_runtime.py`
- `python/rl/runtime/leader_world_batch_runtime.py`
- `python/rl/cooperative_world_batch_vec_env.py`
- `python/rl/runtime/leader_batched_vec_env.py`

## 5. 当前边界

本轮明确没有迁移：

- `world_batch_vec_env.py`
- `cooperative_world_batch_vec_env.py`
- `single_world_batch_runtime.py`
- `leader_world_batch_runtime.py`
- `shared_memory_vec_env.py`
- `leader_batched_vec_env.py`

说明：

- 这些文件仍属于 runtime 语义域；
- 但它们会在后续阶段按依赖簇继续拆分，而不是在本轮一次性搬空。

## 6. 后续建议

下一阶段建议两条路径二选一：

1. 继续 `runtime` 第二阶段
   先迁 `single_world_batch_runtime.py`、`leader_world_batch_runtime.py`、`leader_batched_vec_env.py`

2. 转向 `policy_algo` 子域
   先迁 `policies.py`、`hmoe_routing.py`、`ppo_adaptive_kl.py`、`device_dict_rollout_buffer.py`

如果继续 `runtime`，建议仍然避免一开始就直接搬最重的 `world_batch_vec_env.py` / `cooperative_world_batch_vec_env.py`。
