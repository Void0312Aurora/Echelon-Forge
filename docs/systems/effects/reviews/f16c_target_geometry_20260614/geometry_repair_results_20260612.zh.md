# TG-P6-R11 几何修复结果

状态：`2026-06-12` applied / review-only / `TG-P7` runtime interface 仍需要先明确跨区部件 ownership。
英文辅文：[geometry_repair_results_20260612.md](geometry_repair_results_20260612.md)。

本轮修复 R10 subagent 修正后留下的硬阻塞：左右符号 mismatch、缺失表面 receiver 部件，
以及左右映射修正后暴露出来的翼面部件盒位置问题。

## 已执行修复

| 切片 | 修复 | 边界 |
| --- | --- | --- |
| 左右外壳区域 | 对调主翼、翼根和平尾的审计网格 source nodes，使 `left_*` 对应负 y，`right_*` 对应正 y，与现有部件命名一致。 | 修正审阅映射；不声明真实 F-16 工程站位数据。 |
| 翼面和翼根部件 | 将主翼油箱和副翼作动器移动到 mesh-derived 主翼薄棱柱上；将前缘襟翼作动器移动到翼根整流区域内。 | 仍是 synthetic runtime component boxes，属于 review-only 几何。 |
| 运行时表面 receiver | 在 `f16c_block50.json` 中补座舱盖、进气道、左平尾和右平尾的显式 receiver 组件。 | 添加损伤模型部件；不代表外壳代理已接入近炸 runtime projection。 |
| 表面交接规则 | 将 missing-runtime held 关系替换为已有 receiver 组件，并收窄 radome、canopy、vertical tail 的直接 surface expectation。 | 跨区路径在 ownership 明确前仍保持 review-only。 |
| Stage-C guard 同步 | 将 Stage-C 部件失效概率 surface probe gate 同步到修复后侧向几何的 `surface_incidence_cos=0.0`，恢复 component-specific row 选择，避免回退到 `global-fallback`。 | 仍保持 Stage-C candidate 非权威；这里只是让 test-local guard 与修复后的几何一致。 |

## 重生成 packet 摘要

- 部件绑定：`26` 个部件，`26` 个 bound components，`0` 个 `needs_review`，
  `0` 个 side-sign blockers，`0` 个 hard blockers，`0` 个 geometry-review-required 坏盒。
- 表面部件候选：`14` 个表面，`0` 个 `needs_review`，`0` 个缺失 runtime receiver relation，
  `0` 个 side-sign surface blocker，`8` 个跨区语义 hold/candidate。
- 独立复核视图：共 `75` 页：`26` 个部件页、`29` 个表面交接页、`20` 个测试点候选部件页。

## 剩余边界

- `engine_core` 仍是 `review_only_cross_region_boundary_candidate`，跨 intake、aft engine bay 和 nozzle 语义。
- `wing_spar_center` 仍是 `review_only_cross_region_semantic_hold`，跨 center fuselage、wing root 和 wing skin 语义。
- `TG-P7` 不应在这些 ownership 语义被接受、拆分或明确 held 前，把外壳代理当成 runtime projection 几何。

## 验证

```bash
python tools/geometry/airframe_geometry_review.py --out docs/systems/effects/reviews/f16c_target_geometry_20260614/review_packets/f16c_20260611
pytest -q tests/tools/test_airframe_geometry_review.py
pytest -q tests/architecture/damage_model
```

聚焦测试结果：`2 passed`；architecture damage-model 结果：
`177 passed`。
