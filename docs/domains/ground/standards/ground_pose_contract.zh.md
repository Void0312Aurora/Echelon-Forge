# Ground 移动姿态契约

语言：
- 英文规范：`ground_pose_contract.md`。
- 本文件为中文伴随文档。
文档类型：`standard`
生命周期：`maintained`
规范入口：`docs/domains/ground/standards/ground_pose_contract.md`
所有者：`systems/domains/ground/movement_system.h`
最后核验：`2026-10-10`

## 范围

`GroundInfantryMovement` 为准入的单兵原生 `MoveStatic`、`OccupyStatic` 和
`SupportStatic` 切片负责姿态投影。它仍是水平运动学原语，不引入六自由度地面
积分器、路线规划、掩体、感知或开火权限。

## 姿态所有权

- `Transform.x/y` 是该移动原语推进的水平世界位置。
- `Transform.z` 是地面实体锚点处的绝对地形高程。锚点位于地表，因此该字段不是
  AGL 高度，也不编码视点、武器高度或人体偏移。
- 该原语保持 `Velocity.vz` 为零；地面接触系统和其他消费者可以独立使用绝对锚点高程。
- `Transform.heading` 使用共享 NAV 约定（北方为 0 度，顺时针为正）。

## 航向策略

- 活跃的 `MoveStatic` 将归一化的 `MissionCommandCore::cmd_heading_deg` 写入
  `Transform.heading`，即使请求速度为零或过渡被阻挡；获准移动时水平速度使用同一航向。
- 活跃的 `OccupyStatic` 和 `SupportStatic` 停止该原语并保留现有航向。它们的 ground
  task 切片没有朝向字段，因此命令不会无声替换保持姿态。
- 非活跃或不支持的地面命令停止速度并保留姿态。

## 高程策略

每个活跃移动或保持步长都从
`IEnvironmentModel::get_terrain_elevation(x, y)` 采样，并把有限结果写入
`Transform.z`。环境返回非有限值时保留旧 Z。过渡被阻挡时只对当前位置贴地，不推进
`x/y`。

## 下游边界

维护中的原生视觉路径和环境查询使用绝对世界坐标；通用仪表系统需要航空器飞行组件，
因此不接纳此 ground 切片。目前没有维护中的 ground 视线、直射火力或传感器消费者把该
姿态转化为具有权限的结果。因此原生测试验证姿态契约本身，并单独记录下游可达性，
不宣称端到端交战结果。
