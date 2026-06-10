# 空中平台特化总览

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

状态：`2026-05-18`，当前维护中的 air 接口标准入口。

本目录定义仓库当前维护中的 air-specific 标准。它的目标不是罗列“真实座舱里可能出现的一切概念”，
而是把当前 runtime、测试和 tasking bridge 真正依赖的空中接口合同写清楚。

## 范围

本目录负责四类接口切片：

- 面向 air agent 的 mission/task observation 语义
- 环境与 `PilotAction` 暴露的 pilot action 语义
- 建立在 common core 之上的 air-specialized command/tasking 语义
- air-specific 的 pilot reporting 扩展

它不负责：

- joint/common 的指挥关系
- service-level 的组织 doctrine
- 低层 physics 或 reward 实现细节

这些内容分别应看：

- [标准化文档总览](../README.md)
- [联合指挥与建模基线](../joint/command_and_modeling_baseline.md)
- [联合命令链与汇报基线](../joint/command_link_and_reporting_baseline.md)
- [USAF 画像](../services/air_force.md)
- [运行时工作流与合同基线](../bridge/runtime_workflow_and_contract_baseline.md)

## 阅读顺序

建议按下面顺序进入：

1. [飞行员观测合同](obs.md)
2. [飞行员动作合同](act.md)
3. [空中任务命令与 tasking 合同](aim.md)
4. [飞行员汇报合同](rep.md)

这四份文档共同定义当前 air 接口在下列几层之间的边界：

- tasking/leader logic
- mission command 与 mission observation runtime
- pilot action 输入
- pilot report 输出

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

- common-core 术语继续放在 `joint/` 与 `services/`
- runway、takeoff、approach、formation、slot、recovery 这类 air 术语留在这里
- 先写“当前已经实现的合同”，未来扩展若未落地，应单独标注
- 不要把 action 或 observation surface 写得比当前 runtime/test contract 更宽

## 相关文档

- [场景配置指南](../bridge/scenario_guide.md)
- [运行时工作流与合同基线](../bridge/runtime_workflow_and_contract_baseline.md)
- [USAF 画像](../services/air_force.md)
