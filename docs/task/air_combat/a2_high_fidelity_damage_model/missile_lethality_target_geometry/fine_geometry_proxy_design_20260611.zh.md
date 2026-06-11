# TG-P6 精细几何代理设计

状态：`2026-06-11` TG-P6-R1 design draft。英文辅文：
[fine_geometry_proxy_design_20260611.md](fine_geometry_proxy_design_20260611.md)。

## 目的

当前 TG-P1 到 TG-P5 已经能说明一件事：旧命中盒太粗，新的外壳区域虽然能解释
`nose_axis_4m` 等点，但它仍然是长方体。下一步不能把这些长方体直接当成更真实的飞机外形。

TG-P6 的目标是把“审阅用盒子”升级成“更贴近外形的代理形状”，让近炸距离、连续杆路径和破片路径
先经过更合理的外形判断，再把结果交给已有的部件损伤链。

## 不做什么

- 不把高模 GLB 直接塞进每帧碰撞。
- 不从外形模型自动推断真实内部设备边界。
- 不在这一阶段声明真实 F-16 工程结构、真实弹种杀伤率、结构解体或残骸。
- 不用更复杂的形状来掩盖左右翼坐标符号、部件过大或位置错配问题。

## 代理形状分层

| 层级 | 形状 | 用途 | 进入运行时前的要求 |
| --- | --- | --- | --- |
| `review_aabb` | 当前长方体 | 第一轮人工看位置、发现离谱覆盖 | 只能审阅，不能作为最终几何保真度 |
| `obb` | 可旋转盒子 | 机身段、座舱、进气道、发动机段等有明确方向的区域 | 需要记录中心、三条轴和半尺寸，并能画到三视图 |
| `thin_prism` | 很薄的棱柱 | 机翼、水平尾翼、垂尾等薄面 | 需要避免把大片空气算成飞机本体 |
| `convex_hull` | 外壳点包络 | 机鼻、翼根、尾翼等不适合长方体的区域 | 需要记录顶点来源和简化误差 |
| `simplified_shell` | 简化外壳网格 | 最终外形距离、穿越和扫掠测试候选 | 需要单独的离线审阅和性能评估 |

## 第一轮区域建议

| 区域 | 当前问题 | 第一候选 |
| --- | --- | --- |
| `nose_radome` | 长方体会把机鼻当成等宽块 | `convex_hull` 或渐缩 `thin_prism` |
| `forward_fuselage` | 能解释 4 m 点，但仍然过方 | `obb`，后续可拆成机身和座舱底部 |
| `canopy` | 高度必须独立处理 | 独立 `convex_hull` 或小 `obb` |
| `center_fuselage` | 适合先做方向对齐 | `obb` |
| `intake` | 下方形状不能被机身盒覆盖 | 独立 `convex_hull` |
| `aft_fuselage_engine` | 尾向杀伤对发动机段敏感 | `obb` |
| `engine_nozzle` | 尾喷口更接近圆/短筒 | 短 `obb`，后续可用简化圆截面 |
| `left_wing` / `right_wing` | 长方体会把翼外空气算进去 | `thin_prism` |
| `left_wing_root` / `right_wing_root` | 翼根和机身过渡不应只归单侧 | `convex_hull` 或双侧过渡代理 |
| `left_horizontal_tail` / `right_horizontal_tail` | 薄面，不应变厚盒 | `thin_prism` |
| `vertical_tail` | 高而薄，旧盒子高度缺口明显 | `thin_prism` 或 `convex_hull` |

## 建议数据结构

```json
{
  "schema_version": "a2.target_geometry_fine_proxy_candidate.v1",
  "source_region_id": "left_wing",
  "proxy_kind": "thin_prism",
  "source_basis": "review_mapping_plus_audit_mesh_silhouette",
  "vertices_m": [[0.0, 0.0, 0.0]],
  "obb": {
    "center_m": [0.0, 0.0, 0.0],
    "axes": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    "half_extents_m": [1.0, 1.0, 0.05]
  },
  "fit_metrics": {
    "aabb_volume_ratio": 0.25,
    "max_surface_delta_m": null,
    "review_point_distance_delta_m": null
  },
  "runtime_allowed_use": ["distance_diagnostic_candidate"],
  "review_status": "manual_review_required"
}
```

## 运行时切入点

- 近炸：先用精细外壳代理计算最近外形距离和最近外形区域；它只解释“离飞机外壳有多近”，不直接决定击毁。
- 连续杆：用路径段或扫掠体与外壳代理求交，输出穿过的外壳区域和候选部件，再交给已有损伤链。
- 破片：用破片路径与外壳代理求交，得到进入点、出射方向和候选部件排序，再由部件损伤链决定效果。
- 部件失效：继续通过已有部件损伤和飞行动力学传播，不在几何层单独定义“还能不能飞”。

## 第一轮实现顺序

1. 生成 `fine_geometry_proxy_candidate_20260611.json`，先覆盖 F-16 的 `14` 个外壳区域。
2. 为机翼、水平尾翼和垂尾生成 `thin_prism`，为机身段生成 `obb`，为机鼻/座舱/进气道生成待审阅 `convex_hull` 候选。
3. 在三视图上叠加精细代理和当前长方体，输出体积差、外包差和测试点距离差。
4. 复核左右翼坐标符号后，才允许把翼面代理用于连续杆或破片路径候选。
5. 只有 TG-P6 审阅通过后，TG-P7 才能讨论运行时接入。

## 验收标准

- 每个外壳区域都有一个精细代理候选，或者明确写出为什么暂缓。
- 精细代理比当前长方体少覆盖明显空气，尤其是机翼、尾翼、机鼻和进气道。
- `nose_axis_4m`、`nose_axis_6m`、侧向和上下方位测试点能输出新旧距离对比。
- 左右翼命名和坐标符号问题不得被自动“修正”或静默忽略。
- 输出仍然标记为审阅候选，不进入运行时主路径。
