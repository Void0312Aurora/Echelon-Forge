# `gym_envs/` 层职责

`gym_envs/` 是训练环境封装层。它把 `ef_py` 暴露的 kernel/runtime、`python/scenario_*` 的场景运行时数据，以及训练侧 observation/action/reward 组织成 Gymnasium 风格接口。

主线关系大致为：

```text
ef_py + python/scenario_compiler + python/scenario_runtime
  -> gym_envs/scenario_loader
    -> gym_envs/universal_env.py
    -> gym_envs/leader_env.py
      -> python/rl/runtime + tools/eval + tests
```

## 允许

- Gymnasium env 封装、reset/step/render 组织。
- scenario loader、reward/termination/shaping 的 Python 侧 glue。
- leader 决策层和 execution 层之间的桥接。
- 对 `ef_py` kernel 的轻量运行时适配和 observation 拼装。

## 禁止

- 在 env 文件中重复实现 C++ kernel truth logic。
- 把通用训练算法逻辑直接放进 `gym_envs/`，那应留在 `python/rl/`。
- 为单一实验继续新增同构 env 脚本，而不复用已有 loader/runtime 子域。
- 继续扩大单文件 monster module；应优先进入现有拆分子包。

## 子目录约定

- [universal_env.py](/home/void0312/Workshop/CMO/gym_envs/universal_env.py)
  - 执行层/单机主环境，维护通用 action/observation/reward step 主线。
- [leader_env.py](/home/void0312/Workshop/CMO/gym_envs/leader_env.py)
  - 长机决策层环境，通过 execution backend 驱动底层飞行。
- `scenario_loader/`
  - 场景加载、mission state、route/reward/shaping/transition glue。
- `leader_env_parts/`
  - `leader_env.py` 的拆分子域和共享服务。

## 当前阅读入口

- [universal_env.py](/home/void0312/Workshop/CMO/gym_envs/universal_env.py)
- [leader_env.py](/home/void0312/Workshop/CMO/gym_envs/leader_env.py)
- [scenario_loader/__init__.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/__init__.py)
- [leader_env_parts/__init__.py](/home/void0312/Workshop/CMO/gym_envs/leader_env_parts/__init__.py)

## 当前文件落点

- 根目录
  - [universal_env.py](/home/void0312/Workshop/CMO/gym_envs/universal_env.py)
    - 通用训练环境、观测空间、action 归一化、pilot action 构建。
  - [leader_env.py](/home/void0312/Workshop/CMO/gym_envs/leader_env.py)
    - 长机训练环境、execution backend 接入、decision interval 控制。
- `scenario_loader/`
  - [core.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py)
    - `ScenarioLoader` owner 与跨子域编排。
  - [common.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/common.py)
    - 通用常量、JSON、模式归一化与 shared helper。
  - [loading.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/loading.py)
    - 场景加载、compiled scenario/runtime state 初始化。
  - [mission_observation.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/mission_observation.py)
    - mission observation 拼装与编码。
  - [route_generation.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/route_generation.py)
    - route 生成与派生辅助。
  - [runtime_state.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/runtime_state.py)
    - loader/runtime state 数据结构与当前世界状态衔接。
  - [step_evaluation.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/step_evaluation.py)
    - step 级终止、成功、奖励拆解辅助。
  - `behavior_runtime/`
    - command chain 与 post-waypoint transition。
  - `execution_runtime/`
    - step 主线、shadow 状态、shaping 主路径。
  - `navigation_runtime/`
    - guidance 和 waypoint reward。
  - `preparation_runtime/`
    - mission/task-order/waypoint 准备与随机化。
  - `reward_runtime/`
    - shaping input、objective、安全约束、compiled reward runtime。
  - `spatial_runtime/`
    - geometry、world transform、空间辅助。
- `leader_env_parts/`
  - [common.py](/home/void0312/Workshop/CMO/gym_envs/leader_env_parts/common.py)
    - JSON、角度处理、args stub 等共享 helper。
  - [contracts.py](/home/void0312/Workshop/CMO/gym_envs/leader_env_parts/contracts.py)
    - leader intent / pilot report / task order 的字段与 clone helper。
  - [bridges.py](/home/void0312/Workshop/CMO/gym_envs/leader_env_parts/bridges.py)
    - leader command bridge。
  - [runtime_services.py](/home/void0312/Workshop/CMO/gym_envs/leader_env_parts/runtime_services.py)
    - leader runtime services 汇总。
  - [scripted_exec.py](/home/void0312/Workshop/CMO/gym_envs/leader_env_parts/scripted_exec.py)
    - scripted executive controller。
  - [policy.py](/home/void0312/Workshop/CMO/gym_envs/leader_env_parts/policy.py)
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
  - 先看 `mission_observation.py`
- “为什么 leader policy 输出被解释成这个 command”
  - 先看 `leader_env_parts/decision_runtime/`
- “为什么 leader 环境会走 frozen/scripted execution backend”
  - 先看 `leader_env_parts/execution_runtime/` 与 [leader_env.py](/home/void0312/Workshop/CMO/gym_envs/leader_env.py)

## 迁移备注

- `scenario_loader/` 已经按运行时子域拆开，后续新增 loader 逻辑应进入相应子包，不要把 `core.py` 再次扩成总包。
- `leader_env.py` 仍保留为稳定入口，但实现应继续向 `leader_env_parts/` 下沉。
- 如果未来只保留包入口而不再保留根级单文件 env，需要先保证 `tools/`、`tests/`、训练入口的导入路径同步切换。
