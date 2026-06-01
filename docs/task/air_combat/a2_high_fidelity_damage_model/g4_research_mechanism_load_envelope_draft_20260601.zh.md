# G4-R-B Mechanism-Load Envelope Draft - 2026-06-01

状态：`2026-06-01 / G4-R-B-002-DERIVED-ENVELOPE-DRAFT / pass / research_only / replaceable_data`。

本文是 `G4-R-B` 的 derived envelope research packet。它只把
[mechanism-load source scan](g4_research_mechanism_load_envelope_source_ledger_20260601.zh.md)
整理成可供后续 component fragility surface 使用的机制载荷字段，不写 runtime descriptor、
stock row、calibration row 或型号级真值。

## Worker Packet

| 字段 | 内容 |
|---|---|
| task id | `G4-R-B-002-DERIVED-ENVELOPE-DRAFT` |
| owner | main-thread mechanism-load modeling worker |
| touched files | 本文件 |
| 输入 | `g4_research_mechanism_load_envelope_source_ledger_20260601.zh.md`；`vulnerability_evidence_schema_v1.zh.md`；`research_candidate_data_policy_20260601.zh.md` |
| status | `pass` |
| closure decision | `research_ready` |
| remaining paths | `G4-R-B-003-VALIDATION-GUARD-AUDIT` 需要审查本文和 source scan |

本文中的所有字段都是 `non_authoritative_research_estimate`。如果后续出现更好的公开、
第三方、社区共识或 reviewer-owned 数据，可以按 replacement rule 替换。

## Envelope 字段草案

| envelope field id | mechanism | source rows | value representation | units / axis | assumptions | uncertainty / confidence | replacement rule |
|---|---|---|---|---|---|---|---|
| `G4RB-ENV-BLAST-Z` | blast | `G4RB-BLAST-METHOD-001`；`G4RB-BLAST-XCHECK-002` | `formula_family_slot` for scaled-distance proxy | `m/kg^(1/3)` | 使用公开 scaled-distance 方法族作为研究坐标轴；不声明真实 TNT equivalent | epistemic high / confidence medium | 若获得 scope-near public blast validation 或 frozen benchmark manifest，替换当前 formula-family-only slot |
| `G4RB-ENV-BLAST-P` | blast | `G4RB-BLAST-METHOD-001`；`G4RB-BLAST-TOOL-003` | `qualitative_range_placeholder` for overpressure proxy | `kPa` proxy label only | 只作为排序和敏感性轴，不写具体 overpressure 值 | epistemic high / confidence medium-low | 若 allowed-output hash-only public-tool comparison 进入 retained packet，可替换为 bounded range |
| `G4RB-ENV-BLAST-I` | blast | `G4RB-BLAST-METHOD-001`；`G4RB-BLAST-TOOL-003` | `qualitative_range_placeholder` for impulse proxy | `kPa*ms` proxy label only | 与 overpressure 分开保留，避免把 peak load 等同于 impulse | epistemic high / confidence medium-low | 若公开 blast benchmark 明确 impulse route，可替换为 bounded range |
| `G4RB-ENV-FRAG-MASS` | fragment | `G4RB-FRAG-MASS-004`；`G4RB-FRAG-DEBRIS-006` | `distribution_family_slot` for fragment mass / debris class | distribution family, no retained raw values | Mott / debris vocabulary 只给分布形状和审查字段，不给 warhead-specific mass table | epistemic high / confidence medium | 若公开 fragment test data 或 reviewer-owned debris anchor 提供可引用 distribution，可替换 proxy family |
| `G4RB-ENV-FRAG-V` | fragment | `G4RB-FRAG-VELOCITY-005`；`G4RB-FRAG-DEBRIS-006` | `formula_family_slot` for initial-velocity / residual-velocity proxy | velocity proxy, no numeric value | Gurney route 和 TP-21 vocabulary 只作方法导航；不写具体初速 | epistemic high / confidence medium-low | 固定官方 artifact / rights / checksum 后可升级方法 confidence；scope-near validation 可替换 |
| `G4RB-ENV-FRAG-DENSITY` | fragment | `G4RB-FRAG-DEBRIS-006`；`G4RB-SAMPLING-009` | `surrogate_axis` for areal density / exposure | `fragments/m^2` proxy label only | spherical / isotropic sampling 只作 reproducibility baseline，不声明真实 direction pattern | epistemic high / confidence medium | 若公开 warhead pattern 或 accepted surrogate pattern 出现，替换 isotropic baseline |
| `G4RB-ENV-PEN-MARGIN` | penetration | `G4RB-PEN-MARGIN-007` | `threshold_family_slot` for penetration margin | dimensionless / normalized margin | NASA BLE / Recht-Ipson / V50 只作 thresholding scaffold，不迁移材料系数 | epistemic high / confidence low-medium | 若 conventional fragment penetration examples with rights appear，可替换为 better threshold family |
| `G4RB-ENV-ROD-CUT` | rod / cut | `G4RB-ROD-SHAPE-008` | `mechanism_shape_only` | qualitative cut margin | continuous-rod background 不匹配本候选 weapon family；默认 disabled unless surface requests it | epistemic very high / confidence low | 若 G4/G5 research explicitly includes rod proxy，另建 assumptions；否则保留 background-only |
| `G4RB-ENV-INCIDENCE` | geometry filter | `G4RB-PEN-MARGIN-007`；`G4RB-SAMPLING-009`；schema row fields | `filter_axis` for surface incidence | absolute cosine bucket | 只表达 obliquity / surface relation，不是 damage probability | epistemic medium / confidence medium | 若 target geometry surface produces better local normal evidence，可替换 current bucket |

