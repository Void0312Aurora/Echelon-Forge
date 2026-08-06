# 可视化技术栈演进规划（战役/战略尺度北极星）

Language: Chinese companion of [the English canonical document](viz_stack_evolution.md).

Document kind: `plan`
Lifecycle: `maintained`
Canonical: `docs/operations/visualization/work/issues/viz_stack_evolution.md`
Owner: `operations/visualization`
Last verified: `not established`
Content status: not reverified during the 2026-08-07 ownership migration.

> **状态**: 规划中（部分基础已落地）
> **最后更新**: 2026-07-21
> **相关分支**: `codex/viz-unified-scene-rendering`

## 执行摘要

可视化的远期目标是从当前的战术层（km 级局部场景、平台级实体）扩展到**战役乃至战略层面**：国家规模的地理范围、编制聚合的态势呈现、跨尺度无缝缩放。本文档记录为此确立的演进路径与排序依据，核心结论：

1. **推倒重来的风险在数据契约，不在渲染引擎**。契约种子已提前埋下（见"已就位的基础"）；
2. 大型架构项（状态流 v2、2D WebGL 化）**排在其上游依赖之后**，而非按"迟早要做"提前动手；
3. 排序标准是**决策信息是否齐备**：正确形态今天可确定的立即做，形态取决于未定需求的等上游定型。

## 尺度跨越的本质变化

国家规模可视化不是"更大的战术图"：

| 维度 | 战术层（现状） | 战役/战略层（目标） |
|------|--------------|-------------------|
| 坐标 | 局部 ENU 平面（km 级，平面近似成立） | 全球地理坐标（曲率与投影畸变不可忽略） |
| 实体 | 平台级（架/艘/辆），全量渲染 | 编制聚合（营/旅/师图标、战线、补给轴线） |
| 数据 | 一次性全量载荷 | 瓦片化 / 流式 / 按区域订阅（AOI） |
| 时间 | 分钟级回合，帧即弃 | 天/周跨度，回放与事件流成为一等公民 |

## 已就位的基础（fait accompli）

| 提交 | 内容 | 对远期目标的意义 |
|------|------|----------------|
| `8c46e1f6` | 光照参数化：场景 `environment.illumination` → 引擎 `IEnvironmentModel` → viz 双视图同源 | 确立"显示与作战判定同一真值"范式，可复制到风/天气/能见度 |
| `7bac7da3` | 四颗契约种子：大地锚点（`geodetic_anchor`）、MIL-STD-2525 SIDC 词汇、单位 `echelon` 字段、线上契约版本 | 锚点=局部场景可挂全球；SIDC/编制=聚合渲染的数据前提；版本=协议可协商迁移 |
| `6c3c1ea9` | eventlet 退役，统一 threading | 摆脱弃维护依赖；`socketio.sleep` 委托使未来 ASGI 切换无需改会话代码 |
| `e5374b92` | 零构建 JSDoc 类型化（`types.js` + jsconfig + 核心模块 `@ts-check`） | 线上契约有机器检查的类型镜像，AI/多人协作的质量地板 |

契约测试锚点：`tests/viz/test_strategic_scale_seeds.py`、`tests/viz/test_frontend_typing.py`、`tests/viz/test_illumination_pipeline.py`。

## 排序原则

**种子类工作**（正确形态由既有标准确定：WGS84、2525、语义化版本）→ 立即做，成本低、防返工价值高。已完成。

**架构类工作**（正确形态取决于尚未定型的战役层需求）→ 排在上游之后。提前做会把当前形态固化进去，到战役层仍需推倒，且带着"已迁移"的沉没成本。

## 演进项清单

### 1. 状态流 v2（delta + AOI + 聚合 + 二进制）

- **现状**：30 Hz 全量 JSON 帧（`examples.viz.state_frame.v1`），静态字段每帧重复。
- **为什么不是"JSON 换 MessagePack"**：单纯二进制化只省序列化 CPU，帧语义不变，是最浅收益；真正的 v2 骨架是 delta 帧（帧同步/丢帧恢复）、AOI 订阅（服务端按视口过滤）、聚合帧（战略视图收编制聚合体而非平台）。
- **上游依赖**：战役层数据模型（编制聚合语义、AOI 概念）。
- **触发条件**：单位规模到数百级，或战役层数据模型定型。
- **形态稳定的先行步（可随时做）**：帧语义整理——静态字段（`name`/`side`/`type`/`platform_type`/`echelon`）拆到一次性 roster 消息，状态帧只发动态量。任何 v2 形态都需要这一步，且当下即可将帧体积减半以上。

