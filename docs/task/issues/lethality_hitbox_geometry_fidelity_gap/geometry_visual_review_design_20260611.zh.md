# 命中盒几何审阅工具设计

状态：`2026-06-11` proposed design，用于 [README.zh.md](README.zh.md) 的下一步讨论；本文件只设计工具和数据门，不实现运行时几何替换。

英文辅文：[geometry_visual_review_design_20260611.md](geometry_visual_review_design_20260611.md)。

## 目标

建立一个小型审阅工具，把视觉 GLB、公开尺寸、外形分区、现有部件盒和测试点一起导出为可人工审阅的图样或场景。它先解决“几何是否合理、距离口径是否清楚、部件是否放在合理区域内”，再让后续杀伤概率模型消费这些几何事实。

第一轮目标不是把 GLB 直接塞进运行时，而是生成一个可复核的 geometry review packet：

- 一个静态 HTML/Three.js 场景，用来旋转查看外形、区域、部件盒和测试点。
- 顶视/侧视/正视 SVG 图，用来快速审查外形与部件区域是否贴合。
- 一个 JSON manifest，记录来源、hash、坐标轴、尺度、外形分区、部件绑定和审阅状态。
- 一个诊断表，列出每个测试点的本机坐标、最近外形距离、最近部件距离、是否直接穿入、候选部件数。

## 当前资产观察

本地 F-16 资产：

- 当前可视化 GLB：[examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb](../../../../examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb)
- 当前审计 glTF 场景：[examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf](../../../../examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf)
- 当前审计 glTF 原始包：[examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/4bc2ff75dc584af2afd0aa6bd8b79015_gltf.zip](../../../../examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/4bc2ff75dc584af2afd0aa6bd8b79015_gltf.zip)
- 旧 FlightGear 候选归档：[examples/viz/web_viz/static/assets/archive/f16_flightgear_gplv2_candidate_20260611/f16.glb](../../../../examples/viz/web_viz/static/assets/archive/f16_flightgear_gplv2_candidate_20260611/f16.glb)
- 同一文件也存在于 Godot 归档：[archive/20260530_game_godot_local_archive/game/client/godot_project/assets/models/f16.glb](../../../../archive/20260530_game_godot_local_archive/game/client/godot_project/assets/models/f16.glb)
- 当前替代模型 source：Sketchfab `F16-C Falcon`，UID `4bc2ff75dc584af2afd0aa6bd8b79015`，author `Carlos.Maciel`，license `CC-BY-4.0`。
- 当前替代原始包 SHA256：`47388fb8646e704609712d55e0b53eb014571644b7344c7859276597fc63e248`。
- 当前可视化 GLB SHA256：`243f164005c49bce0bb25202e449911fed99cbfa94e9bef25321dcbd7476d44f`。
- 当前替代几何量级：Sketchfab 元数据 `4,504` faces / `2,563` vertices；本地解析 `4,504` triangles / `13,415` position accessor vertices；节点变换后 world span 约 `5.833 x 2.824 x 9.136`，registry 显示 scale 为 `1.65`。
- 当前替代节点命名可用：`Canopy01_1`、`Eject_Seat_3`、`Pilot_4`、`ElevatorR01_7`、`AileronR01_8`、`AileronL01_9`、`VoletR01_14`、`VoletL01_15`、`EngineL01_17`、`RudderL01_18`。
- 旧 FlightGear 候选 SHA256：`7c432edcaec14bc52a262d2ef311b19c525452e2614400c3c10f8e93da1b7ee0`。
- 旧 FlightGear 候选本地文件系统时间：原 `examples/viz` 副本 birth `2026-01-20T00:35:49+08:00`，mtime `2026-01-20T00:35:50+08:00`；Godot 归档副本 birth/mtime `2026-05-15T17:43:08+08:00`。
- 旧 FlightGear 候选 Git 首次引入：`bf1597d45486f3f866ec523a9d572e84374799d3`，author/commit time `2026-01-21T14:21:10+08:00`，提交标题 `1·21-14：21|更新v0.0.7`。
- 旧 FlightGear 候选 GLB metadata：只有 `Khronos glTF Blender I/O v5.0.21`，没有 `source`、`author`、`license` 或 Sketchfab UID。
- 旧 FlightGear 候选几何量级：约 `4,989` triangles；位置 accessor 顶点计数约 `4,684`；accessor 外包约 `15.65 x 9.59 x 5.17`。

本地来源记录：

