# A2 目标几何建模任务簇

状态：`2026-06-14` finite task-cluster plan with TG-P7-R6 32k opt-in training probe completed，用于
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
| `TG-P6` | main thread | high | 设计精细几何代理，并补外形命中到部件损伤的审阅用表面部件层 | `fine_geometry_proxy_candidate_20260611.json`; `fine_proxy_*.svg`; `fine_proxy_review_dashboard.html`; `surface_component_candidate_20260611.json`; `surface_component_candidate_20260611.csv`; `human_review_triage.html`; `component_review_views/**`; `semantic_damage_geometry_*`; `internal_component_prior_*`; `semantic_parent_child_layout_*`; `cross_region_held_component_segments_*`; `cross_region_ownership_split_candidate_*`; `airframe_constraint_correction_*`; `subcomponent_shape_placement_*`; `subcomponent_latest_promotion_results_20260613.zh.md`; `cross_region_ownership_split_results_20260613.zh.md`; result/status docs; proxy review notes | 不把高模 GLB 直接当每帧碰撞网格；不改 runtime 主路径；不声明真实内部结构 | proxy schema check, mesh silhouette extraction, no bounds-expansion fallback, dashboard smoke, surface component schema check, visual triage smoke, isolated view smoke, semantic/receiver/segment schema checks, ownership split schema checks, subcomponent silhouette checks, focused pytest | 说明粗盒子到精细代理的误差、mesh-derived silhouette、适用边界、表面部件到现有内部部件的候选关系、视觉 triage 卡片、独立部件视图、语义父子布局、held 分段、R21 固化的最新摆放规则、R22 ownership split candidates 和剩余 `TG-P7` acceptance/test 阻塞项 | 依赖 `TG-P4`/`TG-P5` | 22 | pass as review candidate with R22 ownership split candidate |
| `TG-P7` | main thread | high | 做运行时接入决策，只有测试通过后才接入初始训练代理 | `target_geometry_runtime_activation_candidate_20260613.json`; `target_geometry_runtime_activation_candidate_20260613.csv`; `target_geometry_runtime_activation_results_20260613.zh.md`; `target_geometry_runtime_behavior_regression_*`; `target_geometry_training_proxy_database_20260613*`; `target_geometry_training_proxy_results_20260613.zh.md`; `target_geometry_training_probe_results_20260614.zh.md`; `target_geometry_damage_event_trace_20260614.json`; `target_geometry_damage_event_trace_results_20260614.zh.md`; `target_geometry_training_probe_32k_20260614.json`; `target_geometry_training_probe_32k_results_20260614.zh.md`; training bootstrap/train entrypoints; active proxy configs; trace tool/test; README/status/queue docs | 不把未审阅代理写入默认 active main path；默认 unit database 仍是对照路径 | parser/contract checks, focused pytest, C++ loader smoke, packet regeneration, in-memory behavior regression, `runtime.database_path` contract tests, RuntimeFacade proxy database load, local training smoke, active 8k proxy/baseline comparison, targeted damage-event trace, active 32k proxy/baseline comparison | parse-ready patch candidate、in-memory behavior regression、opt-in proxy database、本地 64-step training smoke、active 8k proxy/baseline 对照、全部 `8` 个 split receivers 在 proxy damage-event traces 中可观测，以及 active 32k proxy/baseline 对照完成 | 依赖 `TG-P6` | 6 | pass as opt-in training proxy with targeted trace and 32k comparison |

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
- Targeted runtime tests 必须使用显式 opt-in proxy configs，并保持默认 runtime database 作为对照路径。

## 验收标准

- F-16 审阅包能同时显示外形、旧命中盒、部件盒和测试点。
- 诊断表区分本机坐标、外壳表面距离、部件表面距离、是否直接命中和候选部件数。
- 4 m 鼻向贴近外壳样例不再只能解释为“非直接命中，所以无损”。
- 每个外壳区域都有一个审阅用表面部件候选，并能看到它会牵连哪些现有部件或缺哪些关系。
- 人工复核已有视觉优先的 triage 页面，能按左右符号、部件位置、表面交接和测试点问题查看局部叠加图。
- TG-P7 可以在 separate proxy database、`runtime.database_path` opt-in、proxy
  `32` components、default `26` components、loader/training-entry contracts、本地 proxy smoke
  和 active 8k proxy/baseline 对照均通过，且全部 `8` 个 split receivers 在 targeted proxy
  damage-event traces 中可观测，并且 32k proxy/baseline 对照完成后，进入下游 policy/reward 诊断。
- 文档继续拒绝真实工程几何、结构解体、残骸、Pk 和具体弹种击毁声明。

## 残余地图

- MQ-9 几何：后续复用，不纳入第一轮 F-16 验收。
- 结构解体和残骸：后续独立子项目。
- Pk 与真实弹种校准：后续独立子项目。
- 运行时主路径替换：TG-P7-R6 已有 opt-in proxy database，包含带 feature flag 的
  `damage_model.hitboxes[].components` projection，并且 loader/training-entry contracts、本地 proxy smoke
  和 active 8k proxy/baseline 对照通过，并且全部 `8` 个 split receivers 已有 targeted trace
  覆盖，32k proxy/baseline 对照也已完成；默认 runtime replacement 仍等待下游 policy/reward 诊断和后续 acceptance decision。
  左右符号、缺失 receiver、radar/IFF、nozzle 和翼面位置阻塞已修复。
- 精细几何代理：第一版 F-16 mesh-derived 审阅候选已存在，bounds-expansion fallback 已禁用；
  节点名单、表面部件候选、视觉 triage 卡片、独立部件视图、人工目检结论、subagent 独立评估、
  subagent 修正、几何修复和 R22 跨区 ownership split decisions 仍 gate MQ-9 和其他机型。
