# 训练配置说明

本文件夹包含[train.py](../../../train.py)所维护的JSON配置。

训练配置入口表面使用的状态分类：

- `权威 (Authoritative)`
  - 配置系列默认维护的起点。
- `活跃主线 (Active Mainline)`
  - 正在进行的配置，定义当前正向推进的训练线路集合。
- `冻结基线 (Frozen Baseline)`
  - 维护的稳定配置，用于可复现的冻结后训练和验证。
- `兼容性 (Compatibility)`
  - 维护的桥接配置，仅用于保留当前合约或工作流形态，同时避免直接依赖归档。
- `已归档 (Archived)`
  - 仅为溯源、结果查阅或谱系审查而保留的历史配置。

## 维护表面

- [default_ppo.json](default_ppo.json)
  - `权威`最小通用后备配置，由`train.py --train_config`在未提供配置时使用。
- [curriculum/](curriculum)
  - `权威`可复用的课程/随机化片段。
- [frozen/](frozen/README.md)
  - `冻结基线`维护的冻结后主控和执行层训练入口点。这些不是当前的向前推进训练主线。
- [active/](active/README.md)
  - `活跃主线`正在进行的训练入口，覆盖 cooperative flight/combined、air-combat `1v1` 与 naval `N4` smoke/probe 多条线路。

避免在此目录下直接添加临时实验JSON文件。新的维护运行应放在`frozen/`或一个有意命名的活跃子目录中，并附上说明所有权和验收标准的README。

## 冻结基线

维护的冻结基线现位于[frozen](frozen/README.md)下。

- 使用[leader_task_only_frozen_v1.json](frozen/leader_task_only_frozen_v1.json)进行仅任务/通用核心主控运行。
- 使用[leader_c2_frozen_v1.json](frozen/leader_c2_frozen_v1.json)进行报告/完整链主控运行。
- 使用[leader_task_only_retrain_v1.json](frozen/leader_task_only_retrain_v1.json)和[leader_c2_retrain_v1.json](frozen/leader_c2_retrain_v1.json)进行冻结重训练线。
- 两个配置均直接指向冻结的执行工件，位于`experiments/_archive_20260322_test_results/...`下，而不是依赖历史路径重映射。

## 归档

历史配置保留在[examples/config/Archive/training](../Archive/training)下，仅供溯源：

- [pre_freeze_experiments](../Archive/training/pre_freeze_experiments/README.md)
  - 较旧的根级`p2/p3/p4/p5`、起飞-离场和transformer实验配置。
- [leader_legacy](../Archive/training/leader_legacy/README.md)
  - 历史的`p6_*/p7_*`主控层配置。

## 当前正向线路

- [active/](active/README.md)
  - 当前正在进行的入口覆盖 cooperative flight/combined routes、air-combat `1v1` HMoE probes 与 naval `N4` pre-fire runtime gates。
  - ground 尚不是 active RL training line。受维护的 ground 证据仅限 tasking/native-schema bootstrap coverage；movement、terrain、sensing、fires、damage 与完整 ground runtime 行为仍保持 held。

- 协作HMoE控制脚本：
  - [run_hmoe_cooperative_takeoff_to_cruise_control.sh](../../../scripts/run_hmoe_cooperative_takeoff_to_cruise_control.sh)
  - 运行配对的共享vs-HMoE协作起飞至巡航控制线路，使用`*_shared_fair_v1`和`*_hmoe_fair_v1`配置。

归档配置不是维护的训练入口点。如果需要恢复某个配置，请将其复制到维护的活跃目录，并更新其场景配对、运行时假设和验收目标。

维护的文档、合同和桥接入口点不应直接指向`examples/config/Archive/**`。如果需要保留较旧的行为，请先在`Archive`之外提升或保存一个维护的`冻结基线`或`兼容性`配置。

## 主控性能调节旋钮

主控层配置可以通过以下方式降低冻结执行策略推理成本：

- `leader_env.execution_action_repeat`
  - 将一个低级执行动作重复用于多个60 Hz仿真步骤。
  - `1`表示每个低级步骤都预测。
  - `2`表示一个预测用于两个低级步骤。
  - 较大的值提高吞吐量，但降低低级控制带宽。

此旋钮在[leader_env.py](../../../gym_envs/leader_env.py)中实现，并由[leader_perf_probe.py](../../../tools/diagnostics/leader_perf_probe.py)报告。

## 视觉性能调节旋钮

执行层配置可以通过以下方式降低ARB观测成本：

- `env.visual_downsample`
  - 直接更改ARB渲染分辨率。
  - 这不是“以原生分辨率渲染然后平均池化”。
  - 原生ARB为`48x96x10`。
  - `visual_downsample=2`渲染`24x48x10`。
  - `visual_downsample=4`渲染`12x24x10`。

- `env.visual_update_interval`
  - 在刷新之间重用上一个视觉张量。
  - 这降低了视觉生成频率，但与渲染分辨率无关。

