# 东部平原风格单兵训练 v1

语言：[英文规范页](README.md)；本页为中文配套。

文档类型：`work-package`  
生命周期：`active`  
Canonical: `docs/domains/ground/work/active/eastern_plain_infantry_training_v1/README.md`  
Owner：`domains/ground`，环境输入由 `systems/environment` 负责  
状态：`native-probe-tooling-and-source-fixture`；生产 `WorldBatch` 仍保持 held

本包先建立一个虚构的农业平原训练场和一个单兵原生 schema，范围限定为
“移动与环境观察”切片；其 RL action contract 不引入武器使用或目标选择。
单独的原生 runtime probe 已覆盖有界直射。

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
  权威级别仍是 `engineering_proxy_only`。其观测空间现在使用已验证 fixture 范围和
  episode 上限的有限边界，并显式提供目标相对向量；reset 遇到未知目标地表时会失败关闭，
  不允许把无界目标偷偷送入训练契约。
- 原生单兵 probe：`python/rl/ground/native_probe.py`，以及其 Gymnasium 适配层
  `python/rl/ground/native_env.py`。它们使用编译后的 kernel 做 reset/step/replay，
  权威级别是 `native_probe_only`，仍不属于生产 `WorldBatch`；观测包含 native owner 的
  movement-effect 倍率，trace 会区分航点/失能
  终止与 `max_steps`、`blocked_step_limit` 截断。
  它调用的 kernel 方法绑定在独立的 Ground native-probe 面
  （`bindings_core_kernel_diagnostics_ground.cpp`），不属于维护中的 `SimulationKernel` API。
  WP22-E 守卫的约束有三条：该面必须恰好等于具名白名单；每个名字只注册一次；维护面上
  不允许出现任何名称含 Ground/Arnis 的绑定。
  固定航点预检现在为每段同时保留通行性和 native 采样移动效果十元组，作为地形代价证据；
  这仍不是路线图或路径规划器。

  Gym observation space 现在使用来自已验证 bundle manifest 和有限 episode horizon 的
  有限边界；自定义 bundle 无法读取 manifest 时使用明确标注的有限 horizon fallback。
  这只改善空间契约，不改变 `native_probe_only` 权威边界。
  native Gym action 现在是 heading、speed、stance 三维归一化向量，`route_intent=direct`
  作为固定元数据，不再占用一个虚假的 action 维度；原生 probe 仍兼容旧四字段输入。
- maintained 命令投影：`python/rl/ground/command.py`。它把 heading/speed、原生 stance
  和已有 Ground static-task 片段送入批量契约；对于当前原生命令结构无法表达的 route
  字段会直接拒绝，而不是静默丢弃。`OccupyStatic` 和 `SupportStatic` 作为有界的
  原生位置保持命令被明确消费，会保持单兵位置和零速度；这不等同于掩体、隐蔽、感知
  或火控语义。

  原生 probe 还可以选择生成一个固定敌方接触，并通过带授权的任务命令触发一次步枪
  射击，记录伤害状态、弹药和冷却变化。该入口仍是 `native_probe_only` 的命令/武器验收，
  不提供目标选择、视线、掩体、压制、弹道或学习型火力策略。

代理观测现在包含树带/聚落距离与方位，以及河流/桥面标志；这些仍是可重放的
engineering products。原生 provider 现在准入连续 Arnis 高程/地表覆盖采样、有界河流/桥面
地表以及地形观测 tuple；树线/聚落和 track observation export 仍保持 held。
engineering proxy 现在可以仅基于声明的桥面 overlay 生成可重放航点折线，用于路线契约测试；
它仍是 `engineering_proxy_only`，不是 native 路线图或通用通行性产品。

本次已经用固定 Arnis v3.0.0 CMO patch 实际生成并验证 `expected/` bundle，且
保留了预览和 `field_acceptance.json`。高程与地表覆盖仍来自网络/缓存 provider，
所以这份签入 bundle 是当前证据快照，不等于未来任意时间都能从网络逐字节重建。

## 单兵训练阶梯

1. **S0 契约/重置**：单个具名士兵、固定随机种子、初始观测逐字节一致，并能重放；
2. **S1 平面航路点**：在简单地表上实现确定性 step 和路线进度，不能偷偷穿越河流或
   把 held 语义当作可通行；
3. **S2 地形代价**：坡度、地表类别、农道、河流和桥面通行性成为有 owner/来源的显式产品；
4. **S3 环境观察**：带来源报告树带和聚落，未知值必须显式保留；RL contract 不暴露
   单独的原生直射 probe；
5. **S4 小组扩展**：单兵重置、step、观察和重放门槛通过后，才加入班组/指挥关系，
   再考虑接入已有陆战损伤切片。

首个 runtime 应是脚本控制器加确定性 step/replay harness。强化学习必须排在
reset、action、observation、reward、termination、replay 契约之后，不能用训练曲线
掩盖缺失的地形语义。

当前原生 runtime 的测量结果和剩余问题记录在
[`native_runtime_blockers.md`](native_runtime_blockers.md)。原生切片现在覆盖一个带
地表/坡度/植被代价的确定性 `MoveStatic` 步、显式 Arnis 栅格加载、有限河流/桥面过渡、
地形观测和固定直接航路点序列 native Gym 适配；航点递进只是预先配置序列的进度记录，
不是路线图或路径规划。替代方案继续推进路线/掩体语义，但不释放一般通行性能力。

当前验收还包括一个实际的桥面跨越步：单兵从河流一侧沿声明桥面前进到另一侧，
原生位置发生跨河移动，同时保留局部采样倍率和 `bridge_admitted` 证据。该测试只证明
已声明桥面上的局部过渡，不证明自动找桥、路线规划或一般渡河能力。

## 明确保持 held 的内容

- 自动 Arnis runtime setup 与树线/聚落地图 provider 消费；
- 路网与通行性 mask；
- 一般化坡度/湿地策略和路线级河流渡越规划（局部坡度代价与采样河流/桥面过渡已准入）；
- 视线、掩体、隐蔽和暴露模型；
- Ground track/sensor observation export（地形采样已单独准入）；
- 疲劳、医疗、后勤、间接火力、压制和完整战斗接入。
