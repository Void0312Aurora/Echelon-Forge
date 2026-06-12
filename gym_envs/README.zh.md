# `gym_envs/` 层职责

`gym_envs/` 是训练环境封装层。它把 `ef_py` 暴露的 kernel/runtime、`python/scenario/compiler/` 与 `python/scenario/runtime/` 的场景运行时数据，以及训练侧 observation/action/reward 组织成 Gymnasium 风格接口。

主线关系大致为：

```text
ef_py + python/scenario/compiler + python/scenario/runtime
  -> gym_envs/scenario_loader
    -> gym_envs/universal_env_parts
    -> gym_envs/universal_env.py
    -> gym_envs/leader_env.py
      -> python/rl/runtime + tools/eval + tests
```

## 允许

- Gymnasium env 封装、reset/step/render 组织。
- scenario loader、reward/termination/shaping 的 Python 侧 glue。
- leader 决策层和 execution 层之间的桥接。
- 对 `ef_py` kernel 的轻量运行时适配和 observation 拼装。

## 域状态口径

- maintained env 路径目前仍以 air/execution 与 cooperative/common training 最成熟。
- maintained production training 会通过 `python.rl.runtime.world_batch_vec_env.WorldBatchVecEnv` 进入 execution runtime，并通过 `python.rl.runtime.cooperative_world_batch_vec_env.CooperativeWorldBatchVecEnv` 进入 cooperative execution。
- `UniversalEnv` 仍是隔离的 single-env compatibility import path。active evaluation 与 diagnostics 应使用维护中的 world-batch/facade adapter，而不是构造 raw `ef_py.SimulationKernel` 路径。
- naval hook 只在明确列出的路径中存在，包括 station action、screen behavior、受限 reward surface，以及通过 runtime 路径承载的 N4 contact-evidence plumbing。
- ground-domain 的 movement、sensing、terrain、fires、damage 与完整 runtime behavior 尚未在这里实现。README 中的 takeoff ground roll 或 runway geometry 指空域执行的跑道阶段逻辑，不代表 ground-domain 支持。

## 禁止

- 在 env 文件中重复实现 C++ kernel truth logic。
- 把通用训练算法逻辑直接放进 `gym_envs/`，那应留在 `python/rl/`。
- 为单一实验继续新增同构 env 脚本，而不复用已有 loader/runtime 子域。
- 继续扩大单文件 monster module；应优先进入现有拆分子包。

## 子目录约定

- [universal_env.py](universal_env.py)
  - 隔离的 single-env compatibility import path。它不是 active production training/eval/diagnostics backend。
- [universal_env_parts/](universal_env_parts)
  - `UniversalEnv` 的主实现子域，维护 action、observation、space、step-info 组装逻辑。
- [leader_env.py](leader_env.py)
  - 长机决策层环境，通过 execution backend 驱动底层执行路径。
- `scenario_loader/`
  - 场景加载、mission state、route/reward/shaping/transition glue。
- `leader_env_parts/`
  - `leader_env.py` 的拆分子域和共享服务。

## 当前阅读入口

- [universal_env.py](universal_env.py)
- [universal_env_parts/__init__.py](universal_env_parts/__init__.py)
- [leader_env.py](leader_env.py)
- [scenario_loader/__init__.py](scenario_loader/__init__.py)
- [leader_env_parts/__init__.py](leader_env_parts/__init__.py)

## 当前文件落点

- 根目录
  - [universal_env.py](universal_env.py)
    - 稳定的 single-env compatibility/debug 入口。主 action/observation/space/info helper 已迁到 `universal_env_parts/`；maintained execution training 通常应使用 world-batch runtime adapter。
  - [leader_env.py](leader_env.py)
    - 长机训练环境、execution backend 接入、decision interval 控制。
- `universal_env_parts/`
  - [actions.py](universal_env_parts/actions.py)
    - pilot action 构建、action 归一化与基础数值变换。
  - [naval_actions.py](universal_env_parts/naval_actions.py)
    - `naval_station3` 的受限 naval station-action 适配。
  - [observations.py](universal_env_parts/observations.py)
    - 通用 observation 拼装与 visual downsample helper。
  - [spaces.py](universal_env_parts/spaces.py)
    - action/observation space 定义与 mission observation 维度约定。
  - [info.py](universal_env_parts/info.py)
    - step info 与 terminal-only info 组装。
