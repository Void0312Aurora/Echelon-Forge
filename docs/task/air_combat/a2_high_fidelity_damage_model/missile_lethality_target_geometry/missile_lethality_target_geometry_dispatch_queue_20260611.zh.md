# A2 目标几何建模派发队列

状态：`2026-06-13` TG-P6-R21 complete / latest subcomponent placement
promotion applied。当前记录第一轮进展和 TG-P6 后续推进；R10 使用写入范围受限的
subagent，R11-R21 由 main thread 集成。

英文辅文：[missile_lethality_target_geometry_dispatch_queue_20260611.md](missile_lethality_target_geometry_dispatch_queue_20260611.md)。

## 第一轮建议

| Packet | Cluster | 建议 Owner | 目标 | 写入范围 | 验证 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| `TG-P1-R1` | `TG-P1` | main thread | 解析 F-16 glTF，输出 manifest 和尺度/轴向摘要 | `tools/geometry/airframe_geometry_review.py`; `review_packets/f16c_20260611/manifest.json`; `tests/tools/test_airframe_geometry_review.py` | JSON parse; registry/glTF path existence; public-dimension check; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P2-R1` | `TG-P2` | main thread | 基于 glTF 外包、位置规则和人工映射生成第一版外壳区域候选 | `review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json`; `top.svg`; `side.svg`; `front.svg`; focused tests | region schema; bounds check; SVG smoke; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P3-R1` | `TG-P3` | main thread | 读取现有 F-16 部件盒，绑定外壳区域并标出异常 | `component_binding_report_20260611.json`; `component_binding_report_20260611.csv`; focused tests | every component has region or `needs_review`; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P4-R1` | `TG-P4` | main thread | 生成第一版 HTML/SVG 审阅包 | `review_packets/f16c_20260611/scene.html`; `top.svg`; `side.svg`; `front.svg` | local file existence; no external network dependency; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P5-R1` | `TG-P5` | main thread | 对鼻向 4 m / 6 m 等测试点输出距离诊断 | `review_point_diagnostics_20260611.json`; `review_point_diagnostics_20260611.csv`; focused tests | nearest outer/component distance and candidate count present; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P6-R1` | `TG-P6` | main thread | 设计第一版精细几何代理候选 | `fine_geometry_proxy_design_20260611.zh.md`; `fine_geometry_proxy_design_20260611.md` | markdown links; `git diff --check` | pass as design draft |
| `TG-P6-R2` | `TG-P6` | main thread | 生成第一版精细几何代理 JSON 和叠加审阅 | `fine_geometry_proxy_candidate_20260611.json`; `fine_proxy_top.svg`; `fine_proxy_side.svg`; `fine_proxy_front.svg`; focused tests | proxy schema check; distance sanity; visual smoke; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass as review-only candidate; R7 已记录目检结论，进入 `TG-P7` 前需先修复阻塞项 |
| `TG-P6-R3` | `TG-P6` | main thread | 用审计 glTF 顶点派生的 top/side/front silhouette 替换纯矩形精细叠加图 | `tools/geometry/airframe_geometry_review.py`; `fine_geometry_proxy_candidate_20260611.json`; `fine_proxy_*.svg`; focused tests | mesh silhouette schema check; no bounds-expansion fallback; visual smoke; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass as review-only silhouette candidate; mesh-aligned 修正后 `inflated_fallback_count=0` |
| `TG-P6-R4` | `TG-P6` | main thread | 生成逐区域局部放大和 flags 的人工审阅 dashboard | `fine_proxy_review_dashboard.html`; `scene.html`; focused tests | dashboard smoke; candidate/review/hold 状态可见；component overlays 可见；`pytest -q tests/tools/test_airframe_geometry_review.py` | pass as human review aid; 仍不是 runtime geometry |
| `TG-P6-R5` | `TG-P6` | main thread | 生成外壳区域到表面部件、再到现有内部部件的审阅用候选表 | `surface_component_candidate_20260611.json`; `surface_component_candidate_20260611.csv`; `scene.html`; focused tests | 14 个外壳区域都有表面部件；漂移/缺失关系可见；`pytest -q tests/tools/test_airframe_geometry_review.py` | pass as review-only component modeling layer; 仍需人工修正旧部件盒和缺失部件关系 |
| `TG-P6-R6` | `TG-P6` | main thread | 按实际复核问题生成视觉优先的人工 triage 页面 | `human_review_triage.html`; `scene.html`; focused tests | 左右符号、部件位置、表面交接和测试点卡片都有局部 top/side/front 叠加图；`pytest -q tests/tools/test_airframe_geometry_review.py` | pass as visual review aid; 仍不是 runtime geometry |
| `TG-P6-R7` | `TG-P6` | main thread | 直接目检 triage 页面并记录结论 | `human_review_findings_20260612.zh.md`; `human_review_findings_20260612.md`; README/status/queue/task-cluster docs | findings 指向具体视觉阻塞项；不把候选接入 runtime；`pytest -q tests/tools/test_airframe_geometry_review.py`; `git diff --check` | pass as visual findings record; `TG-P7` held pending repair |
| `TG-P6-R8` | `TG-P6` | main thread | 给每个部件/交接/测试点候选生成独立 top/side/front 视图 | `component_review_views/index.html`; `component_review_views/manifest.json`; `component_review_views/**`; `tools/geometry/airframe_geometry_review.py`; focused tests | R11 重新生成后，26 个部件、29 个表面交接、20 个测试点候选都有独立页面；`pytest -q tests/tools/test_airframe_geometry_review.py`; `git diff --check` | pass as isolated review packet; 已派 subagent 分组评估 |
| `TG-P6-R9` | `TG-P6` | main thread + subagents | 按独立视图做五组只读 subagent 评估并汇总结论 | `subagent_independent_review_findings_20260612.zh.md`; `subagent_independent_review_findings_20260612.md`; README/status/queue/task-cluster docs | 五组评估均基于独立视图和 JSON 追溯；不修改 runtime；`pytest -q tests/tools/test_airframe_geometry_review.py`; `git diff --check` | pass as independent review findings; `TG-P7` 仍 held |
| `TG-P6-R10` | `TG-P6` | main thread + subagents | 按独立评估结论做 scoped corrections 并重新生成 review packet | `examples/config/database/aircraft/units/f16c_block50.json`; `tools/geometry/airframe_geometry_review.py`; `tests/tools/test_airframe_geometry_review.py`; `review_packets/f16c_20260611/**`; `subagent_correction_results_20260612.zh.md`; `subagent_correction_results_20260612.md`; README/status/queue/task-cluster docs | R10 历史快照：radar/IFF/nozzle 源盒已修；component report 当时有 6 个左右符号硬阻塞、2 个跨区语义、0 个 geometry bad-box blockers；`pytest -q tests/tools/test_airframe_geometry_review.py`; `git diff --check` | pass as historical review-only correction pass; 已被 R11 替代 |
| `TG-P6-R11` | `TG-P6` | main thread | 修复 R10 后的左右区域映射、runtime receivers、翼面部件位置和直接 surface handoff 规则 | `examples/config/database/aircraft/units/f16c_block50.json`; `tools/geometry/airframe_geometry_review.py`; `tests/tools/test_airframe_geometry_review.py`; `review_packets/f16c_20260611/**`; `geometry_repair_results_20260612.zh.md`; `geometry_repair_results_20260612.md`; README/status/queue/task-cluster docs | component report 26/26 bound、0 needs_review、0 side-sign blockers、0 geometry bad-box blockers；surface report 0 needs_review、0 missing runtime receiver relations、8 个跨区语义；`pytest -q tests/tools/test_airframe_geometry_review.py`; `git diff --check` | pass as review-only geometry repair; `TG-P7` 只因跨区 ownership 继续 held |
| `TG-P6-R12` | `TG-P6` | main thread | 输出语义外壳损伤几何候选和可解析 runtime component JSON | `semantic_damage_geometry_*`; `semantic_damage_geometry_results_20260612.zh.md`; generator/tests/review packet docs | 14 个语义体积可解析，runtime activation 仍为 0；focused pytest | pass as review-only semantic geometry |
| `TG-P6-R13` | `TG-P6` | main thread | 生成受约束的内部 receiver 先验几何 | `internal_component_prior_*`; `internal_component_prior_results_20260612.zh.md`; generator/tests/review packet docs | 26 个 prior 受约束，post-constraint outside count 为 0，runtime activation 为 0；focused pytest | pass as review-only internal prior geometry |
| `TG-P6-R14` | `TG-P6` | main thread | 生成语义父子布局视图 | `semantic_parent_child_layout_*`; `semantic_parent_child_layout_results_20260612.zh.md`; generator/tests/review packet docs | 14 个父外壳部件和 26 个 receiver overlay 可见；focused pytest | pass as parent-child review layout |
| `TG-P6-R15` | `TG-P6` | main thread | 将跨区 held receiver 拆成 review-only 分段 | `cross_region_held_component_segments_*`; `cross_region_held_segment_results_20260612.zh.md`; generator/tests/review packet docs | 8 个 held segment，outside whole-airframe count 为 0，runtime activation 为 0；focused pytest | pass as held-segment review split |
| `TG-P6-R16` | `TG-P6` | main thread | 增加 shape-aware 整机 silhouette 诊断 | `airframe_constraint_correction_*`; `airframe_constraint_correction_results_20260612.zh.md`; generator/tests/review packet docs | 34 个 receiver/segment item 被诊断，外露项进入 shape-placement review；focused pytest | pass as airframe constraint diagnostic |
| `TG-P6-R17` | `TG-P6` | main thread | 生成保留名义尺寸的子部件形状/摆放候选 | `subcomponent_shape_placement_*`; `subcomponent_shape_placement_results_20260613.zh.md`; generator/tests/review packet docs | 14 个外露子部件获得候选形状族和复核视图；focused pytest | pass as review-only shape-placement candidates |
| `TG-P6-R18` | `TG-P6` | main thread | 将零外露形状候选固化到 review-only 生成规则 | generator/tests/review packet docs; `subcomponent_shape_promotion_results_20260613.zh.md` | 4 个零外露候选被固化；runtime activation 为 0；focused pytest | pass as review-only shape promotion |
| `TG-P6-R19` | `TG-P6` | main thread | 为剩余外露子部件增加局部中心线摆放候选 | generator/tests/review packet docs; `subcomponent_centerline_placement_results_20260613.zh.md` | 剩余 10 项中 8 项清零采样外露；runtime activation 为 0；focused pytest | pass as centerline placement candidate |
| `TG-P6-R20` | `TG-P6` | main thread | 为剩余 radar/cockpit 项增加最新子部件摆放候选，并收敛复核图例 | generator/tests/review packet docs; `subcomponent_latest_placement_results_20260613.zh.md` | 10 个 latest candidate 清零采样外露；runtime activation 为 0；focused pytest | pass as latest placement candidate |
| `TG-P6-R21` | `TG-P6` | main thread | 将已接受的最新摆放固化到 review-only prior 和 held-segment 生成规则 | `tools/geometry/airframe_geometry_review.py`; `tests/tools/test_airframe_geometry_review.py`; `review_packets/f16c_20260611/**`; `subcomponent_latest_promotion_results_20260613.zh.md`; README/status/queue/task-cluster docs | internal prior promotion count 为 9，held segment promotion count 为 5，silhouette exposure count 为 0，shape-placement candidate count 为 0，runtime activation 为 0；`pytest -q tests/tools/test_airframe_geometry_review.py`; packet regeneration; `git diff --check` | pass as latest placement promotion; `TG-P7` 仍因跨区 ownership held |

## Main Thread 合并检查

- 确认 worker 没有保存 token、signed URL 或 Authorization header。
- 确认生成物不声称真实 F-16 工程结构或真实武器杀伤率。
- 确认审阅包能解释 4 m 鼻向样例，而不是仅复述“非直接命中”。
- 确认精细代理输出仍是 review-only，并且明确左右坐标约定，不暗示工程权威几何。
- 确认表面部件候选只作为外形命中到现有部件损伤的审阅用交接表，不声明真实内部结构。
- 确认 triage 页面只是对现有 review-only 候选的视觉复核入口，不是验收或 runtime 接入记录。
- 确认 R11 修复记录已替代 R7/R10 阻塞项，同时把 `engine_core` 与 `wing_spar_center` 跨区 ownership 保留为剩余 `TG-P7` 阻塞项。
- 确认独立视图包按单个部件、单个表面交接或单个测试点候选拆分，不再要求评估者从拥挤总览图里猜。
- 确认 subagent 评估结论已吸收进汇总文档，并修正 `engine_core`、`wing_spar_center` 的跨区语义边界。
- 确认 R10/R11 修正已修复 radar/IFF/nozzle、左右映射、receiver 组件和翼面位置，但没有声称 runtime integration。
- 确认 bounds-expansion fallback 保持禁用；缺少轮廓时必须进入审阅，不能当作精确工程几何。
- 确认父级 README 只由 main thread 同步状态。

## 暂缓项

- Runtime 近炸投影接入：当前 `TG-P7` held，需先明确接受、拆分或继续 held `engine_core` 与 `wing_spar_center` 跨区 ownership。
- MQ-9 几何：等 F-16 工具链可复用后再展开。
- 结构解体、残骸和 Pk：另建后续子项目。
