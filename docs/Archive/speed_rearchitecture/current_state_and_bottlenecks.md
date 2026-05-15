# [ARCHIVED] 当前结构与瓶颈定位

注意：

- 本文件已于 2026-03-22 归档，仅保留热路径归因与收尾记录。
- 本文件只用于热路径归因与收尾记录，不再作为阶段推进清单。
- 自 2026-03-22 起，以下分析不授权继续做 helper 级优化或微调。
- 截至 2026-03-22 晚上的固定 probe，这条 leader decision window 粗粒度结构替换路线已触发止损，并已终止。

## 1. 当前真实热路径

### 1.1 执行层单步链路

当前执行层训练主链仍然是：

`UniversalEnv.step()`
-> `normalize_action()`
-> `build_pilot_action()`
-> `SimulationKernel.step()`
-> `ScenarioLoader.update_behaviors()`
-> `UniversalEnv._get_obs()`
-> `build_universal_observation()`
-> `ScenarioLoader.compute_full_step()`
-> `build_step_info()`

对应主要代码入口：

- `gym_envs/universal_env.py`
- `gym_envs/scenario_loader.py`

关键事实：

- `SimulationKernel.step()` 本身已经在 C++。
- 但 step 后的 mission update、reward、termination、obs 拼装仍主要由 Python 驱动。
- 即使 reward/safety/objective 的底层 helper 已有 C++ 版本，Python 仍然负责：
  - 读取状态
  - 组装输入结构
  - 调用多个 helper
  - 维护 waypoint / approach / objective / termination 的 episode state
  - 拼装最终 `info`

### 1.2 Leader 层单步链路

当前 leader 层训练主链是：

`LeaderTrainingEnv.begin_batched_leader_step()`
-> leader action decode / sanitize
-> scripted C2 update
-> baseline snapshot
-> mission command writeback
-> 在一个 leader decision window 内重复推进低层执行环境
-> `finish_batched_leader_step()`
-> 汇总 execution reward 与 leader reward terms

对应主要代码入口：

- `gym_envs/leader_env.py`
- `python/rl/leader_batched_vec_env.py`
- `python/rl/leader_world_batch_runtime.py`

关键事实：

- Leader 层是“高层一步，低层多步”的嵌套结构。
- 这条链路的业务判断大量在 Python：
  - phase bucket 决策
  - guard / feasibility
  - baseline 偏差惩罚
  - C2 report / transition
  - command sync
- 即使低层执行世界已经支持 shared `WorldBatchRuntime`，高层窗口逻辑依然留在 Python。
- 对固定 `SubprocVecEnv` 主线配置，最新 timing probe 还表明 leader 主时间并不主要卡在 window 尾部聚合，而是卡在 repeated frozen execution policy forward；`execution_action_select_ms` 明显高于 `reward_finalize_ms / obs_build_ms / info_build_ms`。

### 1.3 批处理链路

当前 batch 优化分三层：

1. `ScenarioCompiler` + `scenario_runtime`
   - 解决场景编译、缓存、世界布置复用
2. `WorldBatchRuntime`
   - 解决多 world 的 reset / apply / set / step / readback
3. `WorldBatchVecEnv` / `LeaderWorldBatchExecutionRuntimeGroup`
   - 尝试把执行层或 leader 低层世界接到 batch runtime

对应主要代码入口：

- `python/scenario_compiler.py`
- `python/scenario_runtime.py`
- `src/core/engine/world_batch_runtime.*`
- `python/rl/world_batch_vec_env.py`
- `python/rl/leader_world_batch_runtime.py`

## 2. 已经完成且有效的优化

### 2.1 Helper 级下沉有效

当前仓库已经把以下 helper 迁到 C++：

- spatial query
- mission nav
- waypoint reward
- approach reward
- conditional objective
- safety / termination

实测收益：

- nav helper: `10.99x`
- waypoint reward: `10.33x`
- approach reward: `15.18x`
- objective helper: `39.62x`
- safety helper: `19.22x`

结论：

- “小而纯”的数学/几何逻辑已经证明适合下沉。
- 这条思路是对的，但当前收益已经被 Python orchestrator 吃回去大半。

