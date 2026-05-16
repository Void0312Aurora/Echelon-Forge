# Code Layer Map

本手册用于回答四个问题：

1. 当前仓库从 C++ 内核到 Python 训练入口的主链是什么。
2. `src/`、`python/`、`gym_envs/`、`tests/`、`tools/` 分别承担什么责任。
3. 当某类问题出现时，应该优先去哪个目录看代码。
4. 现有文档入口在哪里，不需要再靠 `find` 和 `rg` 盲查。

本文档描述的是当前维护主线的代码组织，不复用已经归档的旧 `air-first`
架构说明。

## 1. 主链总览

当前代码主链可以概括为：

```text
src/components + src/models + src/systems
  -> src/core/engine + src/core/mission
    -> src/runtime/facade
      -> src/interfaces/python
        -> python/rl + gym_envs
          -> tests/ + tools/
```

如果按运行视角展开，则更接近：

```text
SimulationKernel / WorldBatchRuntime
  -> mission runtime / episode controller
    -> RuntimeFacade / Python bindings
      -> UniversalEnv / LeaderEnv / scenario loader
        -> RL runtime / training / evaluation / diagnostics
```

## 2. `src/` 层

`src/` 是 C++ 真正的运行时基础。

推荐入口：

- [src/README.md](/home/void0312/Workshop/CMO/src/README.md)
- [src/core/README.md](/home/void0312/Workshop/CMO/src/core/README.md)
- [src/runtime/README.md](/home/void0312/Workshop/CMO/src/runtime/README.md)
- [src/interfaces/python/README.md](/home/void0312/Workshop/CMO/src/interfaces/python/README.md)

### `src/components/`

职责：

- ECS component
- command/tasking DTO
- 可绑定、可持久化的轻量值类型

优先看：

- [src/components/README.md](/home/void0312/Workshop/CMO/src/components/README.md)
- [src/components/command/README.md](/home/void0312/Workshop/CMO/src/components/command/README.md)
- [src/components/tasking/README.md](/home/void0312/Workshop/CMO/src/components/tasking/README.md)

典型问题：

- `MissionCommand` / `PilotAction` / `TaskOrder` 字段在哪里定义
- 哪些字段属于 `common`，哪些属于 `air` / `naval`

### `src/systems/`

职责：

- 每 tick 的 ECS mutation 逻辑
- 物理、战斗、平台系统、视觉更新

优先看：

- [src/systems/README.md](/home/void0312/Workshop/CMO/src/systems/README.md)
- [src/systems/physics/README.md](/home/void0312/Workshop/CMO/src/systems/physics/README.md)
- [src/systems/systems/README.md](/home/void0312/Workshop/CMO/src/systems/systems/README.md)

典型问题：

- 命令如何被投递并生效
- 力学、仪表、导航、传感器状态每帧如何推进

### `src/models/`

职责：

- 可替换的领域模型默认实现
- control / sensor / guidance / effects / unit factory

优先看：

- [src/models/README.md](/home/void0312/Workshop/CMO/src/models/README.md)
- [src/models/air/README.md](/home/void0312/Workshop/CMO/src/models/air/README.md)
- [src/models/weapons/README.md](/home/void0312/Workshop/CMO/src/models/weapons/README.md)

典型问题：

- 默认控制律在哪里
- 传感器、制导、武器效果默认模型在哪里

### `src/core/`

职责：

- 单 world kernel
- batch runtime
- mission runtime
- execution episode controller
- geometry query

优先看：

- [src/core/engine/README.md](/home/void0312/Workshop/CMO/src/core/engine/README.md)
- [src/core/mission/README.md](/home/void0312/Workshop/CMO/src/core/mission/README.md)
- [src/core/mission/runtime/README.md](/home/void0312/Workshop/CMO/src/core/mission/runtime/README.md)
- [src/core/mission/episode/README.md](/home/void0312/Workshop/CMO/src/core/mission/episode/README.md)

典型问题：

- `SimulationKernel` 和 `WorldBatchRuntime` 的 owner 在哪里
- reward / objective / termination / episode transition 在哪里

### `src/runtime/`

职责：

- 维护中的 C++ 应用层 contract
- facade request/result
- 前端长期依赖的 typed runtime API

优先看：

