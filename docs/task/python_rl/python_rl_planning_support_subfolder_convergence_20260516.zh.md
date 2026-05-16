# python/rl planning 与 support 子域收敛记录

状态：`2026-05-16` 第一轮已完成
范围：

- `coarse_route_propagator`
- `nonfinite_probe`
- `sb3_vec_env_compat`
- `multi_agent_benchmark`

## 1. 目标

在 `tasking`、`control`、`runtime`、`policy_algo` 之后，继续缩减 `python/rl` 根目录的平铺压力，把语义更清晰、耦合相对可控的剩余模块收纳到新子域中。

这一轮不处理 `world_batch_vec_env.py` 与 `cooperative_world_batch_vec_env.py` 本体，只处理它们周边的轻量规划与支撑模块。

## 2. 本轮结果

已新增子域：

- `python/rl/planning/`
- `python/rl/support/`

已迁移：

- `python/rl/planning/coarse_route_propagator.py`
- `python/rl/support/nonfinite_probe.py`
- `python/rl/support/sb3_vec_env_compat.py`
- `python/rl/support/multi_agent_benchmark.py`

并补充：

- `python/rl/planning/__init__.py`
- `python/rl/support/__init__.py`

## 3. 子域划分理由

### planning

`coarse_route_propagator.py` 是纯规划投影与误差比较逻辑，职责集中在：

- 航迹/航向几何计算
- 粗粒度航路前推
- waypoint 捕获与状态比较

它不承担训练 runtime、策略网络或环境兼容职责，因此更适合作为独立规划子域的起点。

### support

本轮收纳到 `support/` 的模块都更偏“支撑层”，包括：

- 非有限数值训练探针
- SB3 `VecEnv` 兼容桥
- 多机 benchmark 入口

这些模块服务于训练、诊断、兼容或性能观测，但不属于主控制逻辑或任务语义本体。

## 4. 兼容策略（历史）

本轮曾短期保留根级 shim：

- `python/rl/coarse_route_propagator.py`
- `python/rl/nonfinite_probe.py`
- `python/rl/sb3_vec_env_compat.py`
- `python/rl/multi_agent_benchmark.py`

在 `2026-05-16` 完成调用点收敛后，旧路径 shim 已删除，内部实现统一保留在新子域。

与 `tasking` / `control` 不同，本轮没有把这些模块加入 `python/rl/__init__.py` 的预注册别名列表。

原因：

1. `support` 中的模块存在明显的重量级导入链
2. 例如 `multi_agent_benchmark` 会继续拉起 cooperative/world-batch runtime
3. 提前在包导入阶段做别名注册，会放大 import-order 风险与底层构建依赖暴露面

因此本轮曾采用“根级 shim + 子域真模块”的延迟解析方式，和 `runtime` / `policy_algo` 保持一致。

## 5. 已切换到新路径的主链模块

本轮已切换：

- `python/rl/world_batch_vec_env.py`
- `python/rl/cooperative_world_batch_vec_env.py`
- `tools/diagnostics/benchmarks/coarse_route_segments.py`
- `scripts/benchmark_multi_agent.py`

删除前曾短期保留部分旧导入路径用于验证；现已统一切到新子域路径。

## 6. 特别记录

`python/rl/support/__init__.py` 只保留轻量 `__all__` 声明，不做实现级重导出。

原因是包级重导出会在导入 `python.rl.support` 时立即拉起：

- `multi_agent_benchmark`
- `nonfinite_probe`
- `sb3_vec_env_compat`

这会让原本可按需加载的模块变成包导入时的硬依赖，不符合本轮降低导入副作用的目标。

## 7. 验证策略

本轮验证分两层：

1. 轻量导入烟测
   - 新路径模块可导入
   - 根级 shim 能正确回指到新实现

2. 聚焦测试
   - `tests/runtime/test_coarse_route_propagator.py`
   - `tests/runtime/test_multi_agent_benchmark.py`
   - `tests/hmoe/test_hmoe_policy.py`
   - `tests/world_batch/test_world_batch_vec_env.py`

## 8. 后续建议

下一步建议优先看两条线：

1. `python/rl` 根目录剩余重模块
   - `shared_memory_vec_env.py`
   - `world_batch_vec_env.py`
   - `cooperative_world_batch_vec_env.py`

2. 与 `python/rl` 相邻的高堆积目录
   - 继续按子域方式整理 `tools/diagnostics`
   - 梳理 `tests/runtime` 与 `tests/training` 的保留边界

这一轮的意义不是继续“横向加 shim”，而是先把可低风险收敛的轻量模块放进稳定语义边界，为后续处理最重的 world-batch 主链做准备。
