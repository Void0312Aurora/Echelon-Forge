# Fire-Timing 发射窗口位置效应杀伤链诊断

日期：2026-06-15

## 结论

当前结果应先视为杀伤链就绪性诊断，而不是 reward 或策略学习结论。在杀伤链能够完整复盘前，讨论 `total_reward` 的敏感性意义有限。

已确认的事实是：合法发射窗口内不同位置发射导弹会改变 release geometry，并触发不同的 effects/damage/mission-kill 标签；但在本轮修复前，杀伤链曾有三类阻塞，尚不足以把这些标签解释为可靠的距离-杀伤概率或训练 reward 依据：

- 已修复：real missile 的 `rng_state` 已混入 kernel reset RNG 熵；Stage-1 小样本验证显示同一 `delay=32` 下不同 seed 可产生不同 component/sample/platform 结果。
- 已修复：`PlatformConsequenceEvent` 已从 C++ recent-event store 经 facade/export 进入 Python 诊断链，schema 升级为 `6`，并导出 capability before/after、control/engine/fuel/fire delta、AircraftDamageState before/after/delta、air-domain system hit flags、air-domain spatial scales 与 vulnerability scale trace。
- 当前边界：部分平台 capability delta 仍可能来自 air-domain system/scaled consequence 聚合，而不是具名 component damage；schema v6 已能把这条聚合路径结构化导出，后续若要做可校准杀伤概率，应基于 v6 字段继续审查 system/scales 到 capability delta 的阈值合理性。

## 测试边界

- 入口：`tools/diagnostics/fire_timing_fault_localization_probe.py --mode window_position_sweep`
- 场景：`scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`
- 配置：`examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json`
- 行为：oracle legal-mask firing，不是已学习策略评估。
- 自变量：`fire_delay_steps`，即合法发射窗口打开后的延迟步数。
- 样本：每个 delay 使用 `5` 个独立 seed 样本；每个样本以 fresh process probe、`episodes=1` 执行，避免多 episode probe 复用状态污染 release 统计。
- 主要因变量：release range、miss distance、component failure probability、component failure sample、component damage count、system health delta、mission/mobility/sensor/survivability capability delta、effects/damage event、mission kill。
- 当前图中的 `return delta` 仅保留为原始 sweep 输出，不作为本次诊断结论依据。

执行命令：

```powershell
.\.venv\Scripts\python.exe tools\diagnostics\fire_timing_fault_localization_probe.py `
  --mode window_position_sweep `
  --episodes 5 `
  --max_steps 2000 `
  --delays 0,32,64,128,256,512,768,1024,1280,1536,1664 `
  --output_dir docs\task\model\fire_timing_window_position_effect
