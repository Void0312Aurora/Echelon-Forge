# Target Geometry Assumptions - Stage B Effect Scale

状态：`author_frozen_assumption_manifest / candidate / non-authoritative`。

本文档把当前 Stage B `effect_scale_authority_only` 候选包实际依赖的
F-16C Block 50 几何假设固定下来，防止把 repo scaffold、visual sanity
或 open-source config 误写成真实 aircraft vulnerability truth。

本文档不创建 runtime descriptor，不授予几何 authority，也不关闭
`RES-003 target geometry`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `primary_release_scope` | `effect_scale_authority_only` |
| `target_type` | `F-16C_Block50` |
| `author_status` | `frozen_for_stage_b_review_only` |
| `forbidden_claim` | `repo scaffold or beam witness geometry must not be described as true F-16 internal vulnerability geometry` |

## 2. 几何假设表

| `geometry_item` | `runtime_ref` | `source_ids` | `support_level` | `value_or_bucket` | `used_by_stage_b` | `not_supported_claims` | residual |
|---|---|---|---|---|---|---|---|
| `outer_bbox` | [f16c_block50.json](../../../../../../examples/config/database/aircraft/units/f16c_block50.json), `airframe.length_m/wingspan_m/height_m` | `F16-TG-SRC-001/002/012` | `candidate_dimension_anchor` | `length ~= 15 m`, `span ~= 10 m`, `height ~= 5 m` 量级 | `yes` | 真实截面、站位、内部舱段与 vulnerability area | `RES-003` |
| `beam_witness_panel` | [damage_model.py](../../../../../../tools/maintenance/damage_model.py) `candidate-artifacts validation-scaffold`, `_bfm_bm_003()` witness length/height | `F16-TG-SRC-001/002/012` | `repo_authored_witness_geometry` | `side-on rectangular witness area = length * height` | `yes` | 真实 3D beam exposure、occlusion、局部曲面、局部 vulnerable area | `RES-003` |
| `nose_radar_rough_region` | [f16c_block50.json](../../../../../../examples/config/database/aircraft/units/f16c_block50.json), structured hitbox/component scaffold | `F16-TG-SRC-002/005/012` | `rough_component_layout_candidate` | `nose/radome/sensor candidate region` | `no_direct_numeric_use_in_stage_b` | APG-68 precise antenna size、radome thickness、material or fragility truth | `RES-003` |
| `engine_aft_region` | [f16c_block50.json](../../../../../../examples/config/database/aircraft/units/f16c_block50.json), engine/component scaffold | `F16-TG-SRC-002/004/012` | `rough_component_layout_candidate` | `single-engine aft region candidate` | `no_direct_numeric_use_in_stage_b` | F110 installation boundary, accessory placement, fuel/hydraulic routing or vulnerability | `RES-003` |
| `wing_and_control_surface_regions` | [f16c_block50.json](../../../../../../examples/config/database/aircraft/units/f16c_block50.json), wing/control components | `F16-TG-SRC-012`; `F16-TG-3P-006/007` as sanity only | `internal_scaffold_plus_community_sanity` | `rough wing/control-surface grouping` | `no_direct_numeric_use_in_stage_b` | mesh-derived hitboxes, spar/rib layout, fuel cell segmentation or surface-specific fragility | `RES-003` |
| `right_aileron_actuator_projection` | runtime projected component path in [default_effects_model.cpp](../../../../../../src/models/weapons/default_effects_model.cpp) + repo component scaffold | `F16-TG-SRC-012`; `F16-TG-3P-006/007` sanity only | `stage_c_only_component_projection_candidate` | `component-specific projection candidate` | `no_for_stage_b_effect_scale_only` | real actuator size, exposure, redundancy or failure probability truth | `RES-003`, `RES-009` |
| `internal_material_or_armor` | none | none admitted | `unsupported` | `not modeled as public truth` | `no` | canopy thickness, armor, rib/spar counts, material percentages, protected bays | `RES-003` |
| `occlusion_and_exposed_area_truth` | none | none admitted | `unsupported` | `not modeled as public truth` | `no` | true 3D shielding, masked fragments, projected vulnerable area or hit probability | `RES-003` |

## 3. 第三方与社区来源的使用边界

当前允许保留在 candidate 池、但不得上卷成几何 authority 的来源包括：

- `F16-TG-3P-006` JSBSim `f16` open-source config：只允许做 parser/schema 与粗坐标 sanity；
- `F16-TG-3P-007` FlightGear F-16 variants：只允许做外形/命名 sanity；
- 其他 `F16-TG-3P-*` 页面：只允许做 visual/reference sanity 或 search lead。

它们都**不能**支持：

- internal component coordinates；
- material / armor truth；
- mesh-derived hitboxes；
- runtime geometry authority；
- effect-scale 或 component probability row。

## 4. Stage B 当前可宣称的几何层级

当前 Stage B 只允许宣称：

- 已有足够支撑 beam-side witness geometry bookkeeping 的 F-16C 外形量级锚点；
- 已有足够支撑 future structured component grouping 的 repo-authored candidate layout；
- 尚未拥有可宣称为真实 F-16 内部 vulnerability geometry 的公开证据链。

## 5. 当前判定

当前判定为：

> `Stage B currently uses a coarse F-16 outer-dimension anchor and repo-authored beam witness geometry, which is enough for candidate effect-scale bookkeeping but not enough for internal-vulnerability authority`.
