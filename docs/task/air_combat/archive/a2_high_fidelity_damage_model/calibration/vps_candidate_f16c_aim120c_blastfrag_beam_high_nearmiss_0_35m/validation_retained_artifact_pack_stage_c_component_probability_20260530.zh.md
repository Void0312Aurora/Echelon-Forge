# Validation Retained Artifact Pack - Stage C Component Probability

状态：`author_retained / candidate / non-authoritative / stage_c_component_probability_only`。

本文档记录当前 Stage C `component_failure_probability_authority_only` 候选包的第一版 retained
artifact pack。它来自
[damage_model_candidate_artifacts.py](../../../../../../tools/maintenance/damage_model_candidate_artifacts.py) `component-probability-retained-pack`，
把 Stage C 当前的 machine-readable candidate surfaces 固化到 repo 内 canonical JSON 目录。

本文档不创建 runtime descriptor，不授予 authority，也不把 retained pack 冒充成独立 fragility release artifact。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.stage_c_component_probability_retained_artifact_pack.v1` |
| `retained_pack_status` | `author_retained_stage_c_component_probability_candidate_artifacts_only` |
| `retention_scope` | `stage_c_component_probability_author_side_candidate_only` |
| `retained_artifact_count` | `4` |
| `runtime_origin` | `test_local_runtime_authority_exercise_only` |

## 2. 当前 retained artifacts

| `artifact_key` | `sha256` | 当前角色 | 当前不允许的叙述 |
|---|---|---|---|
| `runtime_aligned_authority_pack` | `69c37297edcc1de843010e3b3d85b7a0478fc2183f39730c80345ecebff3943a` | test-local runtime 正向路径证明 | validated fragility truth / stock authority |
| `stage_c_component_probability_snapshot` | `037969252aaeb27172c6873271ed1812b59d64ad596cfee52adbad0c63d5fc76` | author-side candidate snapshot | validated component probability authority |
| `stage_c_component_probability_surface_probe` | `92dec92d70e9a850206cfab74f461b4f67c8e03f552fdc58d99209e9dfbe9535` | author-side candidate surface probe / repeatability snapshot | validated fragility curve / authority release |
| `stage_c_component_probability_result_pack` | `a7edc25da18a54969d6c1ea1e66fd254ba09ad85f7e17bdea2252cbb9cf18993` | author-side candidate result pack | release-grade fragility result |

## 3. 当前 retained chain 的作用

这份 retained pack 当前只允许支持以下结论：

- Stage C 已经不再只靠 stdout 或临时文件维持 candidate surface；
- runtime-aligned authority exercise、snapshot、surface probe 与 result pack 现在都有 repo 内可追踪的 canonical JSON 锚点；
- surface probe retained artifact 明确记录固定 probe 点、固定 seed 集、stock baseline `synthetic_sigmoid`
  和 component-specific row 限域；
- retained pack 只是在保存 author-side candidate evidence，不等于独立 review、release-grade identity 或 stock authority 已经闭合。

## 4. 当前判定

当前判定为：

> `Stage C now has a canonical retained author-side candidate artifact pack, but the retained chain remains bounded to test-local/runtime-aligned origin and does not establish independent fragility release authority`.