```

## 关键结果

| delay steps | samples | release range m | miss distance m | component P(fail) | system delta | mission delta | release | effects\|rel | damage\|rel | mission kill\|rel |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 5 | 34961.0 | 12.12 | 缺失 | 0.000 | 0.000 | 1.00 | 1.00 | 1.00 | 0.00 |
| 32 | 5 | 34343.3 | 4.19 | 0.640 | -0.906 | -0.906 | 1.00 | 1.00 | 1.00 | 1.00 |
| 64 | 5 | 33732.4 | 11.60 | 缺失 | -0.029 | -0.029 | 1.00 | 1.00 | 1.00 | 0.00 |
| 128 | 5 | 32512.6 | 8.66 | 缺失 | -0.295 | -0.295 | 1.00 | 1.00 | 1.00 | 0.00 |
| 256 | 5 | 30032.9 | 12.89 | 缺失 | 0.000 | 0.000 | 1.00 | 1.00 | 1.00 | 0.00 |
| 512 | 5 | 24873.3 | 12.57 | 缺失 | 0.000 | 0.000 | 1.00 | 1.00 | 1.00 | 0.00 |
| 768 | 5 | 19530.4 | 5.14 | 0.950 | -0.566 | -0.566 | 1.00 | 1.00 | 1.00 | 0.00 |
| 1024 | 5 | 14109.7 | 4.82 | 0.591 | -0.405 | -0.402 | 1.00 | 1.00 | 1.00 | 0.00 |
| 1280 | 5 | 8693.2 | 缺失 | 缺失 | 缺失 | 缺失 | 1.00 | 0.00 | 0.00 | 0.00 |
| 1536 | 5 | 3398.6 | 缺失 | 缺失 | 缺失 | 缺失 | 1.00 | 0.00 | 0.00 | 0.00 |
| 1664 | 5 | 823.6 | 3.06 | 0.625 | -1.000 | -1.000 | 1.00 | 1.00 | 1.00 | 1.00 |

Verdict 摘要：

- `release_position_variation_observed=true`
- `release_range_spread_m=34137.42`
- `outcome_variation_observed=true`
- `miss_distance_spread_m=9.83`
- `system_health_delta_spread=1.0`
- `component_failure_probability_spread=0.359`
- `categorical_effect_change=true`
- `learnability_candidate=true`

## 杀伤链解释边界

发射窗口位置确实改变了交战几何：从窗口刚打开时约 `35 km` 发射，到延迟 `1664` 步时约 `0.82 km` 发射。结果不是简单单调曲线，而是非单调的窗口效应：`32` 步和 `1664` 步出现 mission kill，`1280` 和 `1536` 步没有形成 effects/damage event，其他点多为 combat-capable 但有不同程度的 system health delta。

这说明“发射窗口位置”本身不是无关变量，但当前证据只支持“窗口位置改变杀伤链标签”，不支持“这些标签已经是可校准杀伤概率”。在杀伤链就绪前，不应再围绕 reward shaping 下结论。

本次 `5` 个 seed 样本在同一 delay 下给出了相同的聚合标签。源码复查显示 real missile launch seed 当前没有混入 kernel reset seed，因此这个一致性不能解释为概率收敛，只能解释为当前 deterministic 发射/杀伤链在这些窗口位置给出了稳定离散标签。

## Mission-Kill 跳变解释

`32` 和 `1664` 两个 delay 出现 mission kill，并不应解释为 `34 km` 和 `0.8 km` 是两个真实的高杀伤距离峰值。临时链路复盘显示，这两个点分别触发了不同的组件后果：

- `delay=32`：miss distance 约 `4.19 m`，损伤组件为 `eo_ir_sensor_turret / sensor_payload`，component P(fail)=`0.640`，failure sample=`0.181`，平台后果聚合为 `mission_kill`。
- `delay=768`：同样损伤 `eo_ir_sensor_turret / sensor_payload`，component P(fail)=`0.950`，failure sample=`0.133`，但平台后果仍为 `combat_capable`。
- `delay=1024`：损伤 `pusher_propeller_hub / propeller`，component P(fail)=`0.591`，平台后果为 `combat_capable`。
- `delay=1664`：miss distance 约 `3.06 m`，损伤组件为 `data_link_transceiver / data_link`，component P(fail)=`0.625`，failure sample=`0.009`，平台后果聚合为 `mission_kill`。

因此，mission-kill 标签目前是离散组件命中、随机 failure sample、组件系统重要性和平台能力阈值共同作用的结果，而不是关于 release range 的平滑函数。当前数据只支持“发射窗口位置会改变可学习的杀伤链标签”，不支持“距离-杀伤概率曲线已经物理合理”。

这个现象暴露出的诊断缺口已在 schema v6 中补齐：当前 chain CSV/JSON 已导出 `mission_capability_delta`、`mobility_capability_delta`、`sensor_capability_delta`、`survivability_margin_delta`，并能记录 `PlatformConsequenceEvent` 的 capability before/after、AircraftDamageState before/after/delta、air-domain system-hit flags、spatial scales 与 vulnerability scale trace。因此现在可以从最终产物中复盘某个窗口为何跨过或未跨过 `mission_capability <= 0.25` 阈值。

## 下一步阻塞项

1. 使用 schema v6 重新生成完整 fire-window sweep，把 `air_system_hit_flags_counts`、`vulnerability_scale_trace_counts` 与 capability delta 一起作为主诊断表面。
2. 基于 v6 字段审查 air-domain system/scales 到 platform capability delta 的阈值和权重是否物理合理。
3. 只有在杀伤链能解释 component/system/platform 因果后，再讨论 reward 或辅助学习目标。

## 本轮修复验证

- `cmake --build build-local-win --target ef_core ef_py -j2`：通过，`ef_py` 已包含新的 `PlatformConsequenceEvent` 字段。
- 聚焦 pytest：`82 passed`，覆盖 process probe、window sweep、binding/contract、facade export 与 live-event 静态合同。
- Stage-1 小样本：`delay=768` 的平台行已从 `DamageReport` fallback 变为 `PlatformConsequenceEvent`，并导出 `mission_capability_before=1.0`、`mission_capability_after=1.0` 与 AircraftDamageState delta。
- Stage-1 小样本：`delay=32` 下 `seed=20260615` 命中 `synthetic_aperture_radar`，`P(fail)=0.555138`、`sample=0.418448`、`mission delta=-0.873799`；`seed=20260616` 没有 component row，平台保持 `combat_capable`。这说明当前 real missile 杀伤链已经不再是几何固定 seed 的单一样本。
- 2026-06-15 v6 补边界验证：清理重建 `ef_core/ef_py` 后，聚焦 pytest 为 `87 passed`。`delay=32`/`seed=20260615` 导出 `air_system_hit_flags=sensor=1,...,structure=1`、spatial scales 与 `vulnerability_scale_trace=present=1,...,effect_scale=0.950041`；`seed=20260616` 无 component/system damage，trace 为空且平台保持 `combat_capable`。
- v6 小型 sweep smoke：`delays=32,768`、每个 delay `2` 个 seed。`delay=32` 的 `mission_kill_given_release_rate=0.5`，`air_system_hit_flags_counts` 中 1 个非空 hit pattern、1 个空 trace；`delay=768` 的 `mission_kill_given_release_rate=0.0`，两个样本 trace 均为空、`mean_system_health_delta=0.0`。本次补边界不改变杀伤模型计算公式，但修复了 moved-from `EffectsEvent` 导致 platform consequence 丢失 string/vector trace 的导出问题。

## 产物

- `fire_timing_window_position_sweep_20260615.json`
- `fire_timing_window_position_sweep_20260615.csv`
- `fire_timing_window_position_sweep_20260615.png`：最终学习信号视图。

注：`first_release_legal_window_age_steps` 在当前 process summary 中会因为首发射行已经进入 `FiredAssess` 快照而保持为 `0`，本次结论不依赖该字段；窗口位置以 `fire_delay_steps` 和实际 release range 为准。
