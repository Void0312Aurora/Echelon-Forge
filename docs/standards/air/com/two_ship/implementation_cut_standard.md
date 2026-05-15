# 双机实现切分标准 (Two-Ship Implementation Cut Standard)

> ARCHIVED NOTE (2026-03-23): 该文档属于第一版 air-specific 双机标准草案，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/CMO/docs/standards/README.md)。

本文档把双机阶段第一版实现拆成可执行的工程切分，避免一次性把环境、策略和奖励全部推翻。

## 1. 第一批代码目标

第一批实现只做“接口层就绪 + 脚本基线可挂接”：

- 让 `TaskOrder / LeaderIntent / PilotReport` 能表达双机 element 语义
- 让场景能声明 lead / wingman 的从属关系
- 让现有 `C2 -> Leader -> Execution` 主链可以承载双机对象

第一批不直接交付：

- 完整双机 RL 环境
- 四机 package runtime
- 双边 self-play

## 2. 建议代码切分

### 2.1 数据结构层

优先修改：

- `src/components/physics/action.h`
- `src/components/systems/comm.h`
- `src/interfaces/python/python_module.cpp`

目标：

- `TaskOrder` 增加 assignee、element、formation、lead/wingman 身份字段
- `LeaderIntent` 增加 element phase、formation mode、wingman command 字段
- `PilotReport` 增加编队误差与 separation 字段

### 2.2 Python 适配层

优先修改：

- `gym_envs/leader_env.py`
- `python/rl/leader_tasking.py`

目标：

- clone / bridge 逻辑能保留新字段
- `ScriptedC2TaskManager` 和 `RuleBasedLeaderPhaseManager` 能识别 element 级 task 语义

### 2.3 场景层

后续新增：

- 双机 spawn 模板
- `element_id`
- `role_id`
- 初始编队模板
- 默认 join / rejoin policy

建议优先放在：

- `ScenarioLoader`
- `scenario_runtime`
- 场景 JSON schema 解释层

### 2.4 RL 环境层

第一阶段只建议新增一个受限环境：

- `WingmanTrainingEnv`

特点：

- lead 为脚本
- wingman 动作空间受限
- 奖励聚焦 slot 保持、rejoin、安全间隔

`LeadTrainingEnv` 的双机扩展放在第二阶段。

## 3. 现实导向的实现顺序

建议按以下顺序推进：

1. 数据结构与绑定扩展
2. 双机脚本基线
3. 双机场景模板
4. `WingmanTrainingEnv`
5. `LeadTrainingEnv` 双机扩展
6. 四机 package 预研

## 4. 第一批单测要求

第一批实现至少应补：

- 新字段能在 `SimulationKernel` 内 set/get 往返
- Python 绑定可直接访问新字段
- clone / bridge 逻辑不会丢失双机字段
- 不影响现有单机链路回归

## 5. 第二批实现入口

当第一批完成后，再进入以下实现：

- 场景级双机 spawn 与 element routing
- lead 对 wingman 的 formation mode 下达
- wingman 的 join / rejoin 状态机
- 双机奖励与终止

## 6. 复杂度控制原则

双机阶段复杂度上升的控制方式不是“减少真实性”，而是“减少同时自由度”。

因此第一版必须坚持：

- 只激活一个 `Element`
- 只在一个任务线程内做协同
- 只开放受限 wingman 动作集
- 不让 C2、lead、wingman 同时端到端学习
