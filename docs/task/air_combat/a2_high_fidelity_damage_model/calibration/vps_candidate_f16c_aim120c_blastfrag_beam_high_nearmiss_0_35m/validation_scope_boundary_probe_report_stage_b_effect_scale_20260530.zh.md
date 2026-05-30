# Validation Scope Boundary Probe Report - Stage B Effect Scale

状态：`generated_from_candidate_probe / non-authoritative / stage_b_effect_scale_only`。

本文档记录当前候选包第一版 scope boundary probe 结果表。它来自
[a2_blastfrag_scope_boundary_probe.py](/home/void0312/Workshop/CMO/tools/maintenance/a2_blastfrag_scope_boundary_probe.py)
对当前 non-authoritative validation scaffold 的执行结果。

本文档不创建 runtime descriptor，不授予 `effect_scale_authority`、`component_failure_probability_authority`、`pk_authority` 或 `deterministic_fuze_authority`。

## 1. Probe 摘要

| probe | 当前结论 |
|---|---|
| `SCP-PROBE-001` miss distance | `0.25 / 0.35 / 0.45 m` 三点结果表已生成，且当前都落在 runtime coarse bucket `near_miss`。 |
| `SCP-PROBE-002` closure | `700 / 900 / 1100 mps` 三点结果表已生成，但当前 mechanism surrogate 对 closure 没有物理敏感性，结果只验证 scope bookkeeping。 |
| `SCP-PROBE-003` aspect guard | `beam only` guard 已显式记录；`head_on/tail_chase/high_off_boresight/direct_hit` 继续拒绝。 |

## 2. Miss-Distance Boundary Results

| `standoff_m` | `runtime_miss_distance_bucket` | `blast_scaled_distance_m_kg13` | `fragment_areal_density_per_m2` | 判读 |
|---:|---|---:|---:|---|
| `0.25` | `near_miss` | `0.0921007875` | `2.3057105594` | 更近的近失点带来更低 scaled distance 与更高 fragment density。 |
| `0.35` | `near_miss` | `0.1289411025` | `2.2375438053` | 当前 Stage B anchor。 |
| `0.45` | `near_miss` | `0.1657814174` | `2.1753565911` | 更远的近失点带来更高 scaled distance 与更低 fragment density。 |

当前 probe 结论：

- `blast_scaled_distance_m_kg13` 随 `standoff_m` 单调增加；
- `fragment_areal_density_per_m2` 随 `standoff_m` 单调下降；
- 三个 probe 点都仍落在 runtime coarse bucket `near_miss`。

因此当前 `near_miss_0_35m` 已不再只是单点叙述，而是具备最小三点边界表。
但它仍然只是 candidate toy probe，不等于完整子桶 authority。

## 3. Closure Boundary Results

| `closure_mps` | `blast_scaled_distance_m_kg13` | `fragment_areal_density_per_m2` | `surface_incidence_cos` | 判读 |
|---:|---:|---:|---:|---|
| `700` | `0.1289411025` | `2.2375438053` | `1.0` | 与 anchor 相同。 |
| `900` | `0.1289411025` | `2.2375438053` | `1.0` | 当前 Stage B anchor。 |
| `1100` | `0.1289411025` | `2.2375438053` | `1.0` | 与 anchor 相同。 |

当前 probe 结论：

- 这三个 closure probe 在当前 scaffold 中给出完全相同的 mechanism-load 输出；
- 因此 `high` 目前仍更像一个 scope label，而不是已被该 surrogate 消费的物理敏感轴；
- 这对 Stage B 是可接受的，因为本轮目标是 effect-scale review hygiene，而不是 closure-sensitive calibrated surrogate。

因此：

> `SCP-PROBE-002` 当前证明的是“closure 轴的 bookkeeping 已冻结”，而不是“closure 轴的物理敏感性已经验证”。

## 4. Aspect Guard Results

| 类别 | 标签 |
|---|---|
| accepted | `beam` |
| rejected | `head_on`, `tail_chase`, `high_off_boresight`, `direct_hit`, `closure_bucket != high`, `weapon_family != blast_fragmentation` |

当前结论：

- 当前 Stage B candidate 仍严格保持 `beam only`；
- nose/tail/direct-hit 与其他 closure / weapon-family 标签没有被误纳入当前 candidate scope。

## 5. 对 residual 的当前推进

这份结果表生成后，当前 residual 可更准确地解释为：

- `RES-007`：已拥有三点 miss-distance boundary results，但仍缺独立 review 与更强的 bucket sensitivity 审计。
- `RES-008`：已拥有 beam/high 边界结果与 rejection guard，但 closure 轴当前仍未表现出物理敏感性。
- `RES-012`：probe 结果表已经出现，但 benchmark/input independence 仍缺独立 reviewer audit。

## 6. 当前判定

当前判定为：

> `Stage B scope boundary probes now have a first executable result table, but the result table remains candidate-only, non-authoritative, and not yet independently reviewed`.
