# Submarine damage response 与 mobility 契约

Language:
- English canonical contract: `submarine_damage_mobility_contract.md`。
- Chinese companion document。
Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/submarine_damage_mobility_contract.md`
Owner: `architecture/naval-submarine`
Last verified: `2026-10-10`

## 当前接纳范围

Submarine entity 现在接入两个受限的 native mechanism：

1. `SubmarineDamageStateUpdate` 在 naval damage stage 消费 `Health`、`PlatformDamageState` 和 `SubmarinePlatform`，使用显式的 synthetic profile `naval_damage_response_submarine_v1` 推进火灾、进水和船体破损严重度。
2. `SubmarineMotion` 读取可选的共享 `PlatformDamageState`。`mobility_capability` 限制水下可达速度，并缩放加速、航向转动和深度变化权限。mobility kill 或 capability `<= 0.25` 时目标速度置零，平台按受限运动规律滑行/减速。

该 profile 是为了形成可执行的 runtime closure；它是 synthetic、未校准的，不代表任何具体舰级。它不接纳鱼雷、VLS、ASW 武器释放、压力壳物理击毁、乘员伤亡或完整沉没模型。

## 响应 profile

`naval_damage_response_submarine_v1` 使用以下每秒速率：

| 项 | 值 |
| --- | ---: |
| 火灾衰减 | `0.0006` |
| 船体破损衰减 | `0.00008` |
| 破损导致进水增长 | `0.004` |
| 进水衰减 | `0.00015` |
| 火灾导致任务能力损失 | `0.0018` |
| 火灾导致传感器能力损失 | `0.0014` |
| 进水导致机动能力损失 | `0.0030` |
| 进水导致生存能力损失 | `0.0035` |
| 火灾导致生存能力损失 | `0.0012` |

响应通过共享 `sync_platform_damage_loss_state` 负责 capability clamp、kill flags、Health flags、loss state 和销毁。带有 `ShipPlatform` 的实体不会通过 submarine selector，避免双重所有权。

## 时间与顺序

- damage system 使用有限正 entity timestep 策略。零、负数和非有限 iterator delta 解析为维护中的 `1/60 s` 兼容 cadence。
- `SubmarineMotion` 早于 naval damage stage，因此它消费上一个 step 的 damage projection，和现有 ship damage/mobility 的排序一致。测试必须考虑这一 tick lag。
- 正时间步按“速率乘经过秒数”推进严重度和 capability。仅有 content `damage_model` 记录不代表 submarine response 或武器机制已接纳。

## 验证契约

`src/tests/test_ship_maneuvering.cpp` 的 native 测试验证：

- 同一命令下受损 submarine 不能达到 pristine 的速度或深度变化响应；
- 接纳的 submarine profile 会在破损下增加进水并降低 mobility capability，同时保留共享 Health/loss 所有权；
- 没有 `PlatformDamageState` 时现有 pristine submarine motion 和 instrument 行为仍可用。

压力壳机制、舰级校准、鱼雷/反舰导弹执行和完整 ASW 端到端结果仍未接纳，除非有独立的来源支持 profile 和验收测试。
