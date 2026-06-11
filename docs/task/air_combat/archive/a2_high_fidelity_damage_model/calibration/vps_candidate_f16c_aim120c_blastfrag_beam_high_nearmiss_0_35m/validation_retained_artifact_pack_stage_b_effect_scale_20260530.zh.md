# Validation Retained Artifact Pack - Stage B Effect Scale

状态：`author_retained_candidate_artifacts_only / candidate / non-authoritative`。

本文档记录当前 Stage B `effect_scale_authority_only` 候选包已经保留的 canonical
author-side retained artifact pack。它来自
`tools/maintenance/damage_model.py candidate-artifacts effect-scale-retained-pack` 写入的 repo 内
JSON 产物，用来固定当前 candidate evidence chain；它不是 stock authority，
不是 independent validation，也不关闭 `RES-002 surrogate identity`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.stage_b_retained_artifact_pack.v1` |
| `pack_status` | `author_retained_candidate_artifacts_only` |
| `retention_scope` | `stage_b_effect_scale_author_side_candidate_only` |
| `runtime_origin` | `no_stock_runtime_descriptor_author_side_artifacts_only` |
| `review_surface` | `author_side_stage_b_effect_scale_candidate_only` |
| `stage_c_component_probability_artifacts_present` | `false` |
| `manifest_ref` | `docs/task/air_combat/archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/retained_artifacts/stage_b_effect_scale_20260530/manifest.json` |
| `retained_artifact_count` | `4` |
| `stock_runtime_action` | `forbidden` |

## 2. Retained Pack 目录与 Artifact Inventory

当前 retained pack 目录为：

`docs/task/air_combat/archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/retained_artifacts/stage_b_effect_scale_20260530/`

| `artifact_key` | 文件 | 当前状态 | 角色 |
|---|---|---|---|
| `validation_scaffold_snapshot` | `validation_scaffold_snapshot.json` | `not_run` | 固定当前 validation scaffold 输入、benchmarks 与 non-authoritative guards |
| `scope_boundary_probe_snapshot` | `scope_boundary_probe_snapshot.json` | `candidate_non_authoritative_scope_probe_results` | 固定当前 scope boundary probe 表面 |
| `stage_b_effect_scale_snapshot` | `stage_b_effect_scale_snapshot.json` | `candidate_non_authoritative_stage_b_snapshot` | 固定当前 frozen hard-gate snapshot |
| `stage_b_validation_result_pack` | `stage_b_validation_result_pack.json` | `candidate_non_authoritative_stage_b_result_pack` | 固定当前统一 result pack、artifact hashes 与 independence audit |

## 3. Release Boundary Fields

retained `manifest.json` 现在对每个 artifact 都固定了 `origin_class`、`allowed_claim`
和 `forbidden_claim`，用于防止 author-side retained pack 被误读为 release artifact：

| `artifact_key` | `origin_class` | 不允许的叙述摘要 |
|---|---|---|
| `validation_scaffold_snapshot` | `author_side_validation_scaffold_snapshot_only` | independent validation / stock runtime authority / component-probability release / Pk / deterministic-fuze authority |
| `scope_boundary_probe_snapshot` | `author_side_scope_boundary_probe_only` | reviewed closure physics / stock runtime authority / component-probability release / Pk / deterministic-fuze authority |
| `stage_b_effect_scale_snapshot` | `author_side_stage_b_hard_gate_snapshot_only` | release readiness / stock runtime authority / component-probability release / Pk / deterministic-fuze authority |
| `stage_b_validation_result_pack` | `author_side_stage_b_result_pack_only` | independent validation result / stock runtime authority / component-probability release / Pk / deterministic-fuze authority |

## 4. 它如何支撑 Surrogate Identity

当前 retained pack 只支持以下更精确的 author-side 口径：

- 当前 Stage B candidate surface 不再只靠 `/tmp` author snapshot 指针；
- 当前 scaffold / scope probe / Stage B snapshot / result pack 已有 repo 内的 canonical retained JSON；
- 当前 surrogate identity 可以写成 `repo_commit + relevant file hashes + retained artifact pack` 的 author-side identity surface。

它仍然**不**支持：

- release-grade reproducibility claim；
- clean release candidate identity；
- independent validation completion；
- stock runtime authority。

## 5. 它如何支撑 Release / Readiness Audit

当前 retained pack 的作用是把“可复跑 author-side 结果面”固定成 repo 内审阅入口，便于：

- release readiness gate 不再只看到 dirty worktree，而能同时看到当前 retained evidence chain 已存在；
- candidate bundle 在 package-level summary 里明确引用 retained evidence，而不是只引用临时输出；
- reviewer 在不运行脚本的情况下直接检查当前 Stage B candidate surface 的 JSON 入口。

这仍然不等于 release ready。release-ready surrogate identity 还需要 clean release-state、
更严格的 identity record 与独立评审闭环。

## 6. Non-Authoritative Guards

当前 retained pack 必须保持以下边界：

- 不创建 runtime descriptor；
- 不授予 `effect_scale_authority`；
- 不授予 `component_failure_probability_authority`；
- 不授予 `Pk`；
- 不授予 deterministic fuze authority；
- 不把 author-side retained evidence pack 叙述成 stock runtime authority。
- 不把 Stage B retained pack 混入 Stage C component probability release。

## 7. 生成工具与命令

推荐命令：

```bash
python3 tools/maintenance/damage_model.py candidate-artifacts effect-scale-retained-pack
python3 tools/maintenance/damage_model.py candidate-artifacts package-bundle
python3 tools/maintenance/damage_model.py release-governance effect-scale-readiness
python3 -m pytest -q tests/architecture/damage_model/test_candidate_artifact_contracts.py
```

## 8. 当前判定

当前判定为：

> `the Stage B package now retains a canonical author-side artifact pack inside the repo, but that retained evidence chain remains non-authoritative and does not by itself close surrogate identity or release readiness`.
