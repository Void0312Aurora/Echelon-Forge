<!-- Machine-translated draft generated on 2026-05-21 from docs/task/ground/g4_runtime_slice/README.md. Review before treating this file as authoritative. -->

# G4 运行时切片

状态：`2026-05-22` 已实现并验证一个由 G3 选定的有边界 tasking-only
lifecycle-proof 切片。

语言：

- 英文正本：`README.md`
- 中文配套：本文件。

输入：

- [G3 执行表面设计](../g3_execution_surface_design/README.md)
- [地面标准概述](../../../standards/ground/README.md)
- [地面最小任务结构](../../../standards/ground/minimal_task_structure.md)
- [子代理使用策略](../../../standards/governance/subagent_usage_policy.md)

## 目标

通过共享仿真生命周期实现一个选定的、持续维护的地面行为切片。

## 输出

- [G4 选定的运行时切片集群](g4_selected_runtime_slice_cluster_20260521.md)
- [G4 子代理调度包](g4_subagent_dispatch_packets_20260522.md)

## 范围

范围内：

- 一个 G3 选定的运行时行为
- 证明共享生命周期参与的聚焦测试
- 证明无私有地面运行时路径的兼容性保护
- 验证汇总与残差映射

范围外：

- 广泛的地面移动模型
- 直接火力或间接火力运行时
- 完整的地形、后勤或伤害模型
- 超出选定切片的公共模式扩展

## 门控条件

当通过维护的共享入口点执行一个地面行为，并且测试证明空中/海军兼容性得到保持时，G4 即可合并。

已释放切片：

- `tasking-only lifecycle proof through normalized ground TaskOrder ->
  LeaderIntent -> PilotReport status shell`

继续 held：

- formal `CommandPacket`
- formal `ObservationPacket`
- formal `TrackPacket`
- formal `P3`
- formal `P10`
- movement、sensing、terrain、fires、effects、DTO/binding expansion 与 broad
  `MissionCommand` growth

验证结果：

- Runtime batch command-chain sync 现在导入
  `python.rl.tasking.bridge.build_kernel_mission_command`。
- Focused G4 bridge test 已通过。
- Ground/common-core/naval/leader 兼容性测试已通过。
- Ground unit contracts 已通过 contract runner。
