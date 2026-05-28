# Benchmark Gap Update：guidance / evasion public benchmarks

状态：`2026-05-28 benchmark-gap / guidance / non-authoritative`。

本文档是 [source_ledger.zh.md](source_ledger.zh.md) 和 [benchmark_matrix.zh.md](benchmark_matrix.zh.md) 的 gap 补充，只说明公开方法如何进入 benchmark design。它不运行测试，不生成 artifact，不写运行时配置，不授予 runtime authority。

## Benchmark family gap table

| `family_id` | 目标 benchmark | 推荐来源 | 可立即采用的引用角色 | 必须补齐 | 当前 admission |
|---|---|---|---|---|---|
| `GB-FAM-001` | `pn_classical_miss_distance_v1` | `GEB-SRC-001/002/008/011/019` | `method_reference` for PN/LOS/miss-distance; `benchmark_design_reference` for Lukenbill/NASA generic fly-out once artifact pinned | Lukenbill PDF sha256/OCR, scenario parameters, dt/integrator, navigation-ratio sweep, truth/runtime closest-approach metric, output sha256 | `design_ready / artifact_missing` |
| `GB-FAM-002` | `apn_target_accel_v1` | `GEB-SRC-003/007/020/001` | `method_reference` and `validation_criteria_reference` for target-acceleration and filter requirements | target acceleration process, estimator/filter state, covariance/proxy output, APN vs biased-PN naming audit | `criteria_ready / estimator_manifest_missing` |
| `GB-FAM-003` | `miss_distance_lag_noise_v1` | `GEB-SRC-016/017/019/004/006` | `method_reference` for lag/noise/theoretical miss-distance dynamics | old-scope flag, noise distribution, sample rate, autopilot tau/lag, command-vs-achieved acceleration outputs | `design_ready / scope_limited` |
| `GB-FAM-004` | `terminal_evasion_sweep_v1` | `GEB-SRC-009/010/012/014/015/008` | `benchmark_design_reference_pending_artifact` for jink/switching/bang-bang/linearized evasion timing | official fulltext or clear abstract boundary, rights/hash/OCR, scenario axes, maneuver start/switch time, old-scope validity flag | `pending_acquisition` |
| `GB-FAM-005` | `seeker_filter_noise_v1` | `GEB-SRC-004/007/016/017/021` | `method_reference` for filter/noise; Stone Soup as pinned scaffold only | commit/tag/dependency lock, measurement model, noise distribution, dropout/memory manifest, covariance/proxy output, output hash | `design_ready / scaffold_pin_required` |
| `GB-FAM-006` | `track_memory_fov_v1` | `GEB-SRC-002/004/011` + A2 internal evidence route | `validation_criteria_reference` for seeker state and track continuity | local/nonlocal contact policy, FOV/lock range, memory timeout, ballistic transition, miss-distance output | `internal_generated_candidate` |
| `GB-FAM-007` | `dynamic_flyout_vs_envelope_v1` | `GEB-SRC-011/005/018` | `benchmark_design_reference` for generic dynamic fly-out and architecture comparison | launch/test grid, reason-for-miss taxonomy, compute-cost note, dynamic/static disagreement metrics, output hash | `design_ready / old_generic_scope` |
| `GB-FAM-008` | `sixdof_module_boundary_v1` | `GEB-SRC-005/006/013/018` | `validation_criteria_reference` for module boundaries | AD769595 and MIL-HDBK official artifact pin, distribution statement, state vector, integrator, module IO manifest | `pending_artifact` |
| `GB-FAM-009` | `a2_effects_bridge_v1` | A2 internal route + `GEB-SRC-001/005/011/019` as method references | `validation_criteria_reference` for miss-distance/effects chain fields | event-field manifest, miss distance / closure / local detonation / fuze evidence / DamageReport outputs | `internal_generated_candidate / no_runtime_authority` |

## Source status for blocked or limited entries

| source group | Status | Use allowed now | Blocked use |
|---|---|---|---|
| NTIS-only records (`GEB-SRC-009`, `013`, parts of `014`) | `pending_acquisition` due NTIS access block or no artifact hash | search and design notes, source_id references with pending flag | table extraction, scenario parameters, code artifact claims |
| NPS / Calhoun handles (`GEB-SRC-008`, `012`) | handle route stable but official artifact hash/OCR not fixed | benchmark design outline and official handle reference | copying thesis figures/tables or declaring benchmark dataset acquired |
| NASA/NACA NTRS (`GEB-SRC-011`, `016`, `017`) | public metadata checked | method/design criteria for generic fly-out and old noise/miss-distance cases | modern AAM seeker/fly-out validation, 可消费运行时证据 |
| AIAA/IEEE/Springer DOI entries (`GEB-SRC-007`, `014`, `015`, `019`; `GMD-SRC-008`) | DOI metadata checked; fulltext rights pending | bibliographic source_ref, method/criteria labels | fulltext-derived numeric data without lawful artifact manifest |
| BUAA APN article (`GEB-SRC-020`) | public article page checked | APN criteria source and cross-check | unreviewed formula transcription or dataset |
| Stone Soup (`GEB-SRC-021`) | MIT license and tags checked | reproducibility scaffold after commit/tag pin | missile seeker performance evidence |

