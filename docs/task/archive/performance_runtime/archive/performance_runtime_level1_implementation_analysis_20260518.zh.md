# 一级实现优化分析

状态：`2026-05-18` 活跃分析草案。  
范围：等价算法或近似优化之前的 runtime 计算链分析。

## 1. 定位

本文档刻意停留在优化分层的 Level 1。

这意味着：

- 不引入新的近似行为；
- 不做会改变语义的 shortcut；
- 不预设下一步一定要改算法。

这里要回答的问题更窄：

```text
在当前 runtime 契约和语义不变的前提下，
实现侧开销到底还藏在哪里？
```

## 2. 当前测量快照

### 2.1 `world_batch_vec_env` 对齐对比

历史基线来自
`docs/plan/results/wp6_benchmark_world_batch_vec_env_phase4.json`：

- `dummy_reset_ms = 10.051270`
- `world_batch_reset_ms = 11.891172`
- `dummy_ms_per_env_step = 0.392506`
- `world_batch_ms_per_env_step = 0.292365`
- `step_speedup = 1.342521`

当前已在 `2026-05-18` 用 `build-workshop` runtime 路径采到的对齐样本：

- `dummy_reset_ms = 12.701345` (`+26.37%`)
- `world_batch_reset_ms = 12.906878` (`+8.54%`)
- `dummy_ms_per_env_step = 0.506252` (`+28.98%`)
- `world_batch_ms_per_env_step = 0.393277` (`+34.52%`)
- `step_speedup = 1.287264` (`-4.12%`)

解读：

- 绝对 runtime 比旧参考更慢；
- 但 batch 路径相对 dummy 路径仍然保有 step 优势；
- 因而这是值得修的回归，但还没到崩盘级别。

### 2.2 `UniversalEnv` 热点样本

当前采样的单世界 step timing：

- `air_1v1`：约 `0.587 ms/step`，其中 `obs_build_ms ~= 0.179`
- `naval_screen`：约 `0.569 ms/step`，其中 `obs_build_ms ~= 0.173`
- `c2_demo`：约 `0.876 ms/step`，其中 `obs_build_ms ~= 0.433`

解读：

- `c2_demo` 当前是最明显的单世界热点；
- 其中观测构建占了很大一部分成本。

### 2.3 Cooperative 样本

当前 cooperative smoke 样本：

- single：`step_time_ms ~= 0.772`，`obs_build_ms ~= 0.248`
- cooperative（`n_envs=4`，`8` slots total）：
  - `step_time_ms ~= 5.33`
  - `per_agent_step_time_ms ~= 0.666`
  - `obs_build_ms ~= 1.16`
  - `behavior_update_ms ~= 1.13`
  - `command_sync_ms ~= 0.53`

解读：

- cooperative 执行在 per-agent 维度上仍比原始 wall-clock 看起来更划算；
- 但 `obs_build_ms` 和 `behavior_update_ms` 已经足够高，仍然是首批调查目标。

## 3. 当前计算链

### 3.1 单世界参考链

参考文件：`gym_envs/universal_env.py`

当前 step 顺序：

1. 规范化 action 并构建 `PilotAction`
2. 向 kernel 写 action
3. `sim.step()`
4. 读取 truth 和 instruments
5. `loader.update_behaviors(...)`
6. 构建 observation
7. `loader.compute_full_step(...)`
8. 构建 `info`

这个链路是理解 batch / mainline 路径后续增加协调开销的最简单参照。

### 3.2 `WorldBatchVecEnv` 主线链

参考文件：`python/rl/runtime/world_batch_vec_env.py`

当前 `step_wait()` 顺序：

1. 构建 refs 和可选 instrument snapshots，用于 action 准备
2. 准备每个 world 的 action
3. batch-set pilot actions
4. batch step runtime worlds
5. batch 读取 truth 和 instruments
6. per-world `loader.update_behaviors(...)`
7. 把 command chain 同步回 kernel
8. batch 构建 observations
9. 准备 flight-shaping overrides
10. per-world reward/info evaluation 和 autoreset 处理

关键点是：这条路径已经部分 batch 化，但仍然有几处需要回到 Python 做逐 world 组装。

### 3.3 Cooperative 主线链

参考文件：`python/rl/runtime/cooperative_world_batch_vec_env.py`

当前 cooperative step 顺序：

1. 同步当前 command chain
2. 按 world 分组准备 / 应用每个 slot 的 action
3. batch step 所有 worlds
4. 对每个 world roster 做 state read
5. per-slot `loader.update_behaviors(...)`，再做 director update
6. 再次同步 command chain
7. per-world observation batch build
8. per-slot reward/info evaluation
9. shared-world 终止 / 重置处理

和单 agent 链相比，额外成本主要来自：

- roster fan-out；
- 额外的 Python 协调循环；
- 额外的观测组装；
- shared-world 终止 bookkeeping。

## 4. Level 1 热点候选

### 4.1 `WorldBatchVecEnv` 中的重复视觉刷新

候选位置：

- `_build_observations_from_cached_state(...)` 先刷新目标 batch。
- `_attach_visual_observation(...)` 在挂接缓存视觉 tensor 前又刷新一次单 env。

也就是说，视觉路径看起来像：

```text
batch refresh
  -> per-env attach
  -> per-env refresh again
```

这是经典的 Level 1 候选，因为看起来是重复精确工作，不是语义重设计。

### 4.2 即使在编译路径上，Python 观测组装仍然很热

在以下两个文件中：

- `python/rl/runtime/world_batch_vec_env.py`
- `python/rl/runtime/cooperative_world_batch_vec_env.py`

编译后的观测路径仍然在做逐 env / 逐 slot 的 Python 工作：

- `np.asarray(...)`
- `reshape(...)`
- `dict` 组装
- 可选的 `proprio` packing
- 最终 observation 对象拼装

这仍然属于 Level 1，因为输出契约没有变；问题只是能否在不改算法之前，重用 buffer / view 并减少 Python 分配 churn。

### 4.3 Cooperative state read 仍按 world 在 Python 里分组

cooperative 路径当前会对每个 world roster 循环调用 `read_truth_and_instruments(refs)`。

这说明有一个 Level 1 清理空间：

- 先把当前精确读取收拢成更大的 exact batch call；
- 然后把返回的数据包在本地分发回 slot state。

这不需要新的近似，也不需要新的任务契约；它只是现有 runtime surface 内的实现侧 batching 清理。

### 4.4 Reward/info 尾部仍是 Python 逐 env / 逐 slot 循环

两条 batch 主线仍然会在以下位置花 hot-path 时间：

- `loader.compute_full_step(...)`
- `build_step_info(...)` 或 `build_step_info_minimal(...)`

这并不自动意味着“现在就去重写 reward 算法”。

Level 1 的首要问题更窄：

- caller 不需要时，我们是否还在物化完整 info？
- 是否复制或 reshape 了过多状态？
- 是否有重复的精确准备可以在同一步里复用？

只有这些问题穷尽后，这块才应升级到 Level 2。

### 4.5 Behavior-update 和 command-sync 仍是 Python 串行

当前 batch 路径仍然会执行：
