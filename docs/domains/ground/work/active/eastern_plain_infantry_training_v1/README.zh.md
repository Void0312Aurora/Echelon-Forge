# 东部平原风格单兵训练 v1

文档类型：`work-package`  
生命周期：`active`  
Owner：`domains/ground`，环境输入由 `systems/environment` 负责  
状态：`contract-and-source-fixture`

本包先建立一个虚构的农业平原训练场和一个单兵原生 schema，范围限定为
“移动与环境观察”切片，不引入武器使用、目标选择或战斗 runtime。

## 地图范围

地图是东欧农业平原风格的合成样本：大片农田、三条狭长树带、两处小聚落、
一条河、一个桥面和若干农道。它使用美国中部平坦地貌作为非冲突的高程/地表覆盖
类比，几何不指向现实战场。Arnis phase 1 负责冻结
连续米制来源（DEM、地表覆盖、道路、建筑、水系）；当前 Arnis CMO 导出器不会
把农田、树带和聚落锚点自动提升为独立矢量类别，因此另有一个 metadata-only
语义叠加层保存这些来源标签。

叠加层不是导航图，也不是碰撞、通行性、视线、掩体、隐蔽、火控或损伤权威。
这些产品必须由各自 owner 派生，并通过 fail-closed 合同后才能被 runtime 消费。

## 当前产物

- 冻结的 Arnis request 与合成 OSM 输入：
  `tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/eastern_plain_infantry_phase1/`；
- 单兵原生单位定义：
  `examples/config/database/ground/units/ground_infantry_soldier_mvp.json`；
- 训练契约（尚不是 `train.py` 入口）：
  `examples/config/training/active/ground/eastern_plain_infantry_single_v1.contract.json`；
- metadata-only 语义叠加层生成器：
  `tools/environment/arnis/field_overlay.py`。
- 地形组成验收器：`tools/environment/arnis/field_acceptance.py`；当前样本必须先
  通过坡度、开放地表、树覆盖和关键语义数量门槛，才允许进入后续 passability
  派生工作。
- 确定性的契约/代理脚手架：`python/rl/ground/infantry_proxy.py`。它明确标记为
  engineering-proxy-only，不是原生陆战 runtime，也不是 RL 训练入口。
- Gymnasium 契约 harness：`python/rl/ground/proxy_env.py`
  （`GroundInfantryProxyEnv`）。它只验证 RL 的 reset/step/观测/奖励/终止/轨迹边界，
  权威级别仍是 `engineering_proxy_only`。
- maintained 命令投影：`python/rl/ground/command.py`。它把 heading/speed、原生 stance
  和已有 Ground static-task 片段送入批量契约；对于当前原生命令结构无法表达的 route
  字段会直接拒绝，而不是静默丢弃。

代理观测现在包含树带/聚落距离与方位，以及河流/桥面标志；这些仍是可重放的
engineering products。原生 provider 现在准入连续 Arnis 高程/地表覆盖采样、有界河流/桥面
地表以及地形观测 tuple；树线/聚落和 track observation export 仍保持 held。

本次已经用固定 Arnis v3.0.0 CMO patch 实际生成并验证 `expected/` bundle，且
保留了预览和 `field_acceptance.json`。高程与地表覆盖仍来自网络/缓存 provider，
所以这份签入 bundle 是当前证据快照，不等于未来任意时间都能从网络逐字节重建。

## 单兵训练阶梯

1. **S0 契约/重置**：单个具名士兵、固定随机种子、初始观测逐字节一致，并能重放；
2. **S1 平面航路点**：在简单地表上实现确定性 step 和路线进度，不能偷偷穿越河流或
   把 held 语义当作可通行；
3. **S2 地形代价**：坡度、地表类别、农道、河流和桥面通行性成为有 owner/来源的显式产品；
4. **S3 环境观察**：带来源报告树带和聚落，未知值必须显式保留，不引入武器行为；
5. **S4 小组扩展**：单兵重置、step、观察和重放门槛通过后，才加入班组/指挥关系，
   再考虑接入已有陆战损伤切片。

首个 runtime 应是脚本控制器加确定性 step/replay harness。强化学习必须排在
reset、action、observation、reward、termination、replay 契约之后，不能用训练曲线
掩盖缺失的地形语义。

当前原生 runtime 的测量结果和剩余问题记录在
[`native_runtime_blockers.md`](native_runtime_blockers.md)。原生切片现在覆盖一个带
地表/坡度代价的确定性 `MoveStatic` 步，以及显式 Arnis 栅格加载和地形观测；替代方案继续
推进路线/掩体语义和训练阶梯，但不释放一般通行性能力。

## 明确保持 held 的内容

- 自动 Arnis runtime setup 与树线/聚落地图 provider 消费；
- 路网与通行性 mask；
- 坡度、湿地、河流渡越策略；
- 视线、掩体、隐蔽和暴露模型；
- Ground track/sensor observation export（地形采样已单独准入）；
- 疲劳、医疗、后勤、火力、压制和战斗接入。