- [src/runtime/contracts/README.md](/home/void0312/Workshop/CMO/src/runtime/contracts/README.md)
- [src/runtime/facade/README.md](/home/void0312/Workshop/CMO/src/runtime/facade/README.md)

典型问题：

- Python 或未来前端应该依赖什么，而不是直接抓 `SimulationKernel`

### `src/interfaces/python/`

职责：

- `ef_py` nanobind 暴露层
- 绑定分区和轻量类型转换

优先看：

- [src/interfaces/python/README.md](/home/void0312/Workshop/CMO/src/interfaces/python/README.md)

典型问题：

- 某个 C++ 类型是从哪个 binding 文件暴露到 Python 的

### `src/gpu/`

职责：

- 维护中的 GPU helper
- packet runtime
- 显式实验探针

优先看：

- [src/gpu/README.md](/home/void0312/Workshop/CMO/src/gpu/README.md)
- [src/gpu/experimental/README.md](/home/void0312/Workshop/CMO/src/gpu/experimental/README.md)

典型问题：

- 哪些 GPU 路径已经是维护 helper
- 哪些仍然只是实验或 parity 探针

## 3. `python/` 层

`python/` 是 Python 侧的运行时支持和训练基础设施，不是单纯脚本堆。

推荐入口：

- [python/README.md](/home/void0312/Workshop/CMO/python/README.md)
- [python/scenario_compiler.py](/home/void0312/Workshop/CMO/python/scenario_compiler.py)
- [python/scenario_runtime.py](/home/void0312/Workshop/CMO/python/scenario_runtime.py)

当前主要分为：

- `python/rl/`
- `python/testing/`
- `python/world_model/`
- 其他跨域支持模块

### `python/rl/`

这是 Python RL 主线的核心目录，已经按子域拆分：

- `control/`
  - 脚本控制器与 wrapper
- `tasking/`
  - leader/tasking bridge 与 common-core profile glue
- `runtime/`
  - vec env、leader runtime、world-batch runtime 适配
- `policy_algo/`
  - PPO、自定义 rollout buffer、HMoE routing/policy glue
- `planning/`
  - 路径/航路规划辅助
- `support/`
  - benchmark、compat、probe 等支持模块
- `profile/`
  - `common/air/naval` profile 推断与默认值

典型问题：

- 为什么某个训练入口会走到 shared/world-batch runtime
- 某个 leader/tasking 语义在 Python 侧怎么桥接
- HMoE 或 policy algo 定制逻辑在哪里

### `python/testing/`

职责：

- contract runner
- Python 侧测试运行时辅助

优先看：

- [scenario_contract_runner.py](/home/void0312/Workshop/CMO/python/testing/scenario_contract_runner.py)

## 4. `gym_envs/` 层

`gym_envs/` 是 Python 环境封装层，负责把 C++ runtime、mission state 和训练接口接起来。

推荐入口：

- [gym_envs/README.md](/home/void0312/Workshop/CMO/gym_envs/README.md)
- [gym_envs/universal_env.py](/home/void0312/Workshop/CMO/gym_envs/universal_env.py)
- [gym_envs/leader_env.py](/home/void0312/Workshop/CMO/gym_envs/leader_env.py)

当前主入口有两个：

- [gym_envs/universal_env.py](/home/void0312/Workshop/CMO/gym_envs/universal_env.py)
  - 执行层/单机主环境
- [gym_envs/leader_env.py](/home/void0312/Workshop/CMO/gym_envs/leader_env.py)
  - 长机层环境

### `gym_envs/scenario_loader/`

这是场景运行时 glue 的核心目录，已经拆成多个子域：

- `core.py`
  - 主 loader owner 与跨子域编排
- `loading.py`
  - 场景加载
- `mission_observation.py`
  - mission observation 相关拼装
- `behavior_runtime/`
  - command chain 与 post-waypoint transition
- `execution_runtime/`
  - step 主线、shadow、shaping
- `navigation_runtime/`
  - 引导与 waypoint reward
- `reward_runtime/`
  - reward 输入、目标、安全、compiled runtime
- `preparation_runtime/`
  - mission / task order / waypoint 准备与随机化
- `spatial_runtime/`
  - geometry 与 world transform 辅助

### `gym_envs/leader_env_parts/`

