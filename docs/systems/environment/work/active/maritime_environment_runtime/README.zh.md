# 海洋环境运行时

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/systems/environment/work/active/maritime_environment_runtime/README.md`
Owner: `systems/environment`
Last verified: `2026-09-28`

状态：`2026-09-28` planning。范围与任务簇已起草；`P0 Boundary` 为 active，尚无实现任务簇开工。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

输入：

- [环境系统](../../../README.zh.md)——owner README；其 G0/G1 边界规定运行时工作包须在此处
  以自己的范围开包
- [跨域系统](../../../../README.zh.md)
- [梯度逼真度原则](../../../../standards/gradient_realism_principles.zh.md)
- [大地坐标系](../../../../physics/work/active/geodetic_frame/README.zh.md)——同级工作包
- [航母打击群对抗](../../../../../domains/naval/work/active/carrier_strike_group_engagement/README.zh.md)
  ——首个需求案例
- [子项目创建标准](../../../../../engineering/automation/rules/subproject_creation_standard.zh.md)
- 代码：`src/core/interfaces/environment_model.h`、`src/models/environment/`、
  `python/scenario/runtime/kernel_apply.py`

## 目的

环境模型已经有风、太阳方向和海洋状态（海况、浪向、浪周期），都在场景开始时设一次后保持不变。
使用方各自零散读取：舰艇机动按海况缩放航速，海面雷达加海杂波，光学探测用太阳高度角。

持续数小时、跨越数百公里的场景需要把这些状态变成运行时权威：随时间和空间变化，从一个声明的
来源一致导出，并让所有域通过同一接口读取。这包括飞行甲板作业与着舰限制、水面与水下探测、
舰艇机动。本工作包把海洋与大气环境做成这样的运行时权威。它是跨域基础设施；海军航母编队项目
是首个需求案例，空域与陆军域读取同一状态。

## 当前状态

| 领域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 风 | 场景常量，带切变项 | `set_wind`（`environment_model.h`）；`default_environment_model.cpp` | 空间均匀、时间恒定 |
| 太阳 / 光照 | 场景常量方位与高度角 | `set_sun_direction`；`default_sensor_model.cpp` 光学系数 | 无时钟驱动的昼夜 |
| 海洋状态 | 场景常量 | `set_maritime_state` / `get_maritime_state` | 全世界一个海况；无涌浪与风浪之分 |
| 使用方 | 零散 | `ship_motion_system.h` 海况缩放；海事雷达适配器 | 每个使用方各自做映射 |
| 海洋声学 | 缺失 | 无 | 无声速剖面、跃层深度或环境噪声场 |
| 运行时环境权威 | 本包之前未授权 | [owner README G0/G1 边界](../../../README.zh.md) | 本包只为海洋与大气状态开启它 |

## 范围

范围内：

- 带声明时空变化的运行时环境状态：风、分为风浪与涌浪的海况、能见度与降水衰减，以及由场景
  日期、时间和大地锚点驱动的太阳位置（从而产生昼夜）；
- 作为数据的海洋声学环境：声速剖面、混合层深度、海底深度类别，以及由海况与航运产生的环境
  噪声。使用这些数据的传播物理属于水下探测使用方，不在本包；
- 所有域读取的统一查询接口，并把现有零散使用方迁到它上面；
- 声明环境及其变化的场景 schema，经现有 substrate 与编译器路线校验。

范围外：

- 天气预报、数值海洋或大气模型，以及海气耦合动力学；
- 地形通行性、掩护与地面视线，保留在现有路线上；
- 任何使用方的物理：舰艇耐波性、飞机着舰限制、声呐传播与雷达杂波模型归各自 owner；
- 实时真实数据接入。

## 阶段计划

| 阶段 | 目标 | 进入条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 冻结范围与环境状态契约。 | owner 批准 | README 与任务簇获批 | active |
| `P1 Evidence` | 清点每处环境读取及其零散映射。 | `P0` | 每个使用方完成分类 | planned |
| `P2 Implementation` | 带时空变化的运行时状态；时钟驱动的太阳；声学环境数据。 | `P1`；太阳位置需 [大地坐标系](../../../../physics/work/active/geodetic_frame/README.zh.md) `P2-A` 的大地锚点 | 对照声明输入与公开太阳几何的测试通过 | planned |
| `P3 Integration` | 把使用方迁到查询接口；场景 schema。 | `P2` | 已迁移使用方中不再有零散环境读取 | planned |
| `P4 Validation` | 跨域回归与吞吐量检查。 | `P3` | 空、陆、海测试通过或按记录的量变化 | planned |
| `P5 Closure` | 验收与索引。 | `P4` | 验收记录；契约提升为 environment 标准 | planned |

## 任务簇

- [maritime_environment_runtime_task_clusters_20260928.md](maritime_environment_runtime_task_clusters_20260928.md)

## 产出与证据

- 运行时环境状态与查询接口；
- 声明环境及其变化的场景 schema；
- 带参考测试的时钟驱动太阳几何；
- 海洋声学环境数据契约；
- 跨域回归记录与吞吐量变化；
- 描述运行时契约的 environment 标准。

## 验收门

本工作包只有满足以下全部条件才能标记为 accepted：

- 每个已迁移的使用方都只通过统一查询接口读取环境；
- 太阳几何在测试日期与地点上与公开参考值一致；
- 时空变化由场景声明，在给定种子下确定，并可在回放中复现；
- 空、陆、海回归测试通过，或每个变化的结果都已解释并记录；
- 本包内不加入任何使用方物理。

## 遗留与下一步

- `P0` owner 审阅。
- 时钟驱动的太阳位置依赖大地锚点；在它落地之前，现有场景的太阳声明仍为权威。

## 归档

已接受的记录移至 `docs/systems/environment/reviews/`；运行时契约提升为 environment 标准。
