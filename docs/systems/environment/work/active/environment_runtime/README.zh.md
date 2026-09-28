# 环境运行时

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/systems/environment/work/active/environment_runtime/README.md`
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
- [公开数据源准入标准](../../../../../research/standards/public_data_source_admission.zh.md)
- [大地坐标系](../../../../physics/work/active/geodetic_frame/README.zh.md)——同级工作包
- 需求案例：[航母打击群对抗](../../../../../domains/naval/work/active/carrier_strike_group_engagement/README.zh.md)
  （海军），以及 `origin/work/army-mechanisms` 上的陆军原生地形线
  （`docs/domains/ground/work/active/ground_arnis_native_terrain_v1/`，未进 `main`）
- [子项目创建标准](../../../../../engineering/automation/rules/subproject_creation_standard.zh.md)
- 代码：`src/core/interfaces/environment_model.h`、`src/models/environment/`、
  `python/scenario/environment_substrate/`、`python/scenario/runtime/kernel_apply.py`

## 目的

离线环境底座已经是共享的跨域契约：一个 manifest，按顺序分层，包括物理基底、地表、水文、
大气与天气、风、光照、海洋、植被、建筑与基础设施。运行时却没有沿用这个模型：它只有一个全局
栅格、一个全局海况，风和太阳都是常量；而唯一的运行时地形线——陆军的原生 Arnis 栅格，位于未合并
分支上——直接把陆军专用的类型和头文件加进了共享接口与实现。

本工作包把分层环境做成唯一的运行时权威，所有域通过与域无关的查询读取。它覆盖陆地、淡水、
海洋与大气，使用同一垂直基准，支持多瓦片、多分辨率，并带有声明的时空变化。它还把陆军的原生
地形运行时迁到这个共享权威上，陆军专属的机动与观测逻辑留在陆军域。

海洋数据的获取是本 owner 之后的另一条线（见[遗留与下一步](#遗留与下一步)）；本包定义这些数据
需要填入的运行时图层与契约。

## 当前状态

| 领域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 离线分层底座 | G0 已接受，在 `main` | `components.py`（`maritime_ocean` 第 38 层、`hydrology` 30、`wind_field` 36、`illumination` 37） | 仅数据契约；无运行时权威 |
| Arnis 陆地/近岸导入 | phase 1 已接受，在 `main` | `tools/environment/arnis/`；`importers/arnis_bundle.py` | OSM + USGS 3DEP + ESA WorldCover；水体只有轮廓和水面高程，没有深度、温度或盐度 |
| 运行时地形 | 一个全局栅格 | `default_environment_model.cpp` 中的 `RasterGrid` | 无多瓦片、无多图层、垂直基准未指定 |
| 陆军原生地形 | 陆军于 `2026-09-24` 接受，**未进 `main`** | `origin/work/army-mechanisms` 提交 `fdbf8ee8`..`986335e3` | 陆军代码位于共享文件内；迁移见下 |
| 海洋状态 | 场景常量，全局 | `set_maritime_state` / `get_maritime_state` | 无风浪/涌浪之分，无空间场 |
| 风、太阳 | 场景常量 | `set_wind`、`set_sun_direction` | 无时钟驱动的昼夜 |
| 海洋数据 | 缺失 | 无 | 无水深、温盐剖面或环境噪声 |

### `origin/work/army-mechanisms` 上的陆军耦合

于 `2026-09-28` 在 `3cee10ff` 测得：

- `src/core/interfaces/environment_model.h` 引入了
  `components/domains/ground/tasking/ground_tasking_enums.h`，并声明了 `get_ground_slope_deg`、
  `load_arnis_terrain_bundle`、`load_arnis_field_overlay`、`get_ground_field_semantic_observation`、
  `get_ground_transition_observation` 与 `get_ground_transition_movement_observation`（最后一个接收
  `GroundStance`）。
- `src/models/environment/default_environment_model.cpp` 引入了
  `systems/domains/ground/movement_effects.h` 并调用
  `ground_infantry_movement_detail::evaluate_movement_effects`。include 方向门
  （`tools/architecture/cpp_include_graph.py`）把这条 `models` → `systems` 边判为不允许，
  该分支也没有登记它。
- `get_terrain_at` 把 `SurfaceType::Water` 当作不可通行，瓦片以外返回 `Obstacle`。两者都是陆军的
  通行语义：舰艇把水当作可航行，陆地瓦片以外的开阔海面也不是障碍。

## 范围

范围内：

- **分层运行时状态**，与底座图层顺序对齐：陆地高程与水深（同一垂直基准）、地表覆盖、淡水与
  海水水体、海岸线与岸线、大气与天气、风、光照、海洋状态；
- **统一垂直基准**，用于陆地高程、水面与水深，每个 bundle 都记录所用基准；
- **多瓦片、多分辨率栅格**，使米级陆地瓦片与公里级海洋网格可以同时查询；边缘与空隙有声明的
  行为，而不是一律判为障碍；
- **与域无关的查询**，只回答某点或某段上环境*是什么*：表面类别、高程、水深、水体类型、坡度、
  地表覆盖、海况、风、能见度、太阳、声学环境数据。能否通行、能否航行、能否隐蔽由各域判断；
- **声明的时空变化**，覆盖天气、风与海况；太阳位置由场景日期、时间与大地锚点驱动；
- **淡水水体作为一等水体**，与海洋共用水体契约：类型（河、湖、水库、海）、水面高程、深度，
  以及可选的流速、盐度、温度字段。本包只填入来源实际提供的值，其余留空并登记遗留项。渡河、
  涉水与架桥行为仍归陆军；
- **作为数据的海洋声学环境**：声速剖面或其温度、盐度、深度输入，混合层深度，海底类别，环境
  噪声。传播物理归 sensing；
- **把陆军原生地形运行时迁到**共享状态与查询上（见阶段计划），陆军专属的机动与观测逻辑迁回陆军域。

范围外：

- 海洋与淡水数据获取（之后的海洋数据线）；
- 天气预报、数值海洋/大气模型、海气耦合动力学、河流水动力模型；
- 任何使用方的物理或决策：舰艇耐波性、飞机着舰限制、声呐传播、雷达杂波、陆军通行性、涉水与
  机动代价；
- 实时真实数据接入。

## 阶段计划

| 阶段 | 目标 | 进入条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 冻结范围与分层运行时契约。 | owner 批准 | README 与任务簇获批 | active |
| `P1 Evidence` | 清点每处环境读取、`main` 上的运行时，以及陆军分支对共享文件的改动。 | `P0` | 每个读取点与每项陆军新增都归为共享、陆军所有或退役 | planned |
| `P2 Contract` | 分层状态、垂直基准、水体契约、瓦片模型、与域无关的查询 API。 | `P1` | 契约成文并有原生测试覆盖 | planned |
| `P3 Implementation` | 多瓦片栅格、水体、海岸线、可变天气与海况、时钟驱动的太阳、声学数据。 | `P2`；太阳位置与瓦片定位需 [大地坐标系](../../../../physics/work/active/geodetic_frame/README.zh.md) `P2-A` 的锚点 | 对照声明输入与参考值的原生与 Python 测试通过 | planned |
| `P4 Migration` | 把陆军原生地形迁到共享运行时；陆军逻辑迁回陆军；其余使用方迁到查询上。 | `P3` | 共享文件不再引入任何域头文件；陆军验收测试重跑通过 | planned |
| `P5 Validation` | 跨域回归与吞吐量。 | `P4` | 空、陆、海测试通过或按记录的量变化 | planned |
| `P6 Closure` | 验收、标准、索引。 | `P5` | 验收记录；运行时契约提升为 environment 标准 | planned |

### 陆军迁移

先在海军分支这条线上完成；与 `origin/work/army-mechanisms` 的冲突在两线合并时解决。

- 共享部分：栅格加载与分瓦片、高程与地表覆盖查询、水体与海岸线查询、由高程算出的原始坡度。
- 陆军所有：依赖 `GroundStance` 的机动效果、通行性、过渡代价、场地语义观测。这些迁到
  `src/systems/domains/ground/` 或 `src/models/domains/ground/`，并基于共享查询实现。
- 从共享接口退役：`get_ground_*` 方法与 `environment_model.h` 中的陆军 include；
  `default_environment_model.cpp` 中不允许的 `models` → `systems` 边。
- 陆军包已接受的测试就是迁移的回归证据；任何变化的结果都要记录，不做重新调参。

## 任务簇

- [environment_runtime_task_clusters_20260928.md](environment_runtime_task_clusters_20260928.md)

## 产出与证据

- 分层运行时环境状态与与域无关的查询接口；
- 垂直基准、瓦片与水体契约；
- 声明环境及其变化的场景 schema；
- 带参考测试的时钟驱动太阳几何；
- 海洋声学环境数据契约；
- 已迁移的陆军地形与重跑的陆军验收测试；
- 跨域回归记录与吞吐量变化；
- 描述运行时契约的 environment 标准。

## 验收门

本工作包只有满足以下全部条件才能标记为 accepted：

- `src/core/interfaces/environment_model.h` 与 `src/models/environment/**` 不引入任何域头文件，
  也不声明任何域专属类型或方法；
- 每个已迁移的使用方都只通过共享查询读取环境；
- 陆地高程、水面与水深共用同一声明的垂直基准，每个 bundle 都记录它；
- 场景可以同时组合陆地瓦片与海洋网格，所有瓦片之外的查询返回声明的结果而不是 `Obstacle`；
- 太阳几何与公开参考值一致；
- 变化在给定种子下确定，并可在回放中复现；
- 陆军已接受的原生地形测试在迁移后的代码上通过，或每个变化的结果都已解释并记录；
- 空、陆、海回归测试通过，或变化已解释；
- 本包内不加入任何使用方物理或域决策。

## 遗留与下一步

- `P0` owner 审阅。
- **海洋数据线**（本 owner，在 `P2 Contract` 之后开启）：从经准入的公开来源导入水深、温盐
  气候态、海况与风、海岸线，并提供带种子的合成海洋生成器，供镜像与虚构场景使用。候选来源只作
  记录，在通过[准入标准](../../../../../research/standards/public_data_source_admission.zh.md)之前不算准入。
- 淡水的深度、流速与温度公开覆盖很少；在有来源准入之前保持留空并登记遗留项，陆军渡河在需要
  时使用水体契约。
- 合成地形生成器与区域/道路派生只存在于 `2026-09-19` 的 WIP 归档
  （`D:/workshop/Research/Echelon-Forge-WIP-archive-20260919-160114/`）；是否恢复是另一项底座决策。
- 时钟驱动的太阳依赖大地锚点；锚点落地前，场景中的太阳声明仍为权威。

## 归档

已接受的记录移至 `docs/systems/environment/reviews/`；运行时契约提升为 environment 标准。
