# Benchmark Candidate Matrix：VPS blast_fragmentation methods

状态：`2026-05-28` 可复现 benchmark 候选矩阵。本文档只定义首个窄域 `validated_physics_surrogate` 候选包的 benchmark 组合、来源角色和准入边界；当前没有 benchmark 已运行，没有 artifact sha256，没有 validation pass 结论，不授予任何 authority。

候选 scope：`F-16C_Block50` x `AIM-120C-class/blast_fragmentation` x `beam` x `high` x `near_miss_0_35m`。

## 准入原则

- `method_ref` 和 `benchmark_dataset` 必须分离。用来定义 surrogate 的公开方法，不能又在未声明独立性的情况下当作验证数据。
- 当前 benchmark 只能是公开方法驱动的 unit / toy / cross-check；没有公开、scope 匹配、可再分发的 AIM-120C vs F-16C blast-fragmentation 外部实测 dataset。
- 所有 benchmark 都必须记录 source_ref、代码版本、配置、随机种子、单位、适用域、输出 checksum 和 residual。
- 验收门槛必须在结果生成前冻结。未冻结 criteria 时，即使跑出数值，也不能声明 validation passed。
- 所有输出默认 `non-authoritative`，不得创建 descriptor row 或设置 Pk / deterministic-fuze / effect-scale / component-probability authority。

## 候选组合矩阵

