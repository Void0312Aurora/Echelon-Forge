# A2 目标几何建模当前状态

状态：`2026-06-11` TG-P5 review packet and diagnostics complete。父级入口和 issue 已把 F-16 几何细化从
问题记录推进到可执行子项目；第一版来源/轴向/尺度 manifest、外壳区域候选、部件绑定报告、离线审阅页和测试点距离诊断已生成。

英文辅文：[missile_lethality_target_geometry_current_status_20260611.md](missile_lethality_target_geometry_current_status_20260611.md)。

## 已知事实

| 项 | 当前事实 | 影响 |
| --- | --- | --- |
| 运行时视觉模型 | `examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb` | 可继续供前端显示使用 |
| 审计模型 | `examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf` | 后续几何审阅从 glTF 读取节点、网格和外包 |
| 来源和许可 | Sketchfab `F16-C Falcon`，Carlos.Maciel，CC-BY-4.0 | 可作为主线外形审阅候选，但仍需署名和边界说明 |
| 公开尺寸 | F-16C 当前数据库记录 length `15.06 m`，wingspan `9.96 m`，height `4.88 m` | 几何代理必须用这些量级做缩放审计 |
| 当前命中盒 | 合并外包约 `15.3 m x 9.8 m x 1.2 m` | 长宽接近公开量级，高度严重不足 |
| 暴露症状 | 鼻向 4 m 近炸点贴近外壳却可能无部件损伤 | 需要外壳距离、部件距离和候选部件数诊断 |
| TG-P1 manifest | [review_packets/f16c_20260611/manifest.json](review_packets/f16c_20260611/manifest.json) | 新模型 scale 后长度误差约 `+0.09%`，翼展约 `-3.37%`，高度约 `-4.50%`；旧命中盒高度误差约 `-75.41%` |
| 节点语义 | glTF 实际 mesh 节点为 `Object_*`；intake metadata 保留 `Canopy01_1`、`EngineL01_17` 等提示名 | P2 不能只靠 glTF 节点名自动分区，需要位置规则和人工映射 |
| TG-P2 外壳区域 | [f16c_geometry_mapping_candidate_20260611.json](review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json) | 已生成 `14` 个低精度区域；`x=4m` 落在 `forward_fuselage`，`x=6m` 落在 `nose_radome` |
| TG-P4 审阅包 | [scene.html](review_packets/f16c_20260611/scene.html)、[top.svg](review_packets/f16c_20260611/top.svg)、[side.svg](review_packets/f16c_20260611/side.svg)、[front.svg](review_packets/f16c_20260611/front.svg) | 三视图叠加外壳区域、旧命中盒、部件盒和编号测试点 |
| TG-P3 部件绑定 | [component_binding_report_20260611.json](review_packets/f16c_20260611/component_binding_report_20260611.json)、[component_binding_report_20260611.csv](review_packets/f16c_20260611/component_binding_report_20260611.csv) | `22` 个部件均有候选区域；`7` 个需要人工复核 |
| TG-P5 距离诊断 | [review_point_diagnostics_20260611.json](review_packets/f16c_20260611/review_point_diagnostics_20260611.json)、[review_point_diagnostics_20260611.csv](review_packets/f16c_20260611/review_point_diagnostics_20260611.csv) | 覆盖 `10` 个测试点；`6` 个点位于外壳区域内；`nose_axis_4m` 距最近部件 `0.2 m`，候选部件 `6` 个 |
| TG-P6 设计草案 | [fine_geometry_proxy_design_20260611.zh.md](fine_geometry_proxy_design_20260611.zh.md) | 定义从长方体升级到倾斜盒、薄棱柱、凸包和简化外壳网格的顺序 |

## 当前边界

- 本状态只证明 TG-P1 来源/尺度 manifest、TG-P2 外壳区域候选、TG-P3 部件绑定、TG-P4 审阅包和
  TG-P5 测试点距离诊断已完成，不证明运行时接入已完成。
- 当前 Sketchfab 模型只作为外形审阅候选，不提供真实内部部件边界。
- 旧 FlightGear F-16 已归档为 GPL v2 强候选来源，不进入主线派生几何。
- 运行时近炸投影仍按现有逻辑运行，直到审阅包和诊断通过后再决定是否接入。

## 下一步

1. 人工复核 `component_binding_report_20260611.csv` 中 `7` 个 `needs_review` 项，特别是左右翼坐标符号和 `wing_spar_center`。
2. 执行 `TG-P6` 后续实现：生成 `fine_geometry_proxy_candidate_20260611.json`，把粗盒子推进为倾斜盒、凸包或简化外壳网格候选，
   再决定是否进入运行时接入评审。

## 验证提醒

每轮变更至少运行：

```bash
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry
```

当前聚焦测试：

```bash
pytest -q tests/tools/test_airframe_geometry_review.py
```

结果：`2 passed`。
