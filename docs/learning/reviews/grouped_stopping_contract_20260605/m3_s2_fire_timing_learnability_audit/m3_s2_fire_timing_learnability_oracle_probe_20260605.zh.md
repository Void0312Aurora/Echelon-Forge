# M3-S2 开火时机 Oracle Probe

父级：[README.zh.md](README.zh.md)。

状态：`2026-06-05`，可学习性审计证据通过；learned policy 仍 held。

## 命令

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/fire_timing_fault_localization_probe.py \
  --mode learnability_audit \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json \
  --episodes 2 \
  --seed 31 \
  --max_steps 2000 \
  --delays 0,31,63 \
  --json_out experiments_tmp/air_combat_fire_timing_learnability_audit_20260605.json
```

Artifact：

```text
experiments_tmp/air_combat_fire_timing_learnability_audit_20260605.json
```

## 摘要

| Case | Mean reward | Mean release count | Release steps | Effects | Damage | Health drop | Rejections |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| `hold_fire` | `71.54782439876094` | `0.0` | `[]` | `0.0` | `0.0` | `0` | `{}` |
| `forced_fire_edge_at_reset` | `71.54782439876094` | `0.0` | `[]` | `0.0` | `0.0` | `0` | `{"no_target": 2}` |
| `legal_mask_fire_delay_0` | `521.547824398761` | `1.0` | `[2, 42]` | `0.0` | `0.0` | `0` | `{}` |
| `legal_mask_fire_delay_31` | `521.547824398761` | `1.0` | `[33, 73]` | `0.0` | `0.0` | `0` | `{}` |
| `legal_mask_fire_delay_63` | `521.5478243987609` | `1.0` | `[65, 105]` | `0.0` | `0.0` | `0` | `{}` |

Verdict：

```json
{
  "primary_breakpoint": "legal_timing_unidentifiable_from_current_return",
  "release_reachable_with_legal_oracle": true,
  "release_vs_hold_reward_distinguishable": true,
  "release_vs_hold_reward_delta": 450.00000000000006,
  "post_release_effect_observable": false,
  "legal_timing_reward_distinguishable": false,
  "legal_timing_reward_spread": 1.1368683772161603e-13,
  "edge_trigger_adapter_hazard": true
}
```

## 解读

当前 Stage-1 问题并不是卡在基础 release reachability：合法 oracle pulse 能发射一枚
authorized missile。

真正的堵点是 timing identifiability。delay `0`、`31`、`63` 的合法 pulse 获得相同
return，并且 `2000` 步内没有 effects event、damage report、health drop 或 kill。
因此当前环境教会的是“合法发射”，而不是“在这个合法时刻发射优于那个合法时刻”。

Action adapter 还有独立风险。`forced_fire` 从 reset 高电平并不等于持续尝试开火。
由于 `air_combat_hybrid_v1` 的 fire 是 edge-triggered，第一个高电平会在无目标时被
`no_target` 拒绝；之后信号保持高，不再产生新的 pulse。

## 后果

继续增加 PPO 步数或扩大 stopping head 本身不太可能根治。下一切片应选择合同级修复：

- 将 stopping/event decision 接到 executable pulse adapter，使其能有意保持窗口前低电平，
  并在窗口内给出一次高脉冲；
- 暴露 timing-quality 或 downstream effects 作为可区分目标；
- 之后再重新考虑 M2 memory/sequence state 是否是表示层升级。
