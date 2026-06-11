# Surrogate Identity Manifest - Stage B Effect Scale

状态：`author_frozen_identity_snapshot / candidate / non-authoritative`。

本文档把当前 Stage B `effect_scale_authority_only` 候选 surrogate 的身份、
输入快照和可复跑锚点整理到同一处，避免把“当前仓库能跑”误写成“已有 release-grade
surrogate identity”。

本文档不授予 authority，也不关闭 `RES-002 surrogate identity`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `model_ref` | `candidate://a2/runtime-aligned-vps/f16c-aim120c-blastfrag-beam-high-nearmiss-0_35m-v0` |
| `model_version` | `v0_candidate_runtime_aligned` |
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `repo_commit` | `e634f3aca7deed73c2918f58a8d07068c5727215` |
| `worktree_state` | `repo_dirty_relevant_stage_b_file_set_hashed_retained_artifacts_present` |
| `retained_artifact_pack_status` | `present_author_side_non_authoritative` |
| `retained_artifact_manifest_ref` | `docs/task/air_combat/archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/retained_artifacts/stage_b_effect_scale_20260530/manifest.json` |
| `retained_artifact_count` | `4` |
| `current_validation_status` | `not_validated` |
| `primary_release_scope` | `effect_scale_authority_only` |
| `forbidden_outputs` | `effect_scale_authority`, `component_failure_probability_authority`, `pk_authority`, `deterministic_fuze_authority` |

## 2. 关键代码与输入快照

| 类别 | 路径 | 角色 | `sha256` |
|---|---|---|---|
| runtime | [default_effects_model.cpp](../../../../../../src/models/weapons/default_effects_model.cpp) | structured-aircraft near-miss / projected-component runtime path | `317dedd29f63978d12428fe65a13a4cfb5f788c36bedbbac19ceb4bb612db394` |
| tooling | [damage_model.py](../../../../../../tools/maintenance/damage_model.py) `candidate-artifacts validation-scaffold` | Stage B candidate benchmark scaffold | historical hash retained from pre-consolidation run |
| tooling | [damage_model.py](../../../../../../tools/maintenance/damage_model.py) `candidate-artifacts scope-boundary-probe` | Stage B scope boundary probes | historical hash retained from pre-consolidation run |
| tooling | [damage_model.py](../../../../../../tools/maintenance/damage_model.py) `candidate-artifacts effect-scale-snapshot` | Stage B hard-gate snapshot artifact generator | historical hash retained from pre-consolidation run |
| tooling | [damage_model.py](../../../../../../tools/maintenance/damage_model.py) `candidate-artifacts effect-scale-retained-pack` | canonical retained Stage B candidate artifact writer/reader | historical hash retained from pre-consolidation run |
| tooling | [damage_model.py](../../../../../../tools/maintenance/damage_model.py) `candidate-artifacts runtime-authority-exercise` | test-local authority exercise pack | historical hash retained from pre-consolidation run |
| input DB | [f16c_block50.json](../../../../../../examples/config/database/aircraft/units/f16c_block50.json) | target outer-dimension / repo component scaffold input | `4259d631c10863cb673a13d365f50f6745c85597992f391ee976087c9f6194c4` |
| input DB | [aim_120c.json](../../../../../../examples/config/database/weapons/air_to_air/aim_120c.json) | candidate warhead/fuze family envelope input | `9983680622a89064230de56a9a54157c2a3d054d33c8770e1f513f09c6f69f34` |

## 3. 命令、临时 author-side 输出与 retained 保留入口

| 命令 | 角色 | 当前输出 `sha256` | 保留边界 |
|---|---|---|---|
| `./.venv/bin/python tools/maintenance/damage_model.py candidate-artifacts validation-scaffold --output /tmp/a2_blastfrag_scaffold_snapshot.json` | fixed-seed scaffold snapshot | historical hash retained from pre-consolidation run | `/tmp` 输出只是 author snapshot，不是 canonical retained artifact |
| `./.venv/bin/python tools/maintenance/damage_model.py candidate-artifacts scope-boundary-probe --output /tmp/a2_scope_boundary_probe_snapshot.json` | scope boundary probe snapshot | historical hash retained from pre-consolidation run | `/tmp` 输出只是 author snapshot，不是 canonical retained artifact |
| `./.venv/bin/python tools/maintenance/damage_model.py candidate-artifacts effect-scale-snapshot --output /tmp/a2_stage_b_effect_scale_snapshot.json` | Stage B hard-gate snapshot | historical hash retained from pre-consolidation run | `/tmp` 输出只是 author snapshot，不是 canonical retained artifact |
| `./.venv/bin/python tools/maintenance/damage_model.py candidate-artifacts effect-scale-retained-pack` | write canonical retained Stage B candidate artifact pack | historical manifest hash retained from pre-consolidation run | `retained_artifacts/stage_b_effect_scale_20260530/` 是当前 canonical author-side retained evidence chain，但仍不是 release-grade identity |

## 4. 固定的运行参数

| 参数 | 值 |
|---|---|
| `seed_policy` | `fixed-seed author snapshot; seed = 20260529` |
| `sample_count` | `4096` |
| `scope_axes` | `F-16C_Block50` × `AIM-120C-class/blast_fragmentation` × `beam` × `high` × `near_miss_0_35m` |
| `candidate_bundle_role` | `review_and_packaging_only` |
| `stock_runtime_action` | `forbidden` |

## 5. 当前身份边界

这份 identity manifest 当前只允许支持以下结论：

- 当前 author-side Stage B surrogate 有可点名的代码、输入文件和复跑命令；
- 当前 Stage B surrogate 已经有 repo 内 canonical retained artifact pack；
- 当前 worktree 不是 clean release state，因此 `repo_commit` 不能单独代表完整 surrogate 身份；
- 当前 `/tmp` 输出 hash 只固定了本轮 author snapshot，而 retained pack 只关闭了 author-side 保留链，不等于 release-grade validation identity。

它当前**不能**支持：

- release-grade reproducibility claim；
- stock runtime authority；
- independent validation；
- `Pk` 或 deterministic fuze authority。

## 6. 当前判定

当前判定为：

> `the Stage B surrogate now has an explicit author-side identity snapshot and a canonical retained artifact pack, but the repo is still not in a clean release-grade identity state, so surrogate identity remains open and author-side only`.
