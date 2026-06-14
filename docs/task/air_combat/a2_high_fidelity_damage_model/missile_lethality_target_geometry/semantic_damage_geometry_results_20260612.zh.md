# TG-P6-R12 语义损伤几何实现结果

状态：`2026-06-12` applied / parse-ready candidate / active runtime activation
仍 held。英文辅文：[semantic_damage_geometry_results_20260612.md](semantic_damage_geometry_results_20260612.md)。

本轮开始把已有语义外壳转成损伤模型可理解的部件几何，而不是继续只作为可视化叠加层。

## 已实现

| 切片 | 实现 | 边界 |
| --- | --- | --- |
| 语义体积候选 | 新增 [semantic_damage_geometry_candidate_20260611.json](review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.json) 和 [semantic_damage_geometry_candidate_20260611.csv](review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.csv)。packet 现在包含 `14` 个语义外壳体积部件：雷达罩、前机身蒙皮、座舱盖、中机身蒙皮、进气道、后机身/发动机舱蒙皮、喷口、左右主翼、左右翼根整流、左右平尾和垂尾。 | 仍是候选几何；`runtime_active_component_count=0`。 |
| 独立语义视图 | 中间语义视图已退役。每个语义体积曾有独立 top/side/front 页面，显示该体积 proxy 以及关联 receiver 部件盒。 | 只作审阅证据，不是碰撞网格。 |
| Runtime component schema | `DamageComponent` 新增 `geometry_primitive`、source refs、OBB axes/half-extents、thin-prism 元数据和 vertices；unit loader 能读取 candidate packet 输出的嵌套 `geometry` 对象。 | 向后兼容：旧部件默认仍是 `aabb`。 |
| Runtime component geometry 使用 | 直接命中和空间投影中的 component 距离/曝光辅助函数开始读取 OBB/thin-prism 支撑几何；`convex_hull` 在闭合 hull 审计完成前先使用 vertices 的轴对齐支撑外包。 | 不声明真实 3D hull/path intersection，也不声明真实 F-16 工程几何。 |

## Packet 摘要

- 语义体积部件：`14`。
- Runtime parse-ready component candidates：`14`。
- 已激活 runtime 语义部件：`0`。
- 几何 primitive 覆盖：`convex_hull`、`obb`、`thin_prism`。
- 跨区 handoff held：`8`，来自 `engine_core` 和 `wing_spar_center` receiver ownership。

## 剩余边界

- 当前 F-16 unit 文件仍只有 `26` 个 active runtime components。R12 语义体积以
  `runtime_component_json_candidate` 输出，供受控激活；没有静默改变现有杀伤行为。
- `engine_core` 仍是 intake、aft engine bay 和 nozzle 语义之间的跨区边界候选。
- `wing_spar_center` 仍是 center fuselage、wing roots 和 wing skins 之间的跨区结构语义 held。
- 当前 `convex_hull` 表示简化 mesh-proxy support vertices，还不是闭合碰撞 hull 或扫掠路径求交目标。

## 验证

```bash
python tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
pytest -q tests/tools/test_airframe_geometry_review.py
cmake --build build-workshop --target ef_test -j2
./build-workshop/ef_test --test-suite=components_basic
pytest -q tests/architecture/damage_model
```

聚焦结果：`2 passed`；`ef_test --test-suite=components_basic` 通过 `23` 个 case；
architecture damage-model suite 通过 `177` 个测试。
