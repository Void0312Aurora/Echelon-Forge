# 杀伤链命中盒几何保真度缺口

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/systems/effects/work/issues/lethality_hitbox_geometry_fidelity_gap/README.md`
Owner: `systems/effects`
Last verified: `2026-08-08`

状态：`2026-06-14` retained / first mainline geometry subproject accepted；A2/MLF-5 扩大方位/距离矩阵暴露的当前命中盒几何和近炸投影过粗问题，已通过 F-16C 精细几何工程代理子项目完成 geometry-only 收口。默认 runtime replacement、训练收益和杀伤结论仍不由该几何子项目声明。

首次观察：`2026-06-11`，A2/MLF-5 热力图复核连续杆鼻向 4 m / 6 m 与爆破/破片尾向直接命中结果时。

问题类别：目标几何、部件暴露、近炸投影和部件失效概率之间的建模缺口。

主线执行入口：
[A2 目标外形与部件几何建模](../../../reviews/f16c_target_geometry_20260614/README.zh.md)。

## 摘要

当前杀伤链已经能把起爆后的载荷或切割曝光转成部件失效概率和部件损伤事实，但目标几何仍是少量轴对齐长方体盒子加内部部件盒。

这导致两个问题：

- 一个非常贴近机体边界的鼻向连续杆近炸点可能没有任何部件损伤。
- 热力图中的“4 m / 6 m”容易被误读为普通脱靶距离，而实际是本机坐标点；其中 4 m 落在鼻部盒外，6 m 落在盒内。

这些事实说明当前几何只能作为工程脚手架，不能当作真实战机外形或真实部件布局。

## 当前证据

### 几何判定

当前直接命中判定使用轴对齐盒：

- `check_hitbox(local_p, box)`：点在盒内即为直接命中。
- `check_component(local_p, component)`：点在部件盒内即为部件直接命中。
- 近炸投影使用爆点到盒子或部件盒表面的距离、暴露面积、方向权重和弹头载荷估计。

相关代码：

- [default_effects_geometry_detail.h](../../../../../../src/models/weapons/detail/default_effects_geometry_detail.h)
- [default_effects_direct_hit_detail.h](../../../../../../src/models/weapons/detail/default_effects_direct_hit_detail.h)
- [default_effects_spatial_projection_detail.h](../../../../../../src/models/weapons/detail/default_effects_spatial_projection_detail.h)

### F-16 当前盒子

当前 F-16 几何来自 [f16c_block50.json](../../../../../../examples/config/database/aircraft/units/f16c_block50.json)：

| 区域 | 中心 | 尺寸 | 外包范围 |
| --- | --- | --- | --- |
| 鼻部 | `[6.0, 0.0, 0.0]` | `[3.6, 1.0, 1.0]` | x: `4.2..7.8`, y: `-0.5..0.5`, z: `-0.5..0.5` |
| 机身 | `[0.0, 0.0, 0.0]` | `[7.6, 1.4, 1.2]` | x: `-3.8..3.8`, y: `-0.7..0.7`, z: `-0.6..0.6` |
| 尾部 | `[-6.0, 0.0, 0.0]` | `[3.0, 1.1, 1.1]` | x: `-7.5..-4.5`, y: `-0.55..0.55`, z: `-0.55..0.55` |
| 机翼 | `[-0.8, 0.0, 0.0]` | `[3.0, 9.8, 0.35]` | x: `-2.3..0.7`, y: `-4.9..4.9`, z: `-0.175..0.175` |

合并外包约为 `15.3 m x 9.8 m x 1.2 m`。公开 F-16 整机长/翼展量级接近该长宽，但真实高度约 `4.8 m`；当前盒子高度显著低于整机高度，主要覆盖机身/机翼受损核心，而不是完整垂尾、座舱高度、进气道、外挂和尾翼外形。

### 触发症状

MLF-5 热力图复核中：

- 连续杆鼻向 `x=4.0` 点位于鼻部盒前缘外约 `0.2 m`，不是直接命中。
- 该点在现有统计中出现 `0.000000` 的任意部件触发率。
- 以杀伤模型直觉看，0.2 m 级贴近机体边界的近炸不应完全无部件损伤，因此该结果不能仅用“非直接命中”解释为合理。

同轮复核还发现爆破/破片尾向直接命中过弱的问题；该项已通过直接命中载荷下限修复，但几何保真度问题仍开放。

## 影响

- 阻塞更高保真的导弹杀伤结论：当前几何不能支撑“真实 AIM-120C 打击真实 MQ-9/F-16 后如何碎裂或坠毁”的严格说法。
- 影响热力图解释：本机坐标点、表面距离、脱靶距离和直接命中类别没有在图面上充分分离。
- 影响连续杆/破片近炸：轴向贴近、掠过、遮挡和扫掠面积可能被过度简化，导致“近但无损”或“直接/近炸跳变过大”。
- 影响后续结构解体阶段：若几何输入太粗，后续结构断裂、残骸和碎片对象即使实现，也会继承错误的受损区域。

## 不能宣称

- 不能把当前轴对齐盒子当作真实战机外形。
- 不能把部件盒尺寸当作真实部件尺寸。
- 不能把当前 4 m / 6 m 热力图列当作普通 miss distance 曲线。
- 不能在解决几何缺口前声称部件损伤概率具备真实弹种/真实目标保真度。
- 不能通过简单调高概率来替代几何建模改进。

## 可能原因

1. **外形盒和部件盒混用**：当前父盒既承担外形命中区域，又承担部件投影候选集合，缺少单独的外壳/蒙皮几何。
2. **轴对齐长方体过粗**：真实机鼻、机翼、垂尾、尾喷口、进气道等不是长方体；盒子边界会制造不自然跳变。
3. **近炸距离口径不清**：图面列值是测试点坐标或偏移，不一定是到外形表面的最近距离。
4. **连续杆轴向投影过脆**：当弹头方向不适合扫切时，模型可能把贴近轴向近炸压到几乎无效。
5. **缺少路径求交**：当前直接命中主要看爆点是否落入盒内，未显式表达导弹路径、连续杆扫掠体或破片云穿过目标外壳的几何过程。

## 相关领域上下文

- A2 MLF-5 归档入口：
  [docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/README.zh.md](../../../reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/README.zh.md)
- MLF-5 扩大方位/距离矩阵：
  missile_lethality_component_failure_expanded_matrix_20260611.zh.md (`git show 77610218:docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/archive/mlf_5_component_failure_accepted_20260611/missile_lethality_component_failure_expanded_matrix_20260611.zh.md`)
- MLF-5 可视化摘要：
  missile_lethality_component_failure_visual_summary_20260611.zh.md (`git show 77610218:docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/archive/mlf_5_component_failure_accepted_20260611/missile_lethality_component_failure_visual_summary_20260611.zh.md`)
- F-16 当前几何数据：
  [examples/config/database/aircraft/units/f16c_block50.json](../../../../../../examples/config/database/aircraft/units/f16c_block50.json)
- MQ-9 当前几何数据：
  [examples/config/database/aircraft/units/mq9_reaper.json](../../../../../../examples/config/database/aircraft/units/mq9_reaper.json)

## 下一步门槛

后续几何细化讨论应先形成设计，而不是直接调参。建议门槛：

1. **定义距离口径**：区分本机坐标、到外壳表面最近距离、导弹路径最近距离、引信起爆距离和部件表面距离。
2. **拆分外形与部件**：外形用于命中/遮挡/路径穿越，部件盒用于脆弱区和状态写入。
3. **建立公开尺寸审计**：用公开长、翼展、高度、翼面积或三视图估计检查每个机型外包误差。
4. **补充关键几何区**：机鼻、座舱、机身、机翼、翼根、发动机/进气道、尾翼/垂尾、外挂点应可独立表达。
5. **修正近炸投影**：贴近外壳的非直接近炸不应出现无部件受损的硬断崖，除非有明确遮挡/方向原因和诊断字段。
6. **更新可视化**：热力图应同时显示坐标点、表面距离、是否直接命中、候选部件数和受影响部件数。

工具设计入口：[命中盒几何审阅工具设计](geometry_visual_review_design_20260611.md)。该设计建议先用 GLB 生成外形审阅包和三视图叠加图，再由人工确认外形区域、部件盒和测试点是否合理。

Sketchfab 替代候选入口：[Sketchfab F-16 替代模型短名单](sketchfab_f16_replacement_shortlist_20260611.md)。主线几何候选应从 CC BY 4.0 或更宽松许可的 Sketchfab 模型重新进入，不再从 FlightGear GPL v2 资产派生。

第一轮主线子项目：[A2 目标外形与部件几何建模](../../../reviews/f16c_target_geometry_20260614/README.zh.md)。该子项目已按 geometry-only 验收门闭合；后续 runtime 默认路径替换、训练诊断或其他机型复用必须另行验收。

## GLB 来源状态补充

`2026-06-11` 初查显示，仓库内 F-16 GLB 本身没有 source、author、license 或 Sketchfab UID；`Temp/Model/resource.md`（本地专用、不入库） 也未记录 F-16 来源。

用户随后补充的下载记录指向 [FlightGear Aircraft-2018 f16.zip](https://mirrors.ibiblio.org/flightgear/ftp/Aircraft-2018/f16.zip)。该 zip 服务器时间为 `Fri, 29 May 2020 00:16:42 GMT`，包内 `f16/Models/f16.ac` 时间为 `2020-05-09T04:15:22`，`LICENSE` 为 GNU GPL v2，`README.md` 标识为 FlightGear F-16 Fighting Falcon，`authors.txt` 列出上游贡献者。已有 A2 source pin 也记录过 GitHub [NikolaiVChr/f16](https://github.com/NikolaiVChr/f16) commit `190a699c77bd3c2c7da1e3bb4bffc7a6013bc8f5`，当前 GitHub `master` 仍指向同一提交。

比对结果显示，本地 GLB 的 `117` 个节点/网格名全部能在 FlightGear `f16.ac` 命名对象中找到，包含 `AirIntake`、`RadarDomeTop`、`CanopyBackInside`、`LeftUpperAileron`、`RightUpperAileron`、`Rudder`、`Tail`、`VentralFins`、`LWStation1` 和 `RWStation1`。几何面数不完全一致，说明本地 GLB 可能经过 Blender 转换、合并、删减或重新三角化；但对象名匹配足以把它从单纯未知来源提升为 FlightGear GPL v2 强候选来源。

用户补充的 `blob:https://github.com/70ccc3e5-b369-4d7d-b88d-0dce6c4ea77f` 是浏览器本地 blob URL，不是可直接抓取的 GitHub 文件路径；它只能说明产生该对象的页面 origin 是 GitHub，不能单独证明来源。

当前结论：该 GLB 只保留为历史来源线索和本地对照，不进入主线几何派生路径。后续应优先从 CC BY 4.0 或更宽松许可的 Sketchfab 替代模型重建外形审阅包；即使替代模型许可更友好，它仍只能支持外形审阅和低精度区域设计，不能单独证明真实 F-16C Block 50 内部结构、部件边界、毁伤区或弹药杀伤效果。

## 闭合验收标准

- 至少 F-16 和 MQ-9 的外包尺寸、部件区和公开尺寸审计有可读记录。
- 连续杆/破片近炸测试能覆盖“贴近外壳但非直接命中”的鼻向、尾向、侧向和上下方案例。
- 0.2 m 级贴近外壳近炸不再无解释地产生零部件损伤。
- 诊断输出能解释：最近外壳距离、最近部件距离、候选部件数、是否被遮挡、是否直接命中。
- 任何修复仍不直接声明坠毁、结构解体、残骸或真实弹种 Pk。
