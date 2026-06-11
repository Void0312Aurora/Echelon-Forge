# A2 Runtime 状态

状态：`2026-06-01 / G1 runtime engineering / non-authoritative`。

本文承接 `TC-A2-RUNTIME`。它描述已经进入维护路径的工程面，不授予
`effect_scale_authority`、`component_failure_probability_authority`、`pk_authority`
或 `deterministic_fuze_authority`。

## 任务簇

| 任务簇 | 粒度 | 当前结论 |
|---|---|---|
| `TC-A2-RUNTIME` | `G1 runtime engineering` | structured aircraft damage/effects 主链进入维护路径；仍非校准 authority |

## 已维护的工程面

- structured aircraft 不再默认由 HP-first bypass 直接取得 kill authority；
- `AircraftDamageState`、`PlatformDamageState` 和 `ComponentDamageState` 已能承接局部命中后的后果传播；
- `EffectsEvent` 已能记录 miss distance、目标机体系起爆点、闭合速度、导弹速度轴、引爆姿态轴、direct/projection 命中形态、spatial/mechanism/component/fuze/vulnerability 证据字段；
- `DamageReport` 已能向 runtime / binding / consumer 暴露 structured-air consequence，包括非终局连续毁伤信号和终局 kill flags；
- row-backed `effect_scale` 与 row-backed `component_failure_probability` 有 runtime 消费路径，但当前只允许在 test-local exercise 或非权威 candidate 包中演练；
- reward / score 层只消费 `DamageReport` 和 loss/capability state，不反向定义物理 effects authority。

## Consequence flags 边界

`DamageReport` 中的 aircraft consequence flags 只表示工程报告面：

| flag | 语义 | 不得解释为 |
|---|---|---|
| `forced_landing` | aircraft damage state 已达到 forced-landing consequence | Pk、mission kill 概率或 release-grade consequence model |
| `flight_control_kill` | flight-control capability 已达到 runtime kill threshold | calibrated component vulnerability 或 authority row |
| `propulsion_kill` | propulsion capability 已达到 runtime kill threshold | engine vulnerability truth 或 stock descriptor release |
| `crew_kill` | crew/pilot capability 已达到 runtime kill threshold | casualty/Pk model 或 deterministic kill-chain |

这些 flags 可以被 binding、debug API、trace/replay 和 score consumer 读取；它们不能反向定义
`effect_scale_authority`、`component_failure_probability_authority`、`pk_authority` 或
`deterministic_fuze_authority`。

## 验收标准

`TC-A2-RUNTIME` 只能按工程回归验收：

1. C++ contract、event recorder、launch adapter、Python binding 和 runtime debug surface 形状稳定；
2. structured aircraft hitbox / component / overlay / fuze / vulnerability evidence 回归通过；
3. live missile 可以产生可审计 `EffectsEvent` 和 `DamageReport`；
4. structured-air physical effects 不直接写 RL `Score`；
5. legacy HP path 保持兼容边界，不被误当作高保真 aircraft kill authority。

## 明确非目标

- 不校准真实 Pk；
- 不发布 deterministic fuze；
- 不把 synthetic vulnerability 或 aircraft JSON 自声明提升为 stock authority；
- 不把 test-local descriptor 正向路径写成 release-grade descriptor；
- 不把运行时事件面闭合写成完整 kill-chain 闭合。

## 验证锚点

维护此簇时优先使用 Windows 本地维护环境：

```powershell
cmake --build build-local-win --target ef_core ef_py -j2
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\runtime\air_combat\test_weapon_guidance_realism_guards.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\runtime\bindings\test_bindings_engagement_surface.py tests\runtime\engagement
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\architecture\test_wp22_structural_guardrails.py
```

如涉及 source admission、candidate package 或 authority 边界，同时运行：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\architecture\damage_model\test_source_admission_audit.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python tools\maintenance\damage_model_source_governance.py admission-audit --strict
```