这是 `leader_env.py` 的拆分子域：

- `decision_runtime/`
  - 长机命令解释和观测构建
- `execution_runtime/`
  - 执行层策略桥接
- `bridges.py`, `runtime_services.py`, `scripted_exec.py`
  - 环境 glue 与服务模块

典型问题：

- 为什么某个 env step 会进到某个 reward/transition 分支
- 长机环境和执行环境的职责怎么分

## 5. `tests/` 层

测试主入口见 [tests/README.md](/home/void0312/Workshop/CMO/tests/README.md)。

当前主要测试域：

- `architecture/`
  - 分层和 target readiness
- `runtime/`
  - mission/runtime/loader/facade 回归
- `world_batch/`
  - batch kernel 与 vec-env 适配
- `leader/`
  - leader/tasking/common-core/naval 语义
- `scenario/`
  - scenario compiler 与 spatial query
- `training/`
  - train entry / callback
- `hmoe/`
  - HMoE 路由与训练 bootstrap
- `contracts/`
  - JSON contract regression 规格
- `support/`
  - 共享测试辅助

当你在改：

- C++ DTO / binding surface
  - 优先看 `tests/runtime/`、`tests/leader/`
- batch runtime / vec env
  - 优先看 `tests/world_batch/`
- facade / layering
  - 优先看 `tests/architecture/`

## 6. `tools/` 层

工具入口见 [tools/README.md](/home/void0312/Workshop/CMO/tools/README.md)。

当前主线分工：

- `tools/eval/`
  - 维护中的评估入口
- `tools/diagnostics/`
  - operator-facing benchmark / probe / replay
- `tools/runners/`
  - 合同与批量 runner
- `tools/maintenance/`
  - 清理、审计、workspace 维护
- `tools/archive/`
  - 旧 probe 和手工脚本归档

## 7. 问题定位建议

如果你遇到的是：

- “字段定义在哪”
  - 从 `src/components/` 开始
- “每帧行为为什么这样变”
  - 从 `src/systems/` 或 `src/models/` 开始
- “mission/reward/termination 为什么这样算”
  - 从 `src/core/mission/` 开始
- “Python 为什么拿到这个观测/奖励”
  - 从 `gym_envs/scenario_loader/` 和 `gym_envs/universal_env.py` 开始
- “leader/tasking 为什么发出这个命令”
  - 从 `python/rl/tasking/` 和 `gym_envs/leader_env_parts/` 开始
- “绑定为什么不一致”
  - 从 `src/interfaces/python/` 和 `tests/runtime/test_bindings_command_surface.py` 开始
- “批量运行或 rollout 为什么慢”
  - 从 `src/core/engine/world_batch_runtime.*`、`python/rl/runtime/`、`tools/diagnostics/` 开始

## 8. 推荐阅读顺序

第一次进仓库，建议按这个顺序读：

1. [README.md](/home/void0312/Workshop/CMO/README.md)
2. [src/README.md](/home/void0312/Workshop/CMO/src/README.md)
3. [src/core/engine/README.md](/home/void0312/Workshop/CMO/src/core/engine/README.md)
4. [src/core/mission/README.md](/home/void0312/Workshop/CMO/src/core/mission/README.md)
5. [src/runtime/facade/README.md](/home/void0312/Workshop/CMO/src/runtime/facade/README.md)
6. [python/README.md](/home/void0312/Workshop/CMO/python/README.md)
7. [gym_envs/README.md](/home/void0312/Workshop/CMO/gym_envs/README.md)
8. [tests/README.md](/home/void0312/Workshop/CMO/tests/README.md)
9. [tools/README.md](/home/void0312/Workshop/CMO/tools/README.md)

如果主要做 Python 环境或训练，再继续读：

1. [python/README.md](/home/void0312/Workshop/CMO/python/README.md)
2. [gym_envs/README.md](/home/void0312/Workshop/CMO/gym_envs/README.md)
3. [gym_envs/scenario_loader/core.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py)
4. [python/rl/runtime/world_batch_vec_env.py](/home/void0312/Workshop/CMO/python/rl/runtime/world_batch_vec_env.py)
5. [python/rl/tasking/leader_tasking.py](/home/void0312/Workshop/CMO/python/rl/tasking/leader_tasking.py)
