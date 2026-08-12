# GPU 执行阶段 4C：推出热路径冻结

状态：下一个维护阶段 4 后续任务的已冻结执行计划。

历史说明（2026-04-18）：
本文档记录了当时混合使用的 `p5` 辅助通道。后续维护的 `p5` 默认值已回退至 `batch_visual_backend=compiled`，此处所有 `gpu_host/fullgpu` 引用应视为历史基准上下文，而非当前主线。

相关：

- [gpu_execution_mainline_integration_checklist.md](gpu_execution_mainline_integration_checklist.md)
- [gpu_execution_runtime_research_and_design.md](../archive/exact_runtime/gpu_execution_runtime_research_and_design.md)
- [tools/diagnostics/benchmark.py](../../../tools/diagnostics/benchmark.py)

## 当前基线

先前的阶段 4 假设已在一个重要方面过时：

- `AdaptiveKLPPO` 已拥有维护状态的 CUDA 推出路径。
- [device_dict_rollout_buffer.py](../../../python/rl/policy_algo/device_dict_rollout_buffer.py) 已能将字典推出张量存储在设备上。
- [ppo_adaptive_kl.py](../../../python/rl/policy_algo/ppo_adaptive_kl.py) 在 CUDA 观测桥激活时自动使用设备缓冲区。
- 因此，CUDA 桥已消除了学习者侧用于推出小批量的 NumPy 往返开销。

当前基准证据清晰显示了这种分离：

- `train()` 在设备驻留小批量使用后显著提升。
- `collect_rollouts()` 表现混合甚至为负。
- 因此，即使学习者侧设备缓冲区已存在，维护的 `p5` 路径仍存在推出侧的热路径瓶颈。

## 研究发现

下一个受限瓶颈是 [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py) 中的主机观测返回契约。

当前维护的适配器仍在每次 `reset()` 和 `step()` 中执行以下操作：

- `_obs_from_buf()` 返回 `deepcopy(self.buf_obs)`
- `step_wait()` 返回 `deepcopy(self.buf_infos)`

观测深拷贝尤其可疑，因为：

- `WorldBatchVecEnv` 是单进程的，且已拥有 `buf_obs`。
- 维护的 CUDA 桥无论如何都会直接从 `buf_obs` 读取。
- 兄弟适配器 [shared_memory_vec_env.py](../../../python/rl/runtime/shared_memory_vec_env.py) 已返回共享观测视图，而非深拷贝观测。
- 终止观测仍需要显式拷贝，但普通的步骤/重置返回路径似乎并不需要。

## 范围

此冻结仅涵盖维护的推出热路径。

范围内：

- `WorldBatchVecEnv.reset()` 和 `WorldBatchVecEnv.step()` 的观测返回语义
- 维护的训练/运行时配置管道以支持该行为
- 针对共享视图安全边界的回归测试
- 对维护的 `p5` 类似案例的吞吐量测量

范围外：

- 精确的 GPU 世界步进
- 奖励/运行时语义重写
- 传感器或通信系统的深度 GPU 集成
- 更改终止观测所有权语义

## 已冻结任务列表

- [x] 为 `WorldBatchVecEnv` 添加明确的维护的观测返回模式。
  允许值：`copy`，`view`。
  兼容性默认值保持为 `copy`。
  两种模式下终止观测均保持拷贝。

- [x] 将观测返回模式通过维护的训练/运行时入口点传递。
  已落地于 [train.py](../../../train.py) 和
  `benchmark.py --family policy_observation_bridge`。

- [x] 在任何默认值更改前锁定回归测试覆盖。
  已落地于 [test_world_batch_vec_env.py](../../../tests/world_batch/test_world_batch_vec_env.py)：
  `view` 模式与 `buf_obs` 共享内存，`copy` 模式分离，并且
  `terminal_observation` 保持分离。

- [x] 在维护的执行路径上对 `copy` vs `view` 进行基准测试。
  主要指标：`collect_plus_train_ms_per_env_step`。
  次要指标：`rollout_ms_per_env_step`，`train_ms_per_env_step`。

