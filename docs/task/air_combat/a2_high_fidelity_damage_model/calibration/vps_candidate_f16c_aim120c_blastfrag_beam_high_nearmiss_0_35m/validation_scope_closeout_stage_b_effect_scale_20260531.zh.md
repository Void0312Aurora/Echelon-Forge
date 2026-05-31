# Validation Scope Closeout - Stage B Effect Scale

状态：`author_side_scope_closeout_complete / non-authoritative / release_blocked / stage_b_effect_scale_only`。

本文档固化 Stage B `effect_scale_authority_only` 的 near-miss bucket closeout、
`beam/high` closure scope closeout，以及 scope / independence 的剩余 release blocker。
它不创建 runtime descriptor，不授予 authority，也不关闭 independent review。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `scope_closeout_status` | `author_side_scope_closeout_complete_release_blocked` |
| `primary_release_scope` | `effect_scale_authority_only` |
| `scope_probe_ref` | [validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md](validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md) |
| `run_manifest_ref` | [validation_run_manifest_stage_b_effect_scale_20260531.zh.md](validation_run_manifest_stage_b_effect_scale_20260531.zh.md) |
| `closeout_tool_ref` | [a2_blastfrag_stage_b_release_closeout.py](../../../../../../tools/maintenance/a2_blastfrag_stage_b_release_closeout.py) |

## 2. Near-Miss Bucket Closeout

当前 `SCP-PROBE-001` 已形成三点 author-side result table：

| `standoff_m` | `runtime_miss_distance_bucket` | `blast_scaled_distance_m_kg13` | `fragment_areal_density_per_m2` | `blast_impulse_kpa_ms_proxy` |
|---:|---|---:|---:|---:|
| `0.25` | `near_miss` | `0.0921007875` | `2.3057105594` | `1962.6229165638` |
| `0.35` | `near_miss` | `0.1289411025` | `2.2375438053` | `1818.2329693285` |
| `0.45` | `near_miss` | `0.1657814174` | `2.1753565911` | `1692.8508813403` |

| metric | 当前结果 |
|---|---|
| `blast_scaled_distance_monotonic_increasing_pass` | `true` |
| `fragment_areal_density_monotonic_decreasing_pass` | `true` |
| `runtime_bucket_consistent_pass` | `true` |
| `anchor_present` | `true` |

`RES-007` 当前 gate result：

> `author_scope_closeout_passed_pending_independent_review`

这意味着 near-miss bucket 已不再只是单点叙述；但它仍不是完整子桶 authority，
release 仍被 bucket sensitivity 与 independent reviewer audit 阻塞。

## 3. Beam / High Closure Scope Closeout

当前 `SCP-PROBE-002` 已形成 closure 三点 author-side result table：

| `closure_mps` | `blast_scaled_distance_m_kg13` | `fragment_areal_density_per_m2` | `blast_impulse_kpa_ms_proxy` | `fragment_energy_j_proxy` |
|---:|---:|---:|---:|---:|
| `700` | `0.1289411025` | `2.1480420531` | `1772.7771450953` | `7691.5615714027` |
| `900` | `0.1289411025` | `2.2375438053` | `1818.2329693285` | `8038.5061543833` |
| `1100` | `0.1289411025` | `2.3270455575` | `1863.6887935617` | `8393.1039266943` |

| metric | 当前结果 |
|---|---|
| `closure_label_probe_executed` | `true` |
| `mechanism_response_active` | `true` |
| `candidate_closure_sensitive_response_observed` | `true` |
| `runtime_bucket_consistent_pass` | `true` |
| `res008_closed_by_probe` | `false` |
| `independent_review_complete` | `false` |

当前 `SCP-PROBE-003` aspect guard：

| 类别 | 标签 |
|---|---|
| accepted | `beam` |
| rejected | `head_on`, `tail_chase`, `high_off_boresight`, `direct_hit`, `closure_bucket != high`, `weapon_family != blast_fragmentation` |

`RES-008` 当前 gate result：

> `author_scope_closeout_passed_pending_independent_review`

这意味着 `beam/high` scope guard 与 candidate closure-sensitive response 已有 author-side closeout；
但 closure response 仍是 candidate surrogate 级观察，不是 reviewed physical closure authority。

## 4. Independence Scope Trace

| benchmark | independence class | 当前 release 角色 | 当前 forbidden claim |
|---|---|---|---|
| `BFM-BM-001` | `partial_independent_method_only` | unit/domain lock | external blast truth |
| `BFM-BM-002` | `synthetic_only` | deferred fragment sanity | AIM-120C fragment truth |
| `BFM-BM-003` | `independent_for_sampler_replay_not_for_target_truth` | sampler reproducibility / convergence | true F-16 exposure geometry |
| `BFM-BM-004` | `partial_independent_method_only` | deferred penetration domain hygiene | aircraft component penetration truth |
| `BFM-BM-005` | `not_independent_real_validation` | integrated mechanism-load hygiene only | independent surrogate validation / authority release |
| `BFM-BM-006` | `administratively_independent` | source trace / rights gate | physics validation by itself |

`RES-012` 当前 gate result：

> `author_independence_trace_complete_pending_independent_review`

## 5. 当前 Scope Gate Result Summary

| residual | author-side result | release result |
|---|---|---|
| `RES-007` | closeout complete | `blocked_pending_independent_review` |
| `RES-008` | closeout complete | `blocked_pending_independent_review` |
| `RES-012` | dependency trace complete | `blocked_pending_independent_review` |

## 6. 当前判定

Stage B scope closeout 已把 near-miss bucket、beam/high closure scope 和 out-of-scope rejection
机器化固定到 author-side 可审状态；但 `RES-007/008/012` 仍不得关闭为 release-ready，
因为 independent review 和 scope leakage audit 仍未完成。
