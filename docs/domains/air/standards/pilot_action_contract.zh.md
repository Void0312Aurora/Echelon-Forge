# 飞行员动作合同

Language:
- English canonical: [pilot_action_contract.md](pilot_action_contract.md)
- Chinese companion: `pilot_action_contract.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/air/standards/pilot_action_contract.md`
Owner: `domains/air`
Last verified: `2026-10-07`

状态：当前维护中的 air action input 特化基线，包含 A5 runtime
event-action overlay；本文档本身不接受 learned-policy behavior。

本文档定义仓库当前维护中的 air action surface。它是一份接口合同，不是座舱控件百科。

## 范围

当前维护中的动作面分成两层：

1. 面向环境的 action vector
2. 面向内核的 `PilotAction`

主要依据：

- [gym_envs/universal_env_parts/actions.py](../../../../gym_envs/universal_env_parts/actions.py)
- [gym_envs/universal_env_parts/spaces.py](../../../../gym_envs/universal_env_parts/spaces.py)
- [gym_envs/universal_env_parts/air_combat_event_action.py](../../../../gym_envs/universal_env_parts/air_combat_event_action.py)
- [src/components/command/pilot_action.h](../../../../src/components/command/pilot_action.h)
- [src/components/domains/air/command/control_input_resolution.h](../../../../src/components/domains/air/command/control_input_resolution.h)
- [tests/runtime/core/test_air_combat_hybrid_action.py](../../../../tests/runtime/core/test_air_combat_hybrid_action.py)
- [tests/runtime/air_combat/test_fire_action_release_gate.py](../../../../tests/runtime/air_combat/test_fire_action_release_gate.py)

## Action Mode

本标准覆盖的 Air action mode 为：

| Mode | 维度 | 作用 |
| :--- | ---: | :--- |
| `full` | 17 | 完整维护中的动作面 |
| `takeoff2` | 2 | 起飞课程用简化动作面 |
| `takeoff4` | 4 | 带横侧向控制的起飞简化动作面 |
| `air_combat_hybrid_v1` | 12 | `1v1` 空战训练面：连续飞行轴 + hybrid 作战命令语义 |
| `air_ew_hybrid_v1` | 14 | 原作战传输向量加 chaff/flare 请求 |
| `air_ew_hybrid_v2` | 16 | v1 EW 向量加 jammer 发射/技术请求 |

`takeoff2` 与 `takeoff4` 是训练导向的 reduced interface，并不直接暴露完整 `PilotAction`。

`air_combat_hybrid_v1` 同样是训练导向的动作面。它为了兼容 PPO/runtime 仍保留 flat
numeric transport vector，但 policy 合同是 hybrid：部分维度按 Bernoulli 开关、
单步 pulse 或 categorical selector 采样和解释，而不是当成原始连续座舱轴。

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

## `air_combat_hybrid_v1` 模式映射

当前维护中的 `air_combat_hybrid_v1` transport vector 映射如下：

- `0`: `stick_pitch` 连续轴
- `1`: `stick_roll` 连续轴
- `2`: `rudder` 连续轴
- `3`: `throttle` 连续轴
- `4`: `radar_scan_az`，映射为 `+/-60 deg`
- `5`: `radar_scan_el`，映射为 `+/-30 deg`
- `6`: `radar_active` Bernoulli 开关状态
- `7`: `tms_up`，由 policy command 上升沿生成单步 pulse
- `8`: `master_arm` Bernoulli 开关状态
- `9`: `fire_weapon`，由 policy command 上升沿生成单步 pulse
- `10`: `fire_gun`，由 policy command 上升沿生成单步 pulse
- `11`: `weapon_select_id`，`[0, 7]` 范围内的 categorical selector

该模式下 `proprio` 与 `proprio_history` 记录送往 `PilotAction` 的 effective
transport action，而不是 raw policy intent。因此对于 pulse 维度，policy command
持续为高时只有上升沿步骤显示为 `1`，后续 held 步骤显示为 `0`。

## EW 版本化传输与准入

`air_ew_hybrid_v1/v2` 已在 `python.env_config.ACTION_MODES` 中显式注册，训练和评估
CLI 从该列表取得选项。原有五项顺序与动作索引保持不变，`ew_state` 仍需显式启用。

前 12 个索引沿用 `air_combat_hybrid_v1` 的传输及运行时事件门控。EW 扩展如下：