## Mechanism Vector

后续 research surface 可以使用下面的机制载荷向量，不得把它当作真实校准数据：

```text
mechanism_load_vector = {
  blast_scaled_distance_axis,
  blast_overpressure_proxy_axis,
  blast_impulse_proxy_axis,
  fragment_mass_distribution_family,
  fragment_velocity_proxy_axis,
  fragment_areal_density_proxy_axis,
  penetration_margin_proxy_axis,
  surface_incidence_filter,
  optional_rod_cut_shape
}
```

每个 axis 的输出必须同时携带：

- `source_rows`
- `value_representation`
- `assumptions`
- `uncertainty_class`
- `confidence`
- `replacement_rule`
- `not_for_stock_runtime=true`

## Conflict Notes

| conflict id | 说明 | 处理 |
|---|---|---|
| `G4RB-CONFLICT-BLAST-DOMAIN` | 公开 blast 方法多来自 TNT / structure / explosives-safety domain | 保留为 method family；不写具体 platform load |
| `G4RB-CONFLICT-FRAG-DIRECTION` | 公开 fragment mass/velocity 方法不含真实 direction pattern | 使用 sampling reproducibility baseline；标注 pattern data gap |
| `G4RB-CONFLICT-PENETRATION-DOMAIN` | BLE / V50 / debris vocabulary 与 aircraft component failure 不同域 | 只保留 threshold scaffold，不生成 component probability |
| `G4RB-CONFLICT-TP21-BECO` | retained TP-21 / BEC-O context 有 hash-only / rights / output-policy 边界 | 只作为 replacement target；不消费为 release evidence |

## Downstream Handoff

`G4-R-C-SURFACE` 可以引用本文的 mechanism axis，但必须继续保持：

- component rows 为 research surface；
- probabilities / thresholds 为 placeholder 或 derived estimate；
- Stage C test-local rows 只作为 comparison / boundary input；
- 每个 surface row 都能回链本文 `envelope field id` 和 source scan row。

## Research 边界

- 本文不提供 AIM-120C-class 战斗部真实 blast / fragment 参数。
- 本文不提供 F-16C 组件真实失效概率。
- 本文不创建 runtime / stock / descriptor artifact。
- 本文不复制任何受限表格、图、正文或 selected output。
