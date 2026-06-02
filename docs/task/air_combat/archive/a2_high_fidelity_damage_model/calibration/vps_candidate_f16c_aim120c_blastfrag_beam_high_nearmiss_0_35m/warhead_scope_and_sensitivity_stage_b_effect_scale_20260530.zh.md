# Warhead Scope And Sensitivity - Stage B Effect Scale

状态：`author_frozen_scope_manifest / candidate / non-authoritative`。

本文档把当前 Stage B `effect_scale_authority_only` 候选包中与
`AIM-120C-class / blast_fragmentation` 相关的 scope 边界、数值消费方式和
sensitivity 约束固定下来，防止把 family-level、third-party candidate 或
repo toy proxy 误写成 AIM-120C truth。

本文档不创建 runtime descriptor，不授予 `effect_scale_authority`、
`Pk` 或 deterministic-fuze authority，也不关闭 `RES-004 warhead scope`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `primary_release_scope` | `effect_scale_authority_only` |
| `weapon_class` | `AIM-120C-class` |
| `weapon_family` | `blast_fragmentation` |
| `forbidden_claim` | `AIM-120C-class candidate must not be described as AIM-120C-7/C-8 warhead or fuze truth` |

## 2. 战斗部 scope / sensitivity 表

| `assumption_id` | `scope_claim` | `source_ids` | `third_party_candidates` | `consumed_by_surrogate` | `sensitivity_axis` | `forbidden_authority_claim` | residual |
|---|---|---|---|---|---|---|---|
| `WAR-001` | `weapon_family = blast_fragmentation` 只作为 family-level label | `AIM120-WF-002`, `AIM120-WF-006` | none required | `yes` | family gate / vocabulary | 不得外推到 AIM-120C variant-specific warhead internals or fragment pattern | `RES-004` |
| `WAR-002` | current scaffold consumes repo `warhead.mass_kg` as toy input, not as AIM-120C truth | `AIM120-WF-002`, internal repo `aim_120c.json` | `AIM120-TPC-001/002/006` only as `sanity_check_only` | `yes` | blast scaled-distance proxy, toy fragment-count / energy proxy | 不得把 repo `warhead.mass_kg` 写成 AIM-120C calibrated warhead mass、TNT equivalent 或 authority row | `RES-004`, `RES-006` |
| `WAR-003` | current scaffold loads repo `lethal_radius` but Stage B hard-gate snapshot 不依赖该字段放行 | internal repo `aim_120c.json` | none | `loaded_but_not_release_gating` | bookkeeping only | 不得把 repo `lethal_radius` 写成 fuze radius、kill radius 或 release threshold | `RES-004`, `RES-014` |
| `WAR-004` | public TDD / target-detection / burst-point terminology 只支持字段命名和 residual 语言 | `AIM120-WF-006` | `AIM120-TPC-001/002/008` 仅术语 sanity | `no_numeric_consumption` | field naming / evidence language | 不得推出 trigger threshold、delay、reliability、safe-arm 或 deterministic fuze behavior | `RES-004`, `RES-014` |
| `WAR-005` | `PHYS-BF-*` 公开方法只支撑 blast / fragment toy proxy，不支撑 missile-specific truth | `PHYS-BF-001/002/006/013/014/015` | none | `yes` | method route, monotonicity, unit and uncertainty hygiene | 不得把 toy method route 写成 AIM-120C fragment count/mass/velocity/directionality truth | `RES-004`, `RES-005`, `RES-006` |
| `WAR-006` | third-party 40 lb / 18 kg mass cluster 只允许做 sanity/sensitivity，不进入 authority row | none official beyond family context | `AIM120-TPC-001/002/005/006/007` | `no_for_stage_b_release` | mass-envelope sanity only | 不得写成 AIM-120C / C-7 / C-8 warhead truth | `RES-004` |
| `WAR-007` | forum / game / commercial sim proximity、damage、fragment 或 Pk 值全部拒绝 | none admitted | rejected: `AIM120-TPC-REJ-001..005` | `no` | rejection guard only | DCS / War Thunder / forum / RPG values 永不进入 Stage B authority path | `RES-004`, `RES-013`, `RES-014` |

## 3. 当前 Stage B 实际消费的 numeric 层级

当前 Stage B surrogate 只实际消费以下 numeric 层级：

- repo candidate database 中的 `warhead.mass_kg`；
- 基于该 toy input 形成的 scaled-distance / toy fragment-count / toy fragment-energy proxy；
- 与公开 `PHYS-BF-*` 方法族一致的单位、单调性和不确定性 hygiene。

当前 Stage B surrogate **不**实际消费：

- deterministic fuze trigger radius；
- target signature threshold；
- live delay / reliability；
- variant-specific fragment pattern；
- validated kill radius；
- `Pk`。

## 4. 当前可宣称的战斗部真实性边界

当前只允许宣称：

- 该 package 已固定在 `AIM-120C-class / blast_fragmentation` family-level candidate 范围内；
- 当前 surrogate 至少把 family label、公开方法路由与 toy numeric proxy 区分开了；
- 仍不能把任何单一数值写成 AIM-120C truth 或 authority row。

## 5. 当前判定

当前判定为：

> `Stage B currently uses an AIM-120C-class blast-fragmentation candidate family label plus repo toy warhead proxies; this is enough for candidate effect-scale hygiene but not enough for warhead authority`.