直接低分辨率渲染路径在[simulation_kernel.cpp](../../../src/core/engine/simulation_kernel.cpp)和[visual_system.h](../../../src/systems/visual/visual_system.h)中实现。

## 运行时并行性

训练运行时配置还支持：

- `runtime.shared_memory_vec_env`
  - 当`n_envs > 1`时，使用[shared_memory_vec_env.py](../../../python/rl/runtime/shared_memory_vec_env.py)替代标准的`SubprocVecEnv`。
  - 工作进程将观测写入父进程拥有的共享内存。
  - 管道流量减少为奖励/完成/信息/重置元数据，避免了每步大型观测序列化的开销。

- `runtime.world_batch_vec_env`
  - 使用[world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)进行执行层训练，替代`DummyVecEnv`/`SubprocVecEnv`。
  - 这将执行轨迹通过一个`ef_py.WorldBatchRuntime`路由，因此步进和回读使用批处理C++ API而不是每环境Python循环。
  - 维护的冻结后执行`p5`配置现在使用此路径，并带有`batch_observation_backend=compiled`和`batch_visual_backend=compiled`。
  - 维护的基线：精确的世界步进仍然是CPU `SimulationKernel::step()`。保留的`gpu_host/fullgpu`辅助线路现在仅为基准测试使用，不再是默认执行路径的一部分。

- `runtime.world_batch_threads`
  - 控制`ef_py.WorldBatchRuntime.set_worker_threads()`。
  - 默认值为`1`。
  - 仅当明确需要自动模式时使用`0`。
  - 当前在此代码库上的Phase 4基准测试显示，激进的运行时内线程化可能比`1`更慢，因为单个世界步进相对于线程调度开销仍然太便宜。
  - 如果增加了更多CPU，更安全的第一步通常是增加`n_envs`；将`world_batch_threads`视为一个经过测量的调节旋钮，而不是“越多越快”的开关。

- 早期的单进程批处理/共享运行时主控路由不再是此repo中的维护基线。
  - 使用[leader_perf_probe.py](../../../tools/diagnostics/leader_perf_probe.py)比较维护的`subproc`、`shared`和`dummy`后端，而不是依赖旧的实验性标志。

## 有用的探针

- 训练时非有限探针：
  - `train.py`支持一个可选加入的运行时非有限张量探针，通过`--nonfinite_probe`启用。
  - 启用后，维护的PPO训练路径记录轨迹、特征、潜在、动作头、损失、梯度和后步参数有限性检查，并在第一个`NaN/Inf`上中止，同时写入JSON报告。
  - 使用`--nonfinite_probe_report <path>`覆盖实验目录内的默认报告位置。
  - 该探针适用于需要精确捕获失败的不稳定运行；它不是默认训练路径。

- 主控吞吐量：

```bash
./.venv/bin/python tools/diagnostics/leader_perf_probe.py \
  --scenario scenarios/takeoff/takeoff.json \
  --train_config examples/config/training/frozen/leader_c2_frozen_v1.json \
  --n_envs 4 \
  --leader_steps 32 \
  --vec_backend subproc
```

- 使用共享内存vec env的主控吞吐量：

```bash
./.venv/bin/python tools/diagnostics/leader_perf_probe.py \
  --scenario scenarios/takeoff/takeoff.json \
  --train_config examples/config/training/frozen/leader_c2_frozen_v1.json \
  --n_envs 4 \
  --leader_steps 32 \
  --vec_backend shared
```

- 视觉下采样扫描：

```bash
./.venv/bin/python tools/diagnostics/benchmark.py --family visual_resolution --family-help
```

- Phase 4执行批处理运行时轨迹基准测试：

```bash
./.venv/bin/python tools/diagnostics/benchmark.py --family world_batch_vec_env -- \
  --scenario scenarios/combined/takeoff_to_landing_continuous_train_v1.json \
  --n-envs 8 \
  --steps 128 \
  --mission-obs-mode nav_v2
```

- Phase 4维护的`p5`主线桥接基准测试：

```bash
./.venv/bin/python tools/diagnostics/benchmark.py --family policy_observation_bridge -- \
  --case p5like_visual_mainline \
  --n-envs 8 \
  --rollout-steps 64 \
  --rollout-repeats 2 \
  --flight-shaping-backend compiled

./.venv/bin/python tools/diagnostics/benchmark.py --family policy_observation_bridge -- \
  --case experimental_p5like_visual_gpuhost_visual \
  --allow-experimental \
  --n-envs 8 \
  --rollout-steps 64 \
  --rollout-repeats 2 \
  --flight-shaping-backend compiled
```

- Phase 4保留的实验性辅助A/B基准测试：

```bash
./.venv/bin/python tools/diagnostics/benchmark.py --family policy_observation_bridge -- \
  --case experimental_p5like_visual_all_gpuhost \
  --allow-experimental \
  --n-envs 8 \
  --rollout-steps 64 \
  --rollout-repeats 2 \
  --flight-shaping-backend gpu_host
```
