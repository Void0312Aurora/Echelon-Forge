# `python/training/` 层职责

`python/training/` 保存主线训练入口的 bootstrap 和 orchestration 支撑。

它的定位不是替代 `python/rl/` 中的算法、policy 或 vec-env 逻辑，而是把
顶层脚本里与“入口协调”强相关的职责收口起来，例如：

- CLI 参数表与默认值
- 训练配置和场景路径校验
- 实验目录、resume / init-from 目录约定
- seed 与 PyTorch runtime bootstrap
- 训练开始前的统一运行时摘要打印

## 已实现的训练表面

- `agent_layer="execution"` 是单策略 air/execution 路径。维护中的 production setup 使用 `runtime.world_batch_vec_env=true` 和 `python.rl.runtime.world_batch_vec_env.WorldBatchVecEnv`；raw `UniversalEnv` / SB3 vec-env 路径是隔离的兼容路径，需要显式设置 `env.runtime_compatibility_enabled=true`。
- `agent_layer="cooperative_execution"` 是 cooperative/common 集成主线。它构建 `python.rl.runtime.cooperative_world_batch_vec_env.CooperativeWorldBatchVecEnv`，支持维护中的 multi-timescale wrapper，是当前 active cooperative training surface。
- `agent_layer="leader"` 构建 `gym_envs.leader_env.LeaderTrainingEnv`，用于 leader-layer policy 工作。单进程 batched leader inference 仍是 opt-in experimental；默认使用常规多进程 vec-env。
- naval N4 训练配置可以声明 `naval_entry`；bootstrap 会校验声明的 scenario/contract 路径，并要求 `action_mode="naval_station3"` 与 `mission_obs_mode="naval_screen_station_v1"`。这是受限的 pre-fire/tasking/contact gate，不是 learned naval weapon-outcome acceptance。
- ground 当前只有 tasking/profile/schema bootstrap。这里没有 maintained full ground runtime，也没有 active ground RL training 入口。

## 当前文件

- [cli.py](cli.py)
  - `train.py` 复用的 argparse 定义。
- [bootstrap.py](bootstrap.py)
  - 路径校验、配置装载、实验目录准备、锁文件、seed / torch runtime 初始化。

## 边界

- 这里可以放训练入口的参数解析、实验目录管理、运行时 bootstrap。
- 不要把 SB3 算法、policy 结构、vec-env 细节重新搬进来。
- `world_model_train.py` 的后续拆分不在这个子域当前阶段的范围内。
