# TG-P6-R22 跨区 ownership 拆分候选结果

状态：`2026-06-13` pass as review-only ownership split candidate；`TG-P7`
runtime activation 仍需等待 ownership acceptance 和 runtime tests。

英文辅文：
[cross_region_ownership_split_results_20260613.md](cross_region_ownership_split_results_20260613.md)。

## 本轮变更

R22 将剩余两个跨区 held receiver 整理成显式 ownership 决策包。它不接受拆分方案，不退役父级 receiver，也不激活任何 runtime component。

新增 packet 产物：

- [cross_region_ownership_split_candidate_20260611.json](review_packets/f16c_20260611/cross_region_ownership_split_candidate_20260611.json)
- [cross_region_ownership_split_candidate_20260611.csv](review_packets/f16c_20260611/cross_region_ownership_split_candidate_20260611.csv)
- [scene.html](review_packets/f16c_20260611/scene.html) 已新增
  `Cross-Region Ownership Split Candidates` section。

## 候选决策

| 父级 receiver | 建议决策 | 候选 receiver | Runtime 状态 |
| --- | --- | --- | --- |
| `engine_core` | `split_into_engine_section_receivers_and_keep_intake_duct_receiver_separate` | `engine_core_afterburner_segment`, `engine_core_hot_section_segment`, `engine_core_forward_compressor_segment` | not active |
| `wing_spar_center` | `split_into_center_carrythrough_root_and_inner_wing_spar_receivers` | `wing_spar_center_left_inner_wing_segment`, `wing_spar_center_left_root_segment`, `wing_spar_center_carrythrough_segment`, `wing_spar_center_right_root_segment`, `wing_spar_center_right_inner_wing_segment` | not active |

## 计数

- Parent decisions: `2`。
- Split receiver candidates: `8`。
- Runtime parse-ready split candidates: `8`。
- Runtime active split components: `0`。
- 仍有 whole-airframe silhouette 采样外露的 split candidates：`0`。
- 位于 whole-airframe bounds 外的 split candidates：`0`。
- Activation 前需要退役父级 receiver 的决策：`2`。

## 边界

拆分候选 payload 是 AABB fallback receiver records，同时保留原始 shape metadata。它们可供后续 `TG-P7` schema/runtime test 解析，但本轮继续把以下 authority flags 保持为 false：

- runtime damage ownership；
- runtime split receiver activation；
- parent receiver retirement acceptance；
- cross-region receiver ownership acceptance；
- true internal component geometry。

## 下一步

1. 对 `engine_core` 与 `wing_spar_center` 的父级 receiver retirement 建议做 accept、reject 或继续 held 决策。
2. 在任何 activation 前，为 split candidates 补 `TG-P7` parse 和 behavior tests。
3. 在 exact capsule/ellipsoid runtime intersection support 被单独接受前，将 payload 保持为 AABB fallback candidates。

## 验证

```bash
python -m py_compile tools/geometry/airframe_geometry_review.py
pytest -q tests/tools/test_airframe_geometry_review.py
python tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
```

当前聚焦结果：`2 passed`；review packet 已重新生成。
