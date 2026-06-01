# G4-R-C Component Fragility Surface Draft - 2026-06-01

状态：`2026-06-01 / G4-R-C-SURFACE / pass / non-authoritative / research_only`。

本文是 `G4-R-C` 的 component fragility research surface draft。它基于
[G4-R-C source scan](../../data_collection/component_fragility_vulnerability/g4_r_c_source_scan_20260601.zh.md)
和 [G4-R-B mechanism-load envelope draft](../../g4_research_mechanism_load_envelope_draft_20260601.zh.md)
定义研究表面字段、row shape 和 replacement path。本文不创建 runtime descriptor，不写
stock row，不替换 `synthetic_sigmoid` baseline，不把 Stage C `right_aileron_actuator`
test-local row 上卷为 F-16C 全机真值。

## Worker Packet

| 字段 | 内容 |
|---|---|
| task id | `G4-R-C-SURFACE` |
| owner | main-thread research surface worker |
| touched files | 本文件 |
| 输入 | `g4_r_c_source_scan_20260601.zh.md`；`g4_research_mechanism_load_envelope_draft_20260601.zh.md`；`vulnerability_evidence_schema_v1.zh.md` |
| status | `pass` |
| closure decision | `research_ready` |
| remaining paths | `G4-R-C-AUDIT` 需要审查 uncertainty / independence；`G4-R-C-INTEGRATE` 需要串行整合 |

## Surface Schema

每个 research row 必须包含：

- `surface_row_id`
- `component_scope_id`
- `mechanism_load_axis_refs`
- `exposure_axis`
- `component_function_state`
- `consequence_class`
- `redundancy_group`
- `fragility_curve_family`
- `threshold_or_sigmoid_placeholder`
- `source_rows`
- `uncertainty_class`
- `confidence`
- `replacement_rule`
- `non_authoritative_research_estimate=true`
- `industrial_admission=false`

本文不写具体 probability 数值。若未来 worker 写入 probability / threshold / sigmoid 参数，
必须引用 source ids、assumptions、unit/value type、uncertainty、confidence 和 replacement rule。

## Research Surface Rows

| surface row id | component scope | mechanism axis refs | exposure / consequence | curve family | source rows | uncertainty / confidence | replacement rule |
|---|---|---|---|---|---|---|---|
| `G4RC-SURF-FC-ACT-001` | lateral flight-control actuator group, including Stage C `right_aileron_actuator` as boundary input only | `G4RB-ENV-FRAG-DENSITY`；`G4RB-ENV-PEN-MARGIN`；`G4RB-ENV-INCIDENCE` | loss/degradation of lateral control path; consequence class requires runtime mapping | `monotonic_threshold_or_sigmoid_placeholder` | `G4RC-KILLCRIT-001`；`G4RC-GEOMETRY-EXPOSURE-007`；Stage C matrix as comparison input | epistemic high / confidence medium | replace with independent actuator fragility curve, public component test data, or reviewer-owned criteria packet |
| `G4RC-SURF-FC-SURF-002` | control-surface structure / hinge-line proxy | `G4RB-ENV-FRAG-DENSITY`；`G4RB-ENV-FRAG-V`；`G4RB-ENV-INCIDENCE` | degraded control authority or jam risk; not mission-kill probability | `piecewise_damage_state_placeholder` | `G4RC-NASA-CONSEQUENCE-005`；`G4RC-FRAG-STRUCTURE-008`；`G4RC-TEXTBOOK-010` | epistemic high / confidence medium-low | replace with target-specific public aero consequence or structure-fragment benchmark |
| `G4RC-SURF-HYD-003` | hydraulic / power transmission line proxy | `G4RB-ENV-PEN-MARGIN`；`G4RB-ENV-FRAG-DENSITY` | loss/degradation of actuator power path; redundancy must be modeled separately | `fault_tree_input_placeholder` | `G4RC-KILLCRIT-001`；`G4RC-SAFETY-CONSEQUENCE-004`；`G4RC-GEOMETRY-EXPOSURE-007` | epistemic high / confidence medium | replace with open redundancy / component routing data or reviewer-owned dependency graph |
| `G4RC-SURF-STRUCT-004` | local skin / frame / control bay structure proxy | `G4RB-ENV-BLAST-P`；`G4RB-ENV-BLAST-I`；`G4RB-ENV-PEN-MARGIN` | local structural damage state; not whole-aircraft kill truth | `multi_mechanism_gate_placeholder` | `G4RC-FRAG-STRUCTURE-008`；`G4RC-NASA-CONSEQUENCE-005`；`G4RC-MSVV-003` | epistemic very high / confidence low-medium | replace with public fragment-structure tests or scoped simulation benchmark manifest |
| `G4RC-SURF-AVIONICS-005` | exposed avionics / wiring / sensor-line proxy | `G4RB-ENV-FRAG-DENSITY`；`G4RB-ENV-PEN-MARGIN` | degraded function / latent fault proxy; requires separate component mapping | `qualitative_failure_state_placeholder` | `G4RC-SAFETY-CONSEQUENCE-004`；`G4RC-TEXTBOOK-010`；`G4RC-LFTE-VALIDATION-002` | epistemic very high / confidence low | replace with public component vulnerability source or mark rejected if no source emerges |

## Algorithm Shape

The research surface should be evaluated as a layered placeholder:

```text
research_fragility_score =
  f(
    mechanism_load_axis,
    exposure_axis,
    component_scope,
    consequence_class,
    redundancy_group,
    uncertainty_class
  )
```

Allowed curve families:

- `monotonic_threshold_or_sigmoid_placeholder`
- `piecewise_damage_state_placeholder`
- `fault_tree_input_placeholder`
- `multi_mechanism_gate_placeholder`
- `qualitative_failure_state_placeholder`

Forbidden interpretations:

- no calibrated probability;
- no aircraft-wide truth;
- no Pk;
- no deterministic fuze behavior;
- no runtime / stock descriptor creation.

## Stage C Boundary

The existing Stage C `right_aileron_actuator` candidate row remains useful only as:

- component naming / scope example;
- comparison input against `synthetic_sigmoid`;
- reminder that author-side repeatability is not independent truth.

It is not a replacement baseline. It is not used to populate this research surface with numeric
probabilities.

## Handoff

`G4-R-C-AUDIT` must verify:

- every row has source rows and mechanism-axis refs;
- every row includes uncertainty, confidence and replacement rule;
- no row uses restricted / game / forum data;
- Stage C test-local materials remain comparison-only.
