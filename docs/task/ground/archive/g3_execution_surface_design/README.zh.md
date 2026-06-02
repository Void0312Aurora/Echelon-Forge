<!-- Machine-translated draft generated on 2026-05-21 from docs/task/ground/g3_execution_surface_design/README.md. Review before treating this file as authoritative. -->

# G3 执行面设计

状态：`2026-05-22` `G3-D` 已验收；`G4` 已释放为一个有边界的
tasking-only lifecycle-proof 切片。

语言：

- 英文规范：`README.md`
- 中文配套：暂不需要；这是一个高变动任务片段。

输入：

- [G1 合约骨架](../g1_contract_skeleton/README.md)
- [G2 内容和测试种子](../g2_content_test_seed/README.md)
- [地面标准概览](../../../standards/ground/README.md)
- [子代理使用政策](../../../standards/governance/subagent_usage_policy.md)

## 目的

在运行时行为编写之前设计第一个地面执行面。

## 输出

- [G3 执行面预检集群](g3_execution_surface_preflight_cluster_20260521.md)
- [G3 子代理调度包](g3_subagent_dispatch_packets_20260522.md)

## 范围

范围内：

- 决定第一个运行时片段是仅任务型还是包含一个微小的命令面
- 定义超出 G1 的阶段覆盖范围
- 命名消耗和产生的数据包
- 定义观察/报告面候选
- 映射地形/环境依赖关系和显式延期

范围外：

- 实现移动、传感、火控或观测导出
- 大型 `MissionCommand` 扩展
- 地形真实感实现

## 门禁

G3 可合并的条件是：它命名了一个安全的 G4 运行时片段，并诚实地记录了所有已延期的面。

当前释放条件：仅设计预检。G4 继续 held，直到 G3 选择一个有界 runtime 候选、
写入范围和聚焦测试计划。

## 分发形态

G3 现已拆成三个可并行的 diagnostics 流和一个串行集成步骤：

- `G3-A 候选与阶段/数据包图谱`：选择最可信的 G4 候选，并冻结其 stage /
  packet map。
- `G3-B 观察/报告与环境边界`：定义第一个 reporting surface，以及 terrain /
  line-of-sight / radio / mobility dependency map。
- `G3-C G4 释放边界与测试计划`：定义 G4 所需的 bounded write scope、
  compatibility guard expectations 与 focused test plan。
- `G3-D 主线程集成`：整合 A-C，并为 G4 发布最终 G3 决策。

主线程拥有 canonical G3 决策权。并行 worker 应返回有边界的 preflight packet，
而不是并发编辑同一张规范性表格。
