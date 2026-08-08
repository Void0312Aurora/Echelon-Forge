# 运行时工作流与合同基线

Language:
- English canonical: `docs/architecture/standards/runtime_workflow_and_contract_baseline.md`
- Chinese companion: [runtime_workflow_and_contract_baseline.zh.md](runtime_workflow_and_contract_baseline.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/runtime_workflow_and_contract_baseline.md`
Owner: `architecture/runtime-workflow`
Last verified: `2026-08-08`

状态：维护中的 runtime workflow 与 contract 基线，服从
[严格仿真架构基线](../../plan/architecture/simulation_system_architecture_design.zh.md)。

本文档固定下面几层之间的边界：

- Python 侧的 scenario/task 输入编排
- `ScenarioLoader` 内的 command/behavior bridge
- C++ mission runtime 的纯计算层
- episode/controller 的状态装配与 roundtrip

当“当前代码实际怎么工作”会影响命名、归属或合同设计时，应以本文档为标准入口。

## 本文档负责什么

当前仓库已经不适合再把 runtime 看成一个不可分解的“环境一步”。维护中的工作流已经有明确分层，
标准化工作必须尊重这些分层。

本文档回答：

1. 哪个阶段拥有哪类数据？
2. 哪些 seam 已经稳定到可以标准化？
3. 哪些职责绝不能跨越 Python/C++ 边界混写？

## 当前维护中的工作流

高层链路如下：

`scenario JSON -> load/compile -> normalize task + mission command -> behavior/command-chain update -> runtime step inputs -> C++ mission/runtime products -> episode/controller roundtrip`

在仓库里的主要阶段可以概括为：

1. 场景加载与规范化
2. command-chain 与 behavior 更新
3. step-evaluation 输入装配
4. C++ mission/runtime 纯计算
5. product 回写、状态追踪与 episode roundtrip

## 阶段 1：场景加载与规范化

主要代码入口：

- [gym_envs/scenario_loader/loading.py](../../../gym_envs/scenario_loader/loading.py)
- [gym_envs/scenario_loader/core.py](../../../gym_envs/scenario_loader/core.py)

本阶段负责：

- scenario JSON 加载与编译 handoff
- randomization seed 准备
- active roster 与 world layout 建立
- `task_order` 与 `mission_command` 规范化
- waypoint cache 物化
- 初始目标解析与场景侧 metadata 准备

本阶段不负责：

- command delivery semantics
- 纯 reward/termination 计算
- 字段命名的 doctrine ownership

## 阶段 2：Behavior 与 Command-Chain 更新

主要代码入口：

- [gym_envs/scenario_loader/behavior_runtime/command_chain.py](../../../gym_envs/scenario_loader/behavior_runtime/command_chain.py)
- [gym_envs/scenario_loader/behavior_runtime/command_chain_owner.py](../../../gym_envs/scenario_loader/behavior_runtime/command_chain_owner.py)
- [gym_envs/scenario_loader/behavior_runtime/behavior_phase_owner.py](../../../gym_envs/scenario_loader/behavior_runtime/behavior_phase_owner.py)
- [gym_envs/scenario_loader/behavior_runtime/post_waypoint_transition.py](../../../gym_envs/scenario_loader/behavior_runtime/post_waypoint_transition.py)

本阶段负责：

- `MissionCommand` 与 `CommandLink` 的桥接行为
- phase transition 与 command-chain ownership
- 将 mission-command state 同步到 kernel/runtime 边界
- pending post-waypoint / landing transition 的激活

它对应的稳定合同含义是：

- behavior phase ownership 和 command-chain ownership 都是一级 seam
- command generation 不等于 command execution
- command 替换时，旧状态应当显式清理或显式保留，不能靠偶然行为

## 阶段 3：Step-Evaluation 输入装配

主要代码入口：

- [gym_envs/scenario_loader/mission_observation.py](../../../gym_envs/scenario_loader/mission_observation.py)
- [gym_envs/scenario_loader/step_evaluation.py](../../../gym_envs/scenario_loader/step_evaluation.py)
- [gym_envs/scenario_loader/navigation_runtime/](../../../gym_envs/scenario_loader/navigation_runtime)

本阶段负责：

- mission-observation 输入装配
- route / waypoint / nav products
- step-info 输入装配
- 进入纯 runtime 计算前的 safety 与 shaping 输入准备

本阶段仍然是 bridge layer。它可能同时消费 truth、instrument、runway、route、
mission-command 等数据，但这不代表这些词全部都是 common-core ontology。

## 阶段 4：C++ Mission/Runtime 纯计算

主要代码入口：

- [src/core/mission/README.md](../../../src/core/mission/README.md)
- [src/core/mission/runtime/mission_runtime.cpp](../../../src/core/mission/runtime/mission_runtime.cpp)
- [src/core/mission/runtime/execution_step_runtime.cpp](../../../src/core/mission/runtime/execution_step_runtime.cpp)
- Frame 契约 [execution_frame_runtime.h](../../../src/core/mission/runtime/execution_frame_runtime.h)；实现 owner [execution_episode_runtime.cpp](../../../src/core/mission/runtime/execution_episode_runtime.cpp)
- [src/core/mission/runtime/execution_observation_runtime.cpp](../../../src/core/mission/runtime/execution_observation_runtime.cpp)
- [src/core/mission/runtime/termination_runtime.h](../../../src/core/mission/runtime/termination_runtime.h)

本阶段负责：

- mission observation products
- step-info products
- reward / termination / objective products
- execution-frame 与 execution-step runtime products
- 对准备好的输入执行确定性的纯计算

本阶段必须保持不包含：

- Python binding 关注点
- scenario JSON 解析
- episode controller state import/export
- loader 侧 command/phase ownership 的临时逻辑

## 阶段 5：Product 回写与 Episode Roundtrip

主要代码入口：

- [gym_envs/scenario_loader/execution_runtime/mainline.py](../../../gym_envs/scenario_loader/execution_runtime/mainline.py)
- [src/core/mission/episode/](../../../src/core/mission/episode)
- [tests/runtime/execution/test_execution_episode_controller.py](../../../tests/runtime/execution/test_execution_episode_controller.py)
- [tests/runtime/execution/test_execution_episode_state.py](../../../tests/runtime/execution/test_execution_episode_state.py)

本阶段负责：

- 将 runtime product 回写到维护中的 episode/controller state
- reward breakdown 持久化
- termination/status tracking
- episode state 的 import/export 与 roundtrip

这些逻辑不应再被塞回纯 runtime kernel。

## 当前已稳定的合同对象

以下对象已经稳定到可以作为维护中的 workflow contract：

- `TaskOrder`
- `LeaderIntent`
- `MissionCommand`
- `CommandLink`
- `DataLink`
- mission observation mode contracts
- execution-step/frame runtime products
- termination-reason 与 reward-breakdown 输出

`[tests/runtime/](../../../tests/runtime/README.md)` 下的回归测试是当前主要守门面。

## 字段可见性规则

并不是每个 runtime field 都会在每种 observation mode 下暴露。

当前维护中的 mission-observation contract 区分了：

- `basic`
- `nav_v1`
- `nav_v2`
- `nav_v2_formation_v1`
- `nav_v2_formation_role_v1`
- `nav_v2_cooperative_takeoff_v1`
- `air_combat_c2_roe_v1`
- `air_combat_c2_roe_v2`
- `naval_screen_station_v1`

标准含义：

- 字段可见性是 mode-dependent 的
- formation fields 不是自动变成 common fields
- takeoff/runway 语义即使出现在通用 runtime 对象里，归属仍是 air specialization
- air-combat C2/ROE 字段即使复用 shared command-context identifier，也属于 air specialization
- naval screen/station 字段属于 naval specialization

## 非目标

本文档不定义：

- 完整的 sensor/track/IFF 合同
- 完整的 weapon/seeker/fuze/damage 合同
- 平台物理实现细节

这些内容应在仓库进一步收敛后，由各自的共享标准或特化标准单独承接。

## 相关文档

- [场景配置指南](../../operations/howto/scenario_configuration_guide.zh.md)
- [联合指挥与建模基线](../../domains/joint/standards/command_and_modeling_baseline.zh.md)
- [联合命令链与汇报基线](../../domains/joint/standards/command_link_and_reporting_baseline.zh.md)
- [仿真约定](simulation_conventions.zh.md)
- [src/core/mission/README.md](../../../src/core/mission/README.md)