| 索引 | 字段 | 解释 |
| --- | --- | --- |
| 12 | `program_chaff` | 值大于 0.5 时请求投放；原生库存与间隔约束生效 |
| 13 | `program_flare` | 值大于 0.5 时请求投放；原生库存与间隔约束生效 |
| 14（v2） | `jammer_transmit` | 值大于 0.5 时请求发射；原生预算与冷却约束生效 |
| 15（v2） | `jammer_mode` | 裁剪后向下取整至 0..2：NoiseBarrage、NoiseSpot、DeceptionDRFM |

本轮准入验证现有 Box 动作 PPO 路径，测试位于 `test_air_ew_admission.py`；它不代表
训练质量验收。专用 `hybrid_action_spec='air_combat_hybrid_v1'` 分布仍限定 12 维，
会拒绝 EW 空间；EW 名称也不是受支持的混合分布规范。注册动作模式不扩展其
Bernoulli/categorical 策略语义。

编队角色门控由 `ew_formation_commanders` 独立启用，只允许或阻止 v2 jammer 请求。
请求、资源消耗、发射状态、测量效果及命名终局验收各有独立证据。

## A5 受约束事件动作 Overlay

状态：`2026-06-10`，A5 S1 C2/ROE event-action runtime surface 的 implementation
contract。本节冻结 runtime surface 所需的字段名；它本身不接受 learned-policy behavior。

对于选择启用维护中 A5 S1 C2/ROE 合同的场景，`fire_weapon` 不作为 policy-facing
逐帧 raw threshold，而是把武器释放建模为事件动作：

```text
event_action in {hold, fire_once}
event_action_mask = [1, fire_mask]
```

为了兼容 PPO/runtime，event-action overlay 仍可以通过 flat action vector transport；
但 policy log-prob、entropy、stochastic sampling 和 deterministic evaluation 必须使用
masked event semantics。

policy-visible event state：

| `engagement_state` | Meaning | Event support |
| :--- | :--- | :--- |
| `Hold` | C2/ROE、target、weapon 或 mission state 不允许 release。 | 仅 `hold` |
| `AuthorizedReady` | 首发 release 已授权且可用。 | `hold`、`fire_once` |
| `FiredAssess` | release 已接受，assessment pending。 | 仅 `hold` |
| `ReattackReady` | assessment 后显式授权 follow-on release。 | `hold`、`fire_once` |
| `Winchester` | 没有有效武器，或 release path 不可用。 | 仅 `hold` |

最终 `fire_mask` 必须从具名 component 派生，包括 C2/ROE authorization、target presence、
shot budget、pending assessment、weapon/ammo readiness 和 reattack permission。
diagnostics 应同时暴露 final mask，以及导致 `fire_once` 不可用的 component 或 rejection
reason。

A5 implementation 所需 runtime info names：

- `engagement_state`
- `fire_mask`
- `fire_once_requested`
- `fire_once_accepted`
- `fire_once_rejected_reason`
- `release_executed`
- `post_launch_suppressed`
- `reattack_ready`

最小 transition rule：

```text
AuthorizedReady + fire_once + fire_mask
  -> consume one release event
  -> enter FiredAssess
  -> suppress fire_once until explicit ReattackReady or a new authorization cycle
```

该 overlay 与 reward shaping 刻意分离。reward 可以评价 outcome、timing、ammo cost
和 tracking quality，但不应作为教会 release legality、shot budget 或 post-launch
suppression 的主要机制。

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
- `jammer_transmit`

### 选择器与有效位

- `weapon_select_id`
- `jammer_mode`（显式 EW v2 指令的 `JammingType` 编码）
- `active`

对于没有暴露 EW v2 jammer tail 的动作面，`jammer_mode = -1` 表示兼容传输
中没有 jammer 指令。这样的 `PilotAction` 不会关闭已经处于发射状态的吊舱。
EW v2 动作面始终提供 `0..2` 的 mode code；即使
`jammer_transmit` 为 false，也会用它表达显式关闭发射。

## 解释规则

- `normalize_action()` 在环境边界执行 shape 校验与 clipping。
- `flaps`、`speedbrake`、`brake` 在进入 `PilotAction` 前会经过 helper 逻辑规范化。
- `radar_scan_az` 与 `radar_scan_el` 在环境层是归一化输入，进入内核前再映射为角度值。
- `weapon_select_id` 是选择器，不是连续控制轴。
- 在 `air_combat_hybrid_v1` 中，`tms_up`、`fire_weapon` 与 `fire_gun`
  是 policy-facing pulse command。policy command 持续为高不会让对应的
  `PilotAction` trigger 在首个 effective 步骤之后继续保持为高。

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
