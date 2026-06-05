# 战术地图界面重构当前状态

状态：`2026-06-06`，`P0` 已通过，尚未开始实现。

父项：[战术地图界面重构](README.zh.md)

## 本检查点变化

- 在 `docs/task/viz` 下创建战术地图界面重构的持久子项目。
- 增加有限任务簇计划，避免未来 UI 工作只依赖聊天中的追加要求。
- 增加现实战术地图、GIS、COP、OSINT 呈现的风格/参考基线，但不声明标准合规。
- 将本子项目挂回 viz 父 README。

## 成熟度矩阵

| 表面 | 状态 | 证据 | 残余 |
| --- | --- | --- | --- |
| 子项目权威 | pass | [README.zh.md](README.zh.md) | 实现开始后需要继续保持当前。 |
| 任务簇 | pass | [任务簇](tactical_map_interface_refactor_task_clusters_20260606.zh.md) | 派发必须保持在有限任务簇和 round cap 内。 |
| 风格/参考基线 | pass | [风格基线](tactical_map_interface_refactor_style_reference_baseline_20260606.zh.md) | 接受 UI 声明前仍需实现证据。 |
| Runtime 壳布局 | planned | [index.html](../../../../examples/viz/web_viz/templates/index.html) | 地图优先重构尚未实现。 |
| 多地图工作区 | planned | 尚无维护中的实现 | 需要 `P2` 实现和浏览器证据。 |
| Profile UI 默认值 | planned/held until needed | [profile_loader.py](../../../../examples/viz/app/profile_loader.py) | 只有 workspace/layer 默认值具体后才添加。 |

## 下一步推荐顺序

1. 执行 `VIZ-TMAP-P1`，重构壳布局，让战术地图保持第一视口主表面。
2. 决定 `VIZ-TMAP-P2` 第一版落 tabbed maps 还是 split-map mode。
3. 在 `VIZ-TMAP-P3` 增加分组图层/符号规则。
4. 只有当 runtime UI 需要稳定持久默认值时，才在 `VIZ-TMAP-P4` 扩展 profile UI 默认值。
5. 在 `VIZ-TMAP-P5` 记录浏览器 smoke、截图和残余。

## 明确拒绝的过度声明

- 本检查点没有实现新的 UI。
- 本检查点没有接受多地图 runtime 工作区。
- 本检查点没有证明军用符号标准合规。
- 本检查点没有释放地形感知机动、LOS、掩蔽、可通行性、天气效果、战斗行为或环境 runtime 变异。
- 本检查点没有改变 scenario/profile 边界。
