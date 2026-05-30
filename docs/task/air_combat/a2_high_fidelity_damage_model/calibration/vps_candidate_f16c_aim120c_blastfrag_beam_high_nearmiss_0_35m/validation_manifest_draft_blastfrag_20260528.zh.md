# Blast-Fragmentation VPS Validation Manifest 草案 - 2026-05-28

状态：`draft / validation_status=not_run / non-authoritative`。本文档把 [VPS blast_fragmentation 公开方法来源](../../data_collection/vps_blast_fragmentation_methods/README.zh.md) 映射到首个 `validated_physics_surrogate` 候选包。它不运行 benchmark，不生成 artifact，不创建 vulnerability descriptor，不授予 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

## Scope

| 轴 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.vulnerability_surrogate_validation.v1` |
| `validation_status` | `not_run` |
| `target_type` | `F-16C_Block50` |
| `weapon_class` | `AIM-120C-class` |
| `weapon_family` | `blast_fragmentation` |
| `aspect_bucket` | `beam` |
| `closure_bucket` | `high` |
| `miss_distance_bucket` | `near_miss_0_35m` |

`near_miss_0_35m`、`beam` 和 `high` 仍是候选 scope 标签；当前没有完成 bucket 内采样密度、边界行为或真实校准验证。

当前可执行 scaffold 入口为 `tools/maintenance/a2_blastfrag_validation_scaffold.py`。该工具会保留候选 scope 标签 `near_miss_0_35m`，但同时显式导出当前 runtime 粗桶 `near_miss`，提醒 benchmark/validation scope 与运行时 row 匹配语义尚未完全细化到 0.35 m 子桶。
同一工具还会导出一个 schema-aligned non-authoritative row draft：descriptor 保持 `source_kind=engineering_surrogate`、`calibration_status=unvalidated`、全部 authority=false，row 只带机制载荷 gate 字段，不带 `effect_scale` 或 `component_failure_probability` 真值。
当前已新增独立 metrics / acceptance criteria artifact：
[validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md](validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md)。
它只冻结 Stage B `effect_scale` 候选评审所需的 hard gates，不等于 validation passed。
当前还新增了独立 scope / independence manifest：
[validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md](validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md)。
它冻结 `beam / high / near_miss_0_35m` 的候选边界和 benchmark/input separation；第一版 boundary result table 已经生成，但独立 review 仍未完成。
当前已补入第一版 boundary probe result report：
[validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md](validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md)。
它证明 boundary probe 已可执行，但仍只属于 candidate scope review，不构成 authority 放行。

## Authority 边界

| authority 字段 | 当前值 | 原因 |
|---|---|---|
| `calibration_status` | `unvalidated` | 没有 benchmark 运行、artifact sha256、冻结指标或审阅记录。 |
| `effect_scale_authority` | `false` | 没有 validated surrogate 或 external calibration dataset。 |
| `component_failure_probability_authority` | `false` | 没有 scope 匹配的组件失效概率校准。 |
| `pk_authority` | `false` | 本包只覆盖 mechanism-load 方法，不覆盖 kill-chain Pk。 |
| `deterministic_fuze_authority` | `false` | 本包不覆盖 live fuze trigger、safe-arm、target signature、delay 或 reliability。 |
| runtime descriptor | `not_created` | 不允许被运行时加载。 |

## Source 输入状态

| source group | source refs | 状态 | 用途 | gate 影响 |
|---|---|---|---|---|
| blast scaled-distance methods | `VPS-BFM-001/002/005` | candidate | `method_ref`、unit/domain criteria | 可进入方法说明；不授权 row。 |
| Kingery-Bulmash / BEC-O route | `VPS-BFM-003/014` | `pending_acquisition` | 未来 blast curve reproducibility | 未固定官方版本/rights/checksum 前不能作为 acquired input。 |
| Mott / fragmentation | `VPS-BFM-006` | candidate | fragment mass distribution method | toy benchmark only。 |
| Gurney route | `VPS-BFM-007` | `pending_acquisition` | future velocity proxy method | 未固定官方公开版本前不能作为 acquired input。 |
| penetration / ballistic-limit | `VPS-BFM-010/011/012/015`; `VPS-BFM-009` rejected | mixed candidate / pending artifact | penetration-margin method/domain check | 仅方法和域外拒绝；不支持组件概率；UFC 3-340-01 不得作为输入。 |
| spatial sampling | `VPS-BFM-013` | candidate | reproducible sphere sampling | 支持采样复现，不代表真实方向图。 |
| DDESB / blast/debris candidate references | `VPS-BFM-014/015`; `016` search lead only | candidate routes identified / artifact-rights-hash pending | blast curve and fragment/debris benchmark design | 可支撑候选 benchmark design reference；未固定官方可达性、rights、checksum/output policy 前不作为 acquired benchmark artifact。 |

## Benchmark 映射

| benchmark | 目标 | source refs | 输出 | 当前指标 | residual |
|---|---|---|---|---|---|
| `BFM-BM-001 blast_scaled_distance_curve_lock` | 固定 scaled-distance、pressure、impulse 单位、域和曲线形状 | `VPS-BFM-001/002/005/014`; `003` pending | `blast_scaled_distance_m_kg13`、`blast_overpressure_kpa`、`blast_impulse_kpa_ms` | unit round-trip、单调性、domain rejection、version trace | `BFM-RES-001`、`RES-006`、`RES-010` |
| `BFM-BM-002 mott_gurney_fragment_cloud_unit` | 固定非型号化 fragment mass / velocity toy sampling | `VPS-BFM-006`; `007` pending | fragment mass/velocity/energy distribution summaries | fixed-seed replay、positive mass/velocity、energy unit sanity、no AIM-120C truth labels | `BFM-RES-002`、`RES-005` |
| `BFM-BM-003 fragment_areal_density_spatial_sampling` | 固定空间方向采样和 witness surface areal-density 收敛 | `VPS-BFM-013` + fragment method refs | `fragment_areal_density_per_m2`、sampling convergence | isotropy、closed-surface count conservation、seed replay | `BFM-RES-003`、`RES-005` |
| `BFM-BM-004 penetration_margin_ble_crosscheck` | 固定 penetration-margin 公式形状、单位和域外拒绝 | `VPS-BFM-010/011/015`; `012` pending artifact; `009` rejected | `penetration_margin` proxy | monotonic residual velocity/margin、domain separation、incidence/domain rejection | `BFM-RES-004`、`RES-005` |
| `BFM-BM-005 integrated_near_miss_mechanism_vector_toy` | 组合 blast、fragment、areal density、penetration 和 surface-incidence 的非权威 mechanism vector | `BFM-BM-001..004` + A2 candidate scope | mechanism-load vector only | source trace completeness、unit consistency、out-of-scope rejection、no Pk/fuze/probability fields | `BFM-RES-005/006/007`、`RES-007/008/009` |
| `BFM-BM-006 source_trace_and_rights_manifest_check` | 审计 source_ref、publisher、rights、Tier、scope、checksum 计划和 authority 边界 | all `VPS-BFM-*` rows | manifest lint result | 100% required fields; pending sources not consumed; no restricted text copied | `RES-001`、`BFM-RES-006` |

## Draft Metrics

| metric | 适用 benchmark | 当前状态 | authority 影响 |
|---|---|---|---|
| `unit_roundtrip_pass` | `BFM-BM-001/004/005` | `not_run` | method validation only |
| `domain_rejection_pass` | `BFM-BM-001/004/005` | `not_run` | prevents scope leakage only |
| `fixed_seed_replay_pass` | `BFM-BM-002/003/005` | `not_run` | reproducibility only |
| `sampling_convergence_summary` | `BFM-BM-003` | `not_run` | sampler confidence only |
| `source_trace_completeness` | `BFM-BM-005/006` | `not_run` | manifest prerequisite only |
| `authority_field_absence` | all | `not_run` | ensures no accidental Pk/fuze/probability output |

并非所有 metric 都已冻结。验收门槛必须在运行 benchmark 前冻结；不得根据结果反推门槛。
当前 Stage B `effect_scale` 的 metrics / thresholds 已冻结到
[validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md](validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md)；
本 manifest 仍保持 `not_run`，并且 Stage C `component_failure_probability` 继续 deferred。

## Manifest 缺失项

| 字段 | 当前状态 | close 条件 |
|---|---|---|
| `validated_surrogate_model_ref` | missing | 指向版本化代码、配置、容器或 archive。 |
| `validation_benchmark_ref` | missing | 指向生成的 benchmark artifact 和 source manifest。 |
| `validation_artifact_sha256` | missing | benchmark 输出生成后固定 sha256。 |
| `validation_metrics_ref` | [validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md](validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md) | 保持 pre-run freeze，不得在结果生成后改写。 |
| `validation_acceptance_criteria_ref` | [validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md](validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md) | 独立 reviewer signoff 与 benchmark result table 仍需补齐。 |
| `validation_scope_ref` | [validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md](validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md) | boundary probes、scope leakage report 和 independence review 仍需补齐。 |
| `validation_scope_probe_report_ref` | [validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md](validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md) | 当前 probe 结果仍是 candidate / non-authoritative，且需要独立 review。 |
| `review_record` | missing | 独立审阅记录和 residual closeout。 |

## Recommended Run Order

1. 先运行 `BFM-BM-006` source trace / rights manifest check，禁止 pending sources 被误当 acquired input。
2. 固定或排除 Kingery-Bulmash、Gurney 等 pending sources；固定 DDESB TP-20/TP-21 artifact sha256、tool package version and allowed-output policy；保持 UFC 3-340-01 rejected。
3. 运行 `BFM-BM-001` 和 `BFM-BM-004` 的 unit/domain checks。
4. 运行 `BFM-BM-002` 和 `BFM-BM-003` 的 fixed-seed toy sampling checks。
5. 最后运行 `BFM-BM-005` integrated mechanism-vector toy benchmark，仍只输出非权威 mechanism-load vector。
6. 生成 validation report 后仍保持 `validation_status=not_run` 或 `pending/failed`，直到所有 artifact、metrics、criteria 和 residual closeout 完整。

## 当前判定

本 manifest 草案当前判定为：`candidate / not_run / non-authoritative`。它可以作为后续 benchmark 生成和审计的执行清单，但不能被 runtime 消费，不能创建 `validated_physics_surrogate` descriptor，不能设置任何 authority 字段为 true。
