# 战术地图界面风格参考基线

状态：`2026-06-06`，战术地图界面重构的 `P0` 参考基线。本文件是视觉设计基线，不是作战标准合规权威。

父项：[战术地图界面重构](README.zh.md)

## 决策

`examples/viz` 战术界面应演进为克制的地图优先态势显示。它可以借鉴军用符号、专业 GIS、航海/图表呈现、通用态势图工具和公开 OSINT 态势图的视觉经验，但不得声明实现具备条令正确性或标准合规性。

## 参考族

| 类型 | 可借鉴经验 | 本地用途 | 边界 |
| --- | --- | --- | --- |
| 军用符号标准 | 阵营、单位身份、战术图形和绘制顺序纪律。 | 使用蓝/红/中立/未知语言、简化单位框、路线、接触/不确定性标记。 | 不声明 MIL-STD-2525 或 APP-6 合规。 |
| GIS 与图表呈现 | 图层层级、比例尺、低饱和底图和密集叠加可读性。 | 分离底图、作战叠加、任务图形、环境图层和调试辅助。 | 不声明大地测量或海图认证。 |
| 通用态势图工具 | 地图优先工作流、可折叠侧栏、接触列表和快速聚焦控制。 | 使用 docked panels 和地图表面切换，同时不隐藏地图。 | 不声明与 TAK 或其他 COP 系统互操作。 |
| 公开 OSINT 态势图 | 区域/控制/前线不确定性和公众可读标注。 | 使用虚线不确定性、低饱和控制填充和紧凑区域标签。 | OSINT 地图惯例只是呈现参考，不是仿真真值。 |

实现前应检查的参考链接：

- DLA QuickSearch MIL-STD-2525 条目：
  <https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=114934>
- Army FM 1-02.2 military symbols public PDF mirror：
  <https://rdl.train.army.mil/catalog-ws/view/100.ATSC/CD4DFE54-1C0B-43D9-B8BA-B869F10E6561-1739243205786/FM1_02x2.pdf>
- ArcGIS Pro Military Symbology Editor：
  <https://pro.arcgis.com/en/pro-app/latest/help/production/military-symbology-editor/military-symbology-editor-intro.htm>
- IHO ENC portrayal：
  <https://iho.int/en/enc-portrayal>
- TAK.gov：
  <https://tak.gov/>
- ISW/CTP cartographical methodology：
  <https://www.understandingwar.org/sites/default/files/Cartographical%20Methodology%20Explanation%20ISW%20CTP%202022.pdf>
- War Mapper public map archive：
  <https://www.warmapper.org/>

## 界面原则

- 地图是第一对象。第一视口应展示作战态势，而不是控件堆叠。
- 控制区应 dock、可折叠、分组且可预期。长期形态不应是永久顶栏塞满图层按钮。
- 允许多张地图。单个“战术地图”可以演进为带具名表面的工作区，而不是一个过载 canvas。
- 文本应紧凑并绑定到地图对象。应用内避免长篇功能说明。
- 调色板应服务功能而不是单色主题：暗中性地图底、蓝/红阵营、琥珀警告、低饱和绿/棕/灰环境叠加，以及虚线不确定性。
- 调试信息属于 debug layer 或 inspector，不应进入默认呈现。

## 拟定地图表面

| Surface | 主要问题 | 默认图层 | 说明 |
| --- | --- | --- | --- |
| `COP` | 发生了什么，友/敌单位在哪里？ | 底图网格、单位、路线、航迹、传感器环、必要时的武器。 | 海/空和混合域战术视图的主默认值。 |
| `Environment` | 哪些地形、区域、道路、建筑、植被或天气上下文重要？ | 底图网格、环境叠加、区域标签、可选任务区域。 | 初始只使用已接受的 G0 overlay payload。 |
| `Tracks/Sensors` | 什么被探测、链接、不确定或瞄准？ | 航迹、传感器环、数据链、武器、不确定性标记。 | 适用于空/海，后续也可承接陆军感知工作。 |
| `3D Inspect` | 聚焦单位或局部几何是什么样？ | 既有 3D 视图与聚焦控制。 | 这是 workspace surface，不是地图的替代品。 |

## 图层分组

| Group | 示例 | 默认 |
| --- | --- | --- |
| Base | 网格、比例尺、范围、可选底图色调 | on |
| Units | 友方、敌方、中立、未知单位 | on |
| Mission | 路线、目标、巡逻区、接触线 | present 时 on |
| Sensors/Tracks | 传感器环、数据链、航迹、目标提示 | 空/海 on；可由 profile 选择 |
| Effects | 武器、爆炸、警告、终局状态 | present 时 on |
| Environment | G0 区域、地形区、建筑、道路、植被、天气叠加 | 陆军/环境 profile on |
| Debug | raw ids、payload diagnostics、evidence flags | 默认 off |

## Profile 与 Scenario 边界

| Concern | 属于 profile/UI | 属于 scenario |
| --- | --- | --- |
| 默认地图表面 | yes | no |
| 默认可见图层组 | yes | no |
| 战术缩放/相机/聚焦 | yes | no |
| 单位初始位置 | no | yes |
| 地形/建筑/道路语义 | no | yes，但需由环境/scenario contract 所有 |
| 机动/可通行/LOS/战斗真值 | no | yes，且只有所属 runtime 工作线验收后才成立 |

## 第一版实现形态

优先的第一版实现：

1. 地图优先壳：中央 map/workspace 区域、细顶栏状态条、可折叠左侧 session/profile 面板、可折叠右侧 inspector/layer 面板。
2. Workspace selector：用于 `COP`、`Environment`、`Tracks/Sensors`、`3D Inspect` 的小型 tab 或 segmented control。
3. Layer tray：分组 toggles，具有清晰 active state 和紧凑标签。
4. 响应式规则：窄屏下 panel 只有用户明确打开时才覆盖地图，不永久占据第一视口。
5. 浏览器证据：接受前保留窄屏和桌面截图。

## Held 项

- 军标级符号合规。
- 真实地理投影和地图瓦片处理。
- Scenario 编辑器和地形生成器 UI。
- 环境 runtime 行为、地形感知机动、LOS、掩蔽、感知或战斗行为。