- [ ] 决定 `view` 是否成为维护的默认值。
  门控条件：
  如果 `view` 在维护的生产批量大小下仅为中性/有噪声，则保持
  `copy` 为默认值并在此停止。

- [ ] 考虑针对信息拷贝缩减的单独后续任务。
  `buf_infos` 不在此冻结范围内。

## 需要控制的风险

- 外部调用者可能会修改返回的观测。
- 回调代码可能跨步骤保留观测引用。
- 自动重置不得将过时的终止数据暴露为下一个实时观测。
- `terminal_observation` 必须与 `buf_obs` 存储保持分离。
- 基准测试胜利必须基于 `collect + train` 测量，而非仅策略前向延迟。

## 验收标准

- `view` 模式可证明与 `buf_obs` 共享内存。
- `copy` 模式保留旧的分离行为。
- `terminal_observation` 在两种模式下均保持拷贝。
- 维护的单元测试通过 `WorldBatchVecEnv`。
- 在任何默认值提升之前，基准测试结果已记录在此文档或总检查列表中。

## 基准测试协议

使用 [tools/diagnostics/benchmark.py](../../../tools/diagnostics/benchmark.py)
使用相同的案例和种子，仅更改 `observation_return_mode`。

最小协议：

```bash
./.venv/bin/python tools/diagnostics/benchmark.py --family policy_observation_bridge -- \
  --case p5like_visual \
  --n-envs 8 \
  --rollout-steps 64 \
  --rollout-repeats 2 \
  --observation-return-mode copy

./.venv/bin/python tools/diagnostics/benchmark.py --family policy_observation_bridge -- \
  --case p5like_visual \
  --n-envs 8 \
  --rollout-steps 64 \
  --rollout-repeats 2 \
  --observation-return-mode view
```

至少比较以下指标：

- `bridge_on.collect_plus_train_ms_per_env_step`
- `bridge_on.rollout_ms_per_env_step`
- `bridge_on.train_ms_per_env_step`

## 初始基准测试结果

环境：

- 解释器：仓库 `.venv`
- GPU：NVIDIA GeForce RTX 3090
- 场景：
  [takeoff_to_landing_continuous_train_v1.json](../../../scenarios/combined/takeoff_to_landing_continuous_train_v1.json)

执行：

- `p5like_visual`，`n_envs=8`，`rollout_steps=64`，`rollout_repeats=2`
- `obs_gpuhost_novis`，`n_envs=8`，`rollout_steps=64`，`rollout_repeats=2`
- 确认性 `p5like_visual`，`n_envs=16`，`rollout_steps=64`，`rollout_repeats=3`

关键比较：仅 `bridge_on`，因为那是维护的 CUDA 学习者路径。

结果：

- `p5like_visual`，`n_envs=8`
  - `copy`：`collect+train = 0.9707 ms/env-step`
  - `view`：`collect+train = 0.9539 ms/env-step`
  - `view` 快约 `1.7%`

- `obs_gpuhost_novis`，`n_envs=8`
  - `copy`：`collect+train = 0.9319 ms/env-step`
  - `view`：`collect+train = 0.8927 ms/env-step`
  - `view` 快约 `4.2%`

- `p5like_visual`，`n_envs=16`
  - `copy`：`collect+train = 0.7957 ms/env-step`
  - `view`：`collect+train = 0.7937 ms/env-step`
  - `view` 快约 `0.25%`

解释：

- 移除 `deepcopy(self.buf_obs)` 并非回归。
- 在较小的维护批量上可能有帮助。
- 在更大的维护批量上，优势趋于噪声。
- 目前尚无足够强的证据将 `view` 提升为维护的默认值。

当前决策：

- 保持 `observation_return_mode=copy` 作为维护的默认值
- 保留 `view` 用于受控基准测试和未来提升
- 将此阶段视为功能已验证，但尚未达到默认值级别

## 冻结规则

请勿将此阶段与精确的 GPU 模拟步进或更深入的运行时重写混合。此冻结的目的是隔离维护的推出热路径，并一次测量一个狭窄的所有权变更。
