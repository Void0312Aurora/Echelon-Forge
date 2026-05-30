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
| `worktree_state` | `dirty_and_untracked_present` |
| `current_validation_status` | `not_validated` |
| `primary_release_scope` | `effect_scale_authority_only` |
| `forbidden_outputs` | `effect_scale_authority`, `component_failure_probability_authority`, `pk_authority`, `deterministic_fuze_authority` |

## 2. 关键代码与输入快照

| 类别 | 路径 | 角色 | `sha256` |
|---|---|---|---|
| runtime | [default_effects_model.cpp](/home/void0312/Workshop/CMO/src/models/weapons/default_effects_model.cpp) | structured-aircraft near-miss / projected-component runtime path | `317dedd29f63978d12428fe65a13a4cfb5f788c36bedbbac19ceb4bb612db394` |
| tooling | [a2_blastfrag_validation_scaffold.py](/home/void0312/Workshop/CMO/tools/maintenance/a2_blastfrag_validation_scaffold.py) | Stage B candidate benchmark scaffold | `3fac25413327fecfc870029e1ad0a90793ef4e85c5750d575c93f3c5b2a38694` |
| tooling | [a2_blastfrag_scope_boundary_probe.py](/home/void0312/Workshop/CMO/tools/maintenance/a2_blastfrag_scope_boundary_probe.py) | Stage B scope boundary probes | `fbcc31fb34df0e810aacc3e58cca426d3e550c3346a91c45612426b2bd1e7782` |
| tooling | [a2_blastfrag_stage_b_effect_scale_snapshot.py](/home/void0312/Workshop/CMO/tools/maintenance/a2_blastfrag_stage_b_effect_scale_snapshot.py) | Stage B hard-gate snapshot artifact generator | `e3b609f20745f177b4470f3e7acdca1933bf9bfe151f0833a54df2ff55d4cc09` |
| tooling | [a2_blastfrag_runtime_aligned_authority_pack.py](/home/void0312/Workshop/CMO/tools/maintenance/a2_blastfrag_runtime_aligned_authority_pack.py) | test-local authority exercise pack | `f4429b048b1f468610c811fb14b717978c6b609aac3c6c5ec32cfbd5c2a81485` |
| input DB | [f16c_block50.json](/home/void0312/Workshop/CMO/examples/config/database/aircraft/units/f16c_block50.json) | target outer-dimension / repo component scaffold input | `4259d631c10863cb673a13d365f50f6745c85597992f391ee976087c9f6194c4` |
| input DB | [aim_120c.json](/home/void0312/Workshop/CMO/examples/config/database/weapons/air_to_air/aim_120c.json) | candidate warhead/fuze family envelope input | `9983680622a89064230de56a9a54157c2a3d054d33c8770e1f513f09c6f69f34` |

## 3. 命令与当前 author-side 输出锚点

| 命令 | 角色 | 当前输出 `sha256` | 保留边界 |
|---|---|---|---|
| `./.venv/bin/python tools/maintenance/a2_blastfrag_validation_scaffold.py --output /tmp/a2_blastfrag_scaffold_snapshot.json` | fixed-seed scaffold snapshot | `e48612ec965c1b8246dbe6c5be80d39456910ca889e3a58d360483f0c50747d5` | `/tmp` 输出只是 author snapshot，不是 canonical retained artifact |
| `./.venv/bin/python tools/maintenance/a2_blastfrag_scope_boundary_probe.py --output /tmp/a2_scope_boundary_probe_snapshot.json` | scope boundary probe snapshot | `dd07c78563b61ac567aa1ab050fe8f09fd610769667c6b9c22c157426e435d66` | `/tmp` 输出只是 author snapshot，不是 canonical retained artifact |
| `./.venv/bin/python tools/maintenance/a2_blastfrag_stage_b_effect_scale_snapshot.py --output /tmp/a2_stage_b_effect_scale_snapshot.json` | Stage B hard-gate snapshot | `62c101e93e0dc91007eb18b7a1f66ca4299cb49c4f33b4ea43f0b8f0ab125647` | `/tmp` 输出只是 author snapshot，不是 canonical retained artifact |

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
- 当前 worktree 不是 clean release state，因此 `repo_commit` 不能单独代表完整 surrogate 身份；
- 当前输出 hash 只固定了本轮 author snapshot，不等于正式 retained validation artifact。

它当前**不能**支持：

- release-grade reproducibility claim；
- stock runtime authority；
- independent validation；
- `Pk` 或 deterministic fuze authority。

## 6. 当前判定

当前判定为：

> `the Stage B surrogate now has an explicit author-side identity snapshot, but the worktree is still dirty and the retained validation artifact chain is not yet closed, so surrogate identity remains open`.
