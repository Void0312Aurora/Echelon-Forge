# 近炸引信 Surrogate Contract

状态：`2026-06-16` PF-R3 pass / PF-R4 已作为聚焦 runtime evidence 实现。本文仍是设计合同；
实现证据见 [proximity_fuze_runtime_implementation_20260616.zh.md](proximity_fuze_runtime_implementation_20260616.zh.md)。

英文辅文：[proximity_fuze_surrogate_contract_20260616.md](proximity_fuze_surrogate_contract_20260616.md)。

## 合同边界

本文定义非权威 surrogate 的行为形状和验证预期。它不释放 deterministic fuze authority、Pk
或具体弹种杀伤。

## 目标链路

```text
nearest_approach
  -> fuze_sensor_opportunity
  -> fuze_detection
  -> fuze_trigger_decision
  -> detonation_solution
  -> warhead_mechanism_coverage
  -> effects or no-load event
```

关键变化是：nearest approach 保持为诊断事实，不再单独拥有 fuze trigger 或 detonation geometry。

## 建议事件/字段合同

| Stage | 必需事实 | Failure reasons | 说明 |
| --- | --- | --- | --- |
| `nearest_approach` | time、local point、center miss distance、closure、aspect bucket | 无；observed event | 现有事件可保留。 |
| `fuze_sensor_opportunity` | sensor family、候选目标表面/投影距离、range-window score、crossing state、terminal-track state | `outside_sensor_window`、`no_terminal_track`、`invalid_closing_state` | 新逻辑阶段；若暂缓 schema churn，可先嵌入 fuze event fields。 |
| `fuze_detection` | detected flag、target signature source、signature value、signature scale、detection confidence | `target_not_detected`、`signature_below_threshold`、`countermeasure_or_clutter_proxy` | 应发生在 trigger probability 之前。 |
| `fuze_trigger_decision` | armed、trigger candidate、trigger probability、sample、reliability、reason | `fuze_no_detonation`、`trigger_probability_failed`、`safety_or_arm_blocked` | 可扩展现有 fuze event。 |
| `detonation_solution` | source、detonation time、local/world point、delay、delay source、missile axis、projected burst point | `no_valid_burst_solution` | proximity 不应静默默认 nearest point。 |
| `warhead_mechanism_coverage` | mechanism family、coverage score、range term、aspect/incidence term、vulnerable-region proxy、component candidate count | `mechanism_coverage_failed` | Blast-fragmentation 和 continuous rod 必须在此分化。 |
| `effects` | 现有 effects 字段和 no-load invariant | existing outcome state | 未起爆仍不得产生正载荷事实。 |

## 最小 Surrogate 规则

1. 保留现有 contact 和 timed 行为。
2. 保留 no-detonation no-load 行为。
3. 对 proximity fuze，先计算 sensor opportunity，再做最终 trigger。
4. 将 target signature 当作 detection evidence，而不只是 reliability scale。
5. 使用 closure/crossing state 判断 delay 和 burst geometry 是否合理。
6. 计算或命名 detonation-point source：
   - `nearest_point_fallback`
   - `sensor_window_delay_solution`
   - `surface_projection_solution`
   - `debug_profiled_local_point`
   - `timed_fuze`
   - `contact_surface`
7. 拆分机制覆盖：
   - blast-fragmentation：distance、exposed area/projection、incidence、fragment density proxy；
   - continuous rod：lateral sweep band、missile-axis relationship、cut margin、component crossing proxy。
8. 所有数字常数都标记为 surrogate 参数，不得写成真实导弹数据。

## 聚焦验证计划

本文档的 docs-only 验证：

```bash
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_proximity_fuze_realism
```

PF-R4 使用的实现验证：

```bash
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/air_combat/test_continuous_rod_surface.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py tests/runtime/air_combat/test_diagnostics_process_probe_summary.py
```

实现后必需新增的聚焦 case：

- Outside sensor window：接近中心距离不足以触发。
- Detection but no trigger：探测到目标，但 trigger probability 或 burst solution 失败。
- Trigger with delay：detonation point 不能静默等于 nearest point。
- High/low pass：高度改变 opportunity 和 coverage score。
- Beam/nose/tail symmetry：对称几何在应对称处给出对称矩阵。
- Blast-fragmentation versus continuous rod：同一 approach 可因机制覆盖不同而分化。
- No detonation：没有正的 fragment、blast 或 rod load facts。

## 实现写集提议

PF-R4 已实现：

- `src/systems/combat/damage_system_common.h`
- 新增公开事件字段所需的 Python bindings。
- `tests/runtime/air_combat/weapon_guidance_realism/` 下聚焦 runtime tests。
- runtime 字段存在后的 diagnostic exporters。

第一轮实现不包含：

- 训练 reward 修改。
- 默认 F-16 proxy database 替换。
- 场景平衡。
- Pk 或 authority promotion。
- 真实武器校准。

## 验收形状

第一轮实现只有在链路更可解释时才应验收。损伤概率变高或变低本身都不是验收证据。
验收证据必须说明引信为什么探测、为什么没探测、为什么触发、为什么失败、为什么延迟、
为什么选择某个起爆点，以及为什么产生或拒绝机制载荷。
