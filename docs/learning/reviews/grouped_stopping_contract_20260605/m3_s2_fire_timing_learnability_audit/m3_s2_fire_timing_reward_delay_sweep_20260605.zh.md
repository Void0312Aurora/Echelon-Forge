# M3-S2 开火时机 Reward Delay Sweep

父级：[README.zh.md](README.zh.md)。

状态：`2026-06-05` evidence update；记录 reward 排序缺陷，并重新聚焦 learned-policy
可达性问题。

## 命令

本 sweep 在维护的 M3-S1 probe 场景/配置下，对 `0` 到 `1778` 的所有 legal-open
delay 逐一运行一个 Stage-1 episode。每个 case 使用 oracle `legal_mask_fire`
transport，因此这是环境/reward surface 审计，不是 learned-policy success claim。

Artifacts：

```text
experiments_tmp/air_combat_fire_timing_full_delay_sweep_seed7_ep1_0_1778_20260605.jsonl
experiments_tmp/air_combat_fire_timing_full_delay_sweep_seed7_ep1_0_1778_20260605_summary.json
experiments_tmp/air_combat_fire_timing_full_delay_sweep_seed7_ep1_0_1778_20260605_compact.csv
experiments_tmp/air_combat_fire_timing_full_delay_sweep_seed7_ep1_0_1778_20260605.png
```

## 结果

| Metric | Value |
| --- | ---: |
| Candidate delays | `1779` |
| Probe errors | `0` |
| Successful releases | `1759` |
| Effects/damage reports | `270` |
| Combat wins | `27` |
| Best delay by episode return | `1664` |
| Best release step | `1666` |
| Best effects/damage step | `1693` |
| Best terminal reason | `combat_win` |
| Best loss state | `mission_kill` |
| Best return | `2009.267824398761` |

最佳 delay 是非常晚的近距离发射。hold trace 在 release step 的几何近似为：

```text
track_range_m: 1341.264
geom_range_m: 823.605
track_age_s: 1.25
closing_mps: 408.303
```

这说明当前 reward surface 存在数学最优点，但该最优点不是维护中的 `8 km` 到
`30 km` quality-window proxy，也不能解释为战术意义上的最佳开火时机。

## Reward 排序缺陷

sweep 解释了为什么晚赢高于早赢。对 terminal shots：

```text
return ~= release_bonus + objective_bonus + accumulated per-step shaping
release_bonus ~= 300 + 50 + 100 = 450
objective_bonus = 1500
```

示例对照：

| Delay | Combat-win step | Return |
| ---: | ---: | ---: |
| `939` | `1233` | `1990.8678243987608` |
| `1664` | `1693` | `2009.267824398761` |

return 差值为：

```text
2009.267824398761 - 1990.8678243987608 = 18.4
1693 - 1233 = 460 steps
18.4 / 460 = 0.04 per step
```

因此任务成功仍然压倒 no-win outcome；但在已经能 win 的 outcome 之间，正的每步
shaping 会奖励更晚终止。当前 reward contract 缺少显式 time-to-success cost，
或吸收态/成功归一化目标。

## 对可达性问题的含义

该发现不能解释 learned policy 的 no-fire 行为。oracle surface 已经证明：

- no fire 在当前 return 下不是最优；
- legal release 可达且有强奖励；
- 部分 delayed oracle shots 可达成 terminal win。

因此剩余 learned-policy blocker 应作为 action/event reachability 与 credit assignment
问题继续审计：

```text
continuous model output -> masked edge-triggered pulse -> executable fire_once
```

下一步审计应区分 learned policy 是否：

- 对 `fire_once` 给出低概率；
- 在 executable mask 打开前选择 `fire_once`，从而消耗 edge；
- stopping/event head 有 boundary crossing，但没有传输到 action；
- action-mask 支持存在，但 logits 或 PPO credit 仍把 deterministic 行为压成 hold。
