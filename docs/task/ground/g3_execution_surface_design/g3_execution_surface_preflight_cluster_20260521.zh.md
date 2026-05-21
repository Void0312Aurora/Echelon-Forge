<!-- Machine-translated draft generated on 2026-05-21 from docs/task/ground/g3_execution_surface_design/g3_execution_surface_preflight_cluster_20260521.md. Review before treating this file as authoritative. -->

# G3 执行表面预检集群

状态：`2026-05-21` 在 G1-G2 证据已验收后，已具备设计预检条件。

输入：

- [G3 说明文档](README.md)
- [地面标准概述](../../../standards/ground/README.md)
- [地面最小任务结构](../../../standards/ground/minimal_task_structure.md)
- [子代理使用政策](../../../standards/governance/subagent_usage_policy.md)

## 目的

选择并指定第一个地面执行表面。这是一项设计和预检任务；不应实现运行时行为。

## 任务项

| ID | 项目 | 验收标准 |
|----|------|------------|
| `G3-A1` | 运行时切片候选 | 选择一个有界 G4 候选，例如仅任务的生命周期证明或最小命令交付。 |
| `G3-A2` | 阶段图谱 | 为所选候选声明确切的 P0-P10 参与情况。 |
| `G3-A3` | 数据包图谱 | 命名消费、生成和推迟的数据包家族。 |
| `G3-A4` | 观察/报告设计 | 决定第一个报告表面，而不暴露世界真相。 |
| `G3-A5` | 环境依赖图谱 | 记录地形、视线、无线电和移动性假设，标注为已实现、占位或推迟。 |
| `G3-A6` | 测试计划 | 命名在 G4 能够声称保持行为之前所需的重点测试。 |

## 写入范围

允许：

- `docs/task/ground/g3_execution_surface_design/**`
- 更新 `docs/task/ground/README.md`
- 仅当 G3 决策改变规范性所有权时才进行标准跟进

不得编辑：

- 运行时实现
- 来自 G1 的原型实现，除非集成负责人要求进行有限的文档更新
- 来自 G2 的固件实现

## 建议验证

```bash
git diff --check
```

## 交接

返回：

- 选定的 G4 候选
- 阶段和数据包图谱
- 观察/报告决策
- 推迟的假设
- 测试计划
- G4 前所需的任何标准更新

## 可用 G1-G2 证据

- G1 已验收 Python-profile-only ground 切片，其中 `army`、`ground`、
  `land` 与 `ServiceProfile.Army` 均规范化为 `ground`。
- G1 已验收 `TASK_MOVE`、`TASK_OCCUPY` 与 `TASK_SUPPORT` 通过 common-core
  字段表达的起步默认值。
- G2 已验收位于
  `examples/config/database/ground/units/ground_platoon_starter.seed` 的非自动加载、
  以 platoon 为中心的内容 seed。
- G2 已验收 `tests/contracts/unit/ground/` 下的可运行起步合同。

设计预检不得把这些证据转化为 runtime movement、terrain、sensing、fires、
weapon、damage 或 combat 声明。
