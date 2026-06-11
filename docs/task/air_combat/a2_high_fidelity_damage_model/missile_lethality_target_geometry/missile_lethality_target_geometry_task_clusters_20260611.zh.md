# A2 目标几何建模任务簇

状态：`2026-06-12` finite task-cluster plan with TG-P6 mesh-derived review candidate generated，用于
[README.zh.md](README.zh.md)。

英文辅文：[missile_lethality_target_geometry_task_clusters_20260611.md](missile_lethality_target_geometry_task_clusters_20260611.md)。

## 边界决策

本子项目只把 F-16 外形、部件区域和测试点距离变成可审阅事实。第一轮不得改变近炸主路径、
不得通过调高概率绕开几何问题，也不得声明真实 F-16 工程几何、真实弹种杀伤率、结构解体或残骸。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `TG-P0` | main thread | n/a | 建立子项目入口、状态和派发队列 | `docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/**`; parent A2 README; issue pointer | 不实现工具、不改 runtime | markdown links, `git diff --check` | 文档入口完整且父级可导航 | 无依赖 | 1 | pass |
| `TG-P1` | main thread | high | 解析 F-16 glTF，生成来源/轴向/尺度 manifest | `tools/geometry/airframe_geometry_review.py`; `.../review_packets/f16c_20260611/manifest.json`; `tests/tools/test_airframe_geometry_review.py` | 不生成 runtime collision mesh | JSON parse, path existence, public-dimension error check, focused pytest | manifest 记录 GLB/glTF 角色、hash、轴向和尺度 | `TG-P0` 后可执行 | 2 | pass |
| `TG-P2` | main thread | high | 从审计模型生成低精度外壳区域 | `review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json`; `top.svg`; `side.svg`; `front.svg`; focused tests | 不把节点名直接当真实部件 | region count check, bounds inside scaled envelope, SVG smoke | 主要区域可在顶视/侧视/正视中看见 | 依赖 `TG-P1` | 2 | pass |
| `TG-P3` | main thread | high | 绑定现有部件盒到外壳区域并标出异常 | `component_binding_report_20260611.json`; `component_binding_report_20260611.csv`; focused tests | 不重写部件脆弱性概率 | schema check, out-of-envelope report check, focused pytest | 每个现有部件有区域或明确 `needs_review` | 依赖 `TG-P2` | 2 | pass |
| `TG-P4` | main thread | medium | 生成静态 HTML/SVG 审阅包 | `review_packets/f16c_20260611/scene.html`; SVG; README summary | 不接入 web app runtime | file existence, no network dependency, basic HTML asset checks | 可离线查看外形、旧盒、部件和测试点 | 依赖 `TG-P2`/`TG-P3`，与 `TG-P5` 同轮完成 | 2 | pass |
| `TG-P5` | main thread | high | 对 MLF-5 测试点输出外壳/部件距离诊断 | review point JSON/CSV; focused tests | 不重跑真实弹种 Pk | CSV rows include nearest outer distance, nearest component distance, candidate count | 4 m 鼻向样例有具体几何解释 | 依赖 `TG-P2`，与 `TG-P4` 同轮完成 | 2 | pass |
| `TG-P6` | main thread | high | 设计精细几何代理：倾斜盒、凸包或简化外壳网格 | `fine_geometry_proxy_candidate_20260611.json`; `fine_proxy_*.svg`; `fine_proxy_review_dashboard.html`; proxy review notes | 不把高模 GLB 直接当每帧碰撞网格；不改 runtime 主路径 | proxy schema check, mesh silhouette extraction, inflated fallback visibility, dashboard smoke, distance sanity, visual overlay smoke, focused pytest | 说明粗盒子到精细代理的误差、mesh-derived silhouette、适用边界和人工复核项 | 依赖 `TG-P4`/`TG-P5` | 2 | pass as mesh-derived review candidate |
| `TG-P7` | main thread | high | 做运行时接入决策和验收/held 边界 | README/status/acceptance docs; optional design note | 不直接把未审阅代理写入主路径 | doc audit, targeted tests if runtime design is accepted | accepted 或 held 决议写清后续工作 | 依赖 `TG-P6` | 1 | planned |

## 派发规则

- 每个 worker packet 必须只对应上表一个任务簇。
- `TG-P1` 到 `TG-P6` 不得修改父级 README 的状态行；父级同步由 main thread 完成。
- 不允许两个 worker 同时修改同一个 mapping JSON、manifest 或状态文档。
- 任何下载、授权或来源补充都必须写明 source、license、hash 和 retrieval date；不得保存 token、signed URL 或 Authorization header。
- 任何 runtime 接入必须等 `TG-P4`、`TG-P5` 和 `TG-P6` 验收或明确 held 决议后再讨论。

## Worker Packet 要求

每个 worker 返回：

- 修改文件列表；
- 关键假设；
- 验证命令和结果；
- 未解决风险；
- 是否触碰禁止声明；
- 是否需要 main thread 合并或人工审阅。

## 验证计划

- `git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry`
- JSON/schema parse for generated manifest/mapping/review-point files.
- F-16 registry/runtime asset path existence check.
- glTF audit asset path existence check.
- Offline packet smoke: generated HTML/SVG/CSV files exist and reference local assets only.
- Targeted runtime tests only after a later runtime-interface decision.

## 验收标准

- F-16 审阅包能同时显示外形、旧命中盒、部件盒和测试点。
- 诊断表区分本机坐标、外壳表面距离、部件表面距离、是否直接命中和候选部件数。
- 4 m 鼻向贴近外壳样例不再只能解释为“非直接命中，所以无损”。
- 文档继续拒绝真实工程几何、结构解体、残骸、Pk 和具体弹种击毁声明。

## 残余地图

- MQ-9 几何：后续复用，不纳入第一轮 F-16 验收。
- 结构解体和残骸：后续独立子项目。
- Pk 与真实弹种校准：后续独立子项目。
- 运行时主路径替换：依赖人工审阅包和诊断验收。
- 精细几何代理：第一版 F-16 mesh-derived 审阅候选已存在；inflated fallback 区域的人工审阅仍 gate
  `TG-P7`、MQ-9 和其他机型。