| `benchmark_id` | 名称 | 主要来源 | 支持角色 | 公共输入 | 复现计划 | 候选指标 / criteria | 独立性 | 当前状态 | admission / authority |
|---|---|---|---|---|---|---|---|---|---|
| `BFM-BM-001` | `blast_scaled_distance_curve_lock` | `VPS-BFM-001` IATG, `VPS-BFM-002` UFC, `VPS-BFM-003` Kingery-Bulmash pending, `VPS-BFM-005` Baker, `VPS-BFM-014` DDESB TP-20/BEC-O | `method_ref`, `validation_criteria`, `benchmark_design_reference`, future `reproducibility` | scaled distance axis, unit definitions, public TNT burst method family; no missile-specific charge | Implement a versioned blast module with explicit unit conversion and domain checks; after official Kingery-Bulmash / BEC-O artifacts are pinned, compare selected non-sensitive curve samples or tool outputs | unit round-trip; monotonic pressure/impulse over valid Z; reject out-of-domain Z; preserve version/sha256; zero scope leakage | Not independent if same coefficients tune the model; can be unit benchmark only unless held-out tool outputs are version-pinned | `candidate / not_run` | method and unit benchmark only; no descriptor row |
| `BFM-BM-002` | `mott_gurney_fragment_cloud_unit` | `VPS-BFM-006` Mott, `VPS-BFM-007` Gurney pending, `VPS-BFM-001` IATG, `VPS-BFM-008` Cooper | `method_ref`, synthetic `benchmark_dataset`, `validation_criteria` | non-sensitive toy casing/charge parameters selected only for numerical stability; not AIM-120C values | Generate fixed-seed fragment mass and velocity samples; compute fragment energy distribution; record config, random seed and summary statistics | distribution normalization; reproducible quantiles; positive mass/velocity; energy units; sensitivity to toy parameters; no inferred warhead count | Synthetic only; independent of real missile data but not validation of real warhead | `candidate / not_run` | can support model implementation test; not component-failure or Pk authority |
| `BFM-BM-003` | `fragment_areal_density_spatial_sampling` | `VPS-BFM-013` Marsaglia, `VPS-BFM-006/007` Mott/Gurney, `VPS-BFM-001/004/015` IATG/GICHD/DDESB TP-21 | `reproducibility`, synthetic `benchmark_dataset`, `validation_criteria`, `benchmark_design_reference` | uniform or declared directional toy fragment cloud; witness surfaces / beam-side panels; fixed seed | Sample directions on a sphere; intersect with analytic witness surfaces and coarse beam-aspect silhouette; compute `fragment_areal_density_per_m2` and convergence vs sample count | isotropy test for uniform mode; areal-density convergence; conservation of fragment count across closed surfaces; stable seed replay; explicit rejection of warhead pattern claims | Independent of physical warhead truth; validates sampler and geometry accounting only | `candidate / not_run` | may support `fragment_areal_density_per_m2` proxy reproducibility; no authoritative row |
| `BFM-BM-004` | `penetration_margin_ble_crosscheck` | `VPS-BFM-010` NASA-HDBK-8719.14, `VPS-BFM-011` Recht-Ipson, `VPS-BFM-012` MIL-STD-662 ASSIST/QuickSearch route, `VPS-BFM-015` DDESB TP-21; `VPS-BFM-009` UFC 3-340-01 rejected | `method_ref`, `validation_criteria`, synthetic `benchmark_dataset` | toy projectile/plate parameters within declared domains; no F-16 materials | Implement dimensionless penetration-margin checks with explicit material/domain labels; compare formula-shape behavior across BLE, residual-velocity, V50-threshold and debris-analysis references without sharing coefficients across domains | monotonic residual velocity / margin behavior; V50-style threshold handling; incidence/domain rejection; no coefficient migration between orbital-debris, armor, debris and aircraft domains | Cross-domain only; not an aircraft component validation | `candidate / not_run` | may support `penetration_margin` gate design; no component probability authority |
| `BFM-BM-005` | `integrated_near_miss_mechanism_vector_toy` | `BFM-BM-001` to `004` plus A2 candidate scope docs | synthetic `benchmark_dataset`, `reproducibility`, `validation_criteria` | declared toy blast-fragmentation event at `beam/high/near_miss_0_35m`; coarse non-authoritative target surface; no real warhead params | Combine blast, fragment sampling, areal-density and penetration-margin modules to emit mechanism-load vector fields only: `blast_scaled_distance_m_kg13`, `blast_overpressure_kpa`, `blast_impulse_kpa_ms`, `fragment_energy_j`, `fragment_areal_density_per_m2`, `penetration_margin`, `surface_incidence_cos` | source trace completeness; unit consistency; no Pk/fuze fields; out-of-scope axis rejection; repeatability across seeds; uncertainty summary present | Synthetic integration test; not independent real validation | `candidate / not_run` | can prepare future validation manifest shape; cannot mark calibration as completed |
| `BFM-BM-006` | `source_trace_and_rights_manifest_check` | all `VPS-BFM-*` rows | `reproducibility`, `validation_criteria` | source ledger records, version pins, rights notes, pending/rejected status | Build a manifest linter that fails missing source_ref, publisher, rights, Tier, scope, role, checksum plan or authority boundary | 100% sources have required ledger fields; pending sources cannot be used as acquired inputs; no restricted text copied | Independent administrative gate | `candidate / not_run` | prerequisite for any later validation report; no physics authority |

## Benchmark-to-schema mapping

| Future schema field / artifact | Candidate source from matrix | Required before runtime consideration | Current status |
|---|---|---|---|
| `validated_surrogate_model_ref` | code/config implementing `BFM-BM-001` to `005` | commit/container/archive, model version, units, assumptions | missing |
| `validation_benchmark_ref` | generated benchmark artifacts from `BFM-BM-001` to `006` | stable artifact path outside transient workspace, sha256, source manifest | not generated |
| `validation_metrics_ref` | metrics listed in each benchmark row | frozen definitions and result table | not defined/frozen |
| `validation_acceptance_criteria_ref` | criteria from IATG/UFC/NASA/MIL-STD plus A2 residual gates | thresholds frozen before run; reviewer signoff | not frozen |
| `validation_scope` | candidate scope in README | exact match to target/weapon/aspect/closure/miss-distance axes | documented, not validated |
| descriptor rows | none | only after full `a2.vulnerability_surrogate_validation.v1` manifest passes | not allowed |

