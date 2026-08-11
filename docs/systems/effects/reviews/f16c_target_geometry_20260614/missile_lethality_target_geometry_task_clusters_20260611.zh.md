# A2 目标几何建模任务簇

状态：`2026-06-14` accepted / closed geometry task-cluster record。TG-P1 至 TG-P6 满足 F-16C
geometry-only closeout；TG-P7-R1 至 R6 作为下游 handoff evidence 保留，不再作为本子项目闭合门。用于
[README.zh.md](README.zh.md)。

英文辅文：[missile_lethality_target_geometry_task_clusters_20260611.md](missile_lethality_target_geometry_task_clusters_20260611.md)。

## 边界决策

本子项目只把 F-16 外形、部件区域和测试点距离变成可审阅事实。第一轮不得改变近炸主路径、
不得通过调高概率绕开几何问题，也不得声明真实 F-16 工程几何、真实弹种杀伤率、结构解体或残骸。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `TG-P0` | main thread | n/a | 建立子项目入口、状态和派发队列 | `docs/systems/effects/reviews/f16c_target_geometry_20260614/**`; parent A2 README; issue pointer | 不实现工具、不改 runtime | markdown links, `git diff --check` | 文档入口完整且父级可导航 | 无依赖 | 1 | pass |
| `TG-P1` | main thread | high | 解析 F-16 glTF，生成来源/轴向/尺度 manifest | `tools/geometry/airframe_geometry_review.py`; `.../review_packets/f16c_20260611/manifest.json`; `tests/tools/test_airframe_geometry_review.py` | 不生成 runtime collision mesh | JSON parse, path existence, public-dimension error check, focused pytest | manifest 记录 GLB/glTF 角色、hash、轴向和尺度 | `TG-P0` 后可执行 | 2 | pass |
| `TG-P2` | main thread | high | 从审计模型生成低精度外壳区域 | `review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json`; 已退役草图三视图 SVG；focused tests | 不把节点名直接当真实部件 | region count check, bounds inside scaled envelope, SVG smoke | 主要区域可在顶视/侧视/正视中看见 | 依赖 `TG-P1` | 2 | pass |
| `TG-P3` | main thread | high | 绑定现有部件盒到外壳区域并标出异常 | `component_binding_report_20260611.json`; `component_binding_report_20260611.csv`; focused tests | 不重写部件脆弱性概率 | schema check, out-of-envelope report check, focused pytest | 每个现有部件有区域或明确 `needs_review` | 依赖 `TG-P2` | 2 | pass |
| `TG-P4` | main thread | medium | 生成静态 HTML/SVG 审阅包 | `review_packets/f16c_20260611/scene.html`; 已退役草图 SVG; README summary | 不接入 web app runtime | file existence, no network dependency, basic HTML asset checks | 可离线查看；当前包现在只链接最终 projected mesh contour 结果 | 依赖 `TG-P2`/`TG-P3`，与 `TG-P5` 同轮完成 | 2 | pass |
| `TG-P5` | main thread | high | 对 MLF-5 测试点输出外壳/部件距离诊断 | review point JSON/CSV; focused tests | 不重跑真实弹种 Pk | CSV rows include nearest outer distance, nearest component distance, candidate count | 4 m 鼻向样例有具体几何解释 | 依赖 `TG-P2`，与 `TG-P4` 同轮完成 | 2 | pass |
| `TG-P6` | main thread | high | 设计精细几何代理，并补外形命中到部件损伤的审阅用表面部件层 | `fine_geometry_proxy_candidate_20260611.json`; 已退役中间可视化 dashboard/SVG；`surface_component_candidate_20260611.json`; `surface_component_candidate_20260611.csv`; semantic/internal/parent-child/segment/ownership/placement 候选数据；`whole_airframe_contour_containment_20260614.*`; `whole_airframe_contour_dashboard.html`; result/status docs; proxy review notes | 不把高模 GLB 直接当每帧碰撞网格；不改 runtime 主路径；不声明真实内部结构 | proxy schema check, mesh silhouette extraction, no bounds-expansion fallback, dashboard smoke, surface component schema check, visual triage smoke, semantic/receiver/segment schema checks, ownership split schema checks, subcomponent silhouette checks, whole-airframe contour containment check, focused pytest | 粗盒子到精细代理的误差、mesh-derived silhouette、适用边界、表面部件到现有内部部件的候选关系、语义父子布局、held 分段、R21 固化的最新摆放规则、R22 ownership split candidates 和最终 projected mesh contour follow-up queue 已记录，可支撑 geometry-only closeout | 依赖 `TG-P4`/`TG-P5` | 22 | accepted for F-16C fine-geometry proxy |
| `TG-P7` | main thread | high | 形成下游 opt-in runtime/training handoff evidence | `target_geometry_runtime_activation_candidate_20260613.json`; `target_geometry_runtime_activation_candidate_20260613.csv`; `target_geometry_runtime_activation_results_20260613.zh.md`; `target_geometry_runtime_behavior_regression_*`; `target_geometry_training_proxy_database_20260613*`; `target_geometry_training_proxy_results_20260613.zh.md`; `target_geometry_training_probe_results_20260614.zh.md`; `target_geometry_damage_event_trace_20260614.json`; `target_geometry_damage_event_trace_results_20260614.zh.md`; `target_geometry_training_probe_32k_20260614.json`; `target_geometry_training_probe_32k_results_20260614.zh.md`; training bootstrap/train entrypoints; active proxy configs; trace tool/test; README/status/queue docs | 不把代理写入默认 active main path；不把训练对照或 trace 作为几何闭合门；默认 unit database 仍是对照路径 | parser/contract checks, focused pytest, C++ loader smoke, packet regeneration, in-memory behavior regression, `runtime.database_path` contract tests, RuntimeFacade proxy database load, local training smoke, active 8k proxy/baseline comparison, targeted damage-event trace, active 32k proxy/baseline comparison | opt-in proxy database、trace 和同预算训练对照可作为后续独立验收输入 | 依赖 `TG-P6` | 6 | retained handoff evidence; not a geometry closure gate |

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