- [Temp/Model/resource.md](../../../../Temp/Model/resource.md) 只记录了 DDG、Patuxent、低多边形导弹等来源，没有记录 F-16。
- [examples/viz/web_viz/static/assets/missiles/ATTRIBUTION.md](../../../../examples/viz/web_viz/static/assets/missiles/ATTRIBUTION.md) 和 [uav/ATTRIBUTION.md](../../../../examples/viz/web_viz/static/assets/uav/ATTRIBUTION.md) 已有导弹/MQ-9 attribution，但 F-16 资产目录没有同级 attribution。

FlightGear 来源线索：

- 用户补充的下载记录指向 [FlightGear Aircraft-2018 f16.zip](https://mirrors.ibiblio.org/flightgear/ftp/Aircraft-2018/f16.zip)；服务器 `Last-Modified` 为 `Fri, 29 May 2020 00:16:42 GMT`，`Content-Length` 为 `312425093`。
- 压缩包包含 `f16/` FlightGear F-16 包，共 `1215` 个条目；关键条目包括 `f16/LICENSE`、`f16/README.md`、`f16/authors.txt`、`f16/Models/f16.ac` 和 `f16/Models/F-16.xml`。
- 包内时间戳：`f16/LICENSE` 为 `2018-10-13T21:07:10`，`f16/authors.txt` 为 `2020-05-09T04:15:28`，`f16/Models/f16.ac` 为 `2020-05-09T04:15:22`，`f16/Models/F-16.xml` 为 `2020-05-29T00:15:10`，`f16/README.md` 为 `2020-05-29T00:15:14`。
- `LICENSE` 为 GNU GPL v2；`README.md` 标识该包为 FlightGear F-16 Fighting Falcon，`authors.txt` 列出 Erik Hofman、Nikolai V. Chr.、J Maverick 16、Richard Harrison、Justin Nicholson 等贡献者。
- 已有 A2 数据采集记录也 pin 过 [FlightGear `NikolaiVChr/f16`](https://github.com/NikolaiVChr/f16)，commit `190a699c77bd3c2c7da1e3bb4bffc7a6013bc8f5`，并将其标为开源社区仿真候选，只允许做外形/命名 sanity。
- GitHub 当前 `master` 仍指向 `190a699c77bd3c2c7da1e3bb4bffc7a6013bc8f5`，和既有 source pin 一致。
- 本地 GLB 与 FlightGear `f16/Models/f16.ac` 的对象名高度吻合：本地 `117` 个节点/网格名全部能在 `f16.ac` 命名对象中找到，包含 `AirIntake`、`RadarDomeTop`、`CanopyBackInside`、`LeftUpperAileron`、`RightUpperAileron`、`LeftUpperFlap`、`RightUpperFlap`、`Rudder`、`Tail`、`VentralFins`、`LWStation1`、`RWStation1`。
- 几何量级不完全相同：本地 GLB 为约 `4,989` triangles / `4,684` 位置 accessor 顶点；FlightGear `f16.ac` 为 `1,706,737` 字节，命名对象 `124` 个，`numvert` 合计 `10,470`，按面 refs 粗略三角化下限约 `17,722`。这说明本地 GLB 很可能经过 Blender 转换、合并、删减或重新三角化；对象名匹配足以支撑“强候选来源”，但不等同于逐顶点可复现证明。
- 用户补充的 `blob:https://github.com/70ccc3e5-b369-4d7d-b88d-0dce6c4ea77f` 是浏览器本地 blob URL，只说明对象产生时页面 origin 是 GitHub；它不是可直接抓取的 GitHub 文件路径，不能单独作为来源证明。

网上初步候选：

- Sketchfab 上存在 `F16-C Falcon` by Carlos.Maciel，免费可下载，但当前本地 GLB 缺少可确认 UID，且 FlightGear 对象名匹配更强；该线索降级为次要候选。
- `F16-C Falcon` 候选的 Sketchfab API 记录：UID `4bc2ff75dc584af2afd0aa6bd8b79015`，createdAt `2022-02-28T12:38:47.839845`，publishedAt `2022-02-28T12:46:12.308593`，author `Carlos.Maciel`，license `CC Attribution / CC BY 4.0`，faceCount `4504`。该 faceCount 接近但不等同于本地解析到的约 `4,989` triangles，因此只能作为候选线索，不能作为匹配证明。
- Sketchfab 上也存在多个 F-16 免费模型，例如 `F-16 Fighting Falcon - Fighter Jet - Free`、`F-16 Fighting Falcon Jet Fighter Aircraft`、`Low-Poly F-16 Fighting Falcon` 等；这些模型的三角数/授权条款和当前本地文件不完全吻合。

结论：当前 F-16 GLB 可确认是 FlightGear GPL v2 强候选来源，但不进入主线几何派生路径。它只保留为历史来源线索和本地对照。后续主线几何候选改从 [Sketchfab F-16 替代模型短名单](sketchfab_f16_replacement_shortlist_20260611.zh.md) 重新进入，优先采用 CC BY 4.0 或更宽松许可的可下载模型。

## 来源准入门

几何工具必须先输出 `asset_source_status`：

| 状态 | 含义 | 允许用途 |
| --- | --- | --- |
| `verified_redistributable` | source、author、license、hash 均已记录，授权允许派生几何随仓库分发 | 可生成并提交外形代理和审阅包 |
| `matched_flightgear_gplv2_candidate` | FlightGear 来源、作者、GPL v2 许可和对象名匹配证据已记录；仍是社区仿真资产，不是官方几何 | 可做本地审阅、三视图、低精度区域草案；派生几何进入主线前必须单独确认 GPL v2 接纳策略 |
| `rejected_for_mainline_license` | 来源可追，但许可会给主线几何数据带来不必要的再授权义务 | 只保留为历史线索或本地对照，不生成主线派生几何 |
| `verified_review_only` | source 和 license 已记录，但授权限制只允许本地/非商业/不可派生主线数据 | 可本地审阅，不可把派生几何作为主线事实提交 |
| `source_unverified` | 只有文件和 hash，缺少来源/授权闭合；如果 FlightGear 匹配后来被推翻，F-16 回落到此状态 | 只能做本地候选审阅，不可提升为权威几何 |
| `rejected` | 来源或授权不适合，或模型与机型明显不符 | 不进入几何管线 |

现有 FlightGear F-16 资产按 `rejected_for_mainline_license` 处理。后续应：

- 保留 FlightGear attribution 和匹配证据，避免以后重复追溯；
- 换用来源清楚、授权更适合仓库派生数据分发的 Sketchfab GLB，再重新生成几何代理。

## 数据分层

### 1. 视觉资产层

字段示例：

```json
{
  "asset_id": "f16c_visual_candidate_20260611",
  "runtime_visual_path": "examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb",
  "audit_scene_path": "examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf",
  "source_status": "visual_reference_derived",
  "source_ref": "Sketchfab F16-C Falcon / UID 4bc2ff75dc584af2afd0aa6bd8b79015",
  "source_license": "CC-BY-4.0",
  "visual_glb_sha256": "243f164005c49bce0bb25202e449911fed99cbfa94e9bef25321dcbd7476d44f",
  "archive_sha256": "47388fb8646e704609712d55e0b53eb014571644b7344c7859276597fc63e248",
  "asset_bounds_m": [5.833, 2.824, 9.136],
  "axis_map": {
    "asset_x": "sim_right",
    "asset_y": "sim_up",
    "asset_z_negative": "sim_forward"
  }
}
```

### 2. 外形区域层

外形区域来自 GLB 节点、节点名规则和人工校正：

```json
{
  "outer_regions": [
    {"id": "nose_radome", "source_nodes": ["RadarDomeTop"], "role": "outer_skin"},
    {"id": "canopy", "source_nodes": ["CanopyBackInside", "CanopyForwardOutside"], "role": "outer_skin"},
    {"id": "air_intake", "source_nodes": ["AirIntake"], "role": "outer_skin"},
    {"id": "left_wing", "source_nodes": ["LeftUpperAileron", "LeftUpperFlap", "LWStation1"], "role": "lifting_surface"},
    {"id": "right_wing", "source_nodes": ["RightUpperAileron", "RightUpperFlap", "RWStation1"], "role": "lifting_surface"},
    {"id": "tail", "source_nodes": ["Tail", "Rudder", "VentralFins"], "role": "tail_surface"}
  ]
}
```

每个区域可导出为：

- `aabb`：最便宜，适合作为第一轮审阅。
- `obb`：更贴合局部姿态。
- `convex_hull`：适合路径/外壳近似。
- `simplified_mesh`：适合最终外形距离和穿越测试。

### 3. 部件脆弱区层

部件仍来自数据库 `damage_model.components`，但必须绑定到外形区域：

```json
{
  "component_bindings": [
    {
      "component_name": "apg68_radar_array",
      "expected_outer_region": "nose_radome",
      "current_box": {"center": [6.6, 0.0, 0.0], "size": [1.2, 0.8, 0.6]},
      "review_status": "needs_visual_check"
    }
  ]
}
```

人工审阅时重点看：

- 部件是否落在对应外形区域内。
- 部件盒是否超出外形表面过多。
- 部件是否过大导致误伤，或过小导致贴近外壳近炸无候选。
- 当前命中盒是否与 GLB 外壳严重偏离。

### 4. 测试点层

每个热力图/探测点都应导出为可视化对象：

```json
{
  "review_points": [
    {
      "id": "mlf5_continuous_rod_nose_x4",
      "local_point": [4.0, 0.0, 0.0],
      "warhead_family": "continuous_rod",
      "expected_question": "0.2m close-to-skin should not silently produce zero component candidates"
    }
  ]
}
```

工具应计算并展示：

- 最近外形区域；
- 最近外形距离；
- 最近部件；
- 最近部件距离；
- 是否位于外形内；
- 是否位于部件盒内；
- 候选部件数；
- 现有模型实际触发部件数。

## 小工具设计

建议入口：

```bash
python tools/geometry/airframe_geometry_review.py \
  --aircraft examples/config/database/aircraft/units/f16c_block50.json \
  --asset examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf \
  --mapping docs/task/issues/lethality_hitbox_geometry_fidelity_gap/f16c_geometry_mapping_candidate_20260611.json \
  --review-points docs/task/issues/lethality_hitbox_geometry_fidelity_gap/mlf5_geometry_review_points_20260611.json \
  --out docs/task/issues/lethality_hitbox_geometry_fidelity_gap/review_packets/f16c_20260611
```

输出：

```text
review_packets/f16c_20260611/
  manifest.json
  geometry_summary.md
  scene.html
  top.svg
  side.svg
  front.svg
  review_points.csv
  component_binding_report.csv
```

`scene.html` 应可离线打开，显示：

- 原始 GLB；
- 简化外形区域；
- 当前大 hitbox；
- 当前部件盒；
- 热力图测试点；
- 连线：测试点到最近外形/最近部件；
- 图例和开关：outer shape、damage regions、components、review points、legacy boxes。

## 实现顺序

1. **资产审计**
   - 解析 GLB metadata、hash、节点名、外包尺寸、三角数。
   - 读取本地 attribution；若缺失，先标记 attribution gap。
   - 记录 FlightGear zip/GitHub commit、GPL v2、authors、关键文件时间戳和对象名匹配证据。
   - 将 FlightGear 标记为 `rejected_for_mainline_license`，只作历史线索和本地对照。
   - 从 Sketchfab 短名单选择 CC BY 4.0 或更宽松许可的替代模型，重新记录 UID、作者、hash 和下载时间。

2. **F-16 只读审阅包**
   - 从 GLB 节点名粗分区。
   - 叠加当前 F-16 hitbox/component box。
   - 输出三视图 SVG 和静态 HTML。
   - 不改变 runtime。

3. **人工映射文件**
   - 人工确认节点到区域的映射。
   - 人工确认部件属于哪个外形区域。
   - 标出明显不合理的盒子：例如高度过低、边界硬断崖、部件不在外形内。

4. **几何事实诊断**
   - 对 MLF-5 热力图测试点输出最近外形距离、最近部件距离和候选部件数。
   - 复查 `x=4.0` 鼻向连续杆近炸是否被识别为贴近外壳。

5. **运行时设计评审**
   - 决定第一轮 runtime 是否使用外形代理距离。
   - 决定连续杆是否使用扫掠体/路径与外形区域求交。
   - 决定是否保留旧 hitbox 作为 fallback。

## 验收标准

- 工具能在不改运行时的情况下生成 F-16 审阅包。
- registry 使用单文件 GLB 做运行时可视化；审阅工具使用 glTF/原始包做来源审计和几何检查。
- 审阅包能同时显示审计模型外形、当前大 hitbox、当前部件盒和测试点。
- manifest 明确写出 FlightGear F-16 为 `rejected_for_mainline_license`；新替代模型必须写出 Sketchfab UID、作者、CC BY 4.0、hash 和下载时间。
- `x=4.0` 鼻向测试点能显示最近外形距离和最近部件距离，而不是只显示“非直接命中”。
- 至少有一张顶视图和一张侧视图能让人直接看出当前旧 hitbox 高度不足的问题。

## 不做事项

- 不在第一轮把高模 GLB 直接用于每帧运行时碰撞。
- 不通过调高概率掩盖几何缺口。
- 不把 FlightGear 社区仿真资产生成的派生几何提交为真实 F-16C Block 50 权威主线数据。
- 不在 GPL v2 接纳策略明确前，把 GPL v2 派生几何静默混入仓库主线数据。
- 不在本工具里声明坠毁、结构解体、残骸或真实弹种 Pk。
