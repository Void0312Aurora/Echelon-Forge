# Validation Scope And Independence Manifest - Stage B Effect Scale

状态：`frozen_pre_run / candidate / non-authoritative / stage_b_effect_scale_only`。

本文档用于冻结当前候选包在 Stage B `effect_scale_authority` 评审中的 scope 轴定义、boundary probe 计划和 benchmark/input independence 边界。

它不提供 validation result，不创建 runtime descriptor，也不授予 `effect_scale_authority`、`component_failure_probability_authority`、`pk_authority` 或 `deterministic_fuze_authority`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `scope_manifest_status` | `frozen_pre_run_stage_b_effect_scale_only` |
| `primary_release_scope` | `effect_scale_authority_only` |
| `independence_status` | `documented_pre_run_pending_result_audit` |
| `runtime_bucket_note` | `candidate near_miss_0_35m maps to runtime coarse bucket near_miss and must not be over-claimed as a validated sub-bucket` |
| `review_status` | `author_frozen_pending_independent_review` |

## 2. 冻结的 scope 轴

| `axis_id` | 冻结值 / 定义 | 当前 anchor | boundary probe plan | 当前不允许的外推 |
|---|---|---|---|---|
| `target_type` | `F-16C_Block50` | stock candidate target in repo DB | none in Stage B | 其他机型、其他 F-16 变型 |
| `weapon_class` | `AIM-120C-class` | repo candidate AIM-120C-family envelope | none in Stage B | AIM-9X、R-77、其他 missile family |
| `weapon_family` | `blast_fragmentation` | warhead family row gate only | none in Stage B | `continuous_rod`、`hit_to_kill` |
| `aspect_bucket` | `beam` = 仅 lateral witness geometry / side-on exposure mode；不是 nose/tail/full-3D target aspect truth | beam-side witness panel | report `beam` center case；显式拒绝 nose/tail/direct-hit 外推 | head-on、tail-chase、high-off-boresight、全向外推 |
| `closure_bucket` | `high` = 当前 candidate benchmark 的高闭合速度标签，不等于全域 closure truth | `closure_mps = 900` | boundary notes at `700 / 900 / 1100 mps`; 结果表必须显式记录 | `medium/low closure`、现代 seeker/target terminal behavior truth |
| `miss_distance_bucket` | `near_miss_0_35m` = 当前 candidate scope label，表示 0.35 m 近失 anchor；不是已验证的完整子桶 | `standoff_m = 0.35` | boundary probes at `0.25 / 0.35 / 0.45 m`; direct-hit 明确排除 | `direct_hit`、大于 0.45 m 的 near-miss、把单点近失当成整桶真值 |

## 3. Out-of-scope Rejection Rules

以下标签当前必须继续显式拒绝：

| `rejection_id` | 标签 | 原因 |
|---|---|---|
| `SCP-REJ-001` | `head_on` | 不属于当前 beam-stage candidate。 |
| `SCP-REJ-002` | `tail_chase` | 不属于当前 beam-stage candidate。 |
| `SCP-REJ-003` | `high_off_boresight` | 不属于当前 beam-stage candidate。 |
| `SCP-REJ-004` | `direct_hit` | 当前 Stage B 只处理 `near_miss_0_35m`。 |
| `SCP-REJ-005` | `closure_bucket != high` | 当前只冻结 `high`。 |
| `SCP-REJ-006` | `weapon_family != blast_fragmentation` | 当前只冻结 blast-fragmentation。 |

## 4. Boundary Probe Plan

下列 probe 计划当前已经进入“已执行并有第一版结果表”的状态，但它们仍然只是
candidate scope audit，不等于 validated physical truth：

| `probe_id` | 轴 | probe 集合 | 目的 | 当前状态 |
|---|---|---|---|---|
| `SCP-PROBE-001` | miss distance | `0.25 / 0.35 / 0.45 m` | 检查 `near_miss_0_35m` 是否只是单点叙述 | `executed_candidate_probe_recorded` |
| `SCP-PROBE-002` | closure | `700 / 900 / 1100 mps` | 检查 `high` 标签是否在 candidate 带内稳定 | `executed_candidate_probe_recorded` |
| `SCP-PROBE-003` | aspect guard | `beam only` + rejection log for nose/tail/direct-hit | 防止 scope leakage | `executed_candidate_probe_recorded` |

当前第一版结果表见
[validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md](validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md)。

## 5. Benchmark / Input Independence Matrix

| `benchmark_id` | 主要输入角色 | 是否独立于模型输入 | 当前 release 角色 | 当前不能宣称 |
|---|---|---|---|---|
| `BFM-BM-001` | public method chain for blast scaled-distance / overpressure / impulse | `partial_independent_method_only` | unit/domain lock | 外部实测 blast truth |
| `BFM-BM-002` | synthetic fragment cloud from public method chain | `synthetic_only` | fragment sanity | AIM-120C fragment truth |
| `BFM-BM-003` | synthetic sampler + repo-authored witness geometry | `independent_for_sampler_replay_not_for_target_truth` | sampler reproducibility / convergence | F-16 true exposure geometry |
| `BFM-BM-004` | toy penetration-margin formulas with explicit domain separation | `partial_independent_method_only` | domain rejection hygiene | aircraft component fragility truth |
| `BFM-BM-005` | integration of `BFM-BM-001..004` + repo candidate scope | `not_independent_real_validation` | integrated mechanism-load hygiene only | validated surrogate truth、authority release by itself |
| `BFM-BM-006` | source ledger / rights / candidate docs | `administratively_independent` | admission and trace gate | physics validation |

## 6. Independence Guard Rules

| `guard_id` | 规则 |
|---|---|
| `IND-GUARD-001` | 不得把同一组调参/拟合输入同时写成 validation pass 证据。 |
| `IND-GUARD-002` | `BFM-BM-005` 只能作为 integrated hygiene benchmark，不能单独支撑 authority release。 |
| `IND-GUARD-003` | repo-authored target geometry 只能支撑 witness geometry 和 integration bookkeeping，不能冒充真实 F-16 内部 vulnerability truth。 |
| `IND-GUARD-004` | candidate scope label `near_miss_0_35m` 与 runtime coarse bucket `near_miss` 必须同时记录，防止把 coarse runtime event 误写成 validated sub-bucket authority。 |

## 7. 对 residual 的推进含义

本文档新增后，当前状态应解释为：

- `RES-007`：从“bucket 未定义”推进到“bucket anchor、boundary probes 与第一版结果表都已存在，但独立 review 仍缺”。
- `RES-008`：从“beam/high 轴未固化”推进到“轴定义、rejection rules、第一版 boundary audit 结果与 candidate closure-sensitive response 都已存在，但该响应仍 non-authoritative 且未独立 review”。
- `RES-012`：从“benchmark/input separation 未证明”推进到“independence 边界与第一版结果表都已成文，但尚无独立 review 与结果级审计”。

它们都**没有**因为本文存在而关闭。

## 8. 当前判定

当前判定为：

> `scope axes and independence boundaries are frozen for Stage B effect-scale-only review; first boundary-probe result tables now exist, but independent review and result-level closeout are still pending`.
