# 战术地图界面重构 P6 Closure And Archive Sync

状态：`2026-06-06`，`VIZ-TMAP-P6` 已关闭。当前 scoped 的战术地图界面重构已接受并闭合。

父项：[战术地图界面重构](README.zh.md)

英文规范页：
[tactical_map_interface_refactor_p6_closure_archive_sync_20260606.md](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.md)

## 决策

`VIZ-TMAP-P6` 接受为 closure/archive 同步切片。`P5` 验证汇总之后，当前 README、
当前状态、任务簇、派发队列、父级 viz README 和 archive 指针已经一致表明：本次 scoped
战术地图界面重构为 `closed`。

这里的 closed 指“已接受的工作加上 index/archive/documentation 同步已经完成”。它不意味着所有未来战术可视化想法都已完成。

## 收口时接受范围

- `P0`：子项目权威和风格/参考基线已建立。
- `P1`：地图优先壳布局已接受。
- `P2`：第一版 tabbed 地图工作区模型已接受。
- `P3`：分组战术图层控制和第一版符号模型已接受。
- `P4`：profile workspace/layer UI 默认值已接受。
- `P5`：验证证据、截图、残余和能力边界已汇总。
- `P6`：父级/子项目状态和 archive 指针已同步。

## 已同步索引

更新后的当前权威表面：

- [README.md](README.md) 和 [README.zh.md](README.zh.md)
- [当前状态](tactical_map_interface_refactor_current_status_20260606.md)
  和
  [当前状态 zh](tactical_map_interface_refactor_current_status_20260606.zh.md)
- [任务簇](tactical_map_interface_refactor_task_clusters_20260606.md)
  和
  [任务簇 zh](tactical_map_interface_refactor_task_clusters_20260606.zh.md)
- [派发队列](tactical_map_interface_refactor_dispatch_queue_20260606.md)
  和
  [派发队列 zh](tactical_map_interface_refactor_dispatch_queue_20260606.zh.md)
- 父级 [viz README](../README.md) 和
  [viz README zh](../README.zh.md)
- [archive README](archive/README.md) 和
  [archive README zh](archive/README.zh.md)

没有本地证据文件被移动到 `archive/`。当前 dated acceptance 和 closure 文档仍是本 closed
子项目的 live evidence。archive 保留给未来被取代的本地记录。

## 验证

收口验证：

```bash
git diff --check -- docs/task/viz
```

`2026-06-06` 观察结果：通过。

Runtime 证据仍是
[P5 验证汇总](tactical_map_interface_refactor_p5_validation_rollup_20260606.zh.md)
整理的 `P1` 到 `P4` 浏览器和回归证据。`P6` 本身只改变文档和索引状态。

## 剩余后续工作

未来工作应开启新的任务簇或子项目，而不是重新打开这个已闭合切片。已知后续方向包括：

- 环境基底接受道路、建筑、植被、天气或其他 derived products 后，再增加更丰富的环境战术图层；
- 如果单模板 catalog 变得过大，再考虑 tactical symbol registry 抽取；
- 如果后续工作流证明 split-map 布局必要且不会破坏地图优先人体工学，再重新评估 split-map。

## 仍然禁止的声明

本次收口仍不接受：

- scenario 编辑或地形生成器 UI；
- 地形感知机动、可通行性、LOS、遮蔽/隐蔽、感知、火力、毁伤、奖励、终止或环境 runtime 行为；
- MIL-STD-2525、APP-6 或其他军用符号标准合规；
- 通过 profile UI defaults 改写 scenario 真实性/世界参数。
