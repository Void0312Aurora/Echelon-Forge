# 飞行员观测空间标准 (Pilot Observation Space Standard)

> Scope note (2026-03-23): 本文档是 `air specialization`，只适用于 air profile 下的平台观测语义。
> 当前标准化主基线请先看 [docs/standards/README.md](/home/void0312/CMO/docs/standards/README.md)、
> [docs/standards/services/air_force.md](/home/void0312/CMO/docs/standards/services/air_force.md)、
> [docs/standards/air/README.md](/home/void0312/CMO/docs/standards/air/README.md)。

本文档定义了“数字飞行员” (RL Agent) 在仿真环境中所能获取的观测数据。这些数据严格模拟现实战斗机飞行员通过仪表、平显 (HUD) 及感官所获取的原始信息。

它不负责定义：

- joint/common core 的指挥关系
- Army/Navy/Marine Corps 的平台观测
- 全项目统一的数据模型骨架

## 1. 飞行状态 (Flight Dynamics)
飞行员对飞机运动状态的直接感知。

| 变量名 | 说明 | 物理单位 | 现实对应 |
| :--- | :--- | :--- | :--- |
| `alt_baro` | 气压高度（平均海平面高度） | 米 (m) | 气压高度计 |
| `alt_radar` | 雷达高度（实际离地高度） | 米 (m) | 雷达高度计 |
| `ias` | 指示空速 (Indicated Airspeed) | 节 (kts) / 米每秒 (m/s) | 空速表 |
| `mach` | 马赫数 | Mach | 马赫数表 |
| `vvi` | 垂直速率 (Vertical Velocity Indicator) | 米每秒 (m/s) | 升降速度表 |
| `pitch` | 俯仰角 | 度 (deg) | 姿态指引仪 (ADI) |
| `roll` | 滚转角 | 度 (deg) | 姿态指引仪 (ADI) |
| `heading` | 磁航向 / 真实航向 | 度 (deg) | 水平状态指示仪 (HSI) |
| `aoa` | 攻角 (Angle of Attack) | 度 (deg) | AoA 指示器 |
| `beta` | 侧滑角 (Sideslip Angle) | 度 (deg) | 侧滑球 / 侧滑仪 |
| `g_load` | 法向过载 | G | 加速度计 |
| `p, q, r` | 角速度（滚转、俯仰、偏航速率） | 度每秒 (deg/s) | 速率陀螺 |

## 2. 动力系统 (Propulsion & Systems)
监控发动机的工作状态及其对机体的影响。

| 变量名 | 说明 | 物理单位 | 备注 |
| :--- | :--- | :--- | :--- |
| `engine_rpm_pct` | 核心转速百分比 | % | N1 / N2 |
| `engine_temp` | 排气温度 / 涡轮前温度 | 摄氏度 (℃) | EGT / FTIT |
| `fuel_internal` | 内部机身燃料重量 | 公斤 (kg) | 燃油表 |
| `fuel_external` | 外部副油箱燃料重量 | 公斤 (kg) | 燃油表 |
| `fuel_flow` | 瞬时燃油流量 | 公斤每小时 (kg/h) | 流量计 |
| `throttle_pos` | 当前油门杆实际位置 | 0.0 - 1.0 | 反馈手感 |

## 3. 飞机配置 (Configuration)
机体机械结构的当前状态。

| 变量名 | 说明 | 状态值 | 备注 |
| :--- | :--- | :--- | :--- |
| `gear_pos` | 起落架状态 | 0.0 (收起) - 1.0 (放下) | 包含转换态 |
| `flaps_pos` | 襟翼角度 | 度 (deg) / 挡位 | |
| `speedbrake_pos` | 减速板开度 | 0.0 - 1.0 | |
| `master_arm` | 武器总开关 | ON / OFF | |

## 4. 环境与指令 (Environment & Navigation)
长机/指挥层下达的任务目标及外界动态。

| 变量名 | 说明 | 物理单位 | 备注 |
| :--- | :--- | :--- | :--- |
| `target_heading` | 指令目标航向 | 度 (deg) | 长机指令内容 |
| `target_alt` | 指令目标高度 | 米 (m) | 长机指令内容 |
| `target_speed` | 指令目标速度 | m/s | 长机指令内容 |
| `oat` | 外界大气温度 | 摄氏度 (℃) | 静态温压 |
| `wind_vec` | 估计风速向量 | m/s | 飞行员感知补偿 |

## 5. 战术与传感器 (Tactical & Sensors)
通过电子设备获取的战场态势。

| 变量名 | 说明 | 物理单位 | 备注 |
| :--- | :--- | :--- | :--- |
| `rwr_state` | 雷达告警接收机状态 | 象限、类型、强度 | 告警音及显示器 |
| `radar_contacts` | 雷达发现的敌我目标列表 | 方位、距离、多普勒速度 | 原始观测 |
| `missile_count` | 剩余可用导弹数量 | 整数 | 各型号计数 |
