# TG-P6-R10 Subagent 修正结果

状态：`2026-06-12` subagent correction applied / review-only / `TG-P7` 仍 held。
英文辅文：[subagent_correction_results_20260612.md](subagent_correction_results_20260612.md)。

已被 R11 main-thread 修复记录替代：
[geometry_repair_results_20260612.zh.md](geometry_repair_results_20260612.zh.md)。
下方左右符号和缺失 receiver 阻塞描述的是 R10 快照，不是当前重生成 packet。

本文记录
[subagent_independent_review_findings_20260612.zh.md](subagent_independent_review_findings_20260612.zh.md)
之后的修正回合。本轮用了两个写入范围互不重叠的 subagent：一个修 F-16 部件源盒，一个修
review semantics 和测试。该回合没有创建新的 Codex 会话，也没有把近炸投影接入 runtime。

## 已应用修正

| 区域 | 结果 | 边界 |
| --- | --- | --- |
| 机鼻 radar/IFF 源盒 | `apg68_radar_array` 和 `iff_interrogator` 现在干净绑定到 `nose_radome`，`component_overlap_fraction=1.0`，没有部件异常。 | 仍只是 review-only 部件几何，不是真实 F-16 内部布局。 |
| 发动机喷口源盒 | `afterburner_nozzle` 现在干净绑定到 `engine_nozzle`；之前的 `vertical_tail` 绑定消失，`invalid_region_binding_blocked_count=0`。 | 表面交接仍是 review-only。 |
| 跨区部件 | `engine_core` 标为 `review_only_cross_region_boundary_candidate`；`wing_spar_center` 标为 `review_only_cross_region_semantic_hold`。低 overlap 保留为 suppressed observation，不再作为坏盒阻塞。 | held/review-only 语义，不是 runtime acceptance。 |
| 左右符号 mismatch | 翼面和翼根部件继续输出 `side_sign_mismatch_hard_blocker`，并保留 side-sign 细节。 | 仍阻塞 `TG-P7`。 |
| 缺失 runtime 承接部件 | 座舱盖、进气道、左平尾和右平尾输出 `missing_runtime_link/held`。 | 仍阻塞 runtime handoff。 |

## 重新生成的 packet 摘要

- 部件绑定：`22` 个部件，`16` 个 bound components，`6` 个 `needs_review`
  硬阻塞，`6` 个左右符号阻塞，`2` 个跨区语义候选，`0` 个
  geometry-review-required 坏盒。
- 表面部件候选：`14` 个表面，`10` 个仍需人工复核，`4` 个缺失 runtime
  承接关系，`4` 个 side-sign surface blockers，`3` 个跨区语义 surface
  held/candidate，`1` 个干净候选表面。
- 独立复核视图：共 `83` 页：`22` 个部件页、`44` 个表面交接/缺失关系页、
  `17` 个测试点候选部件页。

## 仍然 held

- 先解决左右符号约定，之后才能接受翼面或翼根 handoff。
- 为座舱盖、进气道和左右平尾补显式 runtime 承接部件，或记录明确 held 决议。
- `engine_core` 和 `wing_spar_center` 在 ownership 被接受前保持 review-only 跨区语义。
- `surface_nose_radome` 和 `surface_vertical_tail_skin` 仍需继续复核，因为它们仍包含 expected
  component bound elsewhere；不过 radar/IFF 和 nozzle 源盒已修正。

## 验证

```bash
python tools/geometry/airframe_geometry_review.py --out docs/systems/effects/reviews/f16c_target_geometry_20260614/review_packets/f16c_20260611
pytest -q tests/tools/test_airframe_geometry_review.py
git diff --check -- docs/systems/effects/reviews/f16c_target_geometry_20260614 tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py examples/config/database/aircraft/units/f16c_block50.json
```

结果：generator 完成，聚焦 pytest 为 `2 passed`，`git diff --check` 无 whitespace 错误。
