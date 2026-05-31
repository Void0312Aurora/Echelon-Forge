# RES-002 Scoped Release Identity Gate - 2026-05-31

状态：`scoped_res002_identity_pass_non_authoritative / candidate / no-authority`。

本文档记录 `RES-002 surrogate identity` 的窄域 scoped package identity freeze gate。对应工具为
[a2_blastfrag_res002_scoped_release_identity_gate.py](/home/void0312/Workshop/CMO/tools/maintenance/a2_blastfrag_res002_scoped_release_identity_gate.py)。

本 gate 只冻结 A2 candidate package 的 repo-contained identity surface，不提升 validation status，不授予
`effect_scale_authority`、`component_failure_probability_authority`、`pk_authority`
或 `deterministic_fuze_authority`，也不编辑 `residual_register.zh.md`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.res002_scoped_release_identity_gate.v1` |
| `review_target` | `res_002_scoped_package_identity_freeze` |
| `gate_status` | `scoped_res002_identity_pass_non_authoritative` |
| `scoped_identity_decision` | `narrow_scoped_identity_pass` |
| `retained_gate_artifact` | `retained_artifacts/res002_scoped_release_identity_20260531/res002_scoped_release_identity_gate.json` |
| `retained_gate_artifact_sha256` | `ef4e38ccf457c80a96151c20260a52d3a5f6561431d571bc6d32f63983855bda` |
| `retained_manifest` | `retained_artifacts/res002_scoped_release_identity_20260531/manifest.json` |
| `retained_manifest_sha256` | `b8900e7410d3a52e1a4b292a3b9a62563d7f2578dabfe5c614e5a4727b628fd7` |
| `retained_input_artifact_count` | `26` |
| `relevant_file_hash_count` | `16` |
| `scoped_tmp_anchor_count` | `0` |

## 2. 判定

当前判定为窄域通过：

- Stage B / Stage C retained artifacts、source payload pack 和 provenance identity review 均已由 repo 内 retained path 消费。
- 当前 relevant file set 以 sha256 绑定；不把 `HEAD` 单独声明为完整 release identity。
- scoped identity surface 的绝对 `/tmp` anchor scan 结果为 `0`。
- 已记录 dirty worktree note；当前 standards policy 未要求全局 clean worktree，因此 unrelated dirty worktree 不阻止本 scoped identity freeze。
- 如后续 policy 明确要求 globally clean repo，本 gate 必须 fail closed，原因是当前 `git status` 非 clean。

## 3. 保留范围

本 gate 消费以下 retained artifact 目录：

| retained key | 角色 |
|---|---|
| `stage_b_effect_scale_20260530` | Stage B author-side effect-scale retained pack |
| `stage_b_effect_scale_20260531` | Stage B release closeout retained surface |
| `stage_b_independent_review_20260531` | Stage B independent review retained surface |
| `stage_c_component_probability_20260530` | Stage C component-probability retained pack |
| `stage_c_fragility_benchmark_20260531` | Stage C fragility benchmark retained surface |
| `stage_c_fragility_review_20260531` | Stage C fragility review retained surface |
| `source_payload_pack_20260531` | source payload pack and payload hashes |
| `provenance_identity_review_20260531` | RES-001/RES-002 provenance identity review blocker surface |

## 4. Authority Guards

所有 authority guards 保持 `false`：

| guard | 值 |
|---|---|
| `stock_descriptor_created` | `false` |
| `stock_database_authority_granted` | `false` |
| `runtime_authority_granted` | `false` |
| `effect_scale_authority_released` | `false` |
| `component_failure_probability_authority_released` | `false` |
| `pk_authority_released` | `false` |
| `deterministic_fuze_authority_released` | `false` |
| `validation_status_promoted` | `false` |
| `residual_register_edited` | `false` |

## 5. 非目标与剩余路径

- 本 gate 不关闭 `RES-001`，不关闭 `RES-003` 至 `RES-014`。
- 本 gate 不声明 global clean release identity；dirty worktree 仍存在。
- 本 gate 不替代 independent reviewer signoff。
- 本 gate 不把 candidate retained artifacts 提升为 runtime / stock authority。

## 6. 复核命令

```bash
python3 tools/maintenance/a2_blastfrag_res002_scoped_release_identity_gate.py
pytest -q tests/architecture/test_a2_blastfrag_res002_scoped_release_identity_gate.py
```
