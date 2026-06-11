# Sketchfab F-16 替代模型短名单

状态：`2026-06-11` replacement shortlist；用于替代 FlightGear GPL v2 F-16 资产作为几何审阅候选；同日补充非 Sketchfab 站点调研。

英文辅文：[sketchfab_f16_replacement_shortlist_20260611.md](sketchfab_f16_replacement_shortlist_20260611.md)。

## 结论

FlightGear F-16 资产不进入主线几何生成路径。它只保留为历史来源线索和本地对照，不再作为可发布外形代理、hitbox 或部件区的派生输入。

Sketchfab 检索结果显示，没有发现合适的 CC0 F-16；可用池主要是 CC BY 4.0。CC BY 4.0 允许复制、修改和再分发，但必须署名、保留许可链接、说明是否修改。该许可比 GPL v2 更适合本项目的 Apache-2.0 主线分层，但仍需要 attribution 和来源记录。

非 Sketchfab 调研显示，Blend Swap 存在一个 CC0 的 F-16/F16 候选，许可证最友好，应作为新的第一优先下载核验对象；但它是老版本 Blender 文件且体量较小，几何质量需要实际打开后审查。CGTrader、TurboSquid、3DExport、Free3D、CadNav、MakerWorld 等站点多数是 royalty-free、non-commercial、standard digital file license 或付费/混合许可，不适合作为主线开放几何源。

## 准入规则

候选替代模型必须满足：

- Sketchfab API 显示 `isDownloadable: true`。
- License 为 `CC Attribution / CC BY 4.0` 或更宽松许可。
- 不采用 `NC`、`ND`、`SA` 或 GPL 类许可作为主线几何输入。
- 描述中不能出现明显来源不清、游戏抽取、二次搬运、AI 自动生成或“不属于我”的提示。
- 下载后必须保留原始包 hash、GLB/OBJ hash、作者、UID、URL、发布时间、许可证和本地转换步骤。
- 派生的 hitbox/外形代理必须标注为 `visual_reference_derived` 或 `review_geometry_candidate`，不得声称真实 F-16C Block 50 工程几何。

## 优先候选

### 非 Sketchfab 优先候选

| 优先级 | 站点 | 模型 | URL | 作者 | 许可 | 下载 / 体量 | 判断 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Blend Swap | `F16 jet fighter` | <https://blendswap.com/blend/16639> | `GreenMotion` | CC0 | Blender 2.7x / Cycles，`181 KB` | 当前许可证最友好的主候选；页面写明 CC0、可下载、作者说明为自建 F16 jet fighter。缺点是文件很小、上传超过 10 年，必须下载后检查外形质量、尺度、是否含不必要武器/材质问题。 |
| 2 | Blend Swap | `F16 3D Model` | <https://blendswap.com/blend/4226> | `OKMP` | CC-BY | Blender 2.6x / Blender Internal，`575 KB` | 许可也可接受；描述为给 After Effects inflight CGI 建模的 F16 Fighter Jet。作为 CC0 候选失败后的备选。 |

### Sketchfab 优先候选

| 优先级 | 模型 | UID / URL | 作者 | 许可 | 下载 | 几何量级 | 判断 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | `F16-C Falcon` | `4bc2ff75dc584af2afd0aa6bd8b79015` / <https://sketchfab.com/3d-models/f16-c-falcon-4bc2ff75dc584af2afd0aa6bd8b79015> | `Carlos.Maciel` | CC BY 4.0 | `isDownloadable: true`；已于 `2026-06-11` 下载；GLB 可视化包放在 `examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/`，glTF 审计包放在 `examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/` | `4,504` faces / `2,563` vertices；本地解析 `4,504` triangles / `13,415` position accessor vertices / raw span `9.5618 x 14.9752 x 4.62987`；节点变换后 world span 约 `5.833 x 2.824 x 9.136`，注册表显示 scale 为 `1.65` | Sketchfab 中最干净的主候选：作者链简单、许可明确、面数低，适合快速生成外形审阅代理；缺点是细节较少，需要用公开尺寸校正。glTF 审计包 SHA256：`47388fb8646e704609712d55e0b53eb014571644b7344c7859276597fc63e248`；GLB 可视化包 SHA256：`243f164005c49bce0bb25202e449911fed99cbfa94e9bef25321dcbd7476d44f`。 |
| 4 | `F-16 Fighter Jet` | `d84491f443384ee488593cc6f0f0839e` / <https://sketchfab.com/3d-models/f-16-fighter-jet-d84491f443384ee488593cc6f0f0839e> | `iedalton` | CC BY 4.0 | `isDownloadable: true` | `4,214` faces / `2,874` vertices | 低面数备选，描述为 low poly F-16 with weapons；适合与候选 3 交叉看外形，不建议单独作为最终审阅依据。 |
| 5 | `F16` | `4eecf423b8454c2ba2a371a7bfe9f157` / <https://sketchfab.com/3d-models/f16-4eecf423b8454c2ba2a371a7bfe9f157> | `manilov.ap` | CC BY 4.0 | `isDownloadable: true` | `29,226` faces / `15,240` vertices | 中等面数候选，发布时间较早；描述主要是通用百科文本，来源链仍需下载后检查包内文件。 |

## 暂缓候选