### 2. 2D 战术图 WebGL 化

- **现状**：单 Canvas 2D 即时模式全量重绘；当前规模（几十实体、1 km² 矢量）无性能压力。
- **为什么暂缓**：渲染管线骨架取决于战役层渲染需求——聚合军标（符号 atlas + instancing）、控制措施图形（战线/防区/轴线样式管线）、大范围底图（瓦片化）。按战术层需求先做，到战役层需重构一次。
- **上游依赖**：SIDC/编制种子的消费形态（聚合图标集）、控制措施图形集定义。
- **触发条件**：矢量图层显著增长（等高线/传感器覆盖/密集军标）或聚合渲染需求出现。
- **设计原则（届时遵循）**：图层管线与投影解耦（“世界坐标 ↔ 屏幕”变换单点化，现 `toCanvas` 闭包习惯保持），使同一套图层未来可挂地理投影。
- **形态稳定的先行步（可随时做）**：静态矢量层混合渲染——道路/建筑/水系搬进 WebGL（three 正交视图复用 3D 已有几何），动态层留在 Canvas 2D 上层。

### 3. ASGI 迁移（Flask/Werkzeug → FastAPI/uvicorn 等）

- **动机**：开发服务器不适合长期；原生 WebSocket 与二进制帧配合更好。
- **排期**：与状态流 v2 同批（协议与服务器一起换，避免两次迁移）。
- **已铺垫**：会话代码统一走 `socketio.sleep`/`start_background_task` 抽象，线程回收兼容多异步模型。

### 4. 双引擎分层（地理引擎 + 战术 three.js）

- **预判形态**：战略/战役层用地理引擎（Cesium 或 deck.gl globe）渲染聚合态势与全球底图；战术层保留 three.js 局部高保真场景；两层靠 `geodetic_anchor` 契约衔接、靠 SIDC 语义共享。
- **为什么现在不引 Cesium**：当前数据契约是局部 ENU（`local_enu_m`），Cesium 的核心价值（椭球/全球地形流式/影像图层）用不上，反而强加地理坐标复杂度。
- **触发条件**：数据契约升级到全球 CRS（多战区/真实底图需求出现）。

### 5. 2D hillshade GPU 化

- **现状**：太阳角度变更时 CPU 重建整张地形位图（数百 ms 级），一次性变更可接受。
- **触发条件**：光照时间推进上线（环境 Phase B，太阳随仿真时间连续变化）后，每帧/高频重建不可行；届时 2D 明暗走 GPU（WebGL 化顺带解决）或预计算太阳角档位。3D 侧已是实时光照，无此问题。

### 6. store 订阅机制

- **现状**：`vizState` 纯可变对象，状态变更靠调用点手动扇出（如 `applyIllumination` 手动调用两个刷新函数）。
- **触发条件**：环境参数扇出增多（时间/天气/风/传感器覆盖参数化）之前。几十行的轻量 subscribe 即可，不引框架。

### 7. `@ts-check` 渐进推进

- **顺序**：`layers` → `asset-registry` → `scene-geometry` →（大模块）`session`/`ui-shell`/`tactical-map`/`scene3d`。
- **检查命令**：`npx -y -p typescript tsc --noEmit -p examples/viz/web_viz/jsconfig.json`。

## 非目标（明确不做）

- 不在帧语义未整理前做"现有帧形态的二进制化"；
- 不在战术层需求下重写 2D 渲染管线；
- 不在数据契约仍为局部 ENU 时引入 Cesium/全球引擎；
- 前端保持零构建（无 bundler），类型检查停留在编辑器/按需 tsc 层面。

## 交叉引用

- 契约种子测试：`tests/viz/test_strategic_scale_seeds.py`
- 类型化基座：`examples/viz/web_viz/static/js/types.js`、`examples/viz/web_viz/jsconfig.json`
- 光照真值链路：`examples/viz/runtime/illumination.py`、`examples/viz/web_viz/static/js/illumination.js`
- 场景几何契约（锚点所在）：`examples/viz/runtime/scene_geometry.py`
- 编制推断：`examples/viz/runtime/unit_semantics.py`
- SIDC 词汇：`examples/viz/web_viz/static/js/symbology.js`
