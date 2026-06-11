# Validation Release Provenance Closeout Gate - 2026-05-31

状态：`blocked / candidate / non-authoritative / release_provenance_closeout_lane`。

本文档记录 `RES-001 source provenance` 与 `RES-002 surrogate identity` 在 shared provenance / identity gate 之后的细分 closeout gate。对应工具为
[damage_model.py](../../../../../../tools/maintenance/damage_model.py) `release-governance provenance-closeout`。

本文档不创建 runtime descriptor，不授予 `effect_scale_authority`、`component_failure_probability_authority`、`pk_authority` 或 `deterministic_fuze_authority`，也不关闭 Stage B release gate 或 Stage C fragility gate。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.release_provenance_closeout_gate.v1` |
| `review_target` | `res_001_002_release_provenance_closeout_lane` |
| `readiness_level` | `author_side_subitems_present_but_release_grade_closeout_blocked` |
| `gate_status` | `blocked_non_authoritative_release_provenance_closeout_candidate` |

## 2. Closeout 子项

| `check_id` | residual | closeout surface | author-side 是否满足 | release-grade 是否满足 | 当前判定 |
|---|---|---|---|---|---|
| `CLOSEOUT-RES001-001` | `RES-001` | `retained_source_artifact` | yes | no | DENIX public artifacts 已 externally verified 并固定 sha256，但 artifact status 仍含 `retention_pending`，且没有 release-retained source artifact pack。 |
| `CLOSEOUT-RES001-002` | `RES-001` | `allowed_output_policy` | yes | no | candidate-side forbidden outputs 与 forbidden release action 已显式写出，但没有 release-grade allowed-output policy status。 |
| `CLOSEOUT-RES001-003` | `RES-001` | `benchmark_consumption_trace` | yes | no | verified DENIX rows 已显式标成 `not_consumed_for_stage_b_release`，但没有 release-grade benchmark-consumption chain 或 comparison-output hashes。 |
| `CLOSEOUT-RES002-001` | `RES-002` | `release_identity_cleanliness` | yes | no | model/version/repo anchor 已记录；但 `worktree_state` 不是 `clean_release_candidate`，`current_validation_status` 仍是 `not_validated`，identity manifest 仍含 `/tmp` author-side output anchors。 |
| `CLOSEOUT-RES002-002` | `RES-002` | `author_retained_pack_vs_release_identity` | yes | no | Stage B 与 Stage C author-side retained packs 已存在；但 retained origin 仍明确 `independent_release_artifact_present=false` 且 `stock_runtime_authority_present=false`。 |

## 3. RES-001 / RES-002 追踪

| residual | author-side 已满足 check | release-grade 仍阻塞 check | gate result |
|---|---|---|---|
| `RES-001` | `CLOSEOUT-RES001-001`, `CLOSEOUT-RES001-002`, `CLOSEOUT-RES001-003` | `CLOSEOUT-RES001-001`, `CLOSEOUT-RES001-002`, `CLOSEOUT-RES001-003` | `blocked` |
| `RES-002` | `CLOSEOUT-RES002-001`, `CLOSEOUT-RES002-002` | `CLOSEOUT-RES002-001`, `CLOSEOUT-RES002-002` | `blocked` |

## 4. 当前允许结论

- `RES-001`：当前可以说 source pin、forbidden output boundary、DENIX candidate non-consumption trace 已形成 author-side review surface。
- `RES-002`：当前可以说 surrogate identity manifest、Stage B retained pack 和 Stage C retained pack 已形成 author-side retained evidence chain。
- 当前仍不能说 `RES-001` 或 `RES-002` release-grade closed。

## 5. 仍需路径

| residual | release-grade remaining path |
|---|---|
| `RES-001` | canonical retained source artifact pack；release-grade allowed-output policy freeze；benchmark-consumption trace with comparison-output hashes and reviewer signoff。 |
| `RES-002` | clean release candidate identity state；release validation status；release identity manifest distinct from author-side retained packs；independent release artifact / review state external to author-side retained packs。 |

## 6. Fail-closed 边界

- 即使上游字段被乐观改成 release-like，只要 author retained pack 仍只是 author-side / candidate retained evidence，本 gate 仍不得释放 authority。
- 本 gate 不关闭 Stage B release readiness，不关闭 Stage C component fragility review，不写 stock descriptor。
- `effect_scale_authority_released=false`。
- `component_failure_probability_authority_released=false`。
- `pk_authority_released=false`。
- `deterministic_fuze_authority_released=false`。

## 7. 复核命令

```bash
python tools/maintenance/damage_model.py release-governance provenance-closeout --output /tmp/a2_release_provenance_closeout_gate.json
pytest -q tests/architecture/damage_model/test_release_authority_guardrails.py
```