- `git diff --check -- docs/systems/effects/reviews/f16c_target_geometry_20260614`
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
- 语义父子布局、跨区 held 分段、R22 split receiver candidates、整机 silhouette 约束和子部件摆放修正已经形成可追溯交接证据。
- TG-P7 opt-in proxy database、damage-event trace 和 32k proxy/baseline training probe 只作为下游 handoff evidence 保留；它们不再作为本子项目闭合门。
- 文档继续拒绝真实工程几何、结构解体、残骸、Pk 和具体弹种击毁声明。

## 残余地图

- MQ-9 几何：后续复用，不纳入第一轮 F-16 验收。
- 结构解体和残骸：后续独立子项目。
- Pk 与真实弹种校准：后续独立子项目。
- 运行时主路径替换：后续独立验收决策，不属于本几何子项目闭合门。TG-P7-R6 已有 opt-in proxy database，包含带 feature flag 的
  `damage_model.hitboxes[].components` projection，并且 loader/training-entry contracts、本地 proxy smoke
  和 active 8k proxy/baseline 对照通过，并且全部 `8` 个 split receivers 已有 targeted trace
  覆盖，32k proxy/baseline 对照也已完成；默认 runtime replacement 仍等待下游 policy/reward 诊断和后续 acceptance decision。
  左右符号、缺失 receiver、radar/IFF、nozzle 和翼面位置阻塞已修复。
- 精细几何代理：F-16C geometry-only closeout 已验收；节点名单、表面部件候选、视觉 triage 卡片、人工目检结论、subagent 独立评估、subagent 修正、几何修复、R22 跨区 ownership split decisions 和最终投影网格轮廓 follow-up queue 可作为 MQ-9 和其他机型后续复用输入，但不在本包继续展开。