- `scenario_loader/`
  - [core.py](scenario_loader/core.py)
    - `ScenarioLoader` owner 与跨子域编排。
  - [common.py](scenario_loader/common.py)
    - 通用常量、JSON、模式归一化与 shared helper。
  - [loading.py](scenario_loader/loading.py)
    - 场景加载、compiled scenario/runtime state 初始化。
  - [mission_observation.py](scenario_loader/mission_observation.py)
    - mission observation 拼装与编码。
  - [route_generation.py](scenario_loader/route_generation.py)
    - route 生成与派生辅助。
  - [runtime_state.py](scenario_loader/runtime_state.py)
    - loader/runtime state 数据结构与当前世界状态衔接。
  - [step_evaluation.py](scenario_loader/step_evaluation.py)
    - step 级终止、成功、奖励拆解辅助。
  - `behavior_runtime/`
    - command chain、post-waypoint transition，以及受限 naval screen station hold。
  - `execution_runtime/`
    - step 主线、shadow 状态、shaping 主路径。
  - `navigation_runtime/`
    - guidance 和 waypoint reward。
  - `preparation_runtime/`
    - mission/task-order/waypoint 准备与随机化。
  - `reward_runtime/`
    - shaping input、objective、安全约束、compiled reward runtime 与受限 naval reward surface。
  - `spatial_runtime/`
    - geometry、world transform、空间辅助。
- `leader_env_parts/`
  - [common.py](leader_env_parts/common.py)
    - JSON、角度处理、args stub 等共享 helper。
  - [contracts.py](leader_env_parts/contracts.py)
    - leader intent / pilot report / task order 的字段与 clone helper。
  - [bridges.py](leader_env_parts/bridges.py)
    - leader command bridge。
  - [runtime_services.py](leader_env_parts/runtime_services.py)
    - leader runtime services 汇总。
  - [scripted_exec.py](leader_env_parts/scripted_exec.py)
    - scripted executive controller。
  - [policy.py](leader_env_parts/policy.py)
    - 冻结 execution policy 加载与适配。
  - `decision_runtime/`
    - 命令解释、动作解码、观测构建、terminal context。
  - `execution_runtime/`
    - execution env/policy/runtime 构建和状态同步。

## 问题定位建议

如果你遇到的是：

- “为什么 env reset 后 mission/waypoint 状态不对”
  - 先看 `scenario_loader/loading.py` 与 `preparation_runtime/`
- “为什么 step 后走到了某个 shaping/reward/termination 分支”
  - 先看 `execution_runtime/`、`reward_runtime/`、`step_evaluation.py`
- “为什么 mission observation 布局或字段不一致”
  - 先看 `mission_observation.py` 与 `universal_env_parts/observations.py`
- “为什么 action/space/info 被组织成现在这个样子”
  - 先看 `universal_env_parts/`
- “为什么 leader policy 输出被解释成这个 command”
  - 先看 `leader_env_parts/decision_runtime/`
- “为什么 leader 环境会走 frozen/scripted execution backend”
  - 先看 `leader_env_parts/execution_runtime/` 与 [leader_env.py](leader_env.py)
- “为什么直接构造 `UniversalEnv(...)` 会失败”
  - active 调用方应使用 world-batch runtime adapter。raw single-env 构造已从维护中的 tools 与 tests 移除。

## 迁移备注

- `scenario_loader/` 已经按运行时子域拆开，后续新增 loader 逻辑应进入相应子包，不要把 `core.py` 再次扩成总包。
- `gym_envs/` 应使用 `python/scenario/compiler/` 与 `python/scenario/runtime/` 下的打包场景入口。
- 旧 `python/scenario/diagnostics/` setup wrapper 已移除；环境 setup 应直接使用 `python/scenario/runtime/` 的 maintained helper。
- `universal_env.py` 不再提供 raw 构造入口；maintained training、eval、diagnostics 与 regression tests 应保持在 runtime-facade / world-batch adapter 上。
- `leader_env.py` 仍保留为稳定入口，但实现应继续向 `leader_env_parts/` 下沉。
- 如果未来只保留包入口而不再保留根级单文件 env，需要先保证 `tools/`、`tests/`、训练入口的导入路径同步切换。
