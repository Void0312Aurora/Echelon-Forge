<!-- Machine-translated draft generated on 2026-05-21 from docs/task/ground/g4_runtime_slice/g4_selected_runtime_slice_cluster_20260521.md. Review before treating this file as authoritative. -->

# G4 选定运行时切片集群

状态：`2026-05-21` 保留 / 等待 G3。

输入：

- [G4 自述文件](README.md)
- [G3 执行面预检集群](../g3_execution_surface_design/g3_execution_surface_preflight_cluster_20260521.md)
- [子代理使用策略](../../../standards/governance/subagent_usage_policy.md)

## 目的

实现恰好一个 G3 选定的地面运行时切片。该集群将一直保留，
直到 G3 指定安全的候选者、写入范围以及测试计划。

## 候选形态

可能的候选者（待 G3 确认）：

- 仅任务生命周期的证明，涵盖 setup/profile/defaults/report status
- 最小地面命令投递包，不含运动动力学
- 仅基于任务状态的选定观测/报告导出

## 任务项

| ID | 项目 | 验收标准 |
|----|------|----------|
| `G4-A1` | 实现选定切片 | 代码变更仅匹配 G3 批准的写入范围。 |
| `G4-A2` | 针对性测试 | 测试通过维护的共享入口点执行选定的地面路径。 |
| `G4-A3` | 兼容性防护 | 空中/海上配置文件和任务测试保持兼容。 |
| `G4-A4` | 无私有路径证明 | 架构或运行时测试证明没有引入仅地面生命周期。 |
| `G4-A5` | 残留交接 | 记录运动、感知、火力、地形、观测和效果的残留项。 |

## 写入范围

一直保留到 G3。最终的工作人员必须在实现开始前收到一份不重叠的文件列表。

发布前请勿编辑：

- 运动/物理系统
- 传感器/跟踪系统
- 火控、武器或伤害运行时
- 宽泛的外观 API 接口

## 建议的验证

由 G3 填写。基准期望：

```bash
git diff --check
python -m pytest -q <针对性地面测试>
python -m pytest -q <针对性空中/海上兼容性测试>
```

## 交接

返回：

- 触及的文件
- 运行的命令
- 维护入口点的证据
- 兼容性结果
- 残留映射