### 2.2 共享内存多进程是有效方向

`SharedMemorySubprocVecEnv` 的核心价值不是减少计算，而是保留多进程并行的同时，降低大 observation 的序列化成本。

结论：

- 对当前代码库，进程级并行仍然比“回到单进程大循环”更重要。
- 后续重构不应轻易放弃 subprocess actor 模型。

## 3. 已经尝试但收益有限的优化

### 3.1 Phase 4 world_batch 只带来边际收益

实测：

- layout build speedup: `0.96x`
- kernel apply speedup: `1.01x`
- step/read speedup: `1.10x`
- vec env reset speedup: `0.94x`
- vec env env-step speedup: `1.06x`

结论：

- 问题不在“单个 kernel 调用太慢”，而在“kernel 调用之外还有大量 Python 热路径”。
- 因此继续围绕 `step_batch()`、`get_*_batch()` 做小修补，不会带来数量级改善。

### 3.2 Leader 单进程 batched/shared-runtime 路线没有跑赢 subproc

实测：

- `subproc`: `leader_fps = 25.59`
- `batched + leader_world_batch_runtime`: `leader_fps = 15.37`

这说明：

- 当前 leader 热路径中，单进程集中化带来的调度损失，大于共享低层 runtime 带来的收益。
- 把 leader env 全部收回一个进程，等于主动放弃了现成的进程级并行。

## 4. 仍然卡住吞吐的根因

### 4.1 Python 仍是“每步业务核心”

`ScenarioLoader.compute_full_step()` 虽然会调用多个 runtime helper，但整个 episode state machine 仍在 Python 控制。

这导致：

- 每步多个 Python 函数调用
- 多次 Python 对象访问
- 多次 C++ -> Python -> C++ 输入组装
- waypoint / approach / objective / termination 状态都由 Python 持有

### 4.2 observation/build/info 路径仍是 Python 拼装

当前 observation 不是一次性从编译态 runtime 产出，而是：

- 先拿 `InstrumentState`
- 再拿 `AgentObservation`
- 再在 Python 里做 mission obs
- 再拼 contacts / rwr / proprio / visual
- 再单独组装 `info`

这意味着跨语言边界仍然是高频、细粒度的。

### 4.3 Leader 决策窗口仍由 Python 驱动

leader 一次 step 内部要推进多个低层 step。

当前这部分不是一个编译态“window rollout”调用，而是 Python 逐步控制：

- 判断是否 pending
- 拉 observation
- 调 policy
- 推进一步
- 汇总 reward / transition / report

这类嵌套调度极易吞掉 batch runtime 的理论收益。

### 4.4 真实主线配置与 batch backend 兼容性仍不完整

当前主线执行模型是：

- visual observation
- `MultiTimescaleActionWrapper`
- 连续任务执行策略

而 `train.py` 里 `world_batch_vec_env` 仍对 `include_visual=True` 和 wrapper 场景加了 guardrail。

这意味着：

- 当前 Phase 4 backend 并没有真正覆盖主线 execution 训练流。
- 即使测试已扩展支持，训练主入口仍未把它当成可信默认路径。

### 4.5 benchmark hygiene 仍需收紧

一些直接调用 C++ kernel 的 benchmark 脚本没有像 `UniversalEnv` 一样统一下压日志级别，reset/info 日志会污染观测。

这不是主瓶颈，但会放大噪声，影响后续性能判读。

## 5. 本次终止前确认的约束

从当前现状反推，在本次终止前已经确认：

1. 不能只优化 helper，必须优化“单步合同”。
2. 不能默认回到单进程大循环，必须保留多进程 actor 并行。
3. 不能只覆盖 non-visual/unwrapped 分支，必须覆盖主线 visual + wrapper 执行流。
4. 如果新的结构替换仍然只在 `1.00x-1.05x` 波动区间，就必须停止，不得继续在现有 leader window/runtime 线上做增量试验。
5. 不能让 leader 层继续在 Python 中手工推进低层 decision window。
5. 不能要求训练脚本大幅改变外部接口，必须保留与 SB3 兼容的 vec env 语义。