## Candidate acceptance criteria draft

These criteria are draft-only and must be frozen in a future validation report before any run:

| `criteria_id` | Applies to | Draft check | Source basis | Authority effect |
|---|---|---|---|---|
| `BFM-CRIT-001` | all benchmarks | source_ref, publisher, rights, Tier, scope, role and non-authority boundary recorded for every input | A2 source admission rules + `BFM-BM-006` | fails manifest only; no runtime authority |
| `BFM-CRIT-002` | blast benchmark | unit conversion and scaled-distance domain checks are explicit and tested | IATG/UFC/Kingery-Bulmash source chain | method validation only |
| `BFM-CRIT-003` | fragment cloud benchmark | fixed seed replay reproduces sample statistics and no parameter is labeled as AIM-120C truth | Mott/Gurney/IATG/Cooper | method validation only |
| `BFM-CRIT-004` | areal-density benchmark | sampling isotropy/convergence is demonstrated for uniform toy mode; directional pattern remains open residual | Marsaglia + areal-density source chain | reproducibility only |
| `BFM-CRIT-005` | penetration benchmark | orbital-debris, armor, debris-analysis and residual-velocity formula domains remain separated and out-of-domain inputs fail closed | NASA-HDBK/Recht-Ipson/MIL-STD/DDESB TP-21; UFC 3-340-01 explicitly rejected | method gate only |
| `BFM-CRIT-006` | integrated benchmark | output contains mechanism-load vector only and omits Pk, deterministic fuze, component probability and calibrated effect scale | A2 evidence schema and candidate README | prevents accidental authority |

## Current residual blocks

| `residual_id` | Blocks | Description | Close condition |
|---|---|---|---|
| `BFM-RES-001` | `BFM-BM-001` | Kingery-Bulmash official public source/version and BEC-O/CONWEP comparison route not pinned | stable official source_ref, rights, checksum and allowed comparison samples |
| `BFM-RES-002` | `BFM-BM-002` | Gurney BRL-405 official public source not pinned | stable official source_ref and rights, or keep IATG/Cooper as secondary method navigator |
| `BFM-RES-003` | `BFM-BM-003` | Real warhead directional pattern and casing breakup model unavailable | do not close within this package; keep toy uniform/directional modes labeled non-authoritative |
| `BFM-RES-004` | `BFM-BM-004` | Penetration formula domains do not match aircraft component fragility; UFC 3-340-01 is rejected and cannot fill this gap | require separate admitted public aircraft/material or conventional fragment benchmark before any component-probability discussion |
| `BFM-RES-005` | `BFM-BM-005` | F-16C component geometry/material/occlusion and AIM-120C warhead parameters unavailable | require separately admitted geometry/warhead assumptions and sensitivity analysis |
| `BFM-RES-006` | all | Acceptance thresholds are not frozen and no artifact sha256 exists | future validation report must freeze criteria, run benchmarks and record hashes |
| `BFM-RES-007` | all | Pk and deterministic fuze are outside this mechanism-load package | cannot close here; requires independent Pk/fuze evidence chain |

## Recommended next step

Create a future docs-only or code+docs validation scaffold only after this source package is reviewed:

1. Freeze `BFM-BM-006` ledger/rights linter.
2. Pin pending Kingery-Bulmash and Gurney sources; freeze DDESB TP-20/TP-21 artifact hashes and tool-output policy; explicitly exclude any source that remains pending.
3. Implement `BFM-BM-001` to `004` as unit/toy benchmarks with fixed seeds and no real weapon claims.
4. Generate a validation report with sha256 and reviewer notes, still `validation_status=not_run` or `failed/pending` until criteria are met.
5. Only after a full `a2.vulnerability_surrogate_validation.v1` manifest passes may a separate discussion consider a limited `validated_physics_surrogate` descriptor; Pk and deterministic fuze remain out of scope.
