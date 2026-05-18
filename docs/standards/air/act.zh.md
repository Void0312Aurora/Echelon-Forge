<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/air/act.md. Review before treating this file as authoritative. -->

# 飞行员操作空间标准 (Pilot Action Space Standard)

> 范围说明 (2026-03-23): 本文档是 `air specialization`，只适用于 air profile 下的平台执行动作语义。
> 当前标准化主基线请先看 [docs/standards/README.md](../README.md)、
> [docs/standards/services/air_force.md](../services/air_force.md)、
> [docs/standards/air/README.md](README.md)。

本文档定义了“数字飞行员” (RL Agent) 对仿真环境所能施加的操作指令。这些操作严格模拟现实战斗机飞行员在座舱内通过操纵杆、油门杆和各类电磁开关所能进行的物理操作。

它不负责定义：

- joint/common core 的任务组织
- 军种层级结构
- 海战或陆战的执行动作标准

## 1. 飞行控制 (Primary Controls)
最频繁的操作，直接影响飞机的气动面。

| 操作名 | 说明 | 取值范围 | 物理意义 |
| :--- | :--- | :--- | :--- |
| `stick_pitch` | 升降舵/水平尾翼控制 | [-1.0, 1.0] | 向后拉为负(俯仰升), 向前推为正(俯仰降) |
| `stick_roll` | 副翼控制 | [-1.0, 1.0] | 向左压为负, 向右压为正 |
| `rudder_pedals` | 方向舵/机轮转弯控制 | [-1.0, 1.0] | 踩左舵为负, 踩右舵为正 |
| `throttle_lever` | 油门杆位置 | [0.0, 1.0] | 0.0-0.8为军用推力, 0.8-1.0为加力 (AB) |

## 2. 二级控制 (Secondary Controls)
用于调整飞机形态和辅助飞行。

| 操作名 | 说明 | 取值范围 | 备注 |
| :--- | :--- | :--- | :--- |
| `gear_handle` | 起落架手柄 | {0, 1} | 0为收, 1为放 |
| `flaps_switch` | 襟翼开关 | {Up, Takeoff, Landing} | 挡位控制 |
| `speedbrake_switch` | 减速板手柄 | {Retract, Extend} | 离散或连续控制 |
| `trim_pitch` | 俯仰配平 | [-1.0, 1.0] | 调整零位压力 |

## 3. 传感器与电子设备 (Sensors & Avionics)
管理信息获取设备。

| 操作名 | 说明 | 取值范围 | 备注 |
| :--- | :--- | :--- | :--- |
| `radar_power` | 雷达开关/模式 | {Off, Standby, On} | |
| `radar_scan_elevation` | 雷达俯仰扫描中心 | 度 (deg) | |
| `radar_scan_azimuth` | 雷达方位扫描宽度 | 度 (deg) | |
| `target_lock_btn` | 锁定按钮 (TMS Up) | 触发式 | 用于指定跟踪目标 |

## 4. 武器管理 (Weapon Management)
战术执行的核心操作。

| 操作名 | 说明 | 取值范围 | 备注 |
| :--- | :--- | :--- | :--- |
| `master_arm_switch` | 武器总开关 | {Safe, Arm} | |
| `weapon_select` | 武器循环选择 | 离散 ID | 航炮、短程弹、中程弹 |
| `pickle_btn` | 导弹发射/挂铁释放 | 触发式 | |
| `trigger_btn` | 航炮扳机 | 按住式 | |
| `jettison_btn` | 紧急丢弃副油箱/挂载 | 触发式 | 通常为红色紧急按钮 |

## 5. 操作规范
1.  **连续性**: 操纵杆 (`stick_pitch/roll`) 和油门 (`throttle`) 必须作为连续值 (Continuous Action) 处理，以模拟物理反馈。
2.  **物理延迟**: 飞行员的操作通过机载飞控系统 (FBW) 到达致动器会有微小延迟及物理限制。
3.  **安全性**: AI 不应发出超越人体极限的突变指令（例如从全开油门在 0.01 秒内变为全关），模型需包含人类操作的平滑特性。
