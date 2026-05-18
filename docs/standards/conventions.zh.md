<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/conventions.md. Review before treating this file as authoritative. -->

# 仿真约定

本文档是引擎级中性约定的`权威性`文件。

它属于标准树的`联合/公共核心`一侧：

- [标准概览](README.md)
- [联合基线](joint/command_and_modeling_baseline.md)

它**不**定义特定服务的组织或特定平台的任务语义。

本文档定义了在核心系统、绑定和可视化中使用的共享约定。在添加新功能时请保持这些约定一致。

## 坐标系
- 世界坐标系：ENU（东-北-上）。
- 位置：米。
- 速度：米/秒。

## 角度
- 航向采用导航度：0 = 北，顺时针为正，范围 [0, 360)。
- 相对方位角采用导航度：-180..180，顺时针为正。
- 变换存储航向/俯仰/横滚，单位为度。

转换关系：
- 数学角度（atan2 dy, dx）中 0 = 东，逆时针为正。
- 导航度 = 90 - 数学度，归约到 [0, 360)。

## 指令

当前代码仍然暴露了诸如 `MovementCommand` 之类的遗留指令结构。

标准对齐说明：

- 引擎/核心约定保留在此处
- 服务配置文件与平台/任务指令语义属于其他地方
- 航空特定任务语义属于 [air/README.md](air/README.md)

## 传感器
- `Sensor.fov_deg` 是总视场角。如果 `abs(相对方位角) <= fov_deg / 2`，则接触点可见。
- `Detection.bearing` 存储以导航度（-180..180）为单位的相对方位角。
- `TrackData.azimuth` 使用与 `Detection.bearing` 相同的约定。

## 观测
- `AgentObservation.heading/pitch/roll` 采用导航度单位。
- `get_all_units().heading` 由速度导出，并以导航度返回。

## 时间
- 仿真时间以秒为单位。
