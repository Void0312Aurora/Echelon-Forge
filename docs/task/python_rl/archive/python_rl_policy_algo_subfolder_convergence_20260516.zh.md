# python/rl policy_algo 子域收敛记录

状态：`2026-05-16` 第一轮已完成
范围：`policies`、`hmoe_routing`、`ppo_adaptive_kl`、`device_dict_rollout_buffer`

## 1. 目标

在 `tasking`、`control`、`runtime` 前两阶段之后，继续收纳策略与训练算法相关模块。

这组文件共同承担：

- 策略网络定义
- HMoE 语义路由
- PPO 训练变体
- 设备驻留 rollout buffer

它们语义一致、调用边界清晰，比继续直接拆 `world_batch_vec_env.py` 更适合作为下一轮低风险收敛对象。

## 2. 本轮结果

已迁移到：

- `python/rl/policy_algo/policies.py`
- `python/rl/policy_algo/hmoe_routing.py`
- `python/rl/policy_algo/ppo_adaptive_kl.py`
- `python/rl/policy_algo/device_dict_rollout_buffer.py`
- `python/rl/policy_algo/__init__.py`

## 3. 兼容策略（历史）

本轮曾短期保留根级 shim：

- `python/rl/policies.py`
- `python/rl/hmoe_routing.py`
- `python/rl/ppo_adaptive_kl.py`
- `python/rl/device_dict_rollout_buffer.py`

与 `tasking` / `control` 不同，本轮没有把这些模块加入 `python/rl/__init__.py` 的预注册别名列表，而是继续使用按模块导入时再解析的 shim 方式，和 `runtime` 保持一致。

在 `2026-05-16` 完成主链与测试切换后，这些 shim 已删除。

## 4. 已切换到新路径的主链模块

本轮已切换：

- `gym_envs/leader_env.py`
- `python/rl/support/nonfinite_probe.py`
- `tools/eval/sb3_eval_base.py`
- `python/testing/scenario_contract_runner.py`
- `tools/diagnostics/trace_training_nonfinite_source.py`
- `tools/diagnostics/cooperative_trajectory_base.py`
- `tools/diagnostics/diagnose_takeoff_to_landing_trajectory.py`

## 5. 验证

本轮验证覆盖了：

- `tests/hmoe/test_hmoe_routing.py`
- `tests/hmoe/test_hmoe_policy.py`
- `tests/hmoe/test_hmoe_train_bootstrap.py`
- `tests/world_batch/test_world_batch_vec_env.py`

并额外确认新路径子包能稳定导出关键接口；根级 shim 已在收尾阶段移除。

## 6. 当前边界

本轮没有继续处理：

- `nonfinite_probe.py`
- `coarse_route_propagator.py`
- `shared_memory_vec_env.py`
- `world_batch_vec_env.py`
- `cooperative_world_batch_vec_env.py`

这些文件仍然是 `python/rl` 根目录中剩余的主要重项。

## 7. 后续建议

下一阶段建议优先级：

1. `support` / `planning` 轻量收纳
   - `nonfinite_probe.py`
   - `coarse_route_propagator.py`

2. `runtime` 第三阶段
   - `shared_memory_vec_env.py`

3. 最后再评估是否进入：
   - `world_batch_vec_env.py`
   - `cooperative_world_batch_vec_env.py`

这样可以继续平滑降低根目录复杂度，而不会过早进入最大耦合面。
