# 空中平台特化总览

Language:
- English canonical: [README.md](README.md)
- Chinese companion: `README.zh.md`

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/air/README.md`
Owner: `domains/air`
Last verified: `2026-08-08`

状态：当前维护中的 air-specialization 接口 owner 入口。

本目录定义仓库当前维护中的 air-specific 标准。它的目标不是罗列“真实座舱里可能出现的一切概念”，
而是把当前 runtime、测试和 tasking bridge 真正依赖的空中接口合同写清楚。

## 范围

本目录负责四份维护中的接口标准和两个 draft issue 表面：

- 面向 air agent 的 mission/task observation 语义
- 环境与 `PilotAction` 暴露的 pilot action 语义
- 建立在 common core 之上的 air-specialized command/tasking 语义
- air-specific 的 pilot reporting 扩展
- 空空杀伤链期望包络 review 词汇，目前是 draft plan，而不是 runtime contract
- 更广泛的 Air 改进 backlog；其中记录的是候选项，不是已授权实现

它不负责：

- joint/common 的指挥关系
- service-level 的组织 doctrine
- 低层 physics 或 reward 实现细节

这些内容分别应看：

- [仿真约定](../../architecture/standards/simulation_conventions.zh.md)
- [联合指挥与建模基线](../joint/standards/command_and_modeling_baseline.zh.md)
- [联合命令链与汇报基线](../joint/standards/command_link_and_reporting_baseline.zh.md)
- [USAF 画像](../joint/service_profiles/standards/air_force_profile.zh.md)
- [运行时工作流与合同基线](../../architecture/standards/runtime_workflow_and_contract_baseline.zh.md)

## 阅读顺序

建议按下面顺序进入：

1. [飞行员观测合同](standards/pilot_observation_contract.zh.md)
2. [飞行员动作合同](standards/pilot_action_contract.zh.md)
3. [空中任务命令与 tasking 合同](standards/mission_command_and_tasking_contract.zh.md)
4. [飞行员汇报合同](standards/pilot_reporting_contract.zh.md)
5. [空空杀伤链期望包络](work/issues/kill_chain_expectation_envelope.zh.md)
6. [Air 改进 backlog](work/issues/improvement_backlog.zh.md)

前四份文档共同定义当前 air 接口在下列几层之间的边界：

- tasking/leader logic
- mission command 与 mission observation runtime
- pilot action 输入
- pilot report 输出

杀伤链期望包络是 draft issue plan。它提出空空诊断分布的 review labels 和 owner
attribution，但不是 calibration result 或维护中的 runtime/test contract，也不授权实现或
runtime retuning。

Air 改进 backlog 同样属于 draft issue surface。其条目在被单独授权的 work package 提升前
都只是候选项。

## 当前代码对齐点

当前 air specialization 在代码里分散在几层：

- air tasking 扩展：
  [src/components/domains/air/tasking/README.md](../../../src/components/domains/air/tasking/README.md)
- shared command core 与 air command extension：
  [src/components/command/common/README.md](../../../src/components/command/common/README.md)
- action surface：
  [src/components/command/pilot_action.h](../../../src/components/command/pilot_action.h)
- mission observation taxonomy：
  [python/mission_obs_taxonomy.py](../../../python/mission_obs_taxonomy.py)
- scenario-loader mission observation assembly：
  [gym_envs/scenario_loader/mission_observation.py](../../../gym_envs/scenario_loader/mission_observation.py)

这个分层本身就是标准的一部分：

- `TaskOrderAir`、`LeaderIntentAir`、`PilotReportAir` 属于 tasking 侧 air 扩展
- `MissionCommand` 与 `PilotAction` 属于 command/action 侧 runtime carrier
- mission observation 是 mode-based 向量合同，而不是自由发挥的“飞行员感知清单”

## 维护规则

- common-core 术语放在 `domains/joint/standards/`，军种解释放在
  `domains/joint/service_profiles/`
- runway、takeoff、approach、formation、slot、recovery 这类 air 术语留在这里
- 先写“当前已经实现的合同”，未来扩展若未落地，应单独标注
- 不要把 action 或 observation surface 写得比当前 runtime/test contract 更宽
- draft issue plan 必须显式标注 held runtime behavior、引用稳定其词汇的任务证据，且不得暗示
  implementation authority

## 相关文档

- [场景配置指南](../../operations/howto/scenario_configuration_guide.zh.md)
- [运行时工作流与合同基线](../../architecture/standards/runtime_workflow_and_contract_baseline.zh.md)
- [USAF 画像](../joint/service_profiles/standards/air_force_profile.zh.md)
- [着陆任务 Reference](reference/landing_task.zh.md)
- [空空杀伤链期望包络](work/issues/kill_chain_expectation_envelope.zh.md)
- [Kill-chain 期望标准化评审](reviews/kill_chain_expectation_standardization_20260706/README.zh.md)
- [Learning owner 的活跃空战工作](../../learning/README.zh.md)
