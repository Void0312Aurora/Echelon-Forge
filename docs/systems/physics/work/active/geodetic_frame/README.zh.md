# 大地坐标系

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/systems/physics/work/active/geodetic_frame/README.md`
Owner: `systems/physics`
Last verified: `2026-09-28`

状态：`2026-09-28` active。`P0 Boundary` 已于 `2026-09-28` 获 owner 接受；`P1-A` 盘点已开始。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

输入：

- [跨域系统](../../../../README.zh.md)
- [梯度逼真度原则](../../../../standards/gradient_realism_principles.zh.md)
- [物理引擎升级路线图](../../issues/physics_engine_roadmap.md)（草稿规划输入）
- [航母打击群对抗](../../../../../domains/naval/work/active/carrier_strike_group_engagement/README.zh.md)
  ——首个需求案例
- [子项目创建标准](../../../../../engineering/automation/rules/subproject_creation_standard.zh.md)
- 代码：`src/components/basic/common.h`（`Transform`）、`src/components/systems/navigation.h`、
  `src/components/physics/instruments.h`、`src/components/systems/sensor.h`、
  `src/models/systems/default_sensor_model.cpp`

## 目的

运行时把所有实体放在相对场景原点的平面局部东-北-天坐标系中（`src/components/basic/common.h`
里的 `Transform`）。对当前空、陆、海场景几十公里的范围这已足够。航母打击群场景跨越数百公里，
在这个尺度上地球曲率会改变雷达与无线电地平线、传感器视线、大圆航行、导弹射程和数据链覆盖。
目前经纬度只作为 EGI/导航字段存在。

本工作包为整个仿真提供统一的大地坐标系：明确的地球模型、局部仿真坐标与大地坐标之间的
确定关系，以及各域共用的曲率几何查询。它是跨域基础设施；海军航母编队项目是首个需求案例，
任何域都不拥有该坐标系。

## 当前状态

| 领域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 仿真坐标系 | 平面局部 ENU | `Transform`（`src/components/basic/common.h`） | 无地球模型、无曲率 |
| 大地坐标字段 | 仅导航用 | `navigation.h`、`instruments.h` 中的 `lat_deg`/`lon_deg` | 不是坐标系权威；没有 ENU 与大地坐标的换算 |
| 雷达地平线 | 单传感器代理开关 | `sensor.h` 中的 `enforce_radar_horizon`，在 `default_sensor_model.cpp` 中使用 | 仅海面雷达代理；不是共享几何 |
| 地形视线 | 环境模型 | `IEnvironmentModel::check_line_of_sight` | 只考虑地形，无地球凸起 |

## 范围

范围内：

- 明确的地球模型：先用球形地球，并写明升级到 WGS-84 椭球几何的路径；地球模型作为场景输入记录；
- 局部仿真坐标与大地坐标的关系：场景大地锚点、双向换算，以及局部坐标在距锚点给定距离处的
  声明误差上限；
- 曲率几何查询：几何地平线与考虑折射的地平线距离、地球凸起遮挡视线、大圆距离与方位；
- 把现有雷达地平线代理迁移到共享查询上；
- 回归证据：空、陆、海场景结果不变，或只按已记录的、由曲率造成的量变化。

范围外：

- 标准等效地球半径系数之外的大气折射；异常波导仍归 sensing 与 environment；
- 地形高程模型与大地水准面起伏；
- 把实体运动积分改为大地坐标状态；除非后续另有决定，运动仍在局部坐标系中进行；
- 任何域对这些查询的具体使用，由各使用方 owner 自行完成。

## 阶段计划

| 阶段 | 目标 | 进入条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 冻结范围、地球模型选择与坐标契约。 | owner 批准 | README 与任务簇获批 | accepted |
| `P1 Evidence` | 清点所有假设平面坐标或自行计算地平线的位置。 | `P0` | 每处归为必须迁移、可保留或范围外 | active |
| `P2 Implementation` | 地球模型、锚点、换算、几何查询。 | `P1` | 原生与 Python 测试对照参考值通过 | planned |
| `P3 Integration` | 把探测地平线与视线迁到查询上；在场景中暴露锚点。 | `P2` | 使用方调用共享查询；代理开关退役或被包装 | planned |
| `P4 Validation` | 跨域回归与吞吐量检查。 | `P3` | 空、陆、海测试通过或按记录的量变化 | planned |
| `P5 Closure` | 验收与索引。 | `P4` | 验收记录；长期契约提升为 physics 标准 | planned |

## 任务簇

- [geodetic_frame_task_clusters_20260928.md](geodetic_frame_task_clusters_20260928.md)

## 产出与证据

- 地球模型与坐标组件，以及场景级大地锚点；
- 供 sensing 使用的共享几何查询 API；
- 附来源的参考值测试（地平线距离、大圆距离）；
- 跨域回归记录与吞吐量变化；
- 描述坐标契约的 physics 标准。

## 验收门

本工作包只有满足以下全部条件才能标记为 accepted：

- 地球模型、锚点与双向换算都有对照公开参考值的测试；
- `P1` 归为必须迁移的每个使用方都调用共享查询；
- 空、陆、海回归测试通过，或每个变化的结果都能由曲率解释并已记录；
- 局部坐标误差上限已成文，并对场景范围强制执行；
- 本包内不加入任何域专属行为。

## 遗留与下一步

- `P0` owner 审阅。
- 椭球（WGS-84）几何规划为球形模型之后的第二步；哪些场景需要它在 `P1` 中决定。
- 运动本身是否要改为大地坐标状态不在范围内；若 `P4` 显示局部坐标不够用，需另行决策。

## 归档

已接受的记录移至 `docs/systems/physics/reviews/`；坐标契约提升为 physics 标准。