## Minimum artifact manifest before any generated benchmark

```yaml
benchmark_id: <GB-FAM package id>
status: generated_non_authoritative
source_refs:
  - <GEB-SRC-*>
source_artifacts:
  - source_id: <GEB-SRC-*>
    official_url: <URL/DOI/handle/NTRS>
    acquisition_date: <YYYY-MM-DD>
    rights: <public_page_only | public_pdf | paid_fulltext | pending>
    sha256: <required if artifact body is used>
    ocr_or_transcription: <none | pending | audited>
scenario_manifest:
  geometry: <head_on | tail_chase | beam | off_boresight | old_scope_evasion>
  guidance_law: <PN | APN_with_estimator | CLOS | hybrid | declared surrogate>
  seeker_filter: <none | declared_noise_filter_dropouts>
  target_maneuver: <straight | turn | jink | switch | bang_bang | declared>
numerics:
  dt_s: <required>
  integrator: <required>
  seed: <required or deterministic replay>
outputs:
  - truth_min_dist_m
  - runtime_min_dist_m
  - time_of_closest_approach_s
  - los_rate_rad_s
  - closing_speed_mps
  - commanded_accel_mps2
  - achieved_accel_mps2
  - track_state_or_filter_proxy
output_sha256: <required>
residuals:
  - <gap ids from this file>
authority:
  runtime: none
```

## Gap register

| `gap_id` | Applies to | Description | Close condition |
|---|---|---|---|
| `GB-GAP-001 source-artifact-hash` | all | Source refs are pinned more strongly than artifacts; most source bodies do not have sha256/OCR records. | Record official artifact, acquisition date, rights, sha256 and transcription audit before using body content. |
| `GB-GAP-002 output-hash` | all generated packages | No generated benchmark outputs are retained or hashed. | Add output manifest and sha256 after deterministic generation. |
| `GB-GAP-003 fulltext-rights` | AIAA/IEEE/Springer/NTIS/NPS | Some sources are only DOI/abstract/handle records. | Lawful access plus rights note; otherwise stay method/design reference only. |
| `GB-GAP-004 old-simplified-scope` | Lukenbill, Straight, McNamara, Swee, Shinar, Ben-Asher, NASA/NACA | Old 2D, beam-rider, simplified or generic cases do not represent modern AAM. | Mark old/generic scope in every package and block model-family extrapolation. |
| `GB-GAP-005 apn-estimator` | APN | APN requires target acceleration estimate or equivalent filter/model state. | Output estimator/filter state and residual; otherwise label as PN/biased PN. |
| `GB-GAP-006 seeker-ecm` | seeker/filter/noise | Public sources support noise/filter/track proxy, not ECM/ECCM/clutter/decoy truth. | Separate ECM evidence gate; keep current benchmark to track-quality proxy. |
| `GB-GAP-007 validation-independence` | all | Self-generated toy data from method sources is not external validation. | Separate unit checks from external calibration; current package remains non-authoritative. |
| `GB-GAP-008 runtime-authority-closed` | all | No external calibration dataset or validated surrogate manifest exists in this scope. | Future gate must include full source/ref/provenance/rights/scope/artifact/residual closeout. |

## Not admitted sources and uses

| `not_admitted_id` | Item | Reason | Handling |
|---|---|---|---|
| `GB-NOT-001` | Third-party thesis/article PDF mirrors | Rights, completeness and checksum are not established. | Do not use; prefer DOI, NTRS, NTIS, Calhoun, VT or publisher pages. |
| `GB-NOT-002` | Forum/game/community missile data | Provenance and parameters are not auditable and may be gameplay-balanced. | `sanity_check_only` at most; not benchmark design input. |
| `GB-NOT-003` | Single hit-probability, lethal-radius or fuse-radius tables | Missing scope axes, provenance, rights and validation manifest. | Reject for guidance/evasion benchmark and runtime descriptor. |
| `GB-NOT-004` | Controlled tool outputs or restricted manuals | May be restricted or non-redistributable. | Do not copy, summarize into parameters or use as source. |
| `GB-NOT-005` | NASA generic fly-out probability discussion as A2 runtime probability | Scope mismatch and no A2 calibration manifest. | Only use dynamic fly-out/miss-distance/test-matrix ideas. |

## Design priority

| priority | package | Reason | Hard stop |
|---|---|---|---|
| P0 | `pn_classical_miss_distance_v1` | Most source refs are stable and method scope is narrow. | Do not use Lukenbill body content until artifact hash/OCR is pinned. |
| P1 | `seeker_filter_noise_v1` | JHU/APL, Singer and Stone Soup can define proxy benchmark shape. | Do not claim seeker/ECCM performance. |
| P1 | `terminal_evasion_sweep_v1` | Directly covers terminal evasion timing, but source acquisition is weaker. | Keep pending until AFIT/NPS/AIAA artifact rights are clean. |
| P2 | `dynamic_flyout_vs_envelope_v1` | NASA generic model supports comparison architecture. | Do not import probability conclusions. |
| P2 | `sixdof_module_boundary_v1` | Useful manifest shape for later high-fidelity modules. | Keep NTIS/MIL-HDBK artifacts pending. |