| 模型 | UID / URL | 作者 | 许可 | 几何量级 | 暂缓原因 |
| --- | --- | --- | --- | --- | --- |
| `F-16` | `d898c99707324305bc53b4d224f52602` / <https://sketchfab.com/3d-models/f-16-d898c99707324305bc53b4d224f52602> | `Cxyber` | CC BY 4.0 | `129,861` faces / `77,912` vertices | 细节较好，但描述写有 `Model made by codeata, texture fixes cyber`，作者链需要额外确认。 |
| `F-16 Fighting Falcon | GameReady` | `0793379abcf742aa881c319155c61220` / <https://sketchfab.com/3d-models/f-16-fighting-falcon-gameready-0793379abcf742aa881c319155c61220> | `Pan_Ar4ik` | CC BY 4.0 | `114,684` faces / `58,685` vertices | 面数较高且带武器/贴图，适合作视觉参考；主线几何前需要确认作者链和拆除外挂影响。 |
| `F 16 High Poly (Subdive Ready)` | `eb37548347bf408eb4d5547ee7b67322` / <https://sketchfab.com/3d-models/f-16-high-poly-subdive-ready-eb37548347bf408eb4d5547ee7b67322> | `Andante` | CC BY 4.0 | `300,480` faces / `150,497` vertices | 太重，且缺少明确建模来源说明；可作为外形目视参考，不适合作第一轮代理生成。 |
| `Lowpoly F16 Block 70` | `52c6f5ad114c48adad7a3205a53a56ab` / <https://sketchfab.com/3d-models/lowpoly-f16-block-70-52c6f5ad114c48adad7a3205a53a56ab> | `SIpriv` | CC BY 4.0 | `8,133` faces / `4,218` vertices | 描述指向 ArtStation 图样，需核对是否存在外部素材依赖；机型为 Block 70，不优先用于 F-16C Block 50 审阅。 |

## 其他站点调研

| 站点 | 发现 | 许可/下载状态 | 判定 |
| --- | --- | --- | --- |
| Blend Swap | `F16 jet fighter` by `GreenMotion`；页面写明 CC0、Blender 2.7x / Cycles、`181 KB`、上传超过 10 年。 | CC0，最宽松。 | 新第一优先候选；下载后检查几何质量和尺度。 |
| Blend Swap | `F16 3D Model` by `OKMP`；页面写明 CC-BY、Blender 2.6x、`575 KB`、描述为 After Effects inflight CGI 模型。 | CC-BY。 | 可作为备选；需补 attribution。 |
| BlenderKit | `Low Poly F-16` by `chroma 3D`；页面显示 low-poly F-16、`205.9 KiB`、`2,789` polygons。 | 页面抓取中 license 文本未明确展开，且显示 `Full Plan`/`Free` 混合入口。 | 暂缓；需登录/插件或 license 页面确认。 |
| Meshy AI | F16 标签页宣称免费、CC0、可下载 STL/OBJ/FBX/GLB，但条目多为 AI 生成，且示例写作“inspired by an f-16 or f-22 or f-15”。 | CC0 声称友好，但 AI 生成和机型混合风险高。 | 不作为 F-16 外形约束源；最多用于 UI 占位。 |
| Thingiverse | 搜索结果显示 `F-16 Fighting Falcon by Knerdler` 为 CC BY；另有多项 F-16 打印模型。 | 页面当前环境难以稳定打开；多为 STL/打印件。 | 暂缓；即使 CC BY，也更像打印模型，不优先进入外形审阅。 |
| CGTrader | 存在免费 F-16/F16 条目，例如 `F-16 Fighting Falcon` 和 `F16 Fighter Plane`；页面写 `Royalty Free License (no AI)`。 | royalty-free，不是开放许可；下载和条款需账号/平台协议。 | 不作为开放主线几何源；只可本地视觉参考。 |
| TurboSquid | 有 free/low-poly F-16 搜索页，写 royalty-free license / extended usage。 | royalty-free marketplace。 | 不作为开放主线几何源；只可本地视觉参考。 |
| 3DExport | F16 搜索页列出 royalty-free F16 模型，混合免费/付费。 | royalty-free marketplace。 | 不作为开放主线几何源。 |
| CadNav | `F-16 Fighting Falcon 3D Model` 页面写 `.3ds/.max`、`6415` polygons、`6567` vertices。 | 明确 `License: Non-commercial`。 | 拒绝主线使用。 |
| Free3D | F-16 结果多为付费模型，页面未给开放许可。 | 付费/royalty-free marketplace。 | 不作为开放主线几何源。 |
| MakerWorld | F-16 打印模型页面使用 `Standard Digital File License`。 | 非开放许可，偏打印生态。 | 拒绝主线使用。 |

## 后续接入步骤

1. 优先下载 Blend Swap `F16 jet fighter` 原始包，记录下载时间、原包 hash、文件清单和许可证截图/metadata。
2. 若 Blend Swap CC0 模型几何不足，再下载 Sketchfab `F16-C Falcon` 作为备选；运行时保留 GLB，可审计/几何检查保留 glTF 或 source 包，记录 Sketchfab UID、URL、作者、CC BY 4.0、发布时间、下载时间和转换步骤。
3. 用工具解析模型 bounds、三角数、节点名和坐标轴。
4. 用公开长、翼展、高度对模型定标；不直接把模型原始尺度当事实。
5. 生成只读审阅包：三视图、外形代理、旧 hitbox 叠加和 MLF-5 测试点。
6. 人工确认外形区域后，再考虑是否把简化外形代理作为 `review_geometry_candidate` 进入主线。

## 不采用项

- FlightGear GPL v2 F-16：不再作为主线几何派生输入。
- CC BY-SA / GPL / ODbL 等共享同款许可：避免把主线数据带入不必要的再授权义务。
- CC BY-NC / CC BY-ND：不适合主线派生几何。
- 来源不清、疑似游戏抽取、付费包搬运、论坛附件或网盘模型。
