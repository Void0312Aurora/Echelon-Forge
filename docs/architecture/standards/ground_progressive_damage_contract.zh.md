# Ground progressive damage 时间步长契约

Language:
- English canonical contract: `ground_progressive_damage_contract.md`。
- Chinese companion document。
Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/ground_progressive_damage_contract.md`
Owner: `architecture/ground-damage`
Last verified: `2026-10-10`

## 范围

`GroundDamageStateUpdate` 负责地面单位持续火灾、点火源、结构、伤亡以及能力投影的渐进变化。所有随时间演化的项都使用“每仿真秒”的速率。系统每次运行读取一次 Flecs iterator delta，并对每个匹配的地面实体应用该速率。

`1/60 s` kernel cadence 仍是兼容性校准基线：旧的每 tick 系数乘以 60，因此一个基线 tick 在浮点容差内保持既有响应。

## 速率清单

| 项 | 每秒速率 | 状态所有者 |
| --- | ---: | --- |
| 火灾衰减 | `0.048` | `GroundPlatformDamageState.fire_severity` |
| 点火源衰减 | `0.030` | `GroundPlatformDamageState.ignition_source_severity` |
| 持续结构损伤衰减 | `0.006` | `GroundPlatformDamageState.ongoing_structural_damage` |
| 结构完整性损失 | `0.024 * structural_progress` | `GroundPlatformDamageState.structural_integrity` |
| 伤亡增长 | `0.090 * fire_progress` | `GroundPlatformDamageState.casualty_fraction` |
| 任务能力损失 | `0.090 * fire + 0.060 * structure + 0.048 * uncontained_fire` | 共享 `PlatformDamageState` |
| 机动能力损失 | `0.120 * unavailable_mobility + 0.036 * structure` | 共享 `PlatformDamageState` |
| 生存能力损失 | `0.132 * fire + 0.108 * structure` | 共享 `PlatformDamageState` |

每个速率都基于 tick 开始时的状态计算，然后限制在声明范围内。火灾和结构负荷以赋值方式投影到共享状态，不会再次累加同一负荷。

## delta 与暂停语义

- 有限正 `dt` 按 `rate * dt` 推进响应。
- `dt == 0`、负数、`NaN` 和无穷值通过 `ground_damage_detail::resolve_damage_dt` 解析为 `0`，更新保持 no-op。阶段暂停或没有有效经过时间时，地面损伤不得凭空产生伤亡或衰减。
- 该 no-op 策略只适用于地面渐进损伤，不是 air 和刚体系统使用的共享物理积分器 fallback。
- clamp、`sync_platform_damage_loss_state`、Health 所有权、销毁和 loss-state 阈值保持不变。

## 可达性与验证

系统在 stage 30（`builtin.system.ground_damage`）被接纳；安装默认 contribution graph 的 native kernel 和 WorldBatch world 都可到达。它仍是后果状态所有者，不负责地面移动、路线、感知、地形或武器释放。

`src/tests/test_ground_damage_system.cpp` 验证：

- `1/60`、`0.05` 和 `0.1 s` 在一秒 elapsed time 下产生等价的有界状态；
- 一个 `1/60 s` 基线 tick 保持原每 tick 响应；
- 零和无效 delta 为 no-op。

正时间步比较是数值契约，不承诺任意步长或未来非线性损伤模型下逐 bit 相同。
