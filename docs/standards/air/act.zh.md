# 飞行员动作合同

Language:
- English canonical: `act.md`
- Chinese companion: [act.zh.md](act.zh.md)

状态：`2026-05-18`，当前维护中的 air action input 特化基线。

本文档定义仓库当前维护中的 air action surface。它是一份接口合同，不是座舱控件百科。

## 范围

当前维护中的动作面分成两层：

1. 面向环境的 action vector
2. 面向内核的 `PilotAction`

主要依据：

- [gym_envs/universal_env_parts/actions.py](../../../gym_envs/universal_env_parts/actions.py)
- [gym_envs/universal_env.py](../../../gym_envs/universal_env.py)
- [src/components/command/pilot_action.h](../../../src/components/command/pilot_action.h)
- [src/components/command/air/control_input_resolution.h](../../../src/components/command/air/control_input_resolution.h)

## Action Mode

当前维护中的环境 action mode 为：

| Mode | 维度 | 作用 |
| :--- | ---: | :--- |
| `full` | 17 | 完整维护中的动作面 |
| `takeoff2` | 2 | 起飞课程用简化动作面 |
| `takeoff4` | 4 | 带横侧向控制的起飞简化动作面 |

`takeoff2` 与 `takeoff4` 是训练导向的 reduced interface，并不直接暴露完整 `PilotAction`。

## `full` 模式映射

当前维护中的 `full` action vector 映射如下：

- `0`: `stick_pitch`
- `1`: `stick_roll`
- `2`: `rudder`
- `3`: `throttle`
- `4`: `gear_handle`
- `5`: `flaps`
- `6`: `speedbrake`
- `7-8`: brake 输入，最终折叠为 `brake`
- `9`: `radar_active`
- `10`: `radar_scan_az`
- `11`: `radar_scan_el`
- `12`: `tms_up`
- `13`: `master_arm`
- `14`: `fire_weapon`
- `15`: `fire_gun`
- `16`: `weapon_select_id`

## 规范的 `PilotAction` 字段

当前内核侧公开的 `PilotAction` 字段可分为：

### 连续轴

- `stick_pitch`
- `stick_roll`
- `rudder`
- `throttle`
- `gear_handle`
- `flaps`
- `speedbrake`
- `brake`
- `radar_scan_az`
- `radar_scan_el`

### 开关与触发

- `brake_left`
- `brake_right`
- `radar_active`
- `tms_up`
- `master_arm`
- `fire_weapon`
- `fire_gun`
- `jettison_emergency`
- `program_chaff`
- `program_flare`

### 选择器与有效位

- `weapon_select_id`
- `active`

## 解释规则

- `normalize_action()` 在环境边界执行 shape 校验与 clipping。
- `flaps`、`speedbrake`、`brake` 在进入 `PilotAction` 前会经过 helper 逻辑规范化。
- `radar_scan_az` 与 `radar_scan_el` 在环境层是归一化输入，进入内核前再映射为角度值。
- `weapon_select_id` 是选择器，不是连续控制轴。

## Reduced Mode 的自动覆盖

`takeoff2` 与 `takeoff4` 不只是“少几个字段”，它们还会自动附带覆盖逻辑：

- 未暴露字段会被清零或禁用
- reduced mode 仍然生成一个有效的 `PilotAction`
- `gear_handle` 会根据当前 radar altitude 自动管理

因此，这两个 mode 是训练便利层，而不是独立的内核动作协议。

## 保护与门控规则

当前动作合同还包含一些“解释层规则”，它们并不是玩家直接控制量：

- `PilotAction.active` 决定该动作是否有效
- 当 runtime 在 `PilotAction` 与 legacy movement command 之间做选择时，`PilotAction` 优先
- `brake_left/right` 在地面控制解析层可能强制触发满刹车语义
- 武器发射除了 `master_arm` 与 `fire_weapon` 外，仍要经过下游 command/ROE/runtime 检查

## 归属边界

应继续保留在 air specialization 的内容：

- stick/throttle/gear/flaps/speedbrake 等飞行员动作语义
- 直接暴露给 pilot surface 的 radar scan 控制
- weapon select 与 trigger 的 pilot-interface 语义
- reduced takeoff 训练动作面

不应放进本文档的内容：

- joint/common 的 command relationship
- service-level 的 tasking doctrine
- 低层 aerodynamic、propulsion、weapon model 的实现细节

## 非目标

本文档不标准化 `trim_pitch` 字段，不承诺显式的人类平滑模型，也不尝试充当完整 HOTAS 手册。
如果当前 runtime 没有通过 `PilotAction` 或维护中的环境动作面公开该字段，就不应把它写成当前维护合同的一部分。
